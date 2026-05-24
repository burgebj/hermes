---
title: "功能概览"
sidebar_label: "概览"
sidebar_position: 1
---

# 功能概览

Hermes Agent 包含一套丰富的能力，远超基础聊天。从持久记忆（Persistent Memory）和文件感知上下文（File‑Aware Context）到浏览器自动化和语音对话，这些特性协同工作，使 Hermes 成为强大的自主助理。

## 核心

- **[工具与工具集（Tools & Toolsets）](tools.md)** — 工具是扩展代理功能的函数。它们被组织为逻辑工具集，可在每个平台上按需启用或禁用，涵盖网页搜索、终端执行、文件编辑、记忆、委派等。
- **[技能系统（Skills System）](skills.md)** — 按需加载的知识文档，代理在需要时使用。技能遵循渐进披露模式以最小化 token 使用，并兼容 [agentskills.io](https://agentskills.io/specification) 开放标准。
- **[持久记忆（Persistent Memory）](memory.md)** — 有界的、精心策划的记忆，跨会话持久化。Hermes 通过 `MEMORY.md` 与 `USER.md` 记住你的偏好、项目、环境以及学习过的内容。
- **[上下文文件（Context Files）](context-files.md)** — Hermes 会自动发现并加载项目上下文文件（`.hermes.md`、`AGENTS.md`、`CLAUDE.md`、`SOUL.md`、`.cursorrules`），这些文件决定它在项目中的行为方式。
- **[上下文引用（Context References）](context-references.md)** — 输入 `@` 加引用即可将文件、文件夹、git diff 与 URL 直接注入消息。Hermes 会展开引用并自动在后续追加内容。
- **[检查点（Checkpoints）](../checkpoints-and-rollback.md)** — 在对工作目录进行文件更改前，Hermes 会自动创建快照，为出现问题时使用 `/rollback` 提供安全回滚。

## 自动化

- **[计划任务（Cron）](cron.md)** — 使用自然语言或 cron 表达式自动调度任务。作业可附加技能、将结果发送至任意平台，并支持暂停/恢复/编辑操作。
- **[子代理委派（Subagent Delegation）](delegation.md)** — `delegate_task` 工具会生成具有隔离上下文、受限工具集和独立终端会话的子代理实例。默认可并行运行 3 个子代理（可配置），用于并行工作流。
- **[代码执行（Code Execution）](code-execution.md)** — `execute_code` 工具让代理编写 Python 脚本，程序化调用 Hermes 工具，通过沙箱 RPC 将多步骤工作流压缩为单次 LLM 调用。
- **[事件钩子（Event Hooks）](hooks.md)** — 在关键生命周期节点运行自定义代码。网关钩子处理日志、告警和 webhook；插件钩子处理工具拦截、指标与安全护栏。
- **[批量处理（Batch Processing）](batch-processing.md)** — 在数百甚至上千个提示上并行运行 Hermes 代理，生成结构化的 ShareGPT‑format 轨迹数据，用于训练数据生成或评估。

## 媒体与网络

- **[语音模式（Voice Mode）](voice-mode.md)** — 在 CLI 与消息平台上实现完整语音交互。使用麦克风与代理对话，聆听语音回复，并支持在 Discord 语音频道进行实时语音会话。
- **[浏览器自动化（Browser Automation）](browser.md)** — 多后端完整浏览器自动化：Browserbase 云、Browser Use 云、本地 Chrome（CDP）或本地 Chromium。可浏览网站、填写表单、提取信息。
- **[视觉与图像粘贴（Vision & Image Paste）](vision.md)** — 多模态视觉支持。可将剪贴板中的图像粘贴到 CLI，并让代理使用任何具备视觉能力的模型进行分析、描述或处理。
- **[图像生成（Image Generation）](image-generation.md)** — 使用 FAL.ai 根据文本提示生成图像。支持九种模型（FLUX 2 Klein/Pro、GPT‑Image 1.5/2、Nano Banana Pro、Ideogram V3、Recraft V4 Pro、Qwen、Z‑Image Turbo），可通过 `hermes tools` 选择。
- **[语音与文本转语音（Voice & TTS）](tts.md)** — 在所有消息平台上提供文本转语音输出与语音消息转录，内置十种提供商：Edge TTS（免费）、ElevenLabs、OpenAI TTS、MiniMax、Mistral Voxtral、Google Gemini、xAI、NeuTTS、KittenTTS、Piper，以及支持自定义本地 TTS CLI 的命令提供商。

## 集成

- **[MCP 集成（MCP Integration）](mcp.md)** — 通过 stdio 或 HTTP 传输连接任意 MCP 服务器。无需编写本地 Hermes 工具，即可访问 GitHub、数据库、文件系统和内部 API 等外部工具。支持每服务器工具过滤与抽样。
- **[提供商路由（Provider Routing）](provider-routing.md)** — 精细控制哪个 AI 提供商处理请求。通过排序、白名单、黑名单和优先级顺序，在成本、速度或质量之间优化。
- **[后备提供商（Fallback Providers）](fallback-providers.md)** — 当主模型出现错误时自动切换至备用 LLM 提供商，辅助任务（如视觉、压缩）也可独立使用后备提供商。
- **[凭证池（Credential Pools）](credential-pools.md)** — 为同一提供商的多个 API key 分配调用。遇到速率限制或失败时自动轮换。
- **[记忆提供商（Memory Providers）](memory-providers.md)** — 接入外部记忆后端（Honcho、OpenViking、Mem0、Hindsight、Holographic、RetainDB、ByteRover、Supermemory），实现跨会话用户建模与个性化，超越内置记忆系统。
- **[API 服务器（API Server）](api-server.md)** — 将 Hermes 暴露为兼容 OpenAI 的 HTTP 端点。任何支持 OpenAI 格式的前端均可对接——Open WebUI、LobeChat、LibreChat 等。
- **[IDE 集成（ACP）](acp.md)** — 在 ACP 兼容编辑器（VS Code、Zed、JetBrains）中使用 Hermes。聊天、工具活动、文件差异与终端命令均渲染在编辑器内。
- **[强化学习训练（RL Training）](rl-training.md)** — 从代理会话生成轨迹数据，用于强化学习与模型微调。

## 定制化

- **[个性与 SOUL.md（Personality & SOUL.md）](personality.md)** — 完全可自定义的代理个性。`SOUL.md` 是系统提示的首要身份文件，可在会话间切换内置或自定义的 `/personality` 预设。
- **[皮肤与主题（Skins & Themes）](skins.md)** — 自定义 CLI 的视觉呈现：横幅颜色、加载动画、动词、响应框标签、品牌文字以及工具活动前缀。
- **[插件（Plugins）](plugins.md)** — 在不修改核心代码的前提下添加自定义工具、钩子和集成。三类插件：通用插件（工具/钩子）、记忆提供商（跨会话知识）和上下文引擎（替代上下文管理）。通过统一的 `hermes plugins` 交互式 UI 管理。
