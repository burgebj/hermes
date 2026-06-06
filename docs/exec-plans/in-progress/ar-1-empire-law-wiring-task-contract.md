## Task Contract（任务合同）

**Objective (目标)**  
以北冥法典为准则，完成 AR-1 剩余工程化接线：让 M5 能自动读写战时文档、让归档同步器接入结案流程，并把 M5 与 M6 串成一条可一键启动的真实流水线。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理 AR-1 当前剩余的 3 个工程化缺口：1) M5 自动读写 Task Contract / Status Ledger / Verification Chain；2) 归档同步器回写结案报告与 `tech-debt-tracker.md`；3) M5 与 M6 的一键启动接线。  
OUT: 不顺手扩展新的审计规则体系；不重构 M3 业务逻辑；不扩大到新的技术债自动执行；不降低 M6 物理停机与北冥签字门槛。  
WATCHOUTS: 最大风险是把“工程化接线”做成新的平台重构；第二风险是为了追求一键启动而绕过战时文档或人工审批；第三风险是把归档自动化做成静默合并通道；第四风险是让状态机的文档回写与真实现场脱节。

**Inputs (输入)**  
`docs/exec-plans/tech-debt-tracker.md` 中 AR-1 仍未完成的三项缺口；`docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`；`docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`；`~/.hermes/skills/safe-refactor-loop/SKILL.md`；当前已存在的 `hermes_cli/review_orchestrator.py`、`hermes_cli/human_gate_controller.py`、`hermes_cli/gate_controller.py`。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：AR-1 工程化接线代码；可回读的战时文档自动读写能力；归档同步器；一键启动入口；最小必要测试。  
证据：M5 复审结果能自动回写到 AR-1 台账；M6 进入前不会绕过物理闸门；结案报告与 `tech-debt-tracker.md` 能自动同步；一键启动命令可从账本恢复并驱动完整流程；相关测试通过。

**Done (完成标准)**  
1. M5 能自动读取并更新对应任务的 Task Contract / Status Ledger / Verification Chain；  
2. 归档同步器能在经北冥批准后自动生成结案报告并更新 `tech-debt-tracker.md`；  
3. 一键启动入口能从账本接管第一项任务并驱动 `M3 -> M5-v2 -> M6` 流程；  
4. 没有北冥 `Y / Confirm`，任何代码都不准合并；  
5. 工程化接线没有扩大到新的审计法典、没有削弱现有红线、没有引入静默放行通道。
