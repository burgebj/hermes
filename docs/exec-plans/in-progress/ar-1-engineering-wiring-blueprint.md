# AR-1 工程化接线执行蓝图

## 1. 前提与恢复结论

- 本蓝图基于已恢复的现场文档与 Skill：
  - `docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`
  - `docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`
  - `docs/exec-plans/in-progress/ar-1-engineering-wiring-task-contract.md`
  - `docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`
  - `docs/exec-plans/tech-debt-tracker.md`
  - 仓库外：`~/.hermes/skills/safe-refactor-loop/SKILL.md`
- 当前主线 worktree（`/tmp/p3-ar1-wiring-prep`）基于 `main`，未自带上述战时文档；本文件用于把已恢复现场转成下一轮工程化接线的执行蓝图。
- 本轮只做预备规划，不直接修改 M5 / M6 代码，不改业务逻辑，不 push，不 merge。

## 2. 三个缺口的依赖顺序

### 顺序建议
1. M5 自动读写战时文档
2. M5 与 M6 的一键启动真实流水线
3. 归档同步器

### 为什么是这个顺序
- 第 1 刀是地基：没有稳定的战时文档恢复、回写与 fail-closed 行为，后续一键启动只会把错误状态自动化放大。
- 第 2 刀是主干：只有先把 `APPROVE_CANDIDATE -> M6` 的真实闸门串起来，才算“整机能跑”，并且能为归档阶段提供真实的审批结果输入。
- 第 3 刀是收口：归档同步器天然依赖前两刀产出的最新台账、验证链、审批结果；否则只能生成空报告或假平账。

## 3. 哪一刀应先打

应先打第 1 刀：M5 自动读写战时文档。

原因：
- safe-refactor-loop 的 Skill 已明确“战时文档恢复必须 fail-closed”，任务合同缺失时必须直接失败。
- 已恢复的 Task Contract / Status Ledger / Verification Chain 都把“自动读写战时文档”列为后续接线的共同前提。
- 从现有原型接口看，`restore_or_create_battle_documents()`、`_write_status_ledger()`、`_write_verification_chain()` 已经天然构成最小骨架；先把这层接口定义稳，后面的一键启动与归档同步都能围绕同一组 battle document contract 接线。

## 4. 每一刀的最小可交付物

### 第 1 刀：M5 自动读写战时文档
最小可交付物：
- 一组稳定的 battle document path contract（任务合同、状态台账、验证链、账本、归档报告）。
- fail-closed 的恢复入口：任务合同缺失时直接失败；状态台账 / 验证链缺失时允许按模板重建。
- M5 复审完成后，至少能把 `review_verdict`、`entered_m6` 回写到 Status Ledger / Verification Chain。
- 最小测试覆盖：
  - 合同缺失直接失败
  - ledger / verification 缺失可重建
  - 复审后文档被自动回写

### 第 2 刀：M5 与 M6 的一键启动真实流水线
最小可交付物：
- 一个从 `tech-debt-tracker.md` 选择当前活跃战役的启动入口。
- 一个真实串起 `M3 -> M5 -> M6` 的 orchestrator，只在 `APPROVE_CANDIDATE` 时进入 M6。
- M6 仍保留物理停机，且生产路径禁止注入式假 gate；测试覆盖可通过显式 test flag 放行假 gate。
- 最小测试覆盖：
  - 账本选择 AR-1
  - `APPROVE_CANDIDATE` 才进入 M6
  - 非显式测试场景不得覆盖真实 human gate

### 第 3 刀：归档同步器
最小可交付物：
- 只在北冥显式 `Y / Confirm` 后触发的归档入口。
- 自动生成结案报告。
- 自动更新 `tech-debt-tracker.md` 中对应战役状态。
- 人工拒绝时不写结案报告、不更新账本。
- 最小测试覆盖：
  - approval=true 时生成 acceptance report 并更新 tracker
  - approval=false 时不归档、不平账

## 5. 三刀之间的接口关系

### 统一对象层
- 建议统一围绕 `BattleDocumentPaths` 这类路径契约对象。
- 它至少承载：
  - `tracker_path`
  - `task_contract_path`
  - `status_ledger_path`
  - `verification_chain_path`
  - `archive_report_path`
  - `battle_name`

### 接口关系图
1. 账本选择器
   - 输入：`tech-debt-tracker.md`
   - 输出：`battle_name`
2. 战时文档恢复器
   - 输入：`BattleDocumentPaths`
   - 输出：`task_contract/status_ledger/verification_chain` 文本快照
   - 约束：任务合同缺失 fail-closed
3. M5 自动复审器
   - 输入：diff / report / pytest / 当前 battle docs
   - 输出：`review_result`
4. M6 人审闸门
   - 输入：`AutomatedReviewResult`
   - 输出：`HumanGateDecision`
   - 约束：只有 `APPROVE_CANDIDATE` 才允许进入
5. 归档同步器
   - 输入：`BattleDocumentPaths + docs snapshot + HumanGateDecision`
   - 输出：结案报告 + tracker 平账结果
   - 约束：只有 `approved=true` 才允许触发

### 调用顺序
- `select_active_battle()`
- `restore_or_create_battle_documents()`
- `run_self_correcting_review()`
- `_write_status_ledger()` / `_write_verification_chain()`
- `HumanGateController.require_explicit_approval()`
- `_write_archive_report()`
- `_update_tracker_for_stage_closure()`

### 边界纪律
- 文档恢复层只负责“恢复现场 / 写回现场”，不负责审批。
- M5 只负责自动复审与自愈，不负责最终放行。
- M6 只负责真实人审，不负责改写 battle docs 以外的业务逻辑。
- 归档同步器只负责“结案报告 + 账本平账”，不回头篡改复审裁决。

## 6. 推荐切刀方式

### 切刀 1：先稳住文档契约
- 先把 battle document path、恢复规则、回写字段定成固定 contract。
- 这是后续流水线与归档器共享的唯一事实源。

### 切刀 2：再接真实 M6
- 让一键启动只负责“从账本接战役 + 跑到 M6 停机”。
- 不要在这一步顺手把归档也揉进去，否则会把启动链和收口链耦死。

### 切刀 3：最后补归档同步
- 归档器只消费“已审批”的事实，不参与审批判定。
- 这样才能保持 M6 是唯一合法终审官。

## 7. 工程化接线执行蓝图（简版）

- 蓝图目标：把 safe-refactor-loop 从“已有原型函数”收束成“按账本接战役、按文档恢复现场、按裁决进入 M6、按审批归档平账”的可接管流水线。
- 实施顺序：先文档契约，再真实启动链，后归档平账。
- 核心接口：统一围绕 `BattleDocumentPaths`、`review_result`、`HumanGateDecision` 三组对象接线。
- 最小闸门：
  - 无任务合同即 fail-closed
  - 无 `APPROVE_CANDIDATE` 不进 M6
  - 无北冥显式批准不归档
- 验收口径：每一刀都必须拿出最小测试与物理证据，不能靠“报告解释”代替。

## 8. 推荐下一步（唯一）

下一步唯一建议：先把“第 1 刀：M5 自动读写战时文档”单开成实施任务，先冻结 battle document contract 与 fail-closed 回写规则，再允许启动链和归档链继续接线。
