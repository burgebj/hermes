---
sidebar_position: 1
title: "快速入门"
description: "与 Hermes Agent 的首次对话——从安装到聊天，5 分钟搞定"
---

# 快速入门

本指南帮助你从零开始搭建可在真实环境中使用的 Hermes，完成安装、选择**provider（供应商）**、验证聊天功能，并在出现问题时知道该如何处理。

## 更喜欢观看视频？

**Onchain AI Garage** 制作了一套完整的 Masterclass 视频，演示了安装、配置和基础指令的全过程——如果你更倾向于边看边学，可将其作为本页的补充。更多内容请查看完整的 [Hermes Agent 教程与使用案例](https://www.youtube.com/channel/UCqB1bhMwGsW-yefBxYwFCCg) 播放列表。

<div style={{position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', maxWidth: '100%', marginBottom: '1.5rem'}}>
  <iframe
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%'}}
    src="https://www.youtube-nocookie.com/embed/R3YOGfTBcQg"
    title="Hermes Agent Masterclass: Installation, Setup, Basic Commands"
    frameBorder="0"
    allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowFullScreen
  ></iframe>
</div>

## 本指南适合谁

- 完全新手，想要最快速地得到可运行的环境
- 正在更换供应商，不想因配置错误浪费时间
- 为团队、机器人或常驻工作流部署 Hermes
- 对“一键安装，却无任何响应”感到厌倦

## 最速路径

挑选与你目标匹配的那一行：

| 目标 | 首先要做的事 | 然后做什么 |
|---|---|---|
| 我只想在本机运行 Hermes | `hermes setup` | 运行一次真实聊天并确认有响应 |
| 我已经知道要使用的 provider（供应商） | `hermes model` | 保存配置后开始聊天 |
| 我想要机器人或常驻服务 | 在 CLI（命令行界面）工作正常后运行 `hermes gateway setup` | 连接 Telegram、Discord、Slack 或其他平台 |
| 我想使用本地或自托管模型 | `hermes model` → 自定义端点 | 验证端点、模型名称以及上下文长度 |
| 我想要多供应商兜底 | 先执行 `hermes model` | 确认基础聊天可用后再添加路由与兜底 |

**经验法则**：如果 Hermes 还不能完成一次普通聊天，暂不要再添加功能。先让一次干净的对话跑通，然后再逐层加入网关、定时任务、技能、语音或路由。

---

## 1️⃣ 安装 Hermes Agent

运行一行安装命令：

```bash
# Linux / macOS / WSL2 / Android (Termux)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

:::tip Android / Termux
如果在手机上安装，请参阅专门的 [Termux 指南](./termux.md)，了解经测试的手动步骤、支持的扩展以及当前的 Android 限制。
:::

:::tip Windows 用户
先安装 [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)，再在 WSL2 终端中运行以上命令。
:::

完成后，重新加载 shell：

```bash
source ~/.bashrc   # 或者 source ~/.zshrc
```

想了解更详细的安装选项、前置需求和故障排查，请阅读 [安装指南](./installation.md)。

## 2️⃣ 选择 Provider（供应商）

这是唯一最关键的设置步骤。使用 `hermes model` 交互式完成选择：

```bash
hermes model
```

以下是常用的默认选项：

| Provider | 说明 | 设置方式 |
|----------|------|----------|
| **Nous Portal** | 订阅制、零配置 | 在 `hermes model` 中通过 OAuth 登录 |
| **OpenAI Codex** | ChatGPT OAuth，使用 Codex 模型 | 在 `hermes model` 中通过设备码认证 |
| **Anthropic** | Claude 系列模型——需 Max 计划+额外使用额度（OAuth），或使用按 token 计费的 API Key | `hermes model` → OAuth 登录（需要 Max + 额度），或提供 Anthropic API Key |
| **OpenRouter** | 多供应商路由，覆盖众多模型 | 填写 API Key |
| **Z.AI** | GLM / Zhipu 托管模型 | 设置 `GLM_API_KEY` / `ZAI_API_KEY` |
| **Kimi / Moonshot** | Moonshot 托管的编码与聊天模型 | 设置 `KIMI_API_KEY`（或专用于编码的 `KIMI_CODING_API_KEY`） |
| **Kimi / Moonshot China** | 面向中国区的 Moonshot 接口 | 设置 `KIMI_CN_API_KEY` |
| **Arcee AI** | Trinity 系列模型 | 设置 `ARCEEAI_API_KEY` |
| **GMI Cloud** | 多模型直接 API 接入 | 设置 `GMI_API_KEY` |
| **MiniMax (OAuth)** | MiniMax‑M2.7 浏览器 OAuth，无需 API Key | `hermes model` → MiniMax（OAuth） |
| **MiniMax** | 国际版 MiniMax 接口 | 设置 `MINIMAX_API_KEY` |
| **MiniMax China** | 中国区 MiniMax 接口 | 设置 `MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | 通过 DashScope 调用 Qwen 系列模型 | 设置 `DASHSCOPE_API_KEY` |
| **Hugging Face** | 通过统一路由访问 20+ 开源模型（Qwen、DeepSeek、Kimi 等） | 设置 `HF_TOKEN` |
| **AWS Bedrock** | Claude、Nova、Llama、DeepSeek 等通过原生 Converse API 访问 | 采用 IAM 角色或执行 `aws configure`（[指南](../guides/aws-bedrock.md)） |
| **Kilo Code** | KiloCode 托管模型 | 设置 `KILOCODE_API_KEY` |
| **OpenCode Zen** | 按使用量付费的精选模型 | 设置 `OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | 月付 $10 的开源模型订阅 | 设置 `OPENCODE_GO_API_KEY` |
| **DeepSeek** | 直接对接 DeepSeek API | 设置 `DEEPSEEK_API_KEY` |
| **NVIDIA NIM** | 通过 build.nvidia.com 或本地 NIM 调用 Nemotron 系列模型 | 设置 `NVIDIA_API_KEY`（可选 `NVIDIA_BASE_URL`） |
| **GitHub Copilot** | GitHub Copilot 订阅（GPT‑5.x、Claude、Gemini 等） | 在 `hermes model` 中通过 OAuth 登录，或设置 `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` |
| **GitHub Copilot ACP** | Copilot ACP 代理后端（需本地 `copilot` CLI） | `hermes model`（前提是已安装 `copilot` CLI 并完成 `copilot login`） |
| **Vercel AI Gateway** | Vercel AI Gateway 路由 | 设置 `AI_GATEWAY_API_KEY` |
| **Custom Endpoint** | VLLM、SGLang、Ollama 或任意兼容 OpenAI 的 API | 设置基础 URL + API Key |

对于大多数首次使用者：选择一个 provider（供应商），除非明确知道自己在改什么，否则请接受默认值。完整的 provider 目录、对应的环境变量以及设置步骤请参见 [供应商列表](../integrations/providers.md)。

:::caution Minimum context: 64K tokens
Hermes Agent 至少需要 **64,000 token** 的上下文窗口。窗口小于该阈值的模型无法支撑多轮工具调用的工作记忆，在启动时会被拒绝。主流托管模型（Claude、GPT、Gemini、Qwen、DeepSeek）均已轻松满足。若自行部署本地模型，请将上下文长度调至至少 64K（例如在 llama.cpp 中使用 `--ctx-size 65536`，或在 Ollama 中使用 `-c 65536`）。
:::

:::tip
随时可使用 `hermes model` 切换 provider（供应商）——不存在绑定限制。完整的 provider 支持列表及设置细节请查看 [AI 供应商](../integrations/providers.md)。
:::

### 设置如何存储

Hermes 将 **机密信息** 与普通配置分离存放：

- **机密和 token（令牌）** → `~/.hermes/.env`
- **非机密设置** → `~/.hermes/config.yaml`

最省事的方式是通过 CLI（命令行界面）进行设置：

```bash
hermes config set model anthropic/claude-opus-4.6
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...
```

系统会自动将对应值写入正确的文件。

## 3️⃣ 运行你的首个聊天

```bash
hermes            # 经典 CLI（命令行界面）
hermes --tui      # 现代 TUI（推荐）
```

启动后会显示包含模型、可用工具及已加载技能的欢迎横幅。请使用明确且易于验证的提示进行测试：

:::tip 选择交互界面
Hermes 提供两种终端交互方式：传统的 `prompt_toolkit` CLI 与更现代的 [TUI](../user-guide/tui.md)（支持模态覆盖、鼠标选择和非阻塞输入）。两者共享相同的 session（会话）、斜线指令和配置，任选其一即可体验。
:::

```
Summarize this repo in 5 bullets and tell me what the main entrypoint is.
```

```
Check my current directory and tell me what looks like the main project file.
```

```
Help me set up a clean GitHub PR workflow for this codebase.
```

**成功的标志**：

- 横幅显示你选定的模型/供应商
- Hermes 能够无错误回复
- 如需，可使用工具（终端、文件读取、网页搜索）
- 对话能够顺畅进行多轮

如果上述都正常，则已跨过最难的阶段。

## 4️⃣ 验证 Session（会话）恢复

在继续其他操作前，先确认会话恢复功能可用：

```bash
hermes --continue    # 恢复最近一次会话
hermes -c            # 略写形式
```

这应当把你带回刚才的对话。如果没有，检查是否在同一 profile（配置文件）下，或会话是否真的已保存。这在后期切换机器或多套环境时尤为重要。

## 5️⃣ 体验关键功能

### 使用终端工具

```
❯ What's my disk usage? Show the top 5 largest directories.
```

Agent 会在你的机器上执行终端指令并返回结果。

### 斜线指令（Slash commands）

在聊天框输入 `/` 可弹出所有指令的自动补全列表：

| 指令 | 功能 |
|---------|-------------|
| `/help` | 显示所有可用指令 |
| `/tools` | 列出可用工具 |
| `/model` | 交互式切换模型 |
| `/personality pirate` | 尝试有趣的角色设定 |
| `/save` | 保存当前对话 |

### 多行输入

使用 `Alt+Enter`、`Ctrl+J` 或 `Shift+Enter` 换行。`Shift+Enter` 需要终端能够将其识别为独立的键序列（默认支持 Kitty / foot / WezTerm / Ghostty；在 iTerm2 / Alacritty / VS Code 终端中开启 Kitty 键盘协议后亦可）。`Alt+Enter` 与 `Ctrl+J` 在所有终端均可使用。

### 中断 Agent

若 Agent 响应过慢，直接输入新消息并回车即可中断当前任务并切换指令。`Ctrl+C` 也能实现同样效果。

## 6️⃣ 添加下一层功能

仅在基础聊天正常后再继续。根据需求选择下面的扩展路径：

### 机器人或共享助理

```bash
hermes gateway setup    # 交互式平台配置向导
```

可连接 [Telegram](/docs/user-guide/messaging/telegram)、[Discord](/docs/user-guide/messaging/discord)、[Slack](/docs/user-guide/messaging/slack)、[WhatsApp](/docs/user-guide/messaging/whatsapp)、[Signal](/docs/user-guide/messaging/signal)、[Email](/docs/user-guide/messaging/email)、[Home Assistant](/docs/user-guide/messaging/homeassistant)、[Microsoft Teams](/docs/user-guide/messaging/teams) 等平台。

### 自动化与工具

- `hermes tools` — 为不同平台微调工具访问权限
- `hermes skills` — 浏览并安装可复用的工作流
- 定时任务（Cron）— 仅在机器人或 CLI 稳定后使用

### 沙箱终端

为安全起见，可在 Docker 容器或远程服务器中运行 Agent：

```bash
hermes config set terminal.backend docker    # Docker 隔离
hermes config set terminal.backend ssh       # 远程服务器
```

### 语音模式

```bash
# 在 Hermes 安装目录（curl 安装器会放在 ~/.hermes/hermes-agent）
cd ~/.hermes/hermes-agent
uv pip install -e ".[voice]"
# 包含 free local 的 faster-whisper 用于语音转文字
```

随后在 CLI 中使用 `/voice on` 启动。录音请按 `Ctrl+B`。更多请参见 [语音模式](../user-guide/features/voice-mode.md)。

### Skills（技能）

```bash
hermes skills search kubernetes
hermes skills install openai/skills/k8s
```

或在聊天中使用 `/skills`。

### MCP 服务器

```yaml
# 添加到 ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

### 编辑器集成（ACP）

ACP 支持已随 `[all]` extras 一同安装，curl 安装器默认已包含。直接运行：

```bash
hermes acp
```

（若未安装 `[all]`，请先执行 `cd ~/.hermes/hermes-agent && uv pip install -e ".[acp]"`。）

详细请查看 [ACP 编辑器集成](../user-guide/features/acp.md)。

---

## 常见故障模式

以下问题最容易让人浪费时间：

| 症状 | 可能原因 | 解决方案 |
|---|---|---|
| Hermes 启动后返回空白或破碎的回复 | Provider（供应商）认证或模型选择错误 | 重新运行 `hermes model`，确认 provider、model 与 auth 正确 |
| 自定义端点“能用”但返回乱码 | 基础 URL、模型名称错误，或并非真正的 OpenAI 兼容接口 | 先在独立客户端验证端点 |
| Gateway 启动却无法收到消息 | 机器人 token、白名单或平台配置不完整 | 重新运行 `hermes gateway setup` 并检查 `hermes gateway status` |
| `hermes --continue` 找不到旧 session（会话） | 切换了 profile，或会话根本未保存 | 查看 `hermes sessions list`，确认使用正确的 profile |
| 模型不可用或出现异常回退行为 | Provider（供应商）路由或兜底设置过于激进 | 在基础 provider 稳定前关闭路由 |
| `hermes doctor` 检测到配置问题 | 配置缺失或已过期 | 修复配置后先测试普通聊天，再添加其他功能 |

## 恢复工具箱

当感觉一切不对劲时，按以下顺序排查：

1. `hermes doctor`
2. `hermes model`
3. `hermes setup`
4. `hermes sessions list`
5. `hermes --continue`
6. `hermes gateway status`

这样即可快速把系统从“坏掉的状态”恢复到已知的良好状态。

---

## 快速参考

| 命令 | 描述 |
|---------|-------------|
| `hermes` | 开始聊天 |
| `hermes model` | 选择 LLM provider（供应商）和模型 |
| `hermes tools` | 为不同平台配置启用的工具 |
| `hermes setup` | 完整设置向导（一次性配置所有内容） |
| `hermes doctor` | 诊断问题 |
| `hermes update` | 更新到最新版本 |
| `hermes gateway` | 启动消息网关 |
| `hermes --continue` | 恢复最近一次会话 |

## 后续步骤

- **[CLI 指南](../user-guide/cli.md)** — 精通终端交互
- **[配置指南](../user-guide/configuration.md)** — 定制你的 Hermes
- **[消息网关](../user-guide/messaging/index.md)** — 连接 Telegram、Discord、Slack、WhatsApp、Signal、Email、Home Assistant、Teams 等平台
- **[工具与工具集](../user-guide/features/tools.md)** — 探索可用能力
- **[AI 供应商](../integrations/providers.md)** — 完整供应商列表及配置细节
- **[技能系统](../user-guide/features/skills.md)** — 可复用的工作流与知识库
- **[技巧与最佳实践](../guides/tips.md)** — 高阶使用技巧
