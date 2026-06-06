## Task Contract（任务合同）

**Objective (目标)**  
完成 Hermes 目录架构治理任务的正式立项与规划，先基于仓库现状给出目录审计、目标蓝图与分批治理路线，使后续目录治理能够按稳定路径、可验证边界与可接管方式推进。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只读审计当前仓库目录与关键文档层；识别根目录正式入口、应下沉对象、稳定职责目录与混层点；设计目标目录蓝图；制定分批治理路线、风险与验证方法；为本任务建立合同、台账、验证链与蓝图文档。  
OUT: 不移动现有文件，不改代码实现，不重构 import / packaging，不创建计划外大量目录，不把目录治理扩展成业务代码重构。  
WATCHOUTS: 根目录存在 `pyproject.toml` 的 `py-modules` 与脚本入口绑定，误判会导致运行入口漂移；`AGENTS.md` 与 `docs/agents/` 已形成固定接管链，不能为了“整洁”破坏现有锚点；`docs/exec-plans/` 目前既是执行现场又承载部分历史材料，批量调整前必须先定义稳定路径与验证方式。

**Inputs (输入)**  
`AGENTS.md`；`README.md`；`pyproject.toml`；`docs/agents/README.md`；`docs/agents/architecture.md`；`docs/agents/workflows.md`；`docs/agents/guardrails.md`；`docs/agents/beiming-constitution.md`；`docs/agents/mainline-integration-protocol.md`；`docs/exec-plans/tech-debt-tracker.md`；仓库根目录、`docs/`、`docs/exec-plans/`、`docs/plans/`、`plans/`、`.plans/` 的实际文件分布；用户红线：先审计、再蓝图、再分批治理，且必须从维护性、自动化稳定性、路径可预测性、战时接管能力出发。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：一份正式目录治理蓝图文档；本任务合同、状态台账、验证链。  
证据：回读仓库根目录与关键目录结构；回读根入口与文档边界文件；蓝图文档中明确现状问题、目标结构、分批路线、风险与验证；最终汇报按用户指定六段结构输出。

**Done (完成标准)**  
已基于实际目录结构回答根目录混乱点、正式入口、应下沉对象、稳定职责目录、自动化拖累方式；已给出明确的目标目录蓝图与分批治理路线；已明确哪些文件暂时不能动及原因；最终输出与蓝图文档均可直接作为后续治理任务的接管入口，而不需要重新解释背景。