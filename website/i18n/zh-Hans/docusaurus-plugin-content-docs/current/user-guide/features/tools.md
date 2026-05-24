---
sidebar_position: 1
title: "工具 & 工具集"
description: "Hermes Agent 的工具概览 — 可用工具、工具集工作方式以及终端后端"
---

# 工具 & 工具集

工具是扩展代理能力的函数。它们被组织为逻辑上的 **工具集**，可在不同平台上启用或禁用。

## 可用工具

Hermes 自带了丰富的内置工具注册表，涵盖网页搜索、浏览器自动化、终端执行、文件编辑、记忆、任务委派、强化学习训练、消息投递、Home Assistant 等。

:::note
**Honcho 跨会话记忆** 作为记忆提供者插件（`plugins/memory/honcho/`）提供，而非内置工具集。请参阅 [插件](./plugins.md) 了解安装方法。
:::

高级分类如下：

| 类别 | 示例 | 描述 |
|------|------|------|
| **Web** | `web_search`, `web_extract` | 在网页上搜索并提取页面内容。 |
| **终端 & 文件** | `terminal`, `process`, `read_file`, `patch` | 执行命令并操作文件。 |
| **浏览器** | `browser_navigate`, `browser_snapshot`, `browser_vision` | 交互式浏览器自动化，支持文本和视觉。 |
| **多媒体** | `vision_analyze`, `image_generate`, `text_to_speech` | 多模态分析与生成。 |
| **代理编排** | `todo`, `clarify`, `execute_code`, `delegate_task` | 规划、澄清、代码执行以及子代理委派。 |
| **记忆 & 检索** | `memory`, `session_search` | 持久记忆与会话搜索。 |
| **自动化 & 投递** | `cronjob`, `send_message` | 支持创建/列出/更新/暂停/恢复/运行/删除的定时任务，以及外发消息投递。 |
| **集成** | `ha_*`, MCP 服务器工具, `rl_*` | Home Assistant、MCP、强化学习训练及其他集成。 |

欲获取权威的代码派生注册表，请参阅 [内置工具参考](/docs/reference/tools-reference) 与 [工具集参考](/docs/reference/toolsets-reference)。

