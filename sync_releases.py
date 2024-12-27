import glob
import os
import ssl

import requests

from gitee_release import Gitee, get, set_result

# https://gitee.com/api/v5/repos/dromara/mayfly-go/releases/
# https://api.github.com/repos/rustdesk/rustdesk/releases

GITHUB_RELEASES_URL = "https://api.github.com/repos"
GITEEE_RELEASES_URL = "https://gitee.com/api/v5/repos"

requests.packages.urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

_debug = get('debug', False)
_token = get('gitee_token')


def get_releases_by_github(owner, repo):
    _url = f'{GITHUB_RELEASES_URL}/{owner}/{repo}/releases'
    r = requests.get(_url, verify=False)
    if _debug:
        print(f'request {_url} , data: {r.text}')
    return r.json(), _url


def get_releases_by_gitee(owner, repo):
    """获取所有的tag"""
    _url = f'{GITEEE_RELEASES_URL}/{owner}/{repo}/releases'
    r = requests.get(_url, verify=False, data={'access_token': _token})
    if _debug:
        print(f'request {_url} , data: {r.text}')
    _json = r.json()
    return {_['tag_name']: _ for _ in _json}, _url


def get_release_by_github(owner, repo, release_id):
    _url = f'{GITHUB_RELEASES_URL}/{owner}/{repo}/releases/{release_id}'
    req = requests.get(f'{GITHUB_RELEASES_URL}/{owner}/{repo}/releases/{release_id}', verify=False)
    if _debug:
        print(f'request {_url} , data: {req.text}')
    _j = req.json()
    return (_j,
            {_['name']: _ for _ in _j['assets']} if 'assets' in _j and len(_j['assets']) > 0 else {},
            _url)


def upload_assets(gitee_files, gitee_client, gitee_repo, gitee_release_id):
    result = []
    uploaded_path = set()
    for file_path_pattern in gitee_files:
        file_path_pattern = file_path_pattern.strip()
        recursive = True if "**" in file_path_pattern else False
        files = glob.glob(file_path_pattern, recursive=recursive)
        if len(files) == 0:
            raise ValueError('file_path_pattern does not match: ' + file_path_pattern)
        for file_path in files:
            if file_path in uploaded_path or os.path.isdir(file_path):
                continue
            success, msg = gitee_client.upload_asset(gitee_repo, gitee_release_id,
                                                     file_name=os.path.basename(file_path), file_path=file_path)
            if not success:
                raise Exception("Upload file asset failed: " + msg)
            result.append(msg)
            uploaded_path.add(file_path)
    return result


def create_gitee_release(gitee_owner,
                         gitee_token,
                         gitee_repo,
                         gitee_tag_name,
                         gitee_release_name,
                         gitee_release_body,
                         gitee_target_commitish):
    gitee_client = Gitee(owner=gitee_owner, token=gitee_token)
    success, release_id = gitee_client.create_release(repo=gitee_repo, tag_name=gitee_tag_name, name=gitee_release_name,
                                                      body=gitee_release_body, target_commitish=gitee_target_commitish)
    if success:
        print(f'create releases success , release_id is {release_id}')
        set_result("release-id", release_id)
        return release_id
    else:
        print("create release failed: " + release_id)
        return None


def download_file(url, _path, _name):
    try:
        _p_path = os.path.join(os.getcwd(), _path)
        if not os.path.exists(_p_path):
            os.mkdir(_p_path)
        _file_path = os.path.join(_p_path, _name)
        print(f"prepare to download file {_file_path} from {url}")
        response = requests.get(url, stream=True, verify=False)  # 发送GET请求，stream参数指定以流的方式下载文件
        if response.status_code == 200:  # 检查响应状态码
            with open(_file_path, 'wb') as f:  # 打开本地文件进行写入操作
                for chunk in response.iter_content(chunk_size=1024):  # 分块读取文件内容，每次读取1KB
                    if chunk:  # 检查是否有数据块可读
                        f.write(chunk)  # 将数据块写入本地文件
                        f.flush()  # 刷新缓冲区，确保数据写入磁盘
            print(f'文件 {_name} 下载完成！')
            return _file_path
        else:
            print('下载失败，状态码：', response.status_code)
    except requests.exceptions.RequestException as e:  # 处理网络连接问题和其他HTTP请求错误
        print('请求错误：', str(e))
    except FileNotFoundError as e:  # 处理文件写入错误
        print('文件写入错误：', str(e))
    return None


def sync_releases():
    gitee_owner = get('gitee_owner')
    gitee_token = get('gitee_token')
    gitee_repo = get('gitee_repo')
    github_owner = get('github_owner')
    github_repo = get('github_repo')
    if gitee_owner is None:
        raise ValueError('gitee_owner not exists')
    if gitee_repo is None:
        raise ValueError('gitee_repo not exists')
    if github_owner is None:
        raise ValueError('github_owner not exists')
    if github_repo is None:
        raise ValueError('github_repo not exists')
    if gitee_token is None:
        raise ValueError('gitee_token not exists')
    if _debug:
        print(f'gitee_owner : {gitee_owner}')
        print(f'gitee_repo : {gitee_repo}')
        print(f'github_owner : {github_owner}')
        print(f'github_repo : {github_repo}')
        print(f'gitee_token : {gitee_token[0:9] + len(gitee_token[9:]) * "*"}')
    gitee_releases, _tee_url = get_releases_by_gitee(gitee_owner, gitee_repo)
    github_releases, _hub_url = get_releases_by_github(github_owner, github_repo)
    _gitee = Gitee(gitee_owner, gitee_token)
    for hub_release in github_releases:
        if 'tag_name' not in hub_release:
            continue
        _tag_name = hub_release['tag_name']
        print(f'prepare to sync {_hub_url} , tag is {_tag_name}')
        _id = hub_release['id']
        _hub_release_info, _hub_release_assets, hub_release_url = get_release_by_github(github_owner, github_repo, _id)
        # 存在这个tag说明信息存在，就只需要再同步文件就行
        if _tag_name in gitee_releases:
            gitee_exist_release(_gitee, _hub_release_assets, _tag_name, gitee_releases[_tag_name], gitee_repo)
            continue
        print(f'success get github release url {hub_release_url} , tag is {_hub_release_info["tag_name"]}')
        _tee_release_id = create_gitee_release(gitee_owner, gitee_token, gitee_repo, _tag_name,
                                               hub_release['name'],
                                               hub_release['body'],
                                               hub_release['target_commitish'])
        if _tee_release_id is not None:
            _new_releases = {"assets": [], 'id': _tee_release_id}
            gitee_exist_release(_gitee, _hub_release_assets, _tag_name, _new_releases, gitee_repo)


def gitee_exist_release(_gitee, _hub_release_assets, _tag_name, _gitee_info, gitee_repo):
    """存在这个tag说明信息存在，就只需要再同步文件就行"""
    _gitee_assets = {_['name']: _ for _ in _gitee_info['assets']} if 'assets' in _gitee_info else {}
    for _hub_release_assets_name in _hub_release_assets:
        if _hub_release_assets_name in _gitee_assets:
            continue
        _hub_assets_info = _hub_release_assets[_hub_release_assets_name]
        _down_load_url = _hub_assets_info['browser_download_url']
        if _down_load_url is None:
            continue
        _download_file = download_file(_down_load_url, f'{_tag_name}', _hub_release_assets_name)
        if _download_file is None:
            continue
        # 上传文件
        upload_result = upload_assets([_download_file], _gitee, gitee_repo, _gitee_info['id'])
        set_result("download-url", upload_result)


if __name__ == '__main__':
    sync_releases()
