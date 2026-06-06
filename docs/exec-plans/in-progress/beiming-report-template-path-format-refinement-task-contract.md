## Task Contract（任务合同）

**Objective (目标)**  
在不改动任何执行逻辑与法典红线的前提下，对《北冥汇报模板》及其最小必要引用规范做一次小范围精修，使 CLI 端任务汇报更适合直接复制回本窗口验收。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只修改 `docs/agents/beiming-report-template-v2.md`，并按最小必要同步修正 `docs/agents/mainline-integration-protocol.md`、`docs/agents/beiming-constitution.md` 中与汇报模板引用规范直接相关的文字；为本任务建立合同、状态台账、验证链；统一路径表达为“仓库内相对路径、仓库外绝对路径”；明确汇报字段哪些必须始终输出、哪些允许写“未暴露”；固定 Session ID 真实值 / 固定兜底口径。  
OUT: 不修改任何业务代码、运行时代码、测试代码；不重写 `safe-refactor-loop` 状态机；不批量回刷历史执行文档；不新增与本轮目标无关的字段或法典层级规则。  
WATCHOUTS: 最大风险是把“输出格式精修”误做成法典含义改写；第二风险是为了追求灵活性而放松 Session ID 禁止编造红线；第三风险是把仓库内路径写回投影式绝对路径；第四风险是把“未暴露”滥用于本应给出真实值、无、未执行或不适用的字段。

**Inputs (输入)**  
`docs/agents/beiming-report-template-v2.md`、`docs/agents/mainline-integration-protocol.md`、`docs/agents/beiming-constitution.md`、`docs/exec-plans/tech-debt-tracker.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`；仓库外 Skill 路径为 `/Users/beiming/.hermes/skills/safe-refactor-loop/SKILL.md`；用户明确要求：仓库内文件一律使用仓库相对路径，Skill 若在仓库外可明确标注为绝对路径；Session ID 只能填真实值或固定兜底句式，不得编造。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：精修后的汇报模板；与模板直接耦合的最小必要引用规范修订；本任务合同、状态台账、验证链。  
证据：回读目标文件可见路径表达已统一；模板中已明确列出必须始终输出的字段、允许写“未暴露”的字段及对应口径；Session ID 兼容规则已固定为真实值或指定兜底句式；搜索结果可证明未混入 `.hermes/hermes-agent/...` 这类仓库内投影式路径。

**Done (完成标准)**  
以下条件同时成立才算完成：
1. `docs/agents/beiming-report-template-v2.md` 已明确规定仓库内文件使用仓库相对路径、仓库外 Skill 可使用绝对路径并标明仓库外；
2. 模板已稳定保留 11 个顶层字段，并明确哪些字段必须始终输出、哪些子字段允许写“未暴露”；
3. Session ID 规则已固定为“可读则真实值，不可读则固定兜底句式”，且明确禁止编造或留空不解释；
4. `docs/agents/mainline-integration-protocol.md` 与 `docs/agents/beiming-constitution.md` 中与模板直接相关的引用口径已保持一致；
5. 本轮改动仅限文档与任务现场文档，没有越界到执行逻辑或测试逻辑。

## M1 附件：规则迁移清单
- 规则 1（路径写法统一）：来源为用户本轮指令；目标文件为 `docs/agents/beiming-report-template-v2.md`，并按最小必要同步到 `docs/agents/mainline-integration-protocol.md`、`docs/agents/beiming-constitution.md`。
- 规则 2（11 个顶层字段稳定输出）：来源为用户本轮指令；目标文件为 `docs/agents/beiming-report-template-v2.md`。
- 规则 3（“未暴露”使用边界）：来源为用户本轮指令；目标文件为 `docs/agents/beiming-report-template-v2.md`，并在 `docs/agents/mainline-integration-protocol.md` 保持一致。
- 规则 4（Session ID 真实值 / 固定兜底句式）：来源为既有模板、主线协议、`/Users/beiming/.hermes/skills/safe-refactor-loop/SKILL.md` 与用户本轮指令；目标文件为 `docs/agents/beiming-report-template-v2.md` 与 `docs/agents/mainline-integration-protocol.md`。