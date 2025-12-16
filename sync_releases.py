import glob
import os
import ssl

import requests

from gitee_release import Gitee, get_environment_variable, set_action_output


# GitHub Releases API 基础 URL
GITHUB_RELEASES_API_BASE_URL = "https://api.github.com/repos"
# Gitee Releases API 基础 URL
GITEE_RELEASES_API_BASE_URL = "https://gitee.com/api/v5/repos"

# 禁用 SSL 警告和验证
requests.packages.urllib3.disable_warnings()
ssl._create_default_https_context = ssl._create_unverified_context

# 从环境变量获取调试模式设置，默认关闭
debug_mode = get_environment_variable('debug', False)
# 从环境变量获取 Gitee 访问令牌
gitee_access_token = get_environment_variable('gitee_token')


def fetch_github_releases(owner, repository):
    """
    获取 GitHub 仓库的所有 Release 信息
    
    Args:
        owner (str): GitHub 仓库所有者
        repository (str): GitHub 仓库名称
    
    Returns:
        tuple: (releases_data, request_url)
               - releases_data (list): Release 数据列表
               - request_url (str): 请求的 URL
    """
    request_url = f'{GITHUB_RELEASES_API_BASE_URL}/{owner}/{repository}/releases'
    response = requests.get(request_url, verify=False)
    
    if debug_mode:
        print(f'请求 {request_url} , 返回数据: {response.text}')
        
    return response.json(), request_url


def fetch_gitee_releases(owner, repository):
    """
    获取 Gitee 仓库的所有 Release 信息
    
    Args:
        owner (str): Gitee 仓库所有者
        repository (str): Gitee 仓库名称
    
    Returns:
        tuple: (releases_dict, request_url)
               - releases_dict (dict): 以 tag_name 为键的 Release 字典
               - request_url (str): 请求的 URL
    """
    request_url = f'{GITEE_RELEASES_API_BASE_URL}/{owner}/{repository}/releases'
    response = requests.get(request_url, verify=False, data={'access_token': gitee_access_token})
    
    if debug_mode:
        print(f'请求 {request_url} , 返回数据: {response.text}')
        
    response_json = response.json()
    # 构建以 tag_name 为键的字典
    releases_dict = {release_item['tag_name']: release_item for release_item in response_json}
    return releases_dict, request_url


def fetch_github_release_details(owner, repository, release_id):
    """
    获取 GitHub 特定 Release 的详细信息
    
    Args:
        owner (str): GitHub 仓库所有者
        repository (str): GitHub 仓库名称
        release_id (int): Release ID
    
    Returns:
        tuple: (release_info, assets_dict, request_url)
               - release_info (dict): Release 详细信息
               - assets_dict (dict): 以文件名为键的附件字典
               - request_url (str): 请求的 URL
    """
    request_url = f'{GITHUB_RELEASES_API_BASE_URL}/{owner}/{repository}/releases/{release_id}'
    response = requests.get(request_url, verify=False)
    
    if debug_mode:
        print(f'请求 {request_url} , 返回数据: {response.text}')
        
    release_info = response.json()
    # 构建以文件名为键的附件字典
    assets_dict = {asset['name']: asset for asset in release_info['assets']} if 'assets' in release_info and len(release_info['assets']) > 0 else {}
    return release_info, assets_dict, request_url


def upload_release_assets(asset_files, gitee_client, gitee_repository, gitee_release_id):
    """
    上传附件到 Gitee Release
    
    Args:
        asset_files (list): 待上传的文件路径列表
        gitee_client (Gitee): Gitee 客户端实例
        gitee_repository (str): Gitee 仓库名称
        gitee_release_id (str): Gitee Release ID
    
    Returns:
        list: 上传成功的文件下载链接列表
    
    Raises:
        ValueError: 当文件路径模式不匹配任何文件时抛出
        Exception: 当文件上传失败时抛出
    """
    upload_results = []
    uploaded_file_paths = set()
    
    for file_path_pattern in asset_files:
        file_path_pattern = file_path_pattern.strip()
        # 检查是否使用递归匹配
        is_recursive = True if "**" in file_path_pattern else False
        matched_files = glob.glob(file_path_pattern, recursive=is_recursive)
        
        if len(matched_files) == 0:
            raise ValueError('文件路径模式未匹配到任何文件: ' + file_path_pattern)
            
        for file_path in matched_files:
            # 跳过已上传的文件和目录
            if file_path in uploaded_file_paths or os.path.isdir(file_path):
                continue
            
            # 上传单个文件
            success, message = gitee_client.upload_asset(
                gitee_repository, 
                gitee_release_id,
                file_name=os.path.basename(file_path), 
                file_path=file_path
            )
            
            if not success:
                raise Exception("上传文件附件失败: " + message)
                
            upload_results.append(message)
            uploaded_file_paths.add(file_path)
            
    return upload_results


