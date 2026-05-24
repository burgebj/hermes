---
sidebar_position: 3
title: "持久记忆"
description: "Hermes Agent 如何在会话之间记忆 — MEMORY.md、USER.md 与会话搜索"
---

# 持久记忆

Hermes Agent 拥有有界且精心策划的记忆，可在会话之间持久保存。这让它能够记住你的偏好、项目、环境以及它所学到的东西。

## 工作原理

记忆由两个文件组成：

| 文件 | 用途 | 字符限制 |
|------|------|----------|
| **MEMORY.md** | 代理的个人笔记——环境事实、约定、学习到的内容 | 2,200 字符（≈800 tokens） |
| **USER.md** | 用户画像——你的偏好、沟通风格、期望 | 1,375 字符（≈500 tokens） |

这两个文件存放在 `~/.hermes/memories/`，在会话启动时以冻结快照的形式注入系统提示。代理通过 `memory` 工具自行管理记忆——可以添加、替换或删除条目。

:::info
字符限制可以让记忆保持聚焦。当记忆已满时，代理会合并或替换条目，为新信息腾出空间。
:::

## 记忆在系统提示中的呈现方式

每次会话开始时，记忆条目会从磁盘加载并渲染到系统提示中，形成一个冻结块：

```
══════════════════════════════════════════════
MEMORY (your personal notes) [67% — 1,474/2,200 chars]
══════════════════════════════════════════════
User's project is a Rust web service at ~/code/myapi using Axum + SQLx
§
This machine runs Ubuntu 22.04, has Docker and Podman installed
§
User prefers concise responses, dislikes verbose explanations
```

格式包括：
- 显示存储源（MEMORY 或 USER PROFILE）的标题
- 使用率和字符数，帮助代理了解容量
- 条目之间使用 `§`（章节符）分隔
- 条目可以是多行的

**冻结快照模式**：系统提示的注入只在会话开始时进行一次，期间不会改变。这是有意为之，以保持 LLM 前缀缓存的性能。当代理在会话中添加/删除记忆条目时，改动会立即写入磁盘，但不会在本次会话的系统提示中出现。工具的响应始终展示实时状态。

## 记忆工具操作

代理使用 `memory` 工具并提供以下动作：

- **add** — 添加新记忆条目
- **replace** — 用更新的内容替换已有条目（通过 `old_text` 子串匹配）
- **remove** — 删除不再相关的条目（通过 `old_text` 子串匹配）

没有 `read` 动作——记忆内容会在会话开始时自动注入系统提示。代理将记忆视为对话上下文的一部分。

### 子串匹配

`replace` 与 `remove` 动作使用短唯一子串匹配——不需要完整的条目文本。`old_text` 参数只需提供能够唯一标识单个条目的子串：

```python
# 若记忆中包含 "User prefers dark mode in all editors"
memory(action="replace", target="memory",
       old_text="dark mode",
       content="User prefers light mode in VS Code, dark mode in terminal")
```

如果子串匹配到多个条目，系统会返回错误并要求提供更具体的匹配。

## 两种目标的解释

### `memory` — 代理的个人笔记
用于记住与环境、工作流以及学习经验相关的信息：

- 环境事实（操作系统、工具、项目结构）
- 项目约定与配置
- 工具的怪癖与解决办法
- 已完成任务的日志条目
- 有效的技能与技巧

### `user` — 用户画像
用于记住用户的身份、偏好以及沟通风格：

- 姓名、角色、时区
- 沟通偏好（简洁 vs 详细、格式偏好）
- 讨厌的事物与需要避免的行为
- 工作习惯
- 技术熟练度

## 保存与略过的内容

### 主动保存
代理会自动保存——无需额外指令。它会在学习到以下信息时保存：

- **用户偏好**："我更喜欢 TypeScript 而不是 JavaScript" → 保存到 `user`
- **环境事实**："这台服务器运行 Debian 12，PostgreSQL 16" → 保存到 `memory`
- **纠正**："不要使用 `sudo` 来运行 Docker 命令，用户已在 docker 组中" → 保存到 `memory`
- **约定**："项目使用 Tab、行宽 120、Google 风格文档字符串" → 保存到 `memory`
- **已完成工作**："2026-01-15 将数据库从 MySQL 迁移到 PostgreSQL" → 保存到 `memory`
- **明确请求**："记住我的 API 密钥轮换是每月一次" → 保存到 `memory`

### 略过保存

- **琐碎/显而易见的信息**："用户询问了 Python" — 信息过于宽泛
- **易于重新发现的事实**："Python 3.12 支持 f-string 嵌套" — 可直接网络搜索
- **原始数据转储**：大段代码、日志文件、数据表格 — 超出记忆容量
- **会话特定的临时信息**：一次性调试路径、一次性文件
- **已在上下文文件中出现的内容**：SOUL.md 与 AGENTS.md 的内容

