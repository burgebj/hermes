## Task Contract（任务合同）

**Objective (目标)**  
完成 AR-1 第三刀：实现“只有在 M6 收到北冥显式 `Y / Confirm` 后，才自动生成 acceptance report、更新 `tech-debt-tracker.md` 并把 Status Ledger / Verification Chain 回写为归档完成态”的归档同步器，且当前只服务 AR-1。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理 AR-1 当前战役的 acceptance report 路径解析、M6 批准态判定、归档报告生成、tracker 平账、Status Ledger / Verification Chain 回写、最小必要测试与现场文档回写。  
OUT: 不重做第一刀、第二刀；不修改 M3 审计逻辑；不修改 M5 复审逻辑；不削弱 M6 物理闸门；不让未签字状态也能归档；不扩展到其他技术债；不 push / merge。  
WATCHOUTS: 最大风险是把等待批准、已拒绝、已批准三种状态混写成同一种“完成”；第二风险是把归档器做成对所有战役的全局清扫器；第三风险是误用旧 acceptance report 当作当前完成证明；第四风险是未进入 M6 或未签字时误写 tracker / acceptance report 假完成。

**Inputs (输入)**  
- `docs/exec-plans/tech-debt-tracker.md`  
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`  
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`  
- `docs/exec-plans/in-progress/ar-1-engineering-wiring-blueprint.md`  
- `docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`（仅作目标归档路径，不作当前子阶段已完成证明）  
- 仓库外：`~/.hermes/skills/safe-refactor-loop/SKILL.md`  
- `hermes_cli/safe_refactor_runtime.py`  
- `hermes_cli/human_gate_controller.py` / `hermes_cli/gate_controller.py`  
- `tests/hermes_cli/test_safe_refactor_runtime.py`

**Deliverables / Evidence (交付物 / 证据)**  
交付物：AR-1 专用归档同步器接线、acceptance report 自动生成逻辑、tracker 自动更新逻辑、Status Ledger / Verification Chain 归档回写逻辑、拒绝态/未签字保护、最小必要测试、更新后的 battle docs。  
证据：`discover_battle_document_paths()` 能解析 acceptance report 路径；`run_safe_refactor_pipeline()` 仅在 `human_gate_decision.approved == True` 时写 acceptance report 与 tracker；未签字、已拒绝、未进入 M6 三类状态都不会归档；相关 pytest 通过。

**Done (完成标准)**  
以下条件必须同时成立：  
1. 只有 `human_gate_decision.approved == True` 或等价 M6 明确通过态成立时，才允许写 acceptance report 和更新 tracker  
2. `approved == True` 时，会自动生成 acceptance report，并把 `tech-debt-tracker.md` 推进到“已完成 / 已收编”口径  
3. Status Ledger / Verification Chain 会同步回写成与批准态一致的归档完成状态  
4. 北冥未签字、M6 拒绝、或根本未进入 M6 时，绝不归档、绝不平账、绝不写假完成  
5. 等待批准、已拒绝、已批准三种状态不会被混成同一个状态  
6. 作用范围仅限 AR-1 当前战役，不会误碰无关战役  
7. 最小相关测试通过，并覆盖：批准归档、未签字阻断、拒绝阻断、tracker 更新、台账/验证链回写
