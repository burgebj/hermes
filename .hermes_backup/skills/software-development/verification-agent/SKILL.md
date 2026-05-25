---
name: verification-agent
description: 创建验证/评审 subagent，对主 agent 的最终输出进行独立评审和测试，如不合格则反馈要求修改。包含 Cron Job 故障排查扩展。
version: 2.0.0
tags: [agent-pattern, review, qa, cron, troubleshooting]
---

# 验证 Agent 模式

## 两种实现方式概览

Hermes Agent 提供**两种**验证机制，适用于不同场景：

| 方式 | 机制 | 适用场景 |
|------|------|----------|
| **内置验证循环** | 在 `run_agent.py` 的 `run_conversation()` 末尾自动运行 | 每次文本对话的响应质量把关（零配置） |
| **Subagent 验证** | `delegate_task()` 手动创建独立验证 Agent | 复杂任务（代码生成、数据分析等），需独立评审 |

---

## 方式一：内置文本质量检查（自动运行）

### 概述

代码位于 `run_agent.py`（`_verify_response()`、`_refine_response()`、`_call_llm_simple()` 方法），在 `run_conversation()` 产生最终响应后**自动静默执行**，对用户透明。

> ⚠️ **范围限制：** 这是一个 **保守的文本质量抛光层**，不是真正的验证门。检查器没有工具（不能查事实、不能执行代码、不能看图片），且使用与主 agent **相同的模型/供应商**。它不能可靠捕获幻觉、错误代码或缺失的工具调用结果。

### 运行条件

检查循环在以下条件**同时满足**时触发：

1. `final_response` 不为空
2. `interrupted` 为 `False`（本轮未被用户后续消息打断）
3. `verification_user_message` 是字符串类型（即纯文本请求，非多模态消息）

### 流程

```
最终响应 → 调用 _verify_response()（JSON 格式裁决）
  ├─ PASSED → 通过
  ├─ UNVERIFIABLE → 通过（记录 warning，不阻塞）
  ├─ FAILED → 有反馈 → _refine_response() 改进 → 下一轮（最多2轮）
  └─ 无反馈/JSON解析失败 → 通过（记录 warning，不阻塞）
```

- 最多 **2 轮**静默迭代（从5轮减少，因为同模型验证的价值递减）
- 使用 **严格 JSON 格式** 裁决（`{"verdict": "PASSED|FAILED|UNVERIFIABLE", ...}`）
- 有独立的 `verify_max_tokens` 参数（verifier=1024, refiner=2048）
- Verifier/Refiner 独立于主 agent 的 `max_tokens`
- Verifier prompt 包含**反注入防护**：声明 request/response 块为不可信数据
- Verifier 新增 **`UNVERIFIABLE`** 裁决类别：对无法仅从文本验证的事实不判 fail
- Refiner 包含**内容保持规则**：不编造事实、保留语言/格式、不破坏代码块
- 空白标准化后再做 identical-output 比较（避免空白震荡误判）
- 每轮 refine 后更新历史消息中的 assistant message

### 关键行为特征

- **完全静默**：无控制台输出、无用户可见提示
- **日志分级**：
  - `ERROR` — 检查生命周期开始/结束、轮次耗尽、异常
  - `WARNING` — 每轮通过/失败、JSON解析失败、无反馈、refine 无变化
- **错误安全**：任何异常（LLM 调用失败等）都会静默放过（返回 `(True, "")`）
- **空响应/空白响应直接通过**：`_verify_response()` 会先检查 `not response.strip() or response == "(empty)"`
- **JSON 解析容错**：先尝试直接解析，失败后查找第一个 `{...}` 块

### 如何验证是否生效

```bash
# 检查 agent.log 中是否有 verifier 日志
grep '\[VERIFY\]' ~/.hermes/logs/agent.log

# 预期输出示例：
# [VERIFY] Starting text quality check (max_rounds=2, response_len=1234, model=...)
# [VERIFY] Passed round 1/2 (response len=1234)
```

### 日志级别说明（quiet_mode 兼容）

Gateway 的 `quiet_mode=True` 会将 `run_agent` logger 的 WARNING 级别以下日志抑制。为平衡可观测性和日志洁净度：

- **启动/结束** (`ERROR`) — 穿透 quiet_mode，写入 agent.log
- **每轮状态** (`WARNING`) — quiet_mode 下被抑制（正常运行时不可见），但关键生命周期可追踪
- **异常** (`ERROR`) — 始终可见
- **JSON 解析失败** (`WARNING`) — 被 quiet_mode 抑制，但通常无害（fail-open 通过）

