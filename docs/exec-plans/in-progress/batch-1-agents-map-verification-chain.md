## Verification Chain（默认验证链）

**Verification Target (验证目标)**  
- 对应合同项：直接对应本次 Task Contract 的交付物 / 证据与完成标准。  
- 目标 1：证明重构后的根目录 `AGENTS.md` 是“地图型入口”，而不是厚重总说明书；其内容能够明确读取顺序、渐进式信息披露原则、以及不同任务类型的跳转入口。  
- 目标 2：证明 `docs/agents/` 目录下 4 个关键文件 `README.md`、`architecture.md`、`workflows.md`、`guardrails.md` 已真实存在，且职责边界与目录方案一致。  
- 目标 3：证明本轮目录初始化没有越界生成计划外空文件夹，也没有把 `docs/agents/` 写成历史文档堆放区或培训手册集合。  
- 目标 4：证明新版 `AGENTS.md` 保留了原有开发指南中的核心关键路径，但已被入口化、分层化，且主文档控制在 150 行以内。

**Verification Actions (验证动作)**  
- 动作 1：使用 file 读取工具回读 `AGENTS.md`，核对是否明确写出“地图而非手册”的定位、阅读顺序、渐进式信息披露原则，以及对 `docs/agents/`、`docs/exec-plans/`、`docs/specs/`、`docs/migration/` 的入口指引。  
- 动作 2：使用 `wc -l AGENTS.md` 核对总行数不超过 150 行，并检查是否保留原开发指南中的核心关键路径入口，例如项目结构、关键模块入口、执行现场文档入口，而不是把这些内容全部删除。  
- 动作 3：使用搜索与 file 工具核实 `docs/agents/README.md`、`docs/agents/architecture.md`、`docs/agents/workflows.md`、`docs/agents/guardrails.md` 四个文件真实存在，并逐个回读其标题和前段内容，确认职责没有错位。  
- 动作 4：使用搜索与目录核查，确认没有额外创建计划外空文件夹、没有新增 `docs/decisions/`、`docs/reference/`、`docs/qa/`、`docs/runbooks/`、`docs/standards/`、`docs/reviews/` 等未获批准目录。  
- 动作 5：将 `AGENTS.md` 与 `docs/agents/` 四个文件的存在性、职责边界、行数控制与目录洁净度逐项写回本验证链，并据此给出放行结论。

**Verification Result (验证结果)**  
- 目标 1：通过 —— 已回读 `AGENTS.md`，确认其明确写出“这是仓库协作地图，不是开发手册”，并提供了从根地图到 `docs/agents/README.md`、`architecture.md`、`workflows.md`、`guardrails.md` 以及 `docs/exec-plans/`、`docs/specs/`、`docs/migration/` 的分层入口；主文档没有退回厚重说明书。  
- 目标 2：通过 —— 已检索并回读 `docs/agents/README.md`、`docs/agents/architecture.md`、`docs/agents/workflows.md`、`docs/agents/guardrails.md`；四个文件都真实存在，且职责分别稳定在二级导航、系统结构、任务型入口、风险与交接纪律，没有再次出现自造模板越界。  
- 目标 3：通过 —— 已核查目录与文件，未新增 `docs/decisions/`、`docs/reference/`、`docs/qa/`、`docs/runbooks/`、`docs/standards/`、`docs/reviews/` 等计划外目录；本轮仅创建了 `docs/agents/` 与 4 个批准文件，没有空壳目录污染。  
- 目标 4：通过 —— `wc -l AGENTS.md` 输出为 `82 AGENTS.md`，满足 150 行上限；同时 `AGENTS.md` 仍保留了旧版开发指南中的关键路径，包括 `source venv/bin/activate`、常用 pytest 入口、`run_agent.py` / `model_tools.py` / `toolsets.py` / `cli.py` / `tools/registry.py` / `gateway/` 等核心入口，并已全部改造成入口化索引。  

**Release / Handoff Gate (放行 / 接管闸门)**  
- 当前判断：可收口  
- 当前缺口：本轮合同要求的根地图重构、4 个二级文档初始化、行数控制、目录洁净度与职责边界校验均已完成，没有剩余阻断缺口。  
- 接手后第一步：若进入后续批次 1 深化工作，应先以根 `AGENTS.md` 为总入口，再按任务类型逐层补充 `docs/agents/` 内容，不要回头把根地图写胖。  
- 接手入口：先看根 `AGENTS.md`，再按任务需要进入 `docs/agents/README.md`、`architecture.md`、`workflows.md`、`guardrails.md`。