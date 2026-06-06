## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：交付物 / 证据、完成标准。
- 目标 1：证明本轮目录治理结论基于真实仓库结构，而不是凭印象整理建议。
- 目标 2：证明蓝图已明确区分正式入口、应下沉对象、长期稳定入口、战时材料与归档对象。
- 目标 3：证明分批治理路线不是一次性大搬迁，而是可控、可验证、可接管的批次计划。

**Verification Actions (验证动作)**
- 动作 1：回读仓库根目录顶层条目与 `docs` 子树统计，确认根目录、`docs/agents`、`docs/exec-plans`、`docs/plans`、`plans`、`.plans/` 的真实分布。
- 动作 2：回读 `pyproject.toml`、`README.md`、`AGENTS.md`、`docs/agents/*.md`，确认正式入口与目录职责边界。
- 动作 3：回读 `docs/exec-plans` 当前文件清单，确认执行现场、蓝图、battle packet、备份与状态文件的混层现状。
- 动作 4：回读本任务输出文档，核对是否已覆盖当前问题总览、现状审计、目标蓝图、分批路线、风险验证与起始批次建议。

**Verification Result (验证结果)**
- 目标 1：通过 —— 已用目录清单、统计结果与关键文件回读确认根目录与文档层事实，而非凭空假设。
- 目标 2：通过 —— 蓝图中已区分根正式入口、`docs/agents`、`docs/exec-plans`、`policies/`、归档层与战时材料边界，并标明 `policies/` 当前尚不存在。
- 目标 3：通过 —— 路线按根目录入口清理、文档层整理、法典/模板/蓝图归位、历史材料归档四批设计，并逐批列出风险与验证，不要求一次性迁移。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：本轮仅完成立项与规划，尚未开始任何目录迁移；后续实施前仍需针对每个批次补执行级验证链。
- 接手后第一步：从批次 1 的“根目录入口清理”开始，先建立执行批次专用合同与验证链，再做最小迁移试点。
- 接手入口：先看 `docs/exec-plans/in-progress/hermes-directory-architecture-governance-task-contract.md`、`docs/exec-plans/in-progress/hermes-directory-architecture-governance-status-ledger.md`、`docs/exec-plans/in-progress/hermes-directory-architecture-governance-blueprint.md`。