如需完整观察检查循环行为，可临时在 `~/.hermes/run_agent.py` 的 `__init__` 中注释掉 `'run_agent'` 的 setLevel：

```python
for quiet_logger in ['tools', ...]:  # 移除 'run_agent'
    logging.getLogger(quiet_logger).setLevel(logging.ERROR)
```

### 已知局限

1. **无法捕获事实性错误** — 无工具、无检索、无代码执行
2. **同模型偏差** — verifier 使用与主 agent 相同的模型，会重复同样的错误
3. **纯文本限制** — 无法看到图片、文件内容或其他多模态输入
4. **Prompt 注入防护（有限）** — 反注入声明可以防止大多数意外情况，但对有意的 prompt 注入攻击不是绝对防护
5. **非并行** — 最多 2 轮 refine 增加了延迟（每轮一次 LLM 调用）
6. **语言匹配问题（已修复）** — 原 bug 中 `verification_user_message` 在翻译后错误地使用了英文版本，导致中文用户请求+中文回答时，验证器误判为语言不匹配并 FAILED。修复方式：`verification_user_message` 始终使用 `original_user_message`（原始语言），不随翻译改变。[`run_agent.py:10758`]
7. **Refiner 输出泄漏（已修复）** — 原 bug 中 `_refine_response()` 直接返回 LLM 原始输出，可能包含分析文本（"I see the issue..."、"The improved version:"）、JSON 或双版本回答。修复方式：新增 `_sanitize_refined_response()` 方法，剥离标记分隔符、元注释行；净化结果为空时回退到 `current_response`。[`run_agent.py:10579+`]

对于关键任务（代码生成、事实核查、数据分析、文件操作），应使用 **Subagent 验证模式**（见下文）。

---

## 方式二：Subagent 验证模式（手动调用）

### 概述

**双 Agent 工作流**：主 Agent 完成任务 → 验证 Agent（verifier）**只看最终结果** → 评审/测试 → 通过 or 打回修改。

### 关键规则

1. **信息隔离** — 验证 Agent 永远不知道主 Agent 的中间步骤、推理过程、使用了哪些工具
2. **只给结果** — 传给验证 Agent 的只有：最终输出的内容（文件、文本、数据等） + 原始用户需求
3. **严格把关** — 验证 Agent 扮演"挑剔的评审员"角色，对质量负责
4. **反馈回路** — 验证不通过时，输出具体的修改意见，由主 Agent 迭代修改

## 使用场景

- 代码生成 → 验证 Agent 审查代码质量、运行测试
- 数据分析 → 验证 Agent 校验结果正确性
- 文档写作 → 验证 Agent 检查准确性和完整性
- 配置生成 → 验证 Agent 验证配置语法和一致性

## 工作流（通用模板）

### 第1步：主 Agent 完成任务

正常执行用户指令，输出最终结果。

### 第2步：调用验证 Agent

使用 `delegate_task` 创建验证 subagent，只传入：

#### context 字段，包含：
1. **用户原始需求**（原文）
2. **最终输出**（主 Agent 产出的完整结果，如代码、文件、文字等）
3. **验证要求**（e.g. "执行代码并确认运行正常"、"检查逻辑正确性"、"对照需求逐条核对"）

关键：**不传**任何中间步骤、推理过程、使用的命令、尝试过程。

#### 验证 Agent 的 toolsets
- `terminal` — 如果需要执行和测试
- `file` — 如果需要读取检查文件
- 根据任务类型可选：`web`（查证引用）、`browser`（UI 校验）

### 第3步：处理验证结果

验证 Agent 返回结果包含：
- ✅ 结论（通过/不通过）
- 📋 具体问题清单（如有）
- 🔧 修改建议（如有）
- 🔄 是否建议重新评审

如果反馈要求修改：
1. 根据反馈进行修改
2. 再次调用验证 Agent（只传新版最终结果）
3. 重复直到通过

## 验证 Agent prompt 模板

```markdown
你是一个严格的验证/评审 Agent。你的职责是对以下最终输出进行独立的质量评估。

## ⚠️ 严格规则（必须遵守）
1. 你只知道最终结果，**不知道**生成它的人用了什么步骤、工具或方法
2. 不要猜测或假设中间过程，只评审你看到的东西
3. 如果发现问题，请明确指出并给出可操作的修改建议
4. 如果一切合格，明确说"通过"

## 用户需求
<用户原始需求>

## 最终输出
<主Agent的最终产出>

## 验证要求
<具体的验证项目，如：>
- 代码是否正确？能否编译/运行？（请实际执行测试）
- 是否完整覆盖了用户需求？
- 有没有遗漏边界情况？
- 输出格式和内容质量如何？
```

