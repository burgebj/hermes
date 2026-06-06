# Workflows / 任务型入口

## 1. 通用推进顺序
所有任务默认按这个顺序推进：

1. **Task Contract（任务承诺）**
2. **Architecture Read（结构定位）**
3. **Change Set（改动集）**
4. **Verification Chain（验证链）**
5. **Status Ledger（状态台账）**

注意：这里说明的是推进顺序，不是模板定义。
涉及 Contract / Ledger / Verification 时，必须直接服从已落地标准骨架：
- `hermes-harness-task-contract`
- `hermes-harness-status-ledger`
- `hermes-harness-verification-chain`
- `hermes-harness-skill-change-loop`

禁止在本文另造任何缩水版模板、口袋版字段或并行规范。

## 2. 新增工具 Tool
### 2.1 入口
先读：
1. `docs/agents/architecture.md`
2. `tools/registry.py`
3. 目标相邻工具文件
4. `toolsets.py`

### 2.2 最小步骤
1. 在 `tools/` 下新增或扩展目标工具实现
2. 使用注册中心注册 schema / handler / requirements
3. 在 `toolsets.py` 把工具接入正确工具集
4. 检查 `model_tools.py` 是否需要动态描述或可用性处理
5. 补最小测试，至少覆盖：
   - 注册与暴露
   - handler 返回格式
   - 缺依赖时的表现
   - 关键安全边界

### 2.3 必查点
- 返回值是否符合现有工具约定
- 是否误把跨工具依赖硬编码进 schema 描述
- 是否写入了 profile-unsafe 路径
- 是否真的需要新工具，而不是复用已有工具

## 3. 新增 slash command
### 3.1 入口
先读：
1. `hermes_cli/commands.py`
2. `cli.py`
3. `gateway/run.py`（若 gateway 也要支持）

### 3.2 最小步骤
1. 在 `COMMAND_REGISTRY` 中新增 `CommandDef`
2. 在 `cli.py` 中接入处理逻辑
3. 若命令需要进入 gateway，再在 `gateway/run.py` 接入
4. 若命令影响持久化设置，走现有配置保存路径
5. 补 CLI / gateway 对应测试

### 3.3 何时只加 alias
- 如果只是命令别名，优先只改 `CommandDef.aliases`
- 不要复制分发逻辑或再造一套帮助文本

## 4. 新增配置
### 4.1 `config.yaml` 配置项
1. 改 `hermes_cli/config.py` 的 `DEFAULT_CONFIG`
2. 需要迁移时，更新配置版本与迁移逻辑
3. 检查 CLI 与 gateway 是否都读取该项

### 4.2 `.env` / 环境变量
1. 改 `hermes_cli/config.py` 的 `OPTIONAL_ENV_VARS`
2. 补说明、提示文案、是否密码字段、分类
3. 检查实际消费点是否存在且命名一致

### 4.3 必查点
- CLI、`hermes tools`、setup、gateway 是否读取路径一致
- 用户可见说明是否与真实行为一致
- 是否需要补回归测试

## 5. 调整路径、profiles、状态持久化
### 5.1 入口
先读：`guardrails.md` 第 2 节

### 5.2 操作顺序
1. 先确认该路径是代码内部路径还是用户可见路径
2. 内部路径统一走 `get_hermes_home()`
3. 用户可见路径统一走 `display_hermes_home()`
4. profile 相关测试同时处理 `HERMES_HOME` 与 `Path.home()`
5. 回归测试中确认不会写入真实 `~/.hermes`

## 6. 测试与交付
### 6.1 常用测试入口
- `source venv/bin/activate`
- `python -m pytest tests/ -q`
- `python -m pytest tests/test_model_tools.py -q`
- `python -m pytest tests/cli/test_cli_init.py -q`
- `python -m pytest tests/gateway/ -q`
- `python -m pytest tests/tools/ -q`

### 6.2 交付时至少要带上的证明
- 改了什么文件，为什么改
- 对应哪条 Task Contract
- 跑了哪些验证，结果是什么
- 是否存在未完成项、风险项、人工复核点

### 6.3 回写入口
- Task Contract：回到已落地的 `hermes-harness-task-contract`
- Verification Chain：回到已落地的 `hermes-harness-verification-chain`
- Status Ledger：回到已落地的 `hermes-harness-status-ledger`
- 涉及 skill 新建/修改：再服从 `hermes-harness-skill-change-loop`

不要在本文复制模板；只引用标准骨架。

## 7. 本文边界
- 本文只给任务入口与最小操作顺序。
- 具体结构解释回 `architecture.md`。
- 风险边界、禁区与交接纪律回 `guardrails.md`。