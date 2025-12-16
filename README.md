# GitHub Release 同步到 Gitee

将 GitHub 项目的 Release 信息（包括附件）自动同步到 Gitee 项目。

**使用前请确保已在 Gitee 上创建了与 GitHub 同名的仓库及分支**

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

## 工作流程说明

此 Action 会执行以下操作：

1. 获取 GitHub 仓库的所有 Release 信息
2. 获取 Gitee 仓库的所有 Release 信息
3. 对比两个仓库的 Release：
   - 如果 Gitee 上不存在某个 GitHub Release，则创建新 Release
   - 如果 Gitee 上已存在相同 tag 的 Release，则只同步附件
4. 下载 GitHub Release 的附件
5. 上传附件到 Gitee Release

## 注意事项

- Token 需要以 [Secrets](https://docs.github.com/cn/actions/reference/encrypted-secrets) 方式配置，避免 Token 泄露
- 同步操作会检查 Gitee 上是否已存在相同 tag 的 Release，如果存在则只同步附件
- 如果 Release 没有描述信息，会尝试从对应 commit 中获取 commit message 作为描述
- 上传失败时可根据 `gitee_upload_retry_times` 参数进行重试

## 贡献
本仓库基于[H-TWINKLE/sync-action](https://github.com/H-TWINKLE/sync-action)进行构建
感谢开源社区的支持