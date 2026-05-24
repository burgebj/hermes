---
sidebar_position: 7
title: "子代理委派"
description: "使用 delegate_task 生成隔离的子代理，以并行工作流"
---

# 子代理委派

`delegate_task` 工具会生成拥有独立上下文、受限工具集以及独立终端会话的子 AIAgent 实例。每个子代理拥有全新的对话并独立工作 —— 只有它们的最终摘要会进入父代理的上下文。

## 单任务

```python
delegate_task(
    goal="调试测试失败的原因",
    context="错误：test_foo.py 第 42 行的断言",
    toolsets=["terminal", "file"]
)
```

## 并行批处理

默认最多可同时运行 3 个子代理（可配置，无硬性上限）：

```python
delegate_task(tasks=[
    {"goal": "研究主题 A", "toolsets": ["web"]},
    {"goal": "研究主题 B", "toolsets": ["web"]},
    {"goal": "修复构建", "toolsets": ["terminal", "file"]}
])
```

## 子代理上下文如何工作

:::warning Critical: Subagents Know Nothing
子代理 **从全新对话开始**。它们对父代理的对话历史、先前的工具调用或任何之前讨论的内容一无所知。子代理唯一的上下文来源于父代理在调用 `delegate_task` 时传入的 `goal` 与 `context` 字段。
:::

这意味着父代理必须在调用中 **提供子代理所需的全部信息**：

```python
# ❌ 错误示例——子代理不知道“错误”是什么
delegate_task(goal="修复错误")

# ✅ 正确示例——子代理拥有所有必要上下文
delegate_task(
    goal="修复 api/handlers.py 中的 TypeError",
    context="""文件 api/handlers.py 第 47 行出现 TypeError：
'NoneType' 对象没有属性 'get'。
函数 process_request() 从 parse_body() 获取 dict，
但当 Content-Type 缺失时，parse_body() 返回 None。
项目位于 /home/user/myproject，使用 Python 3.11。"""
)
```

子代理会收到一个由你的目标和上下文构建的系统提示，指示它完成任务并提供结构化摘要，包括执行了什么、发现了什么、修改了哪些文件以及遇到的任何问题。

## 实用示例

### 并行研究

同时研究多个主题并收集摘要：

```python
delegate_task(tasks=[
    {
        "goal": "研究 2025 年 WebAssembly 的现状",
        "context": "关注点：浏览器支持、非浏览器运行时、语言支持",
        "toolsets": ["web"]
    },
    {
        "goal": "研究 2025 年 RISC‑V 的采用情况",
        "context": "关注点：服务器芯片、嵌入式系统、软件生态",
        "toolsets": ["web"]
    },
    {
        "goal": "研究 2025 年量子计算的进展",
        "context": "关注点：错误纠正突破、实际应用、关键企业",
        "toolsets": ["web"]
    }
])
```

### 代码审查 + 修复

将审查‑修复工作流交给全新上下文的子代理：

```python
delegate_task(
    goal="审查认证模块的安全问题并修复所有发现的缺陷",
    context="""项目位于 /home/user/webapp。
认证模块文件：src/auth/login.py、src/auth/jwt.py、src/auth/middleware.py。
项目使用 Flask、PyJWT 和 bcrypt。
关注点：SQL 注入、JWT 验证、密码处理、会话管理。
修复所有发现的问题并运行测试套件 (pytest tests/auth/)。""",
    toolsets=["terminal", "file"]
)
```

### 多文件重构

当一次性重构大量文件会把父代理的上下文塞满时，可以交给子代理完成：

```python
delegate_task(
    goal="将 src/ 下所有 Python 文件的 print() 替换为合适的日志调用",
    context="""项目位于 /home/user/myproject。
使用 `logging` 模块，获取 logger = logging.getLogger(__name__)。
将 print() 调用映射为对应的日志级别：
- print(f"Error: ...") -> logger.error(...)
- print(f"Warning: ...") -> logger.warning(...)
- print(f"Debug: ...") -> logger.debug(...)
- 其他 print -> logger.info(...)
不要修改测试文件或 CLI 输出中的 print()。
完成后运行 pytest 验证功能未受影响。""",
    toolsets=["terminal", "file"]
)
```

## 批处理模式细节

当提供 `tasks` 数组时，子代理会使用 **线程池** 并行运行：