## 容量管理

记忆采用严格的字符限制，以保持系统提示的规模可控：

| 存储 | 限制 | 常见条目数量 |
|------|------|--------------|
| memory | 2,200 字符 | 8-15 条 |
| user | 1,375 字符 | 5-10 条 |

### 当记忆已满会怎样

当尝试添加会导致超出上限的条目时，工具会返回错误：

```json
{
  "success": false,
  "error": "Memory at 2,100/2,200 chars. Adding this entry (250 chars) would exceed the limit. Replace or remove existing entries first.",
  "current_entries": ["..."],
  "usage": "2,100/2,200"
}
```

随后代理应当：
1. 读取错误响应中给出的当前条目列表
2. 确定可以删除或合并的条目
3. 使用 `replace` 将相关条目合并为更短的版本
4. 再 `add` 新条目

**最佳实践**：当系统提示头部显示记忆使用率超过 80% 时，先合并条目再添加新内容。例如，将三个独立的 “项目使用 X” 条目合并为一个综合的项目描述。

### 优秀记忆条目示例

**简洁、信息密集的条目效果最佳：**

```
# 好的：打包多个相关事实
User runs macOS 14 Sonoma, uses Homebrew, has Docker Desktop and Podman. Shell: zsh with oh-my-zsh. Editor: VS Code with Vim keybindings.

# 好的：具体可操作的约定
Project ~/code/api uses Go 1.22, sqlc for DB queries, chi router. Run tests with 'make test'. CI via GitHub Actions.

# 好的：带上下文的经验教训
The staging server (10.0.1.50) needs SSH port 2222, not 22. Key is at ~/.ssh/staging_ed25519.

# 糟糕：太模糊
User has a project.

# 糟糕：冗长
On January 5th, 2026, the user asked me to look at their project which is
located at ~/code/api. I discovered it uses Go version 1.22 and...
```

## 去重防止

记忆系统会自动拒绝完全重复的条目。如果尝试添加已经存在的内容，会返回成功但附带 “no duplicate added” 信息。

## 安全扫描

记忆条目在接受之前会进行注入与泄露模式的安全扫描，因为它们会被注入系统提示。匹配威胁模式（提示注入、凭证泄露、SSH 后门）或包含不可见 Unicode 字符的内容将被阻止。

## 会话搜索

除了 MEMORY.md 与 USER.md，代理还可以使用 `session_search` 工具搜索过去的对话记录：

- 所有 CLI 与消息会话均存储在 SQLite (`~/.hermes/state.db`) 中，使用 FTS5 全文检索
- 搜索结果返回相关的历史对话，并通过 Gemini Flash 进行摘要
- 代理可以查找数周前的讨论，即便这些内容不在当前活跃记忆中

```bash
hermes sessions list    # 浏览过去的会话
```

### session_search 与 memory 的对比

| 功能 | 持久记忆 | 会话搜索 |
|------|----------|----------|
| **容量** | ~1,300 tokens 总计 | 无限（所有会话） |
| **速度** | 即时（已在系统提示中） | 需要搜索+LLM 摘要 |
| **使用场景** | 关键事实始终可用 | 查找特定的过去对话 |
| **管理方式** | 代理手动策划 | 自动——所有会话均被保存 |
| **令牌成本** | 每会话固定约 1,300 tokens | 按需求搜索时产生成本 |

**Memory** 适用于必须始终在上下文中的关键事实。**Session search** 适用于 “我们上周讨论过 X 吗？” 之类需要回溯历史的查询。

## 配置

```yaml
# 在 ~/.hermes/config.yaml 中
memory:
  memory_enabled: true
  user_profile_enabled: true
  memory_char_limit: 2200   # ~800 tokens
  user_char_limit: 1375     # ~500 tokens
```

## 外部记忆提供者

若需要超越 MEMORY.md 与 USER.md 的更深层持久记忆，Hermes 内置了 8 种外部记忆提供者插件——包括 Honcho、OpenViking、Mem0、Hindsight、Holographic、RetainDB、ByteRover 与 Supermemory。

外部提供者 **并行** 于内置记忆运行（永不取代），并提供知识图、语义搜索、自动事实抽取、跨会话用户建模等功能。

```bash
hermes memory setup      # 选择并配置提供者
hermes memory status     # 查看当前激活的提供者
```

请参阅 [Memory Providers](./memory-providers.md) 指南，获取每个提供者的完整细节、设置步骤以及对比表。
