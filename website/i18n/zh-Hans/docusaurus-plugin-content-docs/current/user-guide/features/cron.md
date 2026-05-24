---
sidebar_position: 5
title: "定时任务 (Cron)"
description: "使用自然语言调度自动化任务，通过一个 cron 工具管理，且可附加一个或多个技能"
---

# 定时任务 (Cron)

使用自然语言或 cron 表达式调度任务自动执行。Hermes 通过单一的 `cronjob` 工具提供 cron 管理，以操作式（action）方式代替独立的 schedule/list/remove 工具。

## 现在 cron 能做什么

Cron 任务可以：

- 调度一次性或周期性任务
- 暂停、恢复、编辑、触发和删除任务
- 为任务附加零个、一个或多个技能
- 将结果返回至原始聊天、本地文件或配置好的平台目标
- 在全新的代理会话中运行，并使用常规静态工具列表
- 在 **无代理模式** 下运行 —— 脚本按计划执行，其 stdout 原样返回，不涉及 LLM（参见下方的 [无代理模式（仅脚本任务）](#no-agent-mode-script-only-jobs)）

所有这些都通过 Hermes 自身的 `cronjob` 工具实现，你可以通过自然语言创建、暂停、编辑、删除任务，无需 CLI。

:::warning
Cron 运行的会话无法递归创建更多 cron 任务。Hermes 在 cron 执行中会禁用 cron 管理工具，以防止调度循环失控。
:::

## 创建定时任务

### 在聊天中使用 `/cron`

```bash
/cron add 30m "提醒我检查构建"
/cron add "every 2h" "检查服务器状态"
/cron add "every 1h" "总结新 feed 条目" --skill blogwatcher
/cron add "every 1h" "使用多个技能并合并结果" --skill blogwatcher --skill maps
```

### 使用独立 CLI

```bash
hermes cron create "every 2h" "检查服务器状态"
hermes cron create "every 1h" "总结新 feed 条目" --skill blogwatcher
hermes cron create "every 1h" "使用多个技能并合并结果" \
  --skill blogwatcher \
  --skill maps \
  --name "技能组合"
```

### 通过自然对话

直接向 Hermes 发起请求，例如：

```text
每天早上 9 点，检查 Hacker News 上的 AI 新闻并在 Telegram 上发送摘要。
```

Hermes 会内部使用统一的 `cronjob` 工具完成此操作。

## 具备技能的 cron 任务

cron 任务可以在运行提示前加载一个或多个技能。

### 单一技能

```python
cronjob(
    action="create",
    skill="blogwatcher",
    prompt="检查已配置的 feed 并总结任何新内容。",
    schedule="0 9 * * *",
    name="早间 Feed",
)
```

### 多个技能

技能会按顺序加载。提示成为在这些技能之上叠加的任务指令。

```python
cronjob(
    action="create",
    skills=["blogwatcher", "maps"],
    prompt="寻找本地新活动和有趣地点，并合并为简短简报。",
    schedule="every 6h",
    name="本地简报",
)
```

这在你希望定时代理继承可复用工作流，而不必把完整技能文本塞进 cron 提示时非常有用。

## 在项目目录中运行任务

默认情况下 cron 任务在脱离任何仓库的环境中运行——不会加载 `AGENTS.md`、`CLAUDE.md` 或 `.cursorrules`，终端/文件/代码执行工具的工作目录为网关启动时的目录。使用 `--workdir`（CLI）或 `workdir=`（工具调用）来改变此行为：

```bash
# 独立 CLI（schedule 与 prompt 为位置参数）
hermes cron create "every 1d at 09:00" \
  "审计打开的 PR，汇总 CI 健康并发布到 #eng" \
  --workdir /home/me/projects/acme
```

```python
# 从聊天中，通过 cronjob 工具调用
cronjob(
    action="create",
    schedule="every 1d at 09:00",
    workdir="/home/me/projects/acme",
    prompt="审计打开的 PR，汇总 CI 健康并发布到 #eng",
)
```

设置 `workdir` 后：

- `AGENTS.md`、`CLAUDE.md`、`.cursorrules` 会注入系统提示（同交互式 CLI 的发现顺序）
- `terminal`、`read_file`、`write_file`、`patch`、`search_files`、`execute_code` 等工具的工作目录均为该目录（通过 `TERMINAL_CWD`）
- 必须提供绝对且已存在的目录——相对路径或不存在的目录会在创建/更新时被拒绝
- 使用 `--workdir ""`（或 `workdir=""`）可在编辑时清除并恢复默认行为

:::note Serialization
带有 `workdir` 的作业会在调度器 tick 时顺序执行，而非并行池中。这是刻意的——`TERMINAL_CWD` 为进程全局变量，同时运行的工作目录作业会相互冲突。没有 `workdir` 的作业仍然并行运行。
:::

## 编辑任务

无需删除后重新创建即可修改任务。

### 聊天中

```bash
/cron edit <job_id> --schedule "every 4h"
/cron edit <job_id> --prompt "使用修订后的任务"
/cron edit <job_id> --skill blogwatcher --skill maps
/cron edit <job_id> --remove-skill blogwatcher
/cron edit <job_id> --clear-skills
```

### 独立 CLI

```bash
hermes cron edit <job_id> --schedule "every 4h"
hermes cron edit <job_id> --prompt "使用修订后的任务"
hermes cron edit <job_id> --skill blogwatcher --skill maps
hermes cron edit <job_id> --add-skill maps
hermes cron edit <job_id> --remove-skill blogwatcher
hermes cron edit <job_id> --clear-skills
```

注意：

- 重复 `--skill` 会替换作业的技能列表
- `--add-skill` 会在现有列表后追加
- `--remove-skill` 删除指定技能
- `--clear-skills` 删除所有技能

## 生命周期操作

cron 任务现在拥有更完整的生命周期，而不仅仅是创建/删除。

### 聊天中

```bash
/cron list
/cron pause <job_id>
/cron resume <job_id>
/cron run <job_id>
/cron remove <job_id>
```

### 独立 CLI

```bash
hermes cron list
hermes cron pause <job_id>
hermes cron resume <job_id>
hermes cron run <job_id>
hermes cron remove <job_id>
hermes cron status
hermes cron tick
```

作用说明：

- `pause` — 保留任务但停止调度
- `resume` — 重新启用任务并计算下次运行时间
- `run` — 在下一个调度 tick 时触发任务
- `remove` — 完全删除任务

## 工作原理

**Cron 执行由网关守护进程处理。** 网关每 60 秒 tick 一次调度器，运行到期任务于隔离的代理会话中。

```bash
hermes gateway install     # 安装为用户服务
sudo hermes gateway install --system   # Linux 系统服务（服务器）
hermes gateway             # 前台运行

hermes cron list
hermes cron status
```

### 网关调度器行为

每一次 tick Hermes 会：

1. 从 `~/.hermes/cron/jobs.json` 加载任务
2. 将 `next_run_at` 与当前时间比较
3. 为每个到期任务启动全新的 `AIAgent` 会话
4. 如有附加技能则注入
5. 运行提示直至完成
6. 交付最终响应
7. 更新运行元数据并计算下次调度时间

文件锁 `~/.hermes/cron/.tick.lock` 防止多实例重复运行同一批任务。

## 交付选项

调度任务时，你可以指定结果的发送目标：

| 选项 | 描述 | 示例 |
|------|------|------|
| `"origin"` | 发送回创建任务的地方 | 默认在消息平台 |
| `"local"` | 仅保存到本地文件 (`~/.hermes/cron/output/`) | 默认在 CLI |
| `"telegram"` | Telegram 主频道 | 使用 `TELEGRAM_HOME_CHANNEL` |
| `"telegram:123456"` | 指定 Telegram 会话 ID | 直接发送 |
| `"telegram:-100123:17585"` | 指定 Telegram 主题 | `chat_id:thread_id` 格式 |
| `"discord"` | Discord 主频道 | 使用 `DISCORD_HOME_CHANNEL` |
| `"discord:#engineering"` | 指定 Discord 频道 | 按频道名 |
| `"slack"` | Slack 主频道 |
| `"whatsapp"` | WhatsApp 主渠道 |
| `"signal"` | Signal |
| `"matrix"` | Matrix 主房间 |
| `"mattermost"` | Mattermost 主频道 |
| `"email"` | 邮件 |
| `"sms"` | 通过 Twilio 发送 SMS |
| `"homeassistant"` | Home Assistant |
| `"dingtalk"` | DingTalk |
| `"feishu"` | 飞书/Lark |
| `"wecom"` | 企业微信 |
| `"weixin"` | 微信 |
| `"bluebubbles"` | BlueBubbles (iMessage) |
| `"qqbot"` | QQ Bot |
| `"all"` | 向所有已连接的渠道广播 |
| `"telegram,discord"` | 向特定集合广播 |
| `"origin,all"` | 同时发送到原始和所有渠道 |

代理的最终响应会自动交付，你无需在 cron 提示中调用 `send_message`。仅在需要额外或不同目标时才使用 `send_message`。

### 路由意图 (`all`)

`all` 让你将单个 cron 任务发送到所有已配置的消息渠道，无需逐个列出名称。它在触发时解析——如果在创建任务后才配置了 Telegram，下一次 tick 时该任务会自动包括 Telegram。

语义：`all` 展开为所有已配置了主页渠道的平台。若没有配置任何渠道，任务仅记录交付失败。

`all` 可与显式目标组合，例如 `origin,all`，会把原始聊天与所有其他已连接渠道一起发送，并按 `(platform, chat_id, thread_id)` 去重。

### 响应包装

默认情况下，交付的 cron 输出会加上头尾，以便接收方知道这是来自计划任务的消息：

```
Cronjob Response: Morning feeds
-------------

<agent output here>

Note: The agent cannot see this message, and therefore cannot respond to it.
```

若想直接返回原始代理输出，可在 `~/.hermes/config.yaml` 中设置 `cron.wrap_response: false`：

```yaml
# ~/.hermes/config.yaml
cron:
  wrap_response: false
```

### 静默抑制

如果代理的最终响应以 `[SILENT]` 开头，则会完全抑制交付。输出仍会保存在本地 (`~/.hermes/cron/output/`) 供审计，但不会发送到任何目标。

这对仅在出现异常时报告的监控任务很有用：

```text
检查 nginx 是否运行。若一切正常，仅回复 [SILENT]。
否则，报告问题。
```

失败的任务始终会交付——只有成功运行且标记为 `[SILENT]` 时才会被静默。

## 脚本超时

预运行脚本（通过 `script` 参数）默认超时 120 秒。如需更长时间（例如加入随机延迟以规避机器行为），可在配置中增加：

```yaml
# ~/.hermes/config.yaml
cron:
  script_timeout_seconds: 300   # 5 分钟
```

或设置环境变量 `HERMES_CRON_SCRIPT_TIMEOUT`。解析顺序为：环境变量 → config.yaml → 默认 120s。

## 无代理模式（仅脚本任务）

对于不需要 LLM 推理的循环任务——经典的看门狗、磁盘/内存告警、心跳、CI ping——在创建时传入 `no_agent=True`。调度器仅运行脚本并把 stdout 直接交付，完全跳过代理：

```bash
hermes cron create "every 5m" \
  --no-agent \
  --script memory-watchdog.sh \
  --deliver telegram \
  --name "memory-watchdog"
```

语义：

- 脚本 stdout（去除前后空白） → 原样交付为消息
- 空 stdout → 静默 tick，不交付
- 非零退出或超时 → 发送错误警报，防止看门狗失效而沉默
- 最后一行 `{"wakeAgent": false}` → 静默 tick（同 LLM 任务的门控）
- 完全不使用模型、提供商回退——任务永不触及推理层

`.sh` / `.bash` 文件在 `/bin/bash` 下运行，其他文件使用当前 Python 解释器 (`sys.executable`)。脚本必须放在 `~/.hermes/scripts/`（同预运行脚本的沙箱规则）。

### 代理为你设置的内容

`cronjob` 工具的 schema 暴露 `no_agent` 给 Hermes，因此你可以在聊天中描述看门狗，代理会自动创建脚本并调用：

```text
如果 RAM 超过 85%，每 5 分钟在 Telegram 上提醒我。
```

Hermes 会将检查脚本写入 `~/.hermes/scripts/`（通过 `write_file`），随后调用：

```python
cronjob(action="create", schedule="every 5m",
        script="memory-watchdog.sh", no_agent=True,
        deliver="telegram", name="memory-watchdog")
```

当消息内容完全由脚本决定时，`no_agent=True` 会被自动添加。

参见 [脚本仅 cron 任务指南](/docs/guides/cron-script-only) 获取完整示例。

## 使用 `context_from` 链接作业

cron 作业在隔离会话中运行，默认不记忆前一次运行的输出。但有时需要将一个作业的输出作为下一个作业的输入。`context_from` 参数可以自动完成此连接——作业 B 的提示会在运行时自动把作业 A 最近的输出当作上下文前置。

```python
# 作业 1：收集原始数据
cronjob(
    action="create",
    prompt="获取 Hacker News 上前 10 条 AI/ML 新闻，保存到 ~/.hermes/data/briefs/raw.md，格式为 markdown，包含标题、URL、分数。",
    schedule="0 7 * * *",
    name="AI News Collector",
)

# 作业 2：筛选 —— 接收作业 1 的输出作为上下文
# 获取作业 1 的 ID：cronjob(action="list")
cronjob(
    action="create",
    prompt="读取 ~/.hermes/data/briefs/raw.md。为每条新闻打 1-10 分的参与度和新颖度分数。输出前 5 条到 ~/.hermes/data/briefs/ranked.md。",
    schedule="30 7 * * *",
    context_from="<job1_id>",
    name="AI News Triage",
)

# 作业 3：发送 —— 接收作业 2 的输出作为上下文
cronjob(
    action="create",
    prompt="读取 ~/.hermes/data/briefs/ranked.md。生成 3 条 tweet 草稿（标题 + 正文 + 标签）。发送至 telegram:7976161601。",
    schedule="0 8 * * *",
    context_from="<job2_id>",
    name="AI News Brief",
)
```

**工作原理：**

- 作业 2 触发时，Hermes 会读取作业 1 最近的输出文件 `~/.hermes/cron/output/{job1_id}/*.md`
- 该内容会预置到作业 2 的提示前部，无需显式 `read_file`
- 作业 3 同理，链式处理可任意长度

### `context_from` 支持的格式

| 格式 | 示例 |
|------|------|
| 单个作业 ID（字符串） | `context_from="a1b2c3d4"` |
| 多个作业 ID（列表） | `context_from=["job_a", "job_b"]` |

输出会按列出顺序拼接。

## 提供商恢复

cron 作业会继承全局配置的回退提供商和凭证池轮换策略。如果主 API 密钥被限流或返回错误，cron 代理可以：

- **回退到备用提供商**（若在 `config.yaml` 中配置 `fallback_providers` 或旧的 `fallback_model`）
- **轮转同提供商的下一个凭证**（使用 [credential pool](/docs/user-guide/configuration#credential-pool-strategies)）

这确保高频或高峰期运行的 cron 作业更具弹性——单个限流键不会导致整个任务失败。

## 调度格式

### 相对延迟（一次性）

```
30m     → 30 分钟后运行一次
2h      → 2 小时后运行一次
1d      → 1 天后运行一次
```

### 间隔（循环）

```
every 30m    → 每 30 分钟一次
every 2h     → 每 2 小时一次
every 1d     → 每天一次
```

### Cron 表达式

```
0 9 * * *       → 每天 9:00 AM
0 9 * * 1-5     → 工作日 9:00 AM
0 */6 * * *     → 每 6 小时一次
30 8 1 * *      → 每月 1 日 8:30 AM
0 0 * * 0       → 每周日午夜
```

### ISO 时间戳

```
2026-03-15T09:00:00    → 2026 年 3 月 15 日 9:00 的一次性任务
```

## 重复行为

| 调度类型 | 默认重复次数 | 行为 |
|----------|--------------|------|
| 一次性 (`30m`, 时间戳) | 1 | 只运行一次 |
| 间隔 (`every 2h`) | 永久 | 直至手动删除 |
| Cron 表达式 | 永久 | 直至手动删除 |

你可以通过 `repeat` 参数覆盖此行为：

```python
cronjob(
    action="create",
    prompt="...",
    schedule="every 2h",
    repeat=5,
)
```

## 编程方式管理作业

代理侧的统一 API 为：

```python
cronjob(action="create", ...)
cronjob(action="list")
cronjob(action="update", job_id="...")
cronjob(action="pause", job_id="...")
cronjob(action="resume", job_id="...")
cronjob(action="run", job_id="...")
cronjob(action="remove", job_id="...")
```

对 `update`，传入 `skills=[]` 可移除全部已附加技能。

## cron 作业可用的工具集

cron 在每个作业中启动全新的代理会话，且没有任何聊天平台绑定。默认情况下，cron 代理获得 **你在 `hermes tools` 中为 `cron` 平台配置的工具集**——而不是 CLI 默认的全部工具。

```bash
hermes tools
# → 在 curses UI 中选择 "cron" 平台
# → 像配置 Telegram/Discord 那样开关工具集
```

对单个作业的更细粒度控制可通过 `enabled_toolsets` 字段实现（在 `cronjob.create` 或 `cronjob.update` 中）：

```text
cronjob(action="create", name="weekly-news-summary",
        schedule="every sunday 9am",
        enabled_toolsets=["web", "file"],      # 只启用 web + file，其他如 terminal/browser 等关闭
        prompt="总结本周 AI 新闻： ...")
```

若作业设置了 `enabled_toolsets`，它将覆盖全局 `hermes tools` 的 cron 配置；若未设置，则使用全局配置；若全局也未配置，则使用内置默认。这对成本控制非常关键：把 `moa`、`browser`、`delegation` 等工具带入每一个“小型抓取”任务会显著增加工具-schema 提示长度和费用。

### 完全跳过代理：`wakeAgent`

如果你的 cron 作业附带前置检查脚本（通过 `script=`），脚本可以在运行时决定是否真的需要唤起代理。若脚本在最后一行输出 JSON `{"wakeAgent": false}`，则本次 tick 将直接跳过代理运行，仅记录日志。

```text
{"wakeAgent": false}
```

这在高频轮询（每 1‑5 分钟）且仅在状态变更时才需要 LLM 推理的场景下可省去大量费用。

```python
# 前置检查脚本示例
import json, sys
latest = fetch_latest_issue_count()
prev = read_state("issue_count")
if latest == prev:
    print(json.dumps({"wakeAgent": False}))   # 本次 tick 静默
    sys.exit(0)
write_state("issue_count", latest)
print(json.dumps({"wakeAgent": True, "context": {"new_issues": latest - prev}}))
```

如果省略 `wakeAgent`，默认视为 `true`（正常唤起代理）。

#### 示例：零成本前置门控

1. **文件变更门** — 仅当监视文件自上一次成功运行后有更新时才执行。
2. **外部标记门** — 其他进程创建标记文件或设置状态后才运行。
3. **SQL 行数门** — 仅当数据库在最近时间窗口内有新记录时才运行。

上述模式均通过脚本返回 `{"wakeAgent": true/false}`，并可通过 `context` 将计数等信息传递给后续代理任务。

## 作业存储

作业记录保存在 `~/.hermes/cron/jobs.json`。运行输出保存至 `~/.hermes/cron/output/{job_id}/{timestamp}.md`。

作业字段 `model`、`provider` 如未设置会在运行时从全局配置解析。仅在作业级别覆盖时才会出现于记录中。

存储采用原子写入，防止中断导致文件损坏。

## 自包含提示仍然重要

:::warning 重要
cron 作业在全新的代理会话中运行。提示必须包含除已附加技能之外的所有必要信息。
:::

**错误示例**：`"检查服务器问题"`

**正确示例**：`"以用户 'deploy' SSH 登录 192.168.1.100，使用 'systemctl status nginx' 检查 nginx 是否运行，并验证 https://example.com 返回 HTTP 200。"

## 安全性

创建和更新 cron 提示时会进行提示注入和凭证泄露检测。包含不可见 Unicode、SSH 后门或明显的秘密泄露负载的提示会被阻止。
