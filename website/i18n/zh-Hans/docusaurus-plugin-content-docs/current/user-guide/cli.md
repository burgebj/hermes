---
sidebar_position: 1
title: "CLI 界面"
description: "掌握 Hermes Agent 终端界面 —— 命令、快捷键、人格等"
---

# CLI 界面

Hermes Agent 的 CLI 是完整的终端用户界面（TUI）——而不是网页 UI。它支持多行编辑、斜杠指令自动完成、对话历史、打断并重定向，以及流式工具输出。专为在终端中工作的用户打造。

:::tip
Hermes 还提供了带模态覆盖、鼠标选择和非阻塞输入的现代 TUI。使用 `hermes --tui` 启动——参见 [TUI](tui.md) 指南。
:::

## 运行 CLI

```bash
# 启动交互式会话（默认）
hermes

# 单次查询模式（非交互式）
hermes chat -q "Hello"

# 指定模型
hermes chat --model "anthropic/claude-sonnet-4"

# 指定提供商
hermes chat --provider nous        # 使用 Nous Portal
hermes chat --provider openrouter  # 强制使用 OpenRouter

# 指定工具集
hermes chat --toolsets "web,terminal,skills"

# 启动时预加载一个或多个技能
hermes -s hermes-agent-dev,github-auth
hermes chat -s github-pr-workflow -q "open a draft PR"

# 恢复先前会话
hermes --continue             # 恢复最近的 CLI 会话（-c）
hermes --resume <session_id>  # 按 ID 恢复指定会话

# Verbose 模式（调试输出）
hermes chat --verbose

# 隔离的 git worktree（用于并行运行多个代理）
hermes -w                         # 在 worktree 中交互模式
hermes -w -q "Fix issue #123"     # 在 worktree 中单次查询
```

## 界面布局

<img className="docs-terminal-figure" src="/img/docs/cli-layout.svg" alt="Hermes CLI 布局的艺术化预览，展示横幅、对话区域和固定输入提示。" />
<p className="docs-figure-caption">Hermes CLI 横幅、对话流和固定输入提示，以稳定的文档图形方式呈现，而非易碎的文本艺术。</p>

欢迎横幅一目了然地显示模型、终端后端、工作目录、可用工具以及已安装的技能。

### 状态栏

一个持久的状态栏位于输入区之上，实时更新：

```
 ⚕ claude-sonnet-4-20250514 │ 12.4K/200K │ [██████░░░░] 6% │ $0.06 │ 15m
```

| 元素 | 描述 |
|------|------|
| 模型名称 | 当前模型（若超过 26 字符则截断） |
| 令牌计数 | 已使用的上下文令牌 / 最大上下文窗口 |
| 上下文条 | 使用颜色编码阈值的可视化填充指示 |
| 成本 | 估算的会话费用（若模型免费或未知则显示 `n/a`） |
| 时长 | 会话已运行时间 |

状态栏会根据终端宽度自适应——宽度 ≥ 76 列显示完整布局，52–75 列显示紧凑布局，<52 列仅显示模型 + 时长。

**上下文颜色编码：**

| 颜色 | 阈值 | 含义 |
|------|------|------|
| 绿色 | < 50% | 余量充足 |
| 黄色 | 50–80% | 正在使用 |
| 橙色 | 80–95% | 接近上限 |
| 红色 | ≥ 95% | 接近溢出 —— 考虑使用 `/compress` |

使用 `/usage` 可获取包括输入/输出令牌成本在内的详细拆分。

### 会话恢复显示

