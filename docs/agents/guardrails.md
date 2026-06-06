# Guardrails / 风险边界、验证与交接纪律

## 1. 总则
- 先约束，后修改；先证明，后宣称完成。
- 不把根 `AGENTS.md` 写回厚手册。
- 不新增计划外目录、空壳文件夹、未来占位页。
- 不引入 Hook、自动触发器、批次 1 之外能力。
- 触碰高风险锚点前，必须先回查 `Verification Chain`；没有对应验证动作与 Gate，不得执行。

## 2. 路径、profiles 与测试隔离
### 2.1 路径规则
- 代码里凡是持久化路径、状态路径、缓存路径：用 `get_hermes_home()`
- 用户可见输出路径：用 `display_hermes_home()`
- 不要硬编码 `~/.hermes`
- 不要把 `Path.home() / ".hermes"` 当成默认实现

### 2.2 profile-safe 规则
- profile 机制依赖 `HERMES_HOME`
- profile 相关逻辑要考虑 `_apply_profile_override()` 的装配时机
- 测试 profile 时，同时处理：
  - `HERMES_HOME`
  - `Path.home()`

### 2.3 测试隔离
- 测试不得写真实 `~/.hermes/`
- profile 测试要覆盖 HOME 锚点与 profiles 根目录行为
- 任何新测试若触及状态落盘，先确认落盘位置在临时目录

## 3. 运行时高风险入口
高风险入口不是抽象禁令，而是**真实物理落点**。  
具体锚点索引、路径、后果与触碰前动作，统一看：

- `docs/agents/runtime-risk-index.md`

硬规则：

- 只要任务会触碰高风险锚点，必须先有正式 `Task Contract`
- 必须有对应的 `Verification Chain`
- Verification Chain 中必须出现“误伤排除”动作
- 执行前必须回读当前状态
- 执行后必须回读结果
- Gate 未明确前，不得执行或放行

### 3.1 T0 禁区
以下禁区绝对禁止直碰：

- `tools/terminal_tool.py`
- `hermes_cli/uninstall.py`
- `hermes_cli/profiles.py`
- `cli.py` / `gateway/run.py` / `hermes_cli/memory_setup.py` / `hermes_cli/config.py` 中的配置与凭据写入链

没有验证链放行，不得执行。

### 3.2 Prompt Caching 与全局状态风险
不要在对话中途：
- 改写既有上下文
- 动态切换已装配工具集
- 中途重建 system prompt
- 中途重新加载会改变历史语义的记忆内容

涉及 `_last_resolved_tool_names`、delegate、子代理、恢复流程时，先确认当前状态，再动手。

### 3.3 工具与 schema 风险
- 不要在工具 schema 描述里硬编码跨工具引用
- 交叉提示如确有必要，应走集中处理逻辑，不要散落在各工具描述里
- 工具 handler 行为要与现有约定一致，不要悄悄换返回结构

## 4. UI / 终端相关禁区
- 新增交互菜单时，优先复用现有 curses 模式与既有实现模式
- 不要新增依赖 `simple_term_menu` 的新交互路径来解决通用菜单问题
- spinner / display 代码不要依赖 `\033[K` 这类清行方案；沿用现有安全写法

## 5. 验证与交接纪律
### 5.1 验证最低要求
每个任务完成前，至少回答：
- 我改了什么
- 为什么这些改动足够
- 我怎么证明它生效
- 我怎么证明它没越界
- 还剩什么风险或未决项

### 5.2 高风险锚点的最低放行条件
凡触碰高风险锚点，最少必须包含：
1. 目标确认
2. 非目标范围排除
3. 执行前状态回读
4. 执行后结果回读
5. Verification Chain Gate 明确放行

少任一项，不得执行。

### 5.3 证据优先级
1. 文件回读 / 结构核验
2. 目标测试 / 相关测试
3. 行为核验 / 路径核验
4. 状态台账回写

### 5.4 交接最小内容
交给下一个 Agent 时，至少写清：
- **Current State（当前状态）**
- **Evidence Logged（证据登记）**
- **Next Handoff（下一步 / 接管指令）**

不要只写“已完成大部分”“应该没问题”。

## 6. 文档与目录边界
- `AGENTS.md` 只做地图，不做百科
- `docs/agents/README.md` 只做导航
- `architecture.md` 只讲结构与入口
- `workflows.md` 只讲任务型路径
- `guardrails.md` 才承接规则、验证、交接
- 发现职责串位时，优先纠正文档边界，不继续堆内容

## 7. 放行前检查清单
- [ ] 改动是否只覆盖任务合同范围
- [ ] 是否引用了正确入口文件与真实路径
- [ ] 是否避免硬编码 `~/.hermes`
- [ ] 是否避免破坏 prompt caching
- [ ] 是否没有引入计划外目录/文件
- [ ] 是否补足最小验证证据
- [ ] 是否回写 Task Contract / Verification Chain / Status Ledger