def create_gitee_release(gitee_owner, gitee_token, gitee_repository, 
                         release_tag_name, release_name, release_body, target_commitish):
    """
    在 Gitee 上创建新的 Release
    
    Args:
        gitee_owner (str): Gitee 仓库所有者
        gitee_token (str): Gitee 访问令牌
        gitee_repository (str): Gitee 仓库名称
        release_tag_name (str): Release 标签名
        release_name (str): Release 名称
        release_body (str): Release 描述
        target_commitish (str): 目标提交标识
    
    Returns:
        str or None: 创建成功的 Release ID，失败则返回 None
    """
    gitee_client = Gitee(owner=gitee_owner, token=gitee_token)
    success, release_id = gitee_client.create_release(
        repo=gitee_repository, 
        tag_name=release_tag_name, 
        name=release_name,
        body=release_body, 
        target_commitish=target_commitish
    )
    
    if success:
        print(f'创建 Release 成功，Release ID 为 {release_id}')
        set_action_output("release-id", release_id)
        return release_id
    else:
        print("创建 Release 失败: " + release_id)
        return None


def download_file_from_url(url, local_directory, filename):
    """
    从 URL 下载文件到本地
    
    Args:
        url (str): 文件下载地址
        local_directory (str): 本地存储目录
        filename (str): 保存的文件名
    
    Returns:
        str or None: 下载成功返回文件路径，失败返回 None
    """
    try:
        # 构建完整的本地目录路径
        full_directory_path = os.path.join(os.getcwd(), local_directory)
        
        # 如果目录不存在则创建
        if not os.path.exists(full_directory_path):
            os.mkdir(full_directory_path)
            
        # 构建完整的文件路径
        full_file_path = os.path.join(full_directory_path, filename)
        print(f"准备从 {url} 下载文件到 {full_file_path}")
        
        # 发送 GET 请求，使用流式下载
        response = requests.get(url, stream=True, verify=False)
        
        # 检查响应状态码
        if response.status_code == 200:
            # 打开本地文件进行写入
            with open(full_file_path, 'wb') as file_handle:
                # 分块读取文件内容，每次读取 1KB
                for data_chunk in response.iter_content(chunk_size=1024):
                    if data_chunk:  # 确保有数据可写入
                        file_handle.write(data_chunk)  # 将数据块写入本地文件
                        file_handle.flush()  # 刷新缓冲区，确保数据写入磁盘
            print(f'文件 {filename} 下载完成！')
            return full_file_path
        else:
            print('下载失败，状态码：', response.status_code)
    except requests.exceptions.RequestException as e:  # 处理网络连接问题和其他HTTP请求错误
        print('请求错误：', str(e))
    except FileNotFoundError as e:  # 处理文件写入错误
        print('文件写入错误：', str(e))
    return None