当通过 `hermes -c` 或 `hermes --resume <id>` 恢复先前会话时，会在横幅和输入提示之间出现“先前会话”面板，展示会话历史的紧凑回顾。详情请见 [Sessions — Conversation Recap on Resume](sessions.md#conversation-recap-on-resume)。

## 快捷键

| 键 | 操作 |
|-----|------|
| `Enter` | 发送消息 |
| `Alt+Enter`、`Ctrl+J`、或 `Shift+Enter` | 换行（多行输入）。`Shift+Enter` 需要终端能区分此键——见下文。Windows Terminal 中 `Alt+Enter` 被终端捕获（全屏切换），请使用 `Ctrl+Enter` 或 `Ctrl+J` 替代。 |
| `Alt+V` | 在支持的终端中从剪贴板粘贴图像 |
| `Ctrl+V` | 粘贴文本并在可能时附加剪贴板图片 |
| `Ctrl+B` | 在启用语音模式时开始/停止录音（`voice.record_key` 默认 `ctrl+b`） |
| `Ctrl+G` | 在 `$EDITOR` 中打开当前输入缓冲区（vim/nvim/nano/VS Code 等）。保存并退出后将编辑后的文本作为下一条提示发送——适用于长段落提示。 |
| `Ctrl+X Ctrl+E` | Emacs 风格的外部编辑器快捷键（同 `Ctrl+G`） |
| `Ctrl+C` | 打断代理（在 2 秒内双击可强制退出） |
| `Ctrl+D` | 退出 |
| `Ctrl+Z` | 将 Hermes 挂起至后台（仅 Unix）。在 shell 中运行 `fg` 恢复。 |
| `Tab` | 接受自动建议（幽灵文本）或自动完成斜杠指令 |

**多行粘贴预览**：粘贴多行块时，CLI 会回显紧凑的单行预览（`[pasted: 47 lines, 1,842 chars — press Enter to send]`），而非将全部内容打印到滚动缓冲区。实际发送的仍是完整内容，仅为显示美化。

**最终响应的 Markdown 处理**：CLI 会剥除最冗余的 Markdown 代码块以及 `**粗体**` / `*斜体*` 包装，使最终的终端回复成为可读的普通文字。代码块和列表会被保留。这不影响网关平台或工具结果——它们仍保留原始 Markdown 用于原生渲染。

## 斜杠指令

输入 `/` 可弹出自动完成下拉框。Hermes 支持大量 CLI 斜杠指令、动态技能指令以及用户自定义快捷指令。

常用示例：

| 指令 | 描述 |
|------|------|
| `/help` | 显示指令帮助 |
| `/model` | 查看或更改当前模型 |
| `/tools` | 列出当前可用工具 |
| `/skills browse` | 浏览技能中心及官方可选技能 |
| `/background <prompt>` | 在独立后台会话中运行提示 |
| `/skin` | 查看或切换当前 CLI 皮肤 |
| `/voice on` | 启用 CLI 语音模式（按 `Ctrl+B` 录音） |
| `/voice tts` | 切换 Hermes 回复的语音播放 |
| `/reasoning high` | 增强推理力度 |
| `/title My Session` | 为当前会话命名 |

完整的内置 CLI 与消息指令列表请参阅 [Slash Commands Reference](../reference/slash-commands.md)。

关于设置、提供商、安静调校以及消息/Discord 语音使用，请参阅 [Voice Mode](features/voice-mode.md)。

:::tip
指令不区分大小写——`/HELP` 与 `/help` 等价。已安装的技能也会自动成为斜杠指令。
:::

## 快捷指令

您可以定义自定义指令，在不调用 LLM 的情况下直接执行 shell 命令。这些指令在 CLI 与所有消息平台（Telegram、Discord 等）中均可使用。

```yaml
# ~/.hermes/config.yaml
quick_commands:
  status:
    type: exec
    command: systemctl status hermes-agent
  gpu:
    type: exec
    command: nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
  restart:
    type: alias
    target: /gateway restart
```

之后在任意聊天中输入 `/status`、`/gpu` 或 `/restart` 即可。更多示例请见 [配置指南](/docs/user-guide/configuration#quick-commands)。

## 启动时预加载技能

如果已经知道本次会话需要哪些技能，可在启动时一次性传入：

```bash
hermes -s hermes-agent-dev,github-auth
hermes chat -s github-pr-workflow -s github-auth
```

Hermes 会在第一轮对话之前将每个指定技能加载进提示中。该标志在交互模式和单查询模式下均可使用。

## 技能斜杠指令

`~/.hermes/skills/` 中的每个已安装技能会自动注册为斜杠指令。技能名即指令名：

```
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor

# 仅加载技能，让代理询问具体需求：
/excalidraw
```

## 人格（Personalities）

设置预定义人格以改变代理的语气：

```
/personality pirate
/personality kawaii
/personality concise
```

内置人格包括：`helpful`、`concise`、`technical`、`creative`、`teacher`、`kawaii`、`catgirl`、`pirate`、`shakespeare`、`surfer`、`noir`、`uwu`、`philosopher`、`hype`。

您也可以在 `~/.hermes/config.yaml` 中自定义人格：

```yaml
personalities:
  helpful: "You are a helpful, friendly AI assistant."
  kawaii: "You are a kawaii assistant! Use cute expressions..."
  pirate: "Arrr! Ye be talkin' to Captain Hermes..."
  # 添加你的自定义人格
```

## 多行输入

有两种方式输入多行消息：

1. **`Alt+Enter`、`Ctrl+J` 或 `Shift+Enter`** — 插入新行
2. **反斜杠续行** — 在行尾使用 `\` 继续，例如：

```
❯ Write a function that:\
  1. Takes a list of numbers\
  2. Returns the sum
```

:::info
粘贴多行文本同样受支持——使用上述任意换行键，或直接粘贴内容。
:::

### Shift+Enter 兼容性

大多数终端默认将 `Enter` 与 `Shift+Enter` 发送相同字节序列，导致应用无法区分。Hermes 仅在终端通过 [Kitty 键盘协议](https://sw.kovidgoyal.net/kitty/keyboard-protocol/) 或 xterm 的 `modifyOtherKeys` 模式发送独立序列时才识别 `Shift+Enter`。

| 终端 | 支持情况 |
|------|----------|
| Kitty、foot、WezTerm、Ghostty | 默认启用独立 `Shift+Enter` |
| iTerm2（近期）、Alacritty、VS Code 终端、Warp | 在设置中启用 Kitty 协议后支持 |
| Windows Terminal Preview 1.25+ | 在设置中启用 Kitty 协议后支持 |
| macOS Terminal.app、官方 Windows Terminal（稳定版） | 不支持 —— `Shift+Enter` 与 `Enter` 无差别 |

在终端无法区分时，`Alt+Enter` 与 `Ctrl+J` 仍可在所有环境中使用。**在 Windows Terminal 中，`Alt+Enter` 被终端捕获（切换全屏），请使用 `Ctrl+Enter`（等同于 `Ctrl+J`）或直接 `Ctrl+J` 换行。**

## 中断代理

您可以随时中断代理的执行：

- **在代理工作时键入新消息并回车** —— 会中断当前任务并处理新指令
- **`Ctrl+C`** —— 中断当前操作（双击 2 秒内强制退出）
- 正在执行的终端命令会被立即终止（先 SIGTERM，1 秒后 SIGKILL）
- 多条在中断期间键入的消息会合并为一次提示

### 忙碌输入模式

`display.busy_input_mode` 配置键决定在代理工作时按 Enter 的行为：

| 模式 | 行为 |
|------|------|
| `"interrupt"`（默认） | 您的消息立即中断当前操作并被处理 |
| `"queue"` | 您的消息静默排队，在代理完成后作为下一轮发送 |
| `"steer"` | 您的消息通过 `/steer` 注入当前运行的工具调用后——不会中断，也不会生成新轮次 |

```yaml
# ~/.hermes/config.yaml
display:
  busy_input_mode: "steer"   # 可选 "queue" 或 "interrupt"
```

`"queue"` 适用于想准备后续消息却不想意外取消正在进行的工作。`"steer"` 适用于在代码编辑等任务中想在不打断的情况下指示额外操作，例如 “顺便检查测试”。未知值会回落到 `"interrupt"`。

`"steer"` 有两种自动回退：如果代理尚未开始，或附带了图像，消息会退化为 `"queue"` 行为，确保信息不丢失。

您也可以在 CLI 内动态切换：

```text
/busy queue
/busy steer
/busy interrupt
/busy status
```

:::tip First‑touch hint
第一次在 Hermes 工作时按 Enter，Hermes 会打印一行提醒解释 `/busy` 选项（"(tip) Your message interrupted the current run…"）。该提示仅在首次安装时出现——`config.yaml` 中的 `onboarding.seen.busy_input_prompt` 键会记录它。删除该键即可再次看到提示。
:::

## 挂起到后台（Unix）

在 Unix 系统上，按 **`Ctrl+Z`** 可将 Hermes 挂起到后台——与任何终端进程的行为相同。Shell 会显示确认信息：

```
Hermes Agent has been suspended. Run `fg` to bring Hermes Agent back.
```

在 shell 中执行 `fg` 即可恢复会话，继续之前的交互。Windows 不支持此功能。

## 工具进度显示

CLI 会在代理工作时展示动画反馈：

**思考动画（API 调用期间）**：
```
  ◜ (｡•́︿•̀｡) pondering... (1.2s)
  ◠ (⊙_⊙) contemplating... (2.4s)
  ✧٩(ˊᗜˋ*)و✧ got it! (3.1s)
```

**工具执行流**：
```
  ┊ 💻 terminal `ls -la` (0.3s)
  ┊ 🔍 web_search (1.2s)
  ┊ 📄 web_extract (2.1s)
```

使用 `/verbose` 在不同显示模式之间切换：`off → new → all → verbose`。此指令也可在消息平台上启用，参见 [配置](/docs/user-guide/configuration#display-settings)。

### 工具预览长度

`display.tool_preview_length` 配置键控制工具调用预览行的最大字符数（如文件路径、终端命令）。默认 `0` 表示不限制——完整路径和命令都会显示。

```yaml
# ~/.hermes/config.yaml
display:
  tool_preview_length: 80   # 将工具预览截断到 80 字符（0 为无限制）
```

在窄终端或参数包含超长路径时此设置非常有用。

## 会话管理

### 恢复会话

退出 CLI 会话后，会打印恢复指令：

```
Resume this session with:
  hermes --resume 20260225_143052_a1b2c3

Session:        20260225_143052_a1b2c3
Duration:       12m 34s
Messages:       28 (5 user, 18 tool calls)
```

恢复选项：

```bash
hermes --continue                          # 恢复最近的 CLI 会话
hermes -c                                  # 简写
hermes -c "my project"                     # 恢复最近的同系列会话（按标题）
hermes --resume 20260225_143052_a1b2c3     # 按 ID 恢复指定会话
hermes --resume "refactoring auth"         # 按标题恢复
hermes -r 20260225_143052_a1b2c3           # 简写
```

恢复会从 SQLite 中恢复完整对话历史。代理会看到所有先前的消息、工具调用以及响应——就像从未离开一样。

使用 `/title My Session Name` 在聊天中为当前会话命名，或通过 `hermes sessions rename <id> <title>` 在命令行中重命名。`hermes sessions list` 可列出过去的会话。

### 会话存储

CLI 会话保存在 `~/.hermes/state.db` 的 SQLite 数据库中，包含：

- 会话元数据（ID、标题、时间戳、令牌计数）
- 消息历史
- 跨压缩/恢复的会话血缘
- `session_search` 使用的全文索引

部分消息适配器也会在数据库旁边保存平台特定的转录文件，但 CLI 本身仅从 SQLite 恢复。

### 上下文压缩

当会话接近上下文限制时会自动摘要：

```yaml
# ~/.hermes/config.yaml
compression:
  enabled: true
  threshold: 0.50    # 默认在 50% 上下文限制时触发压缩

# 使用的摘要模型（在 auxiliary 中配置）
auxiliary:
  compression:
    model: ""  # 空则使用主聊天模型（默认）。也可指定廉价快速模型，例如 "google/gemini-3-flash-preview"。
```

压缩触发后，会对中间回合进行摘要，而首 3 回合和最后 20 回合始终保留。

## 后台会话

使用斜杠指令在独立后台会话中运行提示，同时继续在前台使用 CLI：

```
/background Analyze the logs in /var/log and summarize any errors from today
```

Hermes 会立即确认任务并返回提示信息：

```
🔄 Background task #1 started: "Analyze the logs in /var/log and summarize..."
   Task ID: bg_143022_a1b2c3
```

### 工作原理

每个 `/background` 提示会在守护线程中生成一个 **完全独立的代理会话**：

- **隔离对话** —— 背景代理不知晓当前会话的历史，仅收到该提示。
- **相同配置** —— 继承当前会话的模型、提供商、工具集、推理设置等。
- **非阻塞** —— 前台会话保持交互，可继续聊天、运行命令或启动更多后台任务。
- **多任务** —— 可同时运行多个后台任务，每个任务都有编号 ID。

### 结果展示

后台任务完成后，结果会以面板形式出现在终端：

```
╭─ ⚕ Hermes (background #1) ──────────────────────────────────╮
│ Found 3 errors in syslog from today:                         │
│ 1. OOM killer invoked at 03:22 — killed process nginx        │
│ 2. Disk I/O error on /dev/sda1 at 07:15                      │
│ 3. Failed SSH login attempts from 192.168.1.50 at 14:30      │
╰──────────────────────────────────────────────────────────────╯
```

若任务失败，将显示错误通知。如果 `display.bell_on_complete` 在配置中启用，任务完成时会响铃。

### 使用场景

- **长期研究** — `/background research the latest developments in quantum error correction` 与此同时继续编码。
- **文件处理** — `/background analyze all Python files in this repo and list any security issues` 与此同时继续对话。
- **并行调查** — 启动多个后台任务，同时探索不同角度。

:::info
后台会话不出现在主对话历史中。它们是拥有独立任务 ID（如 `bg_143022_a1b2c3`）的独立会话。
:::

## 安静模式（Quiet Mode）

默认情况下，CLI 运行在安静模式下，
- 抑制工具的详细日志
- 启用可爱风格的动画反馈
- 保持输出简洁友好

如需调试输出：

```bash
hermes chat --verbose
```
