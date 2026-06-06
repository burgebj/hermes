**Task Contract Snapshot (合同快照)**
- 目标：完成 Hermes 目录架构治理任务的正式立项与规划，产出基于事实的目录审计、目标蓝图与分批治理路线。
- 范围边界：只读审计与规划，不移动文件、不改代码、不做大规模目录调整；必须从维护性、自动化稳定性、路径可预测性、战时接管能力出发。
- 完成标准：已明确根目录正式入口、混乱点、应下沉对象、稳定职责目录、目标结构、分批治理与风险验证；输出可直接作为后续治理接管入口。

**Current State (当前状态)**
- 当前停点：已完成根目录与 `docs/`、`docs/agents/`、`docs/exec-plans/`、`docs/plans/`、`plans/`、`.plans/` 的事实审计，正在汇总正式蓝图与分批治理路线。
- 已完成：已回读 `AGENTS.md`、`README.md`、`pyproject.toml`、`docs/agents` 四页主文档、北冥宪章、主线收编法则、tech-debt-tracker；已统计根目录顶层条目、`docs` 子树概况、`docs/exec-plans` 文件类型与混层情况；已识别 `policies/` 当前不存在、`plans/` / `docs/plans/` / `.plans/` 三处分裂、根目录历史文档与本地状态文件混入等问题。
- 未完成 / 当前阻塞：尚未落地执行批次；目录治理仍停留在规划阶段，后续批次需要单独验收并逐批实施。
- 当前判断：验证中

**Evidence Logged (证据登记)**
- 已有证据：根目录顶层清单、`docs` / `docs/agents` / `docs/exec-plans` / `docs/plans` / `plans` 的实际文件列表；`pyproject.toml` 中 root `py-modules` 与 `project.scripts` 绑定；`docs/agents` 对目录职责边界的显式定义；`docs/exec-plans` 当前存在 `.bak`、`.json`、blueprint、battle packet 等混层样本。
- 证据对应结论：可证明当前问题不是“观感变乱”，而是正式入口、执行现场、历史材料、临时状态与计划文档缺少稳定落点，已经影响自动接管与路径预期。
- 证据缺口：尚未进入任何实际迁移批次，因此没有迁移前后路径验证证据；后续执行时需补根路径 allowlist、引用修复与自动发现规则验证。

**Next Handoff (下一步 / 接管指令)**
- 接手后第一步：先回读本任务合同与目录治理蓝图，确认本轮仅处于立项规划阶段。
- 立即核查：核查 `pyproject.toml` 的 root 入口绑定、`docs/agents` 固定入口链、`docs/exec-plans` 当前混层样本、以及 `plans/` / `docs/plans/` / `.plans/` 的分裂状态。
- 若受阻先排查：若后续要执行批次 1，先补目录治理专用验证链，再决定是否需要创建 `policies/` 或 `docs/archive/`，不要先做大搬迁。