- **最大并发数**：默认 3（可通过 `delegation.max_concurrent_children` 或环境变量 `DELEGATION_MAX_CONCURRENT_CHILDREN` 调整；下限 1，无硬性上限）。超过限制的批次会返回工具错误，而不是悄悄截断。
- **线程池实现**：使用 `ThreadPoolExecutor`，并发数即为最大工作线程数。
- **进度展示**：在 CLI 模式下，以树形视图实时显示每个子代理的工具调用；在网关模式下，进度会被批量收集并通过父代理的进度回调返回。
- **结果顺序**：无论子代理完成顺序如何，返回的结果都会按任务在输入数组中的顺序排序。
- **中断传播**：中断父代理（例如用户发送新消息）会同时中断所有活跃子代理。

单任务委派直接执行，不经过线程池开销。

## 模型覆盖

可以通过 `config.yaml` 为子代理配置不同的模型，以便将简单任务交给更廉价/更快的模型：

```yaml
# 位于 ~/.hermes/config.yaml
delegation:
  model: "google/gemini-flash-2.0"    # 子代理使用的更便宜模型
  provider: "openrouter"              # 可选：为子代理指定不同的提供商
```

若未设置，子代理默认使用与父代理相同的模型。

## 工具集选择建议

`toolsets` 参数决定子代理可以使用哪些工具。请根据任务需求选择：

| 工具集模式 | 使用场景 |
|------------|----------|
| `["terminal", "file"]` | 代码工作、调试、文件编辑、构建 |
| `["web"]` | 研究、事实核查、文档检索 |
| `["terminal", "file", "web"]` | 全栈任务（默认） |
| `["file"]` | 只读分析、代码审查（不执行） |
| `["terminal"]` | 系统管理、进程管理 |

子代理始终会屏蔽以下工具集（即使你显式声明）：
- `delegation` —— 叶子子代理默认不可再委派（除非 `role="orchestrator"` 并且提升 `max_spawn_depth`）。
- `clarify` —— 子代理不能与用户交互。
- `memory` —— 不能写入共享持久内存。
- `code_execution` —— 子代理应通过逐步推理完成任务。
- `send_message` —— 禁止跨平台副作用（如发送 Telegram 消息）。

## 最大迭代次数

每个子代理都有迭代上限（默认 50），控制它可以进行多少次工具调用：

```python
delegate_task(
    goal="快速文件检查",
    context="检查 /etc/nginx/nginx.conf 是否存在并打印前 10 行",
    max_iterations=10  # 简单任务不需要太多轮次
)
```

## 子代理超时

若子代理在 `delegation.child_timeout_seconds` 秒内没有任何输出，则被视为卡死并被强制终止。默认 **600 秒**（10 分钟），比之前的 300 秒更宽松，以防止大型推理任务在中途被杀。可以根据模型速度自行调节：

```yaml
delegation:
  child_timeout_seconds: 600   # 默认值
```

计时器会在子代理每次进行 API 调用或工具调用时重置，只有真正空闲时才会触发。

:::tip Diagnostic dump on zero-call timeout
如果子代理在没有进行任何 API 调用的情况下超时（常见于提供商不可达、凭证错误或工具模式被拒），`delegate_task` 会在 `~/.hermes/logs/` 下生成结构化诊断日志 `subagent-timeout-<session>-<timestamp>.log`，其中包含子代理的配置快照、凭证解析轨迹以及早期错误信息。相比过去的沉默超时，这大大便于排查。
:::

## 监控运行中的子代理（`/agents`）

TUI 自带 `/agents`（别名 `/tasks`）覆盖层，将递归 `delegate_task` 的 fan‑out 以第一类审计视图呈现：

- 实时树形展示运行中和最近结束的子代理，按父子关系分组
- 每个分支的费用、token 消耗、触及文件的汇总
- 终止与暂停控制 —— 可单独取消某个子代理而不影响其兄弟
- 事后回顾：即使子代理已返回父代理，也可以逐步查看其每轮历史记录