## 示例调用

```python
# 验证 Agent 只传最终结果，不传中间步骤
result = await delegate_task(
    goal="作为验证 agent，对以下输出进行独立评审",
    context=f"""用户需求：{user_request}

最终输出：
{final_output}

验证要求：
1. 执行输出中的代码，测试是否能正常运行
2. 对照用户需求逐条检查是否全部覆盖
3. 检查是否有逻辑错误或遗漏
4. 如发现问题，给出具体的修改建议

注意：你不知道这个输出是如何生成的，只看结果本身。""",
    toolsets=["terminal", "file"]  # 根据实际情况调整
)
```

## 注意事项

- 验证 Agent 的 toolsets 要根据任务类型选择：代码任务需要 `terminal` 和 `file`，纯文本任务可能只需要 `file`
- 复杂的任务（涉及多文件、长时间测试）建议单独为其分配较长的超时时间
- 如果任务对时效性要求高，可以设置 `max_rounds=1` 即验证最多一轮，不通过则直接报告问题由人工决定
- 验证 Agent 的上下文不要包含主 Agent 的任何试探/中间产物，这是最重要的隔离原则

---

## Cron Job 故障排查扩展

> 以下小节整合自原 `cron-job-troubleshooting` skill。Cron 任务作为一种定时验证机制，其故障诊断也属于系统验证的范畴。

### 常见问题速查

| 问题 | 原因 | 修复 |
|------|------|------|
| 没发送结果 | `deliver` 设为 `"local"` | `cronjob(action='update', job_id='xxx', deliver='origin')` |
| 工具不可用 | 工具集受限 | 添加 `enabled_toolsets` |
| 静默失败 `[SILENT]` | 缺少工具或超时 | 查看 session 文件 `~/.hermes/sessions/session_cron_<id>_<timestamp>.json` |
| 模型 404 | 固定模型名不可用 | 更新 model 或清空以使用默认模型 |
| 没运行 | job 被暂停或时间错乱 | `cronjob(action='list')` 确认 `enabled: true` 和 `next_run_at` |
| 推送失败但执行成功 | iLink 连接抖动或 aiohttp 问题 | 从 cron output 恢复数据 |
| 日期错乱 | prompt 中硬编码日期 | 更新 prompt，强制使用 `date "+%Y-%m-%d"` |

### 关键排查路径

**查看完整执行记录（最可靠）：**
```bash
ls -la ~/.hermes/sessions/ | grep cron_<job_id>
cat ~/.hermes/sessions/session_cron_<job_id>_<timestamp>.json
```
Session 文件比 `agent.log` 更可靠（日志可能被轮转或截断）。

**查看 cron output（推送失败时的备选方案）：**
```bash
ls -la ~/.hermes/cron/output/<job_id>/
cat ~/.hermes/cron/output/<job_id>/<latest>.md
```

### 自动健康检查 & 自愈机制

创建健康检查 cron job，每天自动诊断并修复失败的 cron 任务：

```python
# 1. 创建数据收集脚本 ~/.hermes/scripts/cron_health_collector.py
# 2. 创建健康检查 cron job
cronjob(action='create',
    name='Cron 健康检查 & 自动恢复',
    schedule='0 18 * * *',  # 每天北京时间 18:00
    deliver='origin',
    enabled_toolsets=['terminal', 'web', 'search'],
    prompt='''...（见原 cron-job-troubleshooting skill 的完整模板）...''')
```

### 强制恢复（当 scheduler 不执行时）

```bash
# 1. 清除残留 lock
rm -f ~/.hermes/cron/.tick.lock

# 2. 手动设置 next_run_at 为过去时间
python3 -c "
import json, os
from datetime import datetime, timezone, timedelta
path = os.path.expanduser('~/.hermes/cron/jobs.json')
with open(path) as f:
    data = json.load(f)
for j in data['jobs']:
    if j['id'] == '<job_id>':
        j['next_run_at'] = (datetime.now(timezone(timedelta(hours=8))) - timedelta(seconds=5)).isoformat()
with open(path, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
"

# 3. 触发 tick
hermes cron tick --accept-hooks
```
