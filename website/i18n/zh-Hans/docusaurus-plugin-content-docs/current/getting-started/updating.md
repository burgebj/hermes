---
sidebar_position: 3
title: "更新与卸载"
description: "如何将 Hermes Agent 更新到最新版本或卸载它"
---

# 更新与卸载

## 更新

使用单个命令更新到最新版本：

```bash
hermes update
```

此命令会拉取最新代码、更新依赖，并提示你配置自上次更新后新增的选项。

:::tip
`hermes update` 会自动检测新配置项并提示你添加。如果你错过了该提示，可以手动运行 `hermes config check` 查看缺失的选项，然后运行 `hermes config migrate` 交互式添加它们。
:::

### 更新期间会发生什么

运行 `hermes update` 时，会执行以下步骤：

1. **配对数据快照** — 在更新前保存轻量级的状态快照（覆盖 `~/.hermes/pairing/`、飞书评论规则以及其他运行时会修改的状态文件）。可通过[快照与回滚](../user-guide/checkpoints-and-rollback.md)章节描述的恢复流程恢复，或通过 Hermes 在 `~/.hermes/` 目录旁写入的最新快速快照 zip 文件进行提取。
2. **Git 拉取** — 从 `main` 分支拉取最新代码并更新子模块。
3. **依赖安装** — 运行 `uv pip install -e ".[all]"` 以获取新的或变更的依赖。
4. **配置迁移** — 检测自你当前版本起新增的配置项并提示你设置。
5. **网关自动重启** — 更新完成后会刷新正在运行的网关，使新代码立即生效。系统服务管理的网关（Linux 上的 systemd、macOS 上的 launchd）会通过服务管理器重启。手动启动的网关在 Hermes 能够将运行的 PID 映射回配置文件时会自动重新启动。

### 仅预览：`hermes update --check`

想在实际拉取之前先了解自己是否落后于 `origin/main`？运行 `hermes update --check` — 它会抓取远程信息，侧边打印本地提交与最新远程提交的对比，并在同步时退出码为 `0`，落后时为 `1`。此过程不修改文件，也不重启网关，适合在脚本和 cron 任务中用作 “是否有更新” 的判断。

### 完整的更新前备份：`--backup`

对于高价值的配置（生产网关、团队共享安装），可以在拉取前对整个 `HERMES_HOME`（配置、认证、会话、技能、配对数据）做完整备份：

```bash
hermes update --backup
```

或者将其设为每次运行的默认行为：

```yaml
# ~/.hermes/config.yaml
updates:
  pre_update_backup: true
```

`--backup` 在早期版本中是默认开启的，但在大型主目录上会导致更新耗时数分钟，因此现在改为可选。上述轻量级的配对数据快照仍然会无条件执行。

预期的输出示例：

```
$ hermes update
Updating Hermes Agent...
📥 Pulling latest code...
Already up to date.  (or: Updating abc1234..def5678)
📦 Updating dependencies...
✅ Dependencies updated
🔍 Checking for new config options...
✅ Config is up to date  (or: Found 2 new options — running migration...)
🔄 Restarting gateways...
✅ Gateway restarted
✅ Hermes Agent updated successfully!
```

### 推荐的更新后验证

`hermes update` 已处理大部分更新流程，但进行一次快速验证可以确保一切顺利：

1. `git status --short` — 若工作树出现意外脏文件，请在继续前检查原因。
2. `hermes doctor` — 检查配置、依赖和服务健康状态。
3. `hermes --version` — 确认版本已如预期提升。
4. 若使用网关：`hermes gateway status`
5. 若 `doctor` 报告 npm audit 问题：在对应目录下运行 `npm audit fix`

:::warning Dirty working tree after update
如果在 `hermes update` 后 `git status --short` 显示意外的更改，请停止并检查这些更改再继续。这通常意味着本地修改被重新应用在更新的代码上，或依赖步骤重新生成了 lock 文件。
:::

### 当终端在更新途中断开连接时

`hermes update` 已对意外的终端掉线做了保护：

- 更新会忽略 `SIGHUP`，因此关闭 SSH 会话或终端窗口不再导致更新中途被杀死。`pip` 与 `git` 子进程会继承此保护，防止因掉线导致环境半装。
- 所有输出会同步写入 `~/.hermes/logs/update.log`。如果终端消失，重新登录后查看日志即可判断更新是否完成以及网关重启是否成功：

```bash
tail -f ~/.hermes/logs/update.log
```

- `Ctrl‑C`（SIGINT）和系统关机（SIGTERM）仍然会被尊重——这些是有意的取消操作。

因此你不再需要借助 `screen` 或 `tmux` 来确保更新过程的持续性。

### 检查当前版本

```bash
hermes version
```

可与最新发布版本进行对比，最新发布页位于 [GitHub releases 页面](https://github.com/NousResearch/hermes-agent/releases)。

### 从即时通讯平台更新

你也可以直接在 Telegram、Discord、Slack、WhatsApp、Teams 等平台发送以下指令进行更新：

```
/update
```

这会拉取最新代码、更新依赖并重启正在运行的网关。更新期间机器人会短暂离线（通常 5–15 秒），随后恢复。

### 手动更新

如果你是手动安装（而非使用快速安装脚本），可按下列步骤自行更新：

```bash
cd /path/to/hermes-agent
export VIRTUAL_ENV="$(pwd)/venv"

# 拉取最新代码
git pull origin main

# 重新安装（获取新依赖）
uv pip install -e ".[all]"

# 检查新配置项
hermes config check
hermes config migrate   # 交互式添加缺失的选项
```

### 回滚说明

若更新后出现问题，可回滚到先前的版本：

```bash
cd /path/to/hermes-agent

# 查看最近的提交记录
git log --oneline -10

# 回滚到指定提交
git checkout <commit-hash>
git submodule update --init --recursive
uv pip install -e ".[all]"

# 若网关在运行，重启它
hermes gateway restart
```

要回滚到特定的发布标签：

```bash
git checkout v0.6.0
git submodule update --init --recursive
uv pip install -e ".[all]"
```

:::warning
回滚可能导致配置不兼容（因为新选项已被加入）。回滚后运行 `hermes config check`，若出现未识别的选项，请在 `config.yaml` 中移除它们以避免错误。
:::

### 对 Nix 用户的提示

如果通过 Nix flake 安装，更新由 Nix 包管理器管理：

```bash
# 更新 flake 输入
nix flake update hermes-agent

# 或者直接使用最新的构建
nix profile upgrade hermes-agent
```

Nix 安装是不可变的，回滚由 Nix 的 generation 系统处理：

```bash
nix profile rollback
```

更多细节请参阅 [Nix Setup](./nix-setup.md)。

---

## 卸载

```bash
hermes uninstall
```

卸载程序会询问是否保留配置文件 (`~/.hermes/`) 供以后重新安装使用。

### 手动卸载

```bash
rm -f ~/.local/bin/hermes
rm -rf /path/to/hermes-agent
rm -rf ~/.hermes            # 如无重新安装计划，可选执行此步骤
```

:::info
如果你将网关作为系统服务安装，请先停止并禁用它：
```bash
hermes gateway stop
# Linux: systemctl --user disable hermes-gateway
# macOS: launchctl remove ai.hermes.gateway
```
:::
