---
slug: /
sidebar_position: 0
title: "Hermes Agent 文档"
description: "由 Nous Research 构建的自我改进 AI 代理。内置学习循环，可从经验中创建技能，在使用过程中改进，并在会话之间保持记忆。"
hide_table_of_contents: true
displayed_sidebar: docs
---

# Hermes Agent

由 [Nous Research](https://nousresearch.com) 构建的自我改进 AI 代理。唯一拥有内置学习循环的代理——它从经验中创建技能，在使用过程中改进，主动推进记忆持久化，并在会话之间构建对用户的深度模型。

<div style={{display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap'}}>
  <a href="/docs/getting-started/installation" style={{display: 'inline-block', padding: '0.6rem 1.2rem', backgroundColor: '#FFD700', color: '#07070d', borderRadius: '8px', fontWeight: 600, textDecoration: 'none'}}>开始使用 →</a>
  <a href="https://github.com/NousResearch/hermes-agent" style={{display: 'inline-block', padding: '0.6rem 1.2rem', border: '1px solid rgba(255,215,0,0.2)', borderRadius: '8px', textDecoration: 'none'}}>在 GitHub 上查看</a>
</div>

## 安装

**Linux / macOS / WSL2**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

**Windows（原生 PowerShell）** — *早期测试版，[详情 →](/docs/user-guide/windows-native)*

```powershell
irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1 | iex
```

**Android（Termux）** — 与 Linux 相同的 curl 单行命令；安装程序会自动检测 Termux。

完整的 **[安装指南](/docs/getting-started/installation)** 详细说明了安装程序的工作原理、用户与根目录布局以及 Windows 的特定注意事项。

## 什么是 Hermes Agent？

它并不是绑定在 IDE 上的编码助手，也不是围绕单一 API 的聊天机器人包装器。它是一个 **自主代理**，运行时间越长能力越强。它可以部署在任何地方——$5 的 VPS、GPU 集群，或几乎不占资源的无服务器基础设施（Daytona、Modal），在空闲时几乎不产生费用。你可以通过 Telegram 与它对话，而它在云端虚拟机上工作，你甚至不需要自行 SSH 登录。它不依赖你的笔记本电脑。

## 快速链接

| | |
|---|---|
| 🚀 **[安装](/docs/getting-started/installation)** | 在 Linux、macOS、WSL2 或原生 Windows（早期测试版）上 60 秒完成安装 |
| 📖 **[快速入门教程](/docs/getting-started/quickstart)** | 第一次对话以及可尝试的关键功能 |
| 🗺️ **[学习路径](/docs/getting-started/learning-path)** | 为你的经验水平找到合适的文档 |
| ⚙️ **[配置](/docs/user-guide/configuration)** | 配置文件、提供商、模型以及各项选项 |
| 💬 **[消息网关](/docs/user-guide/messaging)** | 设置 Telegram、Discord、Slack、WhatsApp、Teams 等平台 |
| 🔧 **[工具与工具集](/docs/user-guide/features/tools)** | 超过 70 项内置工具及其配置方法 |
| 🧠 **[记忆系统](/docs/user-guide/features/memory)** | 跨会话增长的持久记忆 |
| 📚 **[技能系统](/docs/user-guide/features/skills)** | 代理创建并复用的过程性记忆 |
| 🔌 **[MCP 集成](/docs/user-guide/features/mcp)** | 连接 MCP 服务器、过滤工具并安全扩展 Hermes |
| 🧭 **[在 Hermes 中使用 MCP](/docs/guides/use-mcp-with-hermes)** | 实用的 MCP 配置模式、示例与教程 |
| 🎙️ **[语音模式](/docs/user-guide/features/voice-mode)** | CLI、Telegram、Discord 与 Discord 语音频道的实时语音交互 |
| 🗣️ **[在 Hermes 中使用语音模式](/docs/guides/use-voice-mode-with-hermes)** | Hermes 语音工作流的动手设置与使用模式 |
| 🎭 **[人格 & SOUL.md](/docs/user-guide/features/personality)** | 使用全局 SOUL.md 定义 Hermes 的默认声音 |
| 📄 **[上下文文件](/docs/user-guide/features/context-files)** | 影响每次对话的项目上下文文件 |
| 🔒 **[安全性](/docs/user-guide/security)** | 命令批准、授权、容器隔离 |
| 💡 **[技巧与最佳实践](/docs/guides/tips)** | 快速提升 Hermes 使用效果的技巧 |
| 🏗️ **[架构](/docs/developer-guide/architecture)** | 底层工作原理 |
| ❓ **[常见问题与故障排除](/docs/reference/faq)** | 常见问题及解决方案 |

## 关键特性

- **闭环学习** — 代理自行管理记忆并定期 nudging，自动创建技能，在使用过程中自行改进，利用 FTS5 跨会话召回并通过 LLM 摘要，配合 [Honcho](https://github.com/plastic-labs/honcho) 实现辩证用户建模。
- **随处运行，不局限于笔记本** — 支持 6 种终端后端：本地、Docker、SSH、Daytona、Singularity、Modal。Daytona 与 Modal 提供无服务器持久化——空闲时环境进入休眠，费用几乎为零。
- **随你所在之处而存活** — 支持 CLI、Telegram、Discord、Slack、WhatsApp、Signal、Matrix、Mattermost、Email、SMS、钉钉、飞书、企业微信、微信、QQ Bot、元宝、BlueBubbles、Home Assistant、Microsoft Teams、Google Chat 等 20+ 平台的统一网关。
- **模型训练者打造** — 由 [Nous Research](https://nousresearch.com) 构建，背后是 Hermes、Nomos 与 Psyche 系列模型。兼容 Nous Portal、OpenRouter、OpenAI 以及任何兼容的端点。
- **计划任务** — 内置 cron，可将结果投递到任意平台。
- **委派与并行** — 为并行工作流生成隔离子代理。通过 `execute_code` 的程序化工具调用，将多步骤流水线压缩为一次推理调用。
- **开放标准技能** — 与 [agentskills.io](https://agentskills.io) 兼容。技能可移植、可共享，并通过 Skills Hub 社区贡献。
- **完整的网页控制** — 搜索、提取、浏览、视觉、图像生成、文本转语音（TTS）。
- **MCP 支持** — 连接任意 MCP 服务器以获得扩展工具功能。
- **科研就绪** — 批处理、轨迹导出、使用 Atropos 进行强化学习训练。由 [Nous Research](https://nousresearch.com) 打造的实验平台。

## 面向 LLM 和代码代理

机器可读的文档入口点：

- **[`/llms.txt`](/llms.txt)** — 每个文档页面的简要索引，约 17 KB，安全加载到 LLM 上下文。
- **[`/llms-full.txt`](/llms-full.txt)** — 将所有文档页面合并为单一 markdown 文件，约 1.8 MB，适合一次性摄入。

这两个文件也可以通过 `/docs/llms.txt` 与 `/docs/llms-full.txt` 访问。每次部署时都会重新生成。