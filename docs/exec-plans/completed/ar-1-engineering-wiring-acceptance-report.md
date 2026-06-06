# AR-1 工程化接线收口结案报告

## 1. 任务合同（Task Contract）

## Task Contract（任务合同）

**Objective (目标)**  
完成 AR-1 剩余 3 个工程化接线缺口：让 M5 自动读写战时文档、自动接归档同步器、并与 M6 串成一条可一键启动的真实流水线，使 safe-refactor-loop 从“模块齐备”升级为“整机可跑”。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理 M5/M6 与战时文档、归档器、一键启动入口的工程化接线；允许最小必要的 orchestrator 改动、状态回写、归档触发与入口封装；允许补最小必要测试。  
OUT: 不重构 M3 法典引擎；不改 TDB-3 业务代码；不扩展到新的技术债自动接管；不移除 M6 人工审批保险丝；不改 shell/PATH、profile/uninstall 底层业务逻辑。  
WATCHOUTS: 最大风险是把“接线”做成新框架重写；第二风险是为了自动化顺滑而削弱 M6 物理停机；第三风险是战时文档回写不完整，造成跨会话状态错乱；第四风险是一键启动入口直接越过合同/台账/验证链恢复步骤。

**Inputs (输入)**  
- `docs/exec-plans/tech-debt-tracker.md` 中 AR-1 当前仍为最高优先级活跃战役  
- `~/.hermes/skills/safe-refactor-loop/SKILL.md` 中 S0-S7 状态机  
- `hermes_cli/safe_refactor_audit.py`（M3）  
- `hermes_cli/review_orchestrator.py`（M5 / M5-v2）  
- `hermes_cli/human_gate_controller.py` 与 `hermes_cli/gate_controller.py`（M6）  
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`  
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`

**Deliverables / Evidence (交付物 / 证据)**  
交付物：M5 自动读写战时文档能力；归档同步器接线；M5->M6 一键启动入口；最小必要测试；更新后的 Skill 与战时文档。  
证据：运行后能自动恢复/建立 Task Contract、Status Ledger、Verification Chain；能自动把裁决写回 AR-1 台账；在 `APPROVE_CANDIDATE` 时强制进入 M6 物理停机；归档同步器能生成结案报告并平账；一键启动命令可直接从账本接管第一项任务。

**Done (完成标准)**  
以下条件必须同时成立：  
1. M5 能自动读取并回写战时文档，且状态与现场一致  
2. 归档同步器能在任务结束后生成结案报告并更新 `tech-debt-tracker.md`  
3. 一键启动入口能从账本中恢复首个任务并串起 M3 -> M5 -> M6  
4. M6 物理停机仍然存在，且没有北冥显式 `Y / Confirm` 不得合并  
5. 未越界修改 TDB-3 或其他业务技术债  
6. 最小相关测试通过，且至少覆盖：台账回写、归档同步、M6 停机、一键启动接线


---

## 2. 结案结论

- M5 能自动读取并回写战时文档。
- 归档同步器已生成本结案报告并准备同步账本。
- 一键启动链已能从账本接管任务并把 APPROVE_CANDIDATE 送入 M6。
- M6 仍保留物理停机；没有北冥签字，任何代码都不准合并。

## 3. 最终状态台账

**Task Contract Snapshot (合同快照)**
- 目标：完成 AR-1 剩余 3 个工程化接线缺口：让 M5 自动读写战时文档、自动接归档同步器、并与 M6 串成一条可一键启动的真实流水线，使 safe-refactor-loop 从“模块齐备”升级为“整机可跑”。
- 范围边界：只处理 M5 自动复审、战时文档回写、归档同步与 M6 接线；不削弱人工审批。
- 完成标准：M5 能自动读写战时文档，APPROVE_CANDIDATE 会进入 M6，归档同步器可生成结案报告并更新账本。

**Current State (当前状态)**
- 当前停点：M6 已收到北冥签字，允许进入结案归档
- 已完成：M5 已自动读取任务合同、状态台账、验证链并回写当前裁决；当前裁决为 APPROVE_CANDIDATE。
- 未完成 / 当前阻塞：最终放行仍受 M6 人工签字控制；没有北冥签字不得合并。
- 当前判断：可收口

**Evidence Logged (证据登记)**
- 已有证据：M5 已写回 review_verdict=APPROVE_CANDIDATE；entered_m6=yes。
- 证据对应结论：safe-refactor-loop 已能从战时文档恢复现场并把复审结果写回当前战场。
- 证据缺口：无当前阶段缺口。

**Next Handoff (下一步 / 接管指令)**
- 接手后第一步：若 M6 已停机，则只等待北冥输入 Y / Confirm；若未进 M6，则继续修复直到 APPROVE_CANDIDATE。
- 立即核查：确认 M5 仍只负责自动复审与自愈，不负责最终放行。
- 若受阻先排查：先查战时文档路径、review verdict 与人审闸门是否一致。


## 4. 最终验证链

## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应 AR-1 工程化接线交付物、证据与完成标准。
- 目标 1：证明 M5 能自动读取并回写 Task Contract / Status Ledger / Verification Chain。
- 目标 2：证明当 M5 给出 APPROVE_CANDIDATE 时，系统会立即进入 M6。
- 目标 3：证明归档同步器能生成结案报告并回写 tech-debt-tracker。

**Verification Actions (验证动作)**
- 动作 1：恢复或建立任务合同、状态台账、验证链，并运行 safe-refactor-loop。
- 动作 2：检查状态台账与验证链是否已被自动回写。
- 动作 3：如获北冥签字，检查结案报告与 tech-debt-tracker 是否已同步。

**Verification Result (验证结果)**
- 目标 1：通过 —— 当前 review_verdict=APPROVE_CANDIDATE，且战时文档已被自动回写。
- 目标 2：通过 —— 系统已在 APPROVE_CANDIDATE 后进入 M6 并停机等待审批。
- 目标 3：通过 —— 结案报告与账本更新已完成。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：无。
- 接手后第一步：若已进入 M6，则等待北冥输入 Y / Confirm；若已签字，则核查归档报告。
- 接手入口：先看任务合同、状态台账、验证链与最新结案报告。

