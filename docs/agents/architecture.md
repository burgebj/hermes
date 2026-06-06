# Architecture / 系统结构与关键入口

## 1. 先看全景
Hermes Agent 当前可按四层理解：

1. **对话执行层**
   - `run_agent.py`
   - `model_tools.py`
   - `toolsets.py`

2. **交互入口层**
   - `cli.py`
   - `hermes_cli/`
   - `gateway/`
   - `acp_adapter/`

3. **能力实现层**
   - `tools/registry.py`
   - `tools/*.py`
   - `tools/environments/`

4. **证明与回归层**
   - `tests/`
   - `docs/exec-plans/`
   - `docs/specs/`
   - `docs/migration/`

## 2. 主依赖链
旧版开发指南最关键的一条链，保留如下：

```text
tools/registry.py
    ↑
tools/*.py
    ↑
model_tools.py
    ↑
run_agent.py / cli.py / batch_runner.py / acp_adapter / gateway
```

怎么用这条链：
- 看工具为什么没暴露：先查 `tools/*.py` 是否注册，再查 `toolsets.py`，再查 `model_tools.py`
- 看模型为什么没调用工具：查 `model_tools.py` schema 生成与过滤
- 看 CLI / gateway 为什么行为不同：查各自入口如何装配 toolsets、config、callbacks

## 3. 关键文件入口
### 3.1 对话与工具
- `run_agent.py`
  - `AIAgent` 主入口
  - 对话循环、消息拼装、工具回填
- `model_tools.py`
  - `get_tool_definitions()`
  - `handle_function_call()`
  - 工具 schema 汇总、可用性过滤、调用分发
- `toolsets.py`
  - 工具集定义
  - 平台可见范围与默认装配

### 3.2 CLI
- `cli.py`
  - 交互式 CLI 编排
  - slash command 分发
  - 与 agent / tools / config 的接线点
- `hermes_cli/commands.py`
  - `COMMAND_REGISTRY`
  - `resolve_command()`
  - 所有 slash command 的注册中心
- `hermes_cli/config.py`
  - `DEFAULT_CONFIG`
  - `OPTIONAL_ENV_VARS`
  - 配置与环境变量元数据

### 3.3 工具系统
- `tools/registry.py`
  - 注册中心
  - schema、handler、availability 管理
- 常看文件：
  - `tools/terminal_tool.py`
  - `tools/file_tools.py`
  - `tools/web_tools.py`
  - `tools/browser_tool.py`
  - `tools/delegate_tool.py`
  - `tools/mcp_tool.py`
- `tools/environments/`
  - 本地、docker、ssh、modal、daytona、singularity 等后端

### 3.4 其他运行面
- `gateway/run.py`
  - 消息平台主循环与分发
- `gateway/platforms/`
  - Telegram / Discord / Slack / WhatsApp / 其他平台适配
- `acp_adapter/`
  - 编辑器集成入口
- `cron/`
  - 定时与调度
- `batch_runner.py`
  - 批处理并行入口

## 4. 配置、状态与路径
- 用户配置：`~/.hermes/config.yaml`
- 用户环境：`~/.hermes/.env`
- 会话/状态/缓存等持久化路径：代码中必须走 `get_hermes_home()` 系列，不要手写 `~/.hermes`
- 用户可见路径展示：走 `display_hermes_home()`

补充判断：
- **CLI** 默认工作目录是当前目录
- **消息平台** 工作目录受 `MESSAGING_CWD` 影响

## 5. 结构化阅读入口
### 5.1 我想理解主循环
按顺序看：
1. `run_agent.py`
2. `model_tools.py`
3. `tools/registry.py`

### 5.2 我想理解 slash command
按顺序看：
1. `hermes_cli/commands.py`
2. `cli.py`
3. `gateway/run.py`（若命令同时进入 gateway）

### 5.3 我想理解工具注册与暴露
按顺序看：
1. `tools/registry.py`
2. 目标 `tools/*.py`
3. `toolsets.py`
4. `model_tools.py`

### 5.4 我想理解配置项从哪里生效
按顺序看：
1. `hermes_cli/config.py`
2. `cli.py`
3. `gateway/run.py`

## 6. 遇到问题先去哪里
| 问题 | 先看哪里 |
|---|---|
| 工具没出现 | `tools/*.py` → `toolsets.py` → `model_tools.py` |
| 命令别名不生效 | `hermes_cli/commands.py` → `cli.py` |
| gateway 与 CLI 行为不一致 | `cli.py` ↔ `gateway/run.py` |
| profile 路径写乱了 | `guardrails.md` 第 2 节 |
| 测试污染本机 `~/.hermes` | `guardrails.md` 第 2 节 |
| 不知道该补哪些证明 | `guardrails.md` 第 5 节 |

## 7. 本文边界
- 本文只告诉你“系统在哪里、入口在哪里、链路怎么找”。
- 具体操作步骤去 `workflows.md`。
- 风险规则、验证与交接去 `guardrails.md`。