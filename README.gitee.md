# action-gitee-release

在Gitee项目发布release(可以上传附件)

## 示例

### 仅创建release
```
- name: Test create release
  id: create_release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_tag_name: v1.0.0
    gitee_release_name: Test v1.0.0
    gitee_release_body: Release 描述
    gitee_target_commitish: master
```

### 创建release，并上传单个附件
```
- name: Test create release
  id: create_release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_tag_name: v1.0.0
    gitee_release_name: Test v1.0.0
    gitee_release_body: Release 描述
    gitee_target_commitish: master
    gitee_upload_retry_times:  3
    gitee_file_name: 文件名称
    gitee_file_path: 文件本地路径
```

### 创建release，并上传多个附件
```
- name: Test create release
  id: create_release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_tag_name: v1.0.0
    gitee_release_name: Test v1.0.0
    gitee_release_body: Release 描述
    gitee_target_commitish: master
    gitee_upload_retry_times:  3
    gitee_files: |
        文件路径1
        文件路径2
```


### 上传单个附件到现有项目
```
- name: Test create release
  id: create_release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_tag_name: v1.0.0
    gitee_release_name: Test v1.0.0
    gitee_release_body: Release 描述
    gitee_target_commitish: master
    gitee_upload_retry_times:  3
      
- name: Test upload file to exist release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_release_id: ${{ steps.create_release.outputs.release-id }}
    gitee_file_name: 文件名称1
    gitee_file_path: 文件本地路径1
    gitee_upload_retry_times:  3
```

### 上传多个附件到现有项目
```
- name: Test create release
  id: create_release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_tag_name: v1.0.0
    gitee_release_name: Test v1.0.0
    gitee_release_body: Release 描述
    gitee_target_commitish: master

      
- name: Test upload file to exist release
  uses: nicennnnnnnlee/action-gitee-release@v1.0.5
  with:
    gitee_owner: Gitee用户名
    gitee_repo: Gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    gitee_release_id: ${{ steps.create_release.outputs.release-id }}
    gitee_upload_retry_times:  3
    gitee_files: |
        文件路径1
        文件路径2
```


- `gitee_owner`：Gitee 用户名, 项目URL中可获取
- `gitee_repo`：Gitee 项目名, 项目URL中可获取
- `gitee_token`：Gitee api token
- `gitee_tag_name`：Gitee Tag 名称, 提倡以v字母为前缀做为Release名称，例如v1.0或者v2.3.4
- `gitee_release_name`：Gitee release 名称
- `gitee_release_body`：Gitee release 描述
- `gitee_target_commitish`：Gitee 分支名称或者commit SHA
- `gitee_files`：上传的附件列表(多个文件)。此处的文件路径支持规则匹配，参考[python-glob](https://docs.python.org/zh-cn/dev/library/glob.html)
- `gitee_file_name`：上传的附件名称(单个文件)
- `gitee_file_path`：上传的附件的本地路径(单个文件)
- `gitee_release_id`：上传附件对应的release的id。该值存在的话，不会再去尝试创建release。
- `gitee_upload_retry_times`：上传附件失败后的尝试次数。默认为0，不再尝试。
- 注意：Token需要以 [Secrets](https://docs.github.com/cn/actions/reference/encrypted-secrets) 方式给出，以保证token不被泄露

# GitHub Release 同步到 Gitee

将 GitHub 项目的 Release 信息（包括附件）自动同步到 Gitee 项目。

## 使用示例

### 同步 GitHub Release 到 Gitee

```yaml
- name: Sync GitHub Release to Gitee
  uses: h-twinkle/sync-action@v1.0
  with:
    gitee_owner: your-gitee-username
    gitee_repo: your-gitee-repo
    gitee_token: ${{ secrets.GITEE_TOKEN }}
    github_owner: your-github-username
    github_repo: your-github-repo
    gitee_upload_retry_times: 3
    debug: false
```

## 参数说明

| 参数                         | 必填 | 描述                                     |
|----------------------------|----|----------------------------------------|
| `gitee_owner`              | 是  | Gitee 用户名，在项目 URL 中可获取                 |
| `gitee_repo`               | 是  | Gitee 项目名，在项目 URL 中可获取                 |
| `gitee_token`              | 是  | Gitee API Token，建议通过 GitHub Secrets 配置 |
| `github_owner`             | 是  | GitHub 用户名，在项目 URL 中可获取                |
| `github_repo`              | 是  | GitHub 项目名，在项目 URL 中可获取                |
| `gitee_upload_retry_times` | 否  | 上传附件失败后的重试次数，默认为 0 不重试                 |
| `debug`                    | 否  | 是否开启调试模式，显示更多日志信息，默认为 false            |

## 输出参数

| 输出             | 描述               |
|----------------|------------------|
| `release-id`   | 创建的 Release 的 ID |
| `download-url` | 附件的下载地址          |

## 使用前提

1. 在 Gitee 上创建与 GitHub 同名的仓库
2. 在 Gitee 上生成 Personal Access Token
3. 在 GitHub 项目的 Settings > Secrets 中添加 GITEE_TOKEN

## 注意事项

- Token 需要以 [Secrets](https://docs.github.com/cn/actions/reference/encrypted-secrets) 方式配置，避免 Token 泄露
- 同步操作会检查 Gitee 上是否已存在相同 tag 的 Release，如果存在则只同步附件
- 如果 Release 没有描述信息，会尝试从对应 commit 中获取 commit message 作为描述
## 贡献
本仓库基于[H-TWINKLE/sync-action](https://github.com/H-TWINKLE/sync-action)进行构建
感谢开源社区的支持