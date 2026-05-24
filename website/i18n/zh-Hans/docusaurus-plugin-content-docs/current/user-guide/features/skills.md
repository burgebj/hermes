---
sidebar_position: 2
title: "Skills System"
description: "On-demand knowledge documents — progressive disclosure, agent-managed skills, and the Skills Hub"
---

# 技能系统

技能是按需加载的知识文档，代理在需要时加载。它们遵循 **渐进式披露**（progressive disclosure）模式，以最小化 token 使用，并兼容 [agentskills.io](https://agentskills.io/specification) 开放标准。

所有技能都位于 **`~/.hermes/skills/`** —— 这是唯一且权威的目录。全新安装时，捆绑技能会从仓库复制出来。通过 Hub 安装的以及代理创建的技能也会放在此处。代理可以修改或删除任意技能。

你也可以让 Hermes 指向 **外部技能目录**——额外的文件夹会与本地目录一起被扫描。参见下文的 [外部技能目录](#external-skill-directories)。

另请参阅：

- [捆绑技能目录](/docs/reference/skills-catalog)
- [官方可选技能目录](/docs/reference/optional-skills-catalog)

## 使用技能

每个已安装的技能会自动提供一个斜杠命令：

```bash
# 在 CLI 或任意消息平台上：
/gif-search funny cats
/axolotl help me fine-tune Llama 3 on my dataset
/github-pr-workflow create a PR for the auth refactor
/plan design a rollout for migrating our auth provider

# 仅输入技能名即可加载，并让代理询问你的需求：
/excalidraw
```

捆绑的 `plan` 技能是一个典型示例。运行 `/plan [request]` 会加载该技能的说明，指示 Hermes 在必要时检查上下文，写一份 Markdown 实现计划而不是直接执行任务，并将结果保存在工作区/后端工作目录下的 `.hermes/plans/` 中。

你也可以在自然对话中与技能交互：

```bash
hermes chat --toolsets skills -q "What skills do you have?"
hermes chat --toolsets skills -q "Show me the axolotl skill"
```

## 渐进式披露

技能使用一种令牌高效的加载模式：

```
Level 0: skills_list()           → [{name, description, category}, ...]   (~3k tokens)
Level 1: skill_view(name)        → 完整内容 + 元数据       (大小可变)
Level 2: skill_view(name, path)  → 特定引用文件       (大小可变)
```

只有在真正需要时，代理才会加载完整的技能内容。

## SKILL.md 格式

```markdown
---
name: my-skill
description: Brief description of what this skill does
version: 1.0.0
platforms: [macos, linux]     # 可选 — 限制特定操作系统平台
metadata:
  hermes:
    tags: [python, automation]
    category: devops
    fallback_for_toolsets: [web]    # 可选 — 条件激活（见下文）
    requires_toolsets: [terminal]   # 可选 — 条件激活（见下文）
    config:                          # 可选 — config.yaml 设置
      - key: my.setting
        description: "What this controls"
        default: "value"
        prompt: "Prompt for setup"
---

# Skill Title

## When to Use
触发此技能的使用条件。

## Procedure
1. 步骤一
2. 步骤二

## Pitfalls
- 已知的失败模式及解决办法

## Verification
如何确认其成功运行。
```

### 平台特定技能

技能可以通过 `platforms` 字段限制只能在特定操作系统上使用：

| Value | Matches |
|-------|---------|
| `macos` | macOS (Darwin) |
| `linux` | Linux |
| `windows` | Windows |

```yaml
platforms: [macos]            # 仅 macOS（例如 iMessage、Apple Reminders、FindMy）
platforms: [macos, linux]     # macOS 与 Linux 均可
```

设置后，技能会在不兼容的平台上被隐藏，不会出现在系统提示、`skills_list()` 或斜杠命令中。若不设置，则在所有平台均可加载。

### 条件激活（后备技能）

技能可以根据当前会话中可用的工具集自动显示或隐藏。这在 **后备技能**（免费或本地的替代方案）最有用，当高级付费工具不可用时才出现。

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # 仅在这些 toolsets 不可用时显示
    requires_toolsets: [terminal]     # 仅在这些 toolsets 可用时显示
    fallback_for_tools: [web_search]  # 仅在这些具体工具不可用时显示
    requires_tools: [terminal]        # 仅在这些具体工具可用时显示
```

| Field | Behavior |
|-------|----------|
| `fallback_for_toolsets` | 当列出的 toolsets **可用** 时技能 **隐藏**；缺失时显示 |
| `fallback_for_tools` | 同上，但检查单个工具 |
| `requires_toolsets` | 当列出的 toolsets **不可用** 时技能 **隐藏**；可用时显示 |
| `requires_tools` | 同上，检查单个工具 |

**示例**：内置 `duckduckgo-search` 技能使用 `fallback_for_toolsets: [web]`。当你设置了 `FIRECRAWL_API_KEY`，`web` toolset 可用，代理会使用 `web_search`，此时 DuckDuckGo 技能保持隐藏。若缺少该 API key，`web` toolset 不可用，DuckDuckGo 技能则作为后备自动出现。

未声明任何条件字段的技能行为保持不变——始终可见。

## 加载时的安全设置

技能可以声明所需的环境变量，但不会因此从发现列表中消失：

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

当加载该技能时若缺少值，Hermes 会在本地 CLI 中安全地询问用户。你可以跳过设置并继续使用技能。消息平台永远不会在聊天中请求机密信息——它们会提示你使用 `hermes setup` 或在本地的 `~/.hermes/.env` 中配置。

一旦设置，声明的环境变量会 **自动传递** 给 `execute_code` 与 `terminal` 沙箱，脚本可以直接使用 `$TENOR_API_KEY`。对于非技能的环境变量，请使用 `terminal.env_passthrough` 配置项。详情请参见 [环境变量透传](/docs/user-guide/security#environment-variable-passthrough)。

### 技能配置设置

技能还能声明非机密的配置项（路径、偏好），存放于 `config.yaml`：

```yaml
metadata:
  hermes:
    config:
      - key: myplugin.path
        description: Path to the plugin data directory
        default: "~/myplugin-data"
        prompt: Plugin data directory path
```

这些设置会保存在用户的 `config.yaml` 的 `skills.config` 部分。`hermes config migrate` 会提示未配置的项，`hermes config show` 则会展示当前值。技能加载时，其解析后的配置值会注入上下文，代理因此能自动获知已配置的值。

请参阅 [技能设置](/docs/user-guide/configuration#skill-settings) 与 [创建技能 — 配置设置](/docs/developer-guide/creating-skills#config-settings-configyaml)。

## 技能目录结构

```text
~/.hermes/skills/                  # 单一事实来源
├── mlops/                         # 类别目录
│   ├── axolotl/
│   │   ├── SKILL.md               # 必须的主说明文件
│   │   ├── references/            # 附加文档
│   │   ├── templates/             # 输出模板
│   │   ├── scripts/               # 脚本库
│   │   └── assets/                # 资源文件
│   └── vllm/
│       └── SKILL.md
├── devops/
│   └── deploy-k8s/                # 代理创建的技能
│       ├── SKILL.md
│       └── references/
├── .hub/                          # Skills Hub 状态
│   ├── lock.json
│   ├── quarantine/
│   └── audit.log
└── .bundled_manifest              # 记录已种子化的捆绑技能
```

## 外部技能目录

如果你在 Hermes 之外维护技能，例如共享的 `~/.agents/skills/` 目录，可让 Hermes 也扫描这些目录。

在 `~/.hermes/config.yaml` 的 `skills` 部分添加 `external_dirs`：

```yaml
skills:
  external_dirs:
    - ~/.agents/skills
    - /home/shared/team-skills
    - ${SKILLS_REPO}/skills
```

路径支持 `~` 展开以及 `${VAR}` 环境变量替换。

### 工作原理

- **只读**：外部目录仅用于技能发现。代理创建或编辑技能时始终写入 `~/.hermes/skills/`。
- **本地优先**：若同名技能同时存在于本地和外部目录，本地版本会覆盖。
- **完整集成**：外部技能会出现在系统提示索引、`skills_list`、`skill_view` 以及 `/skill-name` 斜杠命令中，表现与本地技能无异。
- **不存在的路径会被静默跳过**：如果配置的目录不存在，Hermes 会忽略且不报错，适用于可选的共享目录。

### 示例

```text
~/.hermes/skills/               # 本地（主、可写）
├── devops/deploy-k8s/
│   └── SKILL.md
└── mlops/axolotl/
    └── SKILL.md

~/.agents/skills/               # 外部（只读、共享）
├── my-custom-workflow/
│   └── SKILL.md
└── team-conventions/
    └── SKILL.md
```

四个技能都会出现在技能索引中。如果你在本地创建同名的 `my-custom-workflow`，它会遮蔽外部版本。

## 代理管理的技能（skill_manage 工具）

代理可以通过 `skill_manage` 工具创建、更新、删除自己的技能。这是代理的 **过程记忆**——当它在一次会话中找出非平凡的工作流后，会将该方法保存为技能以供日后复用。

### 代理创建技能的时机

- 完成一个复杂任务（5+ 工具调用）且成功
- 在出现错误或死胡同时找到可行路径
- 用户纠正了它的做法
- 发现了非平凡的工作流

### 操作表

| Action | 用途 | 关键参数 |
|--------|------|----------|
| `create` | 从零创建新技能 | `name`, `content`（完整 SKILL.md），可选 `category` |
| `patch` | 有针对性的修补（首选） | `name`, `old_string`, `new_string` |
| `edit` | 大幅结构性改写 | `name`, `content`（完整 SKILL.md 替换） |
| `delete` | 完全移除技能 | `name` |
| `write_file` | 添加/更新辅助文件 | `name`, `file_path`, `file_content` |
| `remove_file` | 删除辅助文件 | `name`, `file_path` |

:::tip
`patch` 操作因只传递变更文本而更省 token，推荐用于更新。
:::

## 技能 Hub

浏览、搜索、安装、管理来自在线注册表、`skills.sh`、知名技能端点以及官方可选技能的技能。

### 常用命令

```bash
hermes skills browse                              # 浏览所有 Hub 技能（官方优先）
hermes skills browse --source official            # 只浏览官方可选技能
hermes skills search kubernetes                   # 搜索所有源
hermes skills search react --source skills-sh     # 在 skills.sh 目录中搜索
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect openai/skills/k8s           # 安装前预览
hermes skills install openai/skills/k8s           # 带安全扫描的安装
hermes skills install official/security/1password
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install https://sharethis.chat/SKILL.md              # 直接 URL（单文件 SKILL.md）
hermes skills install https://example.com/SKILL.md --name my-skill # 当 frontmatter 无 name 时覆盖名称
hermes skills list --source hub                   # 列出 Hub 安装的技能
hermes skills check                               # 检查已安装 Hub 技能是否有上游更新
hermes skills update                              # 需要时重新安装有更新的 Hub 技能
hermes skills audit                               # 全部 Hub 技能安全重新扫描
hermes skills uninstall k8s                       # 删除某个 Hub 技能
hermes skills reset google-workspace              # 解除捆绑技能的 “用户已修改” 标记（见下文）
hermes skills reset google-workspace --restore    # 同时恢复为捆绑版本，删除本地编辑
hermes skills publish skills/my-skill --to github --repo owner/repo
hermes skills snapshot export setup.json          # 导出技能配置
hermes skills tap add myorg/skills-repo           # 添加自定义 GitHub 来源
```

### 支持的 Hub 来源

| Source | 示例 | 说明 |
|--------|------|------|
| `official` | `official/security/1password` | 随 Hermes 分发的可选技能 |
| `skills-sh` | `skills-sh/vercel-labs/agent-skills/vercel-react-best-practices` | 通过 `hermes skills search <query> --source skills-sh` 搜索。Hermes 会在 slug 与实际仓库路径不一致时进行解析。 |
| `well-known` | `well-known:https://mintlify.com/docs/.well-known/skills/mintlify` | 直接从网站的 `/.well-known/skills/index.json` 发现的技能。 |
| `url` | `https://sharethis.chat/SKILL.md` | 单文件 `SKILL.md` 的直接 HTTP(S) URL。 |
| `github` | `openai/skills/k8s` | 直接从 GitHub 仓库/路径安装，也可以自定义 tap。 |
| `clawhub`, `lobehub`, `claude-marketplace` | 各社区或市场来源 | 社区或市场集成。 |

### 集成的 Hub 与注册表

#### 1. 官方可选技能 (`official`)
这些技能维护在 Hermes 仓库本身，安装时默认信任。
- 目录：`optional-skills/`
- 示例：
```bash
hermes skills browse --source official
hermes skills install official/security/1password
```

#### 2. skills.sh (`skills-sh`)
Vercel 公开的技能目录。Hermes 可以直接搜索、检查详情页并从底层仓库安装。
- 站点: https://skills.sh/
- CLI/工具仓库: https://github.com/vercel-labs/skills
- 官方 Vercel 技能仓库: https://github.com/vercel-labs/agent-skills
- 示例：
```bash
hermes skills search react --source skills-sh
hermes skills inspect skills-sh/vercel-labs/json-render/json-render-react
hermes skills install skills-sh/vercel-labs/json-render/json-render-react --force
```

#### 3. Well‑known 技能端点 (`well-known`)
基于 URL 的发现，适用于在站点上发布 `/.well-known/skills/index.json` 的情况。
- 示例端点: https://mintlify.com/docs/.well-known/skills/index.json
- 示例：
```bash
hermes skills search https://mintlify.com/docs --source well-known
hermes skills inspect well-known:https://mintlify.com/docs/.well-known/skills/mintlify
hermes skills install well-known:https://mintlify.com/docs/.well-known/skills/mintlify
```

#### 4. 直接 GitHub 技能 (`github`)
Hermes 可以直接从 GitHub 仓库安装技能，亦可添加自定义 tap。
- 常用的默认 tap：
  - openai/skills
  - anthropics/skills
  - huggingface/skills
  - VoltAgent/awesome-agent-skills
  - garrytan/gstack
- 示例：
```bash
hermes skills install openai/skills/k8s
hermes skills tap add myorg/skills-repo
```

#### 5. ClawHub (`clawhub`)
第三方技能市场的社区来源。
- 站点: https://clawhub.ai/
- Hermes source id: `clawhub`

#### 6. Claude Marketplace (`claude-marketplace`)
支持发布 Claude 兼容插件/市场清单的仓库。
- 已集成来源包括：
  - anthropics/skills
  - aiskillstore/marketplace
- Hermes source id: `claude-marketplace`

#### 7. LobeHub (`lobehub`)
Hermes 可搜索 LobeHub 公共目录并转换为可安装的 Hermes 技能。
- 站点: https://lobehub.com/
- 公共 agents 索引: https://chat-agents.lobehub.com/
- 后端仓库: https://github.com/lobehub/lobe-chat-agents
- Hermes source id: `lobehub`

#### 8. 直接 URL (`url`)
安装单文件 `SKILL.md`，适用于作者自行托管技能的情况。
- 仅限单文件 `SKILL.md`；多文件技能需使用其他来源。
```bash
hermes skills install https://sharethis.chat/SKILL.md
hermes skills install https://example.com/my-skill/SKILL.md --category productivity
```

**名称解析顺序**：
1. `name:` frontmatter（推荐）
2. URL 路径父目录名（若满足 `^[a-z][a-z0-9_-]*$`）
3. 交互式提示（终端）
4. 非交互式表面错误并要求 `--name` 参数

```bash
# 前置条件没有 name 且 URL slug 不好用时：
hermes skills install https://example.com/SKILL.md --name sharethis-chat
# 在聊天中使用：
/skills install https://example.com/SKILL.md --name sharethis-chat
```

信任级别始终为 `community`——与其他来源相同的安全扫描。URL 会被记录为安装标识符，`hermes skills update` 会自动从同一 URL 重新获取。

## 安全扫描与 `--force`
所有 Hub 安装的技能都会经过 **安全扫描**，检查数据外泄、提示注入、破坏性命令、供应链信号等威胁。

`hermes skills inspect …` 还会展示上游元数据：
- 仓库 URL
- skills.sh 详情页 URL
- 安装指令
- 周安装次数
- 上游安全审计状态
- well-known 索引/端点 URL

当你审查完第三方技能并决定覆盖非致命的策略阻断时，可使用 `--force`：
```bash
hermes skills install skills-sh/anthropics/skills/pdf --force
```

重要行为：
- `--force` 能覆盖 **警告**（warn）类型的策略阻断。
- `--force` **不能**覆盖 **危险**（dangerous） verdict。
- 官方可选技能 (`official/...`) 被视为内置信任，不会出现第三方警告面板。

## 信任等级

| Level | Source | Policy |
|-------|--------|--------|
| `builtin` | 随 Hermes 分发 | 始终信任 |
| `official` | 仓库中的 `optional-skills/` | 内置信任，无第三方警告 |
| `trusted` | 受信任的注册表/仓库（如 openai/skills 等） | 比社区来源更宽松的策略 |
| `community` | 其它所有来源（skills.sh、well‑known、GitHub 自定义等） | 非危险发现可用 `--force` 覆盖；危险发现仍被阻止 |

## 更新生命周期
Hub 会记录足够的来源信息以便重新检查已安装技能的上游副本：
```bash
hermes skills check          # 报告哪些已安装的 Hub 技能在上游有变更
hermes skills update         # 只重新安装有更新的技能
hermes skills update react   # 单独更新指定的已安装 Hub 技能
```
这通过存储的来源标识符以及当前上游内容哈希来检测漂移。

:::tip GitHub 速率限制
Hub 操作使用 GitHub API，未认证用户每小时 60 次请求。若遇到速率限制错误，可在 `.env` 中设置 `GITHUB_TOKEN` 以提升至 5,000 次/小时。错误信息会提供相应提示。
:::

## 发布自定义技能 Tap
如果你想分享一组经过策划的技能（团队、组织或公开），可以将它们作为 **tap** 发布：一个 GitHub 仓库，其他 Hermes 用户使用 `hermes skills tap add <owner/repo>` 添加。
无需服务器、注册表或发布流水线，只要在仓库中提供 `SKILL.md` 文件即可。

### 仓库布局
```
owner/repo
├── skills/                       # 默认路径，可在 tap 中自定义
│   ├── my-workflow/
│   │   ├── SKILL.md              # 必须
│   │   ├── references/           # 可选支持文件
│   │   ├── templates/
│   │   └── scripts/
│   ├── another-skill/
│   │   └── SKILL.md
│   └── third-skill/
│       └── SKILL.md
└── README.md                     # 可选但有帮助
```
**规则**：
- 每个技能必须在 Tap 根路径（默认 `skills/`）下拥有独立目录。
- 目录名即为技能的安装 slug。
- 必须包含 `SKILL.md`，其中包含标准 frontmatter（`name`、`description`，以及可选的 `metadata.hermes.tags`、`version`、`author`、`platforms`、`metadata.hermes.config` 等）。
- `references/`、`templates/`、`scripts/`、`assets/` 等子目录会在安装时一起下载。
- 以 `.` 或 `_` 开头的目录会被忽略。

Hermes 通过遍历 Tap 路径的每个子目录并检查 `SKILL.md` 来发现技能。

### 最小 Tap 示例
```
my-org/hermes-skills
└── skills/
    └── deploy-runbook/
        └── SKILL.md
```
`skills/deploy-runbook/SKILL.md`:
```markdown
---
name: deploy-runbook
description: 我们的部署运行手册 — 服务、回滚、Slack 频道
version: 1.0.0
author: My Org Platform Team
metadata:
  hermes:
    tags: [deployment, runbook, internal]
---
# Deploy Runbook

Step 1: ...
```
推送到 GitHub 后，任何 Hermes 用户均可订阅并安装：
```bash
hermes skills tap add my-org/hermes-skills
hermes skills search deploy
hermes skills install my-org/hermes-skills/deploy-runbook
```

### 非默认路径
若技能不在 `skills/` 目录下（例如在已有项目中添加 `skills/` 子树），请编辑 `~/.hermes/.hub/taps.json`：
```json
{
  "taps": [
    {"repo": "my-org/platform-docs", "path": "internal/skills/"}
  ]
}
```
`hermes skills tap add` 默认使用 `path: "skills/"`，如需不同路径请手动编辑。`hermes skills tap list` 会显示每个 Tap 的实际路径。

### 直接安装单个技能（无需添加 Tap）
用户也可以直接从任意公开 GitHub 仓库安装单个技能：
```bash
hermes skills install owner/repo/skills/my-workflow
```
适用于只想分享单个技能而不要求用户订阅整个仓库的场景。

### Tap 的信任等级
新添加的 Tap 默认为 `community` 信任。其下的技能会走标准安全扫描并在首次安装时显示第三方警告面板。若你的组织或广受信任的来源需要更高信任，可在 `tools/skills_hub.py` 的 `TRUSTED_REPOS` 中加入对应仓库（需要 Hermes 核心 PR）。

### Tap 管理
```bash
hermes skills tap list                                # 显示所有已配置的 tap
hermes skills tap add myorg/skills-repo               # 添加（默认路径: skills/）
hermes skills tap remove myorg/skills-repo            # 移除
```
在运行中的会话里：
```
/skills tap list
/skills tap add myorg/skills-repo
/skills tap remove myorg/skills-repo
```
Tap 会保存在 `~/.hermes/.hub/taps.json`（首次使用时创建）。

## 捆绑技能更新 (`hermes skills reset`)
Hermes 随仓库自带一套捆绑技能，安装及每次 `hermes update` 时会同步这些技能到 `~/.hermes/skills/`，并在 `~/.hermes/skills/.bundled_manifest` 中记录每个技能的内容哈希（**origin hash**）。

同步时，Hermes 重新计算本地副本的哈希并与 origin hash 对比：
- **未改变** → 安全拉取上游更改，复制新版本并记录新哈希。
- **已修改** → 被视为 **用户已修改**，永久跳过，以防止本地编辑被覆盖。

如果你编辑了捆绑技能，随后想放弃修改并恢复捆绑版本，仅复制 `~/.hermes/hermes-agent/skills/` 的内容是不够的，因为 manifest 仍保留旧的 origin hash。此时需要使用 `hermes skills reset`：
```bash
# 只清除 manifest 条目，保留当前副本；下次同步会以此为基准
hermes skills reset google-workspace

# 完全恢复：删除本地副本并重新复制当前捆绑版本
hermes skills reset google-workspace --restore

# 非交互式（脚本或 TUI）——跳过 --restore 确认
hermes skills reset google-workspace --restore --yes
```
同样的命令可通过聊天斜杠使用：
```text
/skills reset google-workspace
/skills reset google-workspace --restore
```

:::note Profiles
每个配置文件拥有独立的 `.bundled_manifest`，因此 `hermes -p coder skills reset <name>` 只会影响该配置对应的 profile。
:::

## 斜杠命令（在聊天中）
所有相同的命令均可通过 `/skills` 使用：
```text
/skills browse
/skills search react --source skills-sh
/skills search https://mintlify.com/docs --source well-known
/skills inspect skills-sh/vercel-labs/json-render/json-render-react
/skills install openai/skills/skill-creator --force
/skills check
/skills update
/skills reset google-workspace
/skills list
```
官方可选技能仍使用 `official/security/1password`、`official/migration/openclaw-migration` 等标识符。
