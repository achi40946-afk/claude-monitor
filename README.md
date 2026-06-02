# Claude Status Monitor

实时监控 Anthropic/Claude 服务状态，状态变化时通过 ntfy 推送通知到手机。

数据来源：[status.claude.com](https://status.claude.com) 官方状态页。

## 工作原理

```
GitHub Actions (每2分钟) → 拉取 status.claude.com API → 状态变化? → ntfy 推送到 iPhone/Android
```

- 完全免费，无需服务器
- 无需注册账号（ntfy 匿名订阅）
- 电脑关了也照常运行

## 快速部署（5 分钟）

### 1. Fork 本仓库

右上角点 Fork，仓库名随意。

### 2. 手机安装 ntfy

- iPhone: App Store 搜 **ntfy** 
- Android: Google Play 搜 **ntfy**

打开后点 **+ → Add subscription**，Topic 填一个只有你知道的名字（比如 `你的名字-claude-status`）。

### 3. 设置 GitHub Secret

在 Fork 后的仓库中：

`Settings → Secrets and variables → Actions → New repository secret`

| Name | Value |
|------|-------|
| `NTFY_TOPIC` | 你在第 2 步填的那个 topic 名 |

### 4. 启用 Actions

`Actions` 标签 → 点 `I understand my workflows, go ahead and enable them`

然后手动触发一次测试：

`Actions → Claude Status Monitor → Run workflow → Run workflow`

手机上应该会收到一条测试通知。

## 监控范围

- claude.ai（网页版）
- Claude API（api.anthropic.com）
- Claude Code（CLI）
- Claude Console / Cowork / Government

## 本地运行

```bash
pip install -r requirements.txt
python monitor.py
```

本地运行需要设置环境变量 `NTFY_TOPIC`。

## License

MIT
