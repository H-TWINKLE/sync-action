# action-sync-release

在gitee项目同步github release信息和附件

**请务必先新建gitee仓库/与github一致的分支**

## 示例

### 同步github release信息和附件

```
- name: Test sync github release
  id: create_release
  uses: h-twinkle/sync-action@v1.0
  with:
    gitee_owner: gitee用户名
    gitee_repo: gitee项目名
    gitee_token: ${{ secrets.gitee_token }}
    github_owner: github用户名
    github_repo: github项目名
    gitee_upload_retry_times:  3
```

- `gitee_owner`：gitee 用户名, 项目URL中可获取
- `gitee_repo`：gitee 项目名, 项目URL中可获取
- `gitee_token`：gitee api token
- `github_owner`：github 用户名, 项目URL中可获取
- `github_repo`：github 项目名, 项目URL中可获取
- `gitee_upload_retry_times`：上传附件失败后的尝试次数。默认为0，不再尝试。
- 注意：Token需要以 [Secrets](https://docs.github.com/cn/actions/reference/encrypted-secrets) 方式给出，以保证token不被泄露