def sync_github_releases_to_gitee():
    """
    同步 GitHub Release 到 Gitee
    该函数会读取环境变量中的配置信息，获取 GitHub 和 Gitee 的仓库信息，
    然后将 GitHub 的 Release 同步到 Gitee
    """
    # 从环境变量获取配置信息
    gitee_owner = get_environment_variable('gitee_owner')
    gitee_token = get_environment_variable('gitee_token')
    gitee_repo = get_environment_variable('gitee_repo')
    github_owner = get_environment_variable('github_owner')
    github_repo = get_environment_variable('github_repo')
    
    # 验证必要配置是否存在
    if gitee_owner is None:
        raise ValueError('gitee_owner 未设置')
    if gitee_repo is None:
        raise ValueError('gitee_repo 未设置')
    if github_owner is None:
        raise ValueError('github_owner 未设置')
    if github_repo is None:
        raise ValueError('github_repo 未设置')
    if gitee_token is None:
        raise ValueError('gitee_token 未设置')
        
    # 调试模式下打印配置信息（部分隐藏 token）
    if debug_mode:
        print(f'gitee_owner : {gitee_owner}')
        print(f'gitee_repo : {gitee_repo}')
        print(f'github_owner : {github_owner}')
        print(f'github_repo : {github_repo}')
        print(f'gitee_token : {gitee_token[0:9] + len(gitee_token[9:]) * "*"}')
        
    # 获取 Gitee 和 GitHub 的 Release 信息
    gitee_releases, gitee_request_url = fetch_gitee_releases(gitee_owner, gitee_repo)
    github_releases, github_request_url = fetch_github_releases(github_owner, github_repo)
    
    # 创建 Gitee 客户端实例
    gitee_client = Gitee(gitee_owner, gitee_token)
    
    # 遍历 GitHub 的每个 Release
    for github_release in github_releases:
        # 跳过没有 tag_name 的 Release
        if 'tag_name' not in github_release:
            continue
            
        release_tag_name = github_release['tag_name']
        print(f'准备同步 {github_request_url} , 标签为 {release_tag_name}')
        
        github_release_id = github_release['id']
        # 获取 GitHub Release 的详细信息和附件
        github_release_info, github_release_assets, github_release_url = fetch_github_release_details(
            github_owner, github_repo, github_release_id)
            
        # 如果 Gitee 上已存在相同标签的 Release，则只同步附件
        if release_tag_name in gitee_releases:
            sync_release_assets_only(
                gitee_client, github_release_assets, release_tag_name, 
                gitee_releases[release_tag_name], gitee_repo)
            continue
            
        print(f'成功获取 GitHub Release URL {github_release_url} , 标签为 {github_release_info["tag_name"]}')
        
        # 在 Gitee 上创建新的 Release
        gitee_release_id = create_gitee_release(
            gitee_owner, gitee_token, gitee_repo, release_tag_name,
            github_release['name'],
            github_release['body'],
            github_release['target_commitish'])
            
        # 如果创建成功，则同步附件
        if gitee_release_id is not None:
            new_release_info = {"assets": [], 'id': gitee_release_id}
            sync_release_assets_only(
                gitee_client, github_release_assets, release_tag_name, 
                new_release_info, gitee_repo)


def sync_release_assets_only(gitee_client, github_release_assets, release_tag_name, gitee_release_info, gitee_repo):
    """
    同步 Release 的附件文件
    
    Args:
        gitee_client (Gitee): Gitee 客户端实例
        github_release_assets (dict): GitHub Release 附件字典
        release_tag_name (str): Release 标签名
        gitee_release_info (dict): Gitee Release 信息
        gitee_repo (str): Gitee 仓库名称
    """
    # 构建 Gitee Release 附件字典
    gitee_release_assets = {
        asset['name']: asset for asset in gitee_release_info['assets']
    } if 'assets' in gitee_release_info else {}
    
    # 遍历 GitHub Release 的每个附件
    for github_asset_filename in github_release_assets:
        # 如果 Gitee 上已存在同名附件，则跳过
        if github_asset_filename in gitee_release_assets:
            continue
            
        github_asset_info = github_release_assets[github_asset_filename]
        download_url = github_asset_info['browser_download_url']
        
        # 跳过没有下载链接的附件
        if download_url is None:
            continue
            
        # 从 GitHub 下载附件
        downloaded_file_path = download_file_from_url(
            download_url, f'{release_tag_name}', github_asset_filename)
            
        # 如果下载失败则跳过
        if downloaded_file_path is None:
            continue
            
        # 上传附件到 Gitee Release
        upload_result = upload_release_assets(
            [downloaded_file_path], gitee_client, gitee_repo, gitee_release_info['id'])
        set_action_output("download-url", upload_result)


if __name__ == '__main__':
    sync_github_releases_to_gitee()