:::tip Nous Tool Gateway
付费的 [Nous Portal](https://portal.nousresearch.com) 订阅用户可以通过 **[工具网关](tool-gateway.md)** 使用网页搜索、图像生成、文本转语音和浏览器自动化——无需单独的 API Key。运行 `hermes model` 启用，或使用 `hermes tools` 配置单独工具。
:::

## 使用工具集

```bash
# 使用特定工具集
hermes chat --toolsets "web,terminal"

# 查看所有可用工具
hermes tools

# 交互式配置平台工具（交互式）
hermes tools
```

常用工具集包括 `web`, `search`, `terminal`, `file`, `browser`, `vision`, `image_gen`, `moa`, `skills`, `tts`, `todo`, `memory`, `session_search`, `cronjob`, `code_execution`, `delegation`, `clarify`, `homeassistant`, `messaging`, `spotify`, `discord`, `discord_admin`, `debugging`, `safe`, `rl` 等。

完整列表请参见 [工具集参考](/docs/reference/toolsets-reference)，其中包括平台预设如 `hermes-cli`, `hermes-telegram`，以及动态 MCP 工具集 `mcp-<server>`。

## 终端后端

终端工具可以在不同环境中执行命令：

| 后端 | 描述 | 适用场景 |
|------|------|----------|
| `local` | 在本机运行（默认） | 开发、可信任务 |
| `docker` | 隔离容器 | 安全、可复现 |
| `ssh` | 远程服务器 | 沙箱化、避免代理直接修改自身代码 |
| `singularity` | HPC 容器 | 集群计算、无特权 |
| `modal` | 云端执行 | 无服务器、弹性伸缩 |
| `daytona` | 云端沙箱工作区 | 持久远程开发环境 |
| `vercel_sandbox` | Vercel Sandbox 云微VM | 带快照文件系统持久化的云执行 |

### 配置

```yaml
# 位于 ~/.hermes/config.yaml
terminal:
  backend: local    # 或: docker, ssh, singularity, modal, daytona, vercel_sandbox
  cwd: "."          # 工作目录
  timeout: 180      # 命令超时时间（秒）
```

### Docker 后端

```yaml
terminal:
  backend: docker
  docker_image: python:3.11-slim
```

**单一持久容器，整个进程共享**。Hermes 在首次使用时启动一个长期运行的容器（`docker run -d … sleep 2h`），随后所有终端、文件、`execute_code` 调用都通过 `docker exec` 进入同一容器。工作目录切换、已安装的包、写入 `/workspace` 的文件都会在后续调用中保留，跨 `/new`, `/reset` 与 `delegate_task` 子代理均保持。进程关闭时容器会被停止并删除。

这意味着 Docker 后端的行为类似持久化的沙箱 VM，而不是每条指令都重新创建容器。若 `pip install foo` 一次，后续就可以直接使用；若 `cd /workspace/project`，随后的 `ls` 能看到该目录。完整生命周期请参考 [配置 → Docker 后端](../configuration.md#docker-backend) 与控制容器持久性的 `container_persistent` 标志。

### SSH 后端

建议用于安全——代理无法修改自身代码：

```yaml
terminal:
  backend: ssh
```

```bash
# 在 ~/.hermes/.env 中设置凭证
TERMINAL_SSH_HOST=my-server.example.com
TERMINAL_SSH_USER=myuser
TERMINAL_SSH_KEY=~/.ssh/id_rsa
```

### Singularity/Apptainer

```bash
# 为并行工作者预构建 SIF
apptainer build ~/python.sif docker://python:3.11-slim

# 配置
hermes config set terminal.backend singularity
hermes config set terminal.singularity_image ~/python.sif
```

### Modal（无服务器云）

```bash
uv pip install modal
modal setup
hermes config set terminal.backend modal
```

### Vercel Sandbox

```bash
pip install 'hermes-agent[vercel]'
hermes config set terminal.backend vercel_sandbox
hermes config set terminal.vercel_runtime node24
```

需要同时设置 `VERCEL_TOKEN`、`VERCEL_PROJECT_ID` 与 `VERCEL_TEAM_ID`。此方式是 Render、Railway、Docker 等托管环境中部署及长时间运行 Hermes 进程的官方支持路径。支持的运行时包括 `node24`, `node22`, `python3.13`；Hermes 默认将远程工作空间根目录设为 `/vercel/sandbox`。

在本地快速开发时，Hermes 也接受短期的 Vercel OIDC 令牌：

```bash
VERCEL_OIDC_TOKEN="$(vc project token <project-name>)" hermes chat
```

在已关联的 Vercel 项目目录下：

```bash
VERCEL_OIDC_TOKEN="$(vc project token)" hermes chat
```

开启 `container_persistent: true` 时，Vercel 快照会在同一任务的沙箱重建之间保留文件系统状态，可包括 Hermes 同步的凭证、技能与缓存文件。快照不保留活跃进程、PID 空间或相同的沙箱身份。

后台终端命令仍遵循通用的非本地进程流程：生成、轮询、等待、记录、终止，使用普通 `process` 工具，但 Vercel 并未提供沙箱外的分离进程恢复能力。

请保持 `container_disk` 为默认 `51200`；自定义磁盘大小在 Vercel Sandbox 上不受支持，若设置会导致诊断/后端创建失败。

### 容器资源

为所有容器后端统一配置 CPU、内存、磁盘与持久化选项：

```yaml
terminal:
  backend: docker  # 或 singularity, modal, daytona, vercel_sandbox
  container_cpu: 1              # CPU 核数（默认 1）
  container_memory: 5120        # 内存（MB，默认 5GB）
  container_disk: 51200         # 磁盘（MB，默认 50GB）
  container_persistent: true    # 跨会话持久文件系统（默认 true）
```

启用 `container_persistent: true` 后，已安装的依赖、生成的文件与配置将在会话之间保存。

### 容器安全

所有容器后端均进行安全加固：

- 只读根文件系统（Docker）
- 丢弃所有 Linux 能力
- 禁止提权
- 限制 PID 数量（256 个进程）
- 完全的命名空间隔离
- 通过挂载卷实现持久工作区，而非可写根层

Docker 可通过 `terminal.docker_forward_env` 明确转发环境变量列表，但转发的变量对容器内的所有命令可见，请视为已暴露。

## 后台进程管理

启动后台进程并进行管理：

```python
terminal(command="pytest -v tests/", background=true)
# 返回: {"session_id": "proc_abc123", "pid": 12345}

# 使用 process 工具进行管理：
process(action="list")       # 列出所有运行中的进程
process(action="poll", session_id="proc_abc123")   # 检查状态
process(action="wait", session_id="proc_abc123")   # 阻塞直至完成
process(action="log", session_id="proc_abc123")    # 获取完整输出
process(action="kill", session_id="proc_abc123")   # 终止进程
process(action="write", session_id="proc_abc123", data="y")  # 发送输入
```

设置 `pty=true` 可启用交互式 CLI 工具，如 Codex 与 Claude Code。

## Sudo 支持

若命令需要 sudo，系统会提示输入密码（会在会话期间缓存）。也可以在 `~/.hermes/.env` 中预先设置 `SUDO_PASSWORD`。

:::warning
在消息平台上，若 sudo 失败，输出中会包含添加 `SUDO_PASSWORD` 到 `~/.hermes/.env` 的提示。
:::
