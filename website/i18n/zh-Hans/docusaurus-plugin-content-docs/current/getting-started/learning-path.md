---
sidebar_position: 3
title: '学习路径'
description: '根据您的经验水平和目标，在 Hermes Agent 文档中选择合适的学习路径。'
---

# 学习路径

Hermes Agent 功能丰富——包括 CLI 助手、Telegram/Discord 机器人、任务自动化、强化学习（RL）训练等。本页帮助您根据经验水平和目标，确定从何处入手以及阅读顺序。

:::tip 开始前
如果您尚未安装 Hermes Agent，请先阅读[安装指南](/docs/getting-started/installation)，随后完成[快速入门](/docs/getting-started/quickstart)。以下内容默认您已经完成了可用的安装。
:::

## 如何使用本页

- **已知自己的水平？** 跳转至[按经验水平划分](#按经验水平划分)的表格，按照对应层级的阅读顺序进行。
- **有具体目标？** 前往[按使用场景](_#按使用场景)查找匹配的方案。
- **随便浏览？** 查看[功能速览](_#功能速览)表格，快速了解 Hermes Agent 的全部能力。

## 按经验水平划分

| 等级 | 目标 | 推荐阅读 | 预计时间 |
|---|---|---|---|
| **初学者** | 快速上手、进行基本对话、使用内置工具 | [安装](/docs/getting-started/installation) → [快速入门](/docs/getting-started/quickstart) → [CLI 使用](/docs/user-guide/cli) → [配置](/docs/user-guide/configuration) | ~1 小时 |
| **中级** | 部署消息机器人，使用记忆、定时任务（cron）和技能等高级功能 | [会话](/docs/user-guide/sessions) → [消息](/docs/user-guide/messaging) → [工具](/docs/user-guide/features/tools) → [技能](/docs/user-guide/features/skills) → [记忆](/docs/user-guide/features/memory) → [Cron](/docs/user-guide/features/cron) | ~2–3 小时 |
| **高级** | 开发自定义工具、创建技能、使用强化学习训练模型、为项目贡献代码 | [架构](/docs/developer-guide/architecture) → [添加工具](/docs/developer-guide/adding-tools) → [创建技能](/docs/developer-guide/creating-skills) → [RL 训练](/docs/user-guide/features/rl-training) → [贡献指南](/docs/developer-guide/contributing) | ~4–6 小时 |

## 按使用场景

挑选与您需求相符的场景，每个场景都会按推荐顺序链接到相应文档。

### “我想要一个 CLI 编码助手”

使用 Hermes Agent 作为交互式终端助手，协助编写、审查、运行代码。

1. [安装](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [CLI 使用](/docs/user-guide/cli)
4. [代码执行](/docs/user-guide/features/code-execution)
5. [上下文文件](/docs/user-guide/features/context-files)
6. [技巧与窍门](/docs/guides/tips)

:::tip
通过上下文文件直接将项目文件加入对话。Hermes Agent 能读取、编辑并运行代码。
:::

### “我想要一个 Telegram/Discord 机器人”

将在您喜欢的即时通讯平台上部署 Hermes Agent 机器人。

1. [安装](/docs/getting-started/installation)
2. [配置](/docs/user-guide/configuration)
3. [消息概览](/docs/user-guide/messaging)
4. [Telegram 设置](/docs/user-guide/messaging/telegram)
5. [Discord 设置](/docs/user-guide/messaging/discord)
6. [语音模式](/docs/user-guide/features/voice-mode)
7. [在 Hermes 中使用语音模式](/docs/guides/use-voice-mode-with-hermes)
8. [安全](/docs/user-guide/security)

完整项目示例请参见：
- [每日简报机器人](/docs/guides/daily-briefing-bot)
- [团队 Telegram 助手](/docs/guides/team-telegram-assistant)

### “我想要自动化任务”

安排周期性任务、运行批处理作业，或将多个 Agent 动作串联。

1. [快速入门](/docs/getting-started/quickstart)
2. [Cron 调度](/docs/user-guide/features/cron)
3. [批处理](/docs/user-guide/features/batch-processing)
4. [委派](/docs/user-guide/features/delegation)
5. [钩子](/docs/user-guide/features/hooks)

:::tip
Cron 任务让 Hermes Agent 按计划运行——每日摘要、定时检查、自动报表等，无需人工干预。
:::

### “我想要构建自定义工具/技能”

通过插件扩展 Hermes Agent，添加自己的工具和可复用的技能包。

1. [插件](/docs/user-guide/features/plugins)
2. [构建 Hermes 插件](/docs/guides/build-a-hermes-plugin)
3. [工具概览](/docs/user-guide/features/tools)
4. [技能概览](/docs/user-guide/features/skills)
5. [MCP（模型上下文协议）](/docs/user-guide/features/mcp)
6. [架构](/docs/developer-guide/architecture)
7. [添加工具](/docs/developer-guide/adding-tools)
8. [创建技能](/docs/developer-guide/creating-skills)

:::tip
大多数自定义工具请从插件入手。"添加工具"章节针对的是 Hermes 核心的内部开发，不是普通用户的路径。
:::

### “我想要训练模型”

使用强化学习（RL）管道对模型行为进行微调。

1. [快速入门](/docs/getting-started/quickstart)
2. [配置](/docs/user-guide/configuration)
3. [RL 训练](/docs/user-guide/features/rl-training)
4. [提供商路由](/docs/user-guide/features/provider-routing)
5. [架构](/docs/developer-guide/architecture)

:::tip
RL 训练在您已熟悉 Hermes Agent 的对话与工具调用机制后效果最佳。若是新手，请先走初学者路径。
:::

### “我想把它当作 Python 库使用”

在自己的 Python 应用中以库的形式集成 Hermes Agent。

1. [安装](/docs/getting-started/installation)
2. [快速入门](/docs/getting-started/quickstart)
3. [Python 库指南](/docs/guides/python-library)
4. [架构](/docs/developer-guide/architecture)
5. [工具](/docs/user-guide/features/tools)
6. [会话](/docs/user-guide/sessions)

## 功能速览

不确定有哪些功能？下面是一览表，帮助您快速定位想要的特性。

| 功能 | 作用 | 链接 |
|---|---|---|
| **Tools** | 内置工具（文件 I/O、搜索、Shell 等） | [Tools](/docs/user-guide/features/tools) |
| **Skills** | 可安装的插件包，提供新能力 | [Skills](/docs/user-guide/features/skills) |
| **Memory** | 跨会话的持久记忆 | [Memory](/docs/user-guide/features/memory) |
| **Context Files** | 将文件或目录喂入对话上下文 | [Context Files](/docs/user-guide/features/context-files) |
| **MCP** | 通过模型上下文协议连接外部工具服务器 | [MCP](/docs/user-guide/features/mcp) |
| **Cron** | 定时任务调度 | [Cron](/docs/user-guide/features/cron) |
| **Delegation** | 为并行工作生成子代理 | [Delegation](/docs/user-guide/features/delegation) |
| **Code Execution** | 以编程方式运行 Python 脚本并调用 Hermes 工具 | [Code Execution](/docs/user-guide/features/code-execution) |
| **Browser** | 网页浏览与抓取 | [Browser](/docs/user-guide/features/browser) |
| **Hooks** | 事件回调与中间件 | [Hooks](/docs/user-guide/features/hooks) |
| **Batch Processing** | 批量处理多个输入 | [Batch Processing](/docs/user-guide/features/batch-processing) |
| **RL Training** | 使用强化学习微调模型 | [RL Training](/docs/user-guide/features/rl-training) |
| **Provider Routing** | 在多个 LLM 提供商之间路由请求 | [Provider Routing](/docs/user-guide/features/provider-routing) |

## 接下来阅读什么

根据您当前所处阶段：

- **刚完成安装？** → 前往[快速入门](/docs/getting-started/quickstart)开始第一次对话。
- **完成快速入门？** → 阅读[CLI 使用](/docs/user-guide/cli)和[配置](/docs/user-guide/configuration)以自定义设置。
- **已经掌握基础？** → 探索[工具]、[技能]、[记忆]等模块，充分发挥代理的能力。
- **为团队部署？** → 查看[安全]和[会话]章节，了解访问控制和会话管理。
- **准备动手开发？** → 进入[开发者指南](/docs/developer-guide/architecture)了解内部实现并开始贡献。
- **想要实战案例？** → 前往[指南](/docs/guides/tips)获取真实项目和技巧。

:::tip
不必一次阅读完所有内容。选取符合您目标的路径，按顺序阅读链接，即可快速上手。之后随时回到本页寻找下一步。
:::
