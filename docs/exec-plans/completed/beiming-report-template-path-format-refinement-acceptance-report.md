# Acceptance Report / 汇报模板路径与输出格式精修

## 任务名称
- 汇报模板路径与输出格式精修

## 结论
- 已完成。

## 改动范围
- `docs/agents/beiming-report-template-v2.md`
- `docs/agents/mainline-integration-protocol.md`
- `docs/agents/beiming-constitution.md`
- `docs/exec-plans/tech-debt-tracker.md`
- `docs/exec-plans/in-progress/beiming-report-template-path-format-refinement-task-contract.md`
- `docs/exec-plans/in-progress/beiming-report-template-path-format-refinement-status-ledger.md`
- `docs/exec-plans/in-progress/beiming-report-template-path-format-refinement-verification-chain.md`

## 完成项
1. 已把汇报模板中的路径写法收紧为：仓库内文件统一使用仓库相对路径，仓库外 Skill / 系统文件可使用绝对路径并标注“仓库外”。
2. 已固定 11 个顶层字段的稳定输出要求，并明确这些顶层字段不得改名、缺省或重排。
3. 已明确“未暴露”的使用边界：仅允许用于运行时确实无法读取的 `Session ID`、`当前分支`、`当前候选提交（如有）`；其余字段必须按事实写真实值、`无`、`未执行`、`未产出` 或真实执行形态。
4. 已固定 Session ID 兼容规则：可读则输出真实值；不可读则必须写 `Session ID: 未暴露（需北冥通过 /status 补充）`；严禁编造或留空不解释。
5. 已同步主线协议与宪章中的最小必要引用口径，并在账本 AR-1 条目中登记本次法典升级子任务完成情况。

## 关键证据
- 模板回读可见：`docs/agents/beiming-report-template-v2.md`
- 协议回读可见：`docs/agents/mainline-integration-protocol.md`
- 宪章回读可见：`docs/agents/beiming-constitution.md`
- 账本回读可见：`docs/exec-plans/tech-debt-tracker.md`
- 任务现场文档：
  - `docs/exec-plans/in-progress/beiming-report-template-path-format-refinement-task-contract.md`
  - `docs/exec-plans/in-progress/beiming-report-template-path-format-refinement-status-ledger.md`
  - `docs/exec-plans/in-progress/beiming-report-template-path-format-refinement-verification-chain.md`
- 运行时证据：当前环境变量未暴露当前会话 Session ID；当前仓库根为 `/Users/beiming/.hermes/hermes-agent`，当前分支为 `main`。

## 风险复核
- 未修改任何业务代码、运行时代码、测试代码。
- 未放松 Session ID 禁止编造红线。
- 未把仓库内路径改回投影式绝对路径。

## 后续建议
- 后续若继续精修 CLI 汇报，只应在本模板与直接引用它的协议文件中收口，不要再把汇报规则散落到其他法典层正文。