经典 CLI 仅输出文本摘要；TUI 则提供可交互的覆盖层。详见 [TUI — Slash commands](/docs/user-guide/tui#slash-commands)。

## 深度限制与嵌套编排

默认情况下，委派是 **扁平的**：父代理（深度 0）生成子代理（深度 1），而这些子代理不能再进一步委派，以防止无限递归。

若需要多阶段工作流（例如先研究再综合），父代理可以生成 **编排子代理**，它们能够再次委派自己的工作者：

```python
delegate_task(
    goal="评估三种代码审查方法并给出推荐",
    role="orchestrator",  # 允许该子代理自行生成子代理
    context="...",
)
```

- `role="leaf"`（默认）：子代理不可再委派 —— 与扁平委派行为相同。
- `role="orchestrator"`：子代理保留 `delegation` 工具集。受全局 `delegation.max_spawn_depth` 控制（默认 **1**，即平面；提升到 2 允许编排子代理再生成叶子级子代理；3 则支持三层）。
- `delegation.orchestrator_enabled: false`：全局关闭，所有子代理强制为 `leaf`。

**费用警示**：若 `max_spawn_depth: 3` 且 `max_concurrent_children: 3`，树形结构最高可达 3×3×3 = 27 个并发叶子代理。每多一级都会乘以费用——请有意识地提升深度。

## 生命周期与持久性

:::warning delegate_task is synchronous — not durable
`delegate_task` **在父代理的当前回合内同步执行**。它会阻塞父代理直到所有子代理完成（或被取消），并 **不** 作为后台任务队列持久化运行：

- 若父代理被中断（用户发送新消息、`/stop`、`/new`），所有活跃子代理都会被取消，返回 `status="interrupted"`，其进行中的工作将被丢弃。
- 子代理 **不会** 在父回合结束后继续运行。
- 被取消的子代理会返回结构化结果（`status="interrupted"`, `exit_reason="interrupted"`），但由于父回合已被中断，这些结果往往无法展示给用户。

如需 **持久化长时间运行的任务**，请使用以下机制：

- `cronjob`（action=`create`）——调度独立的代理运行，免受父回合中断影响。
- `terminal(background=True, notify_on_complete=True)` —— 在后台运行的 shell 命令，代理仍可继续处理其他事务。
:::

## 关键属性

- 每个子代理拥有 **独立的终端会话**（与父代理分离）
- **嵌套委派为可选** —— 仅 `role="orchestrator"` 子代理可在提升 `max_spawn_depth` 后再委派；全局可通过 `orchestrator_enabled: false` 禁用。
- 叶子子代理 **不能** 调用: `delegate_task`, `clarify`, `memory`, `send_message`, `code_execution`。编排子代理保留 `delegate_task`，但仍受前四项限制。
- **中断传播**：中断父代理会连带中断所有活跃子代理（包括编排子代理的子代理）。
- 仅最终摘要进入父上下文，令 token 使用保持高效。
- 子代理继承父代理的 **API key、提供商配置和凭证池**（便于在速率限制时进行密钥轮换）。

## Delegation 与 execute_code 对比

| 对比维度 | delegate_task | execute_code |
|----------|---------------|--------------|
| **推理** | 完整 LLM 推理循环 | 仅执行 Python 代码 |
| **上下文** | 新的独立对话 | 无对话，仅脚本执行 |
| **工具访问** | 所有非阻塞工具 | 通过 RPC 提供的 7 种工具，无推理 |
| **并行性** | 默认 3 个并发子代理（可配置） | 单脚本执行 |
| **适用场景** | 需要判断、复杂多步骤的任务 | 机械化的多步骤流水线 |
| **Token 成本** | 更高（完整 LLM 循环） | 更低（仅返回 stdout） |
| **用户交互** | 无（子代理不能澄清） | 无 |

**经验法则**：当子任务需要推理、判断或多步骤问题求解时使用 `delegate_task`；当需要机械数据处理或脚本化工作流时使用 `execute_code`。

## 配置示例

```yaml
# 位于 ~/.hermes/config.yaml
delegation:
  max_iterations: 50                        # 每个子代理的最大回合（默认 50）
  # max_concurrent_children: 3              # 每批并行子代理数（默认 3）
  # max_spawn_depth: 1                      # 树深度 1‑3，默认 1 为扁平。提升到 2 允许编排子代理生成叶子子代理；3 为三层。
  # orchestrator_enabled: true              # 关闭则所有子代理强制为 leaf 角色。
  model: "google/gemini-3-flash-preview"   # 可选的模型覆盖
  provider: "openrouter"                    # 可选的内置提供商

# 或使用自建端点覆盖提供商配置：
delegation:
  model: "qwen2.5-coder"
  base_url: "http://localhost:1234/v1"
  api_key: "local-key"
```

:::tip
代理会根据任务复杂度自动决定是否进行委派。用户无需显式请求委派，代理在必要时会自行启动子代理。
:::
