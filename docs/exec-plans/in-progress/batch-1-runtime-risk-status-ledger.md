## Status Ledger / Progress Doc（状态台账 / 进度文档）

**Task Contract Snapshot (合同快照)**  
- 目标：梳理仓库中所有一旦被 AI 误操作就可能导致系统崩盘、数据丢失、配置污染、权限越界或不可逆副作用的高风险操作入口，并建立一套可回查、可导航、可触发验证链的防御索引。  
- 范围边界：本轮只做高风险锚点的物理梳理、防御索引设计与文档入口规划；不直接修改危险实现逻辑本身；不引入 Hook、自动拦截器、运行时 kill-switch；不把普通写文件操作膨胀成高风险入口；不把任务扩成全仓库安全重构。  
- 完成标准：高风险操作入口已按类型梳理并能回溯到真实文件或调用点；`guardrails.md` 的增强方案与是否拆出 `runtime-risk-index.md` 已定稿；后续 Agent 能明确知道哪些点是高风险锚点、为什么危险、触碰前必须回查哪类 Verification Chain；新增文档路径可回读、可验证、无计划外空壳结构。

**Current State (当前状态)**  
- 当前停点：第一轮高风险锚点物理扫描已完成，当前正在建立本任务专属的状态台账与验证链，并准备固化 T0 级禁区条款。  
- 已完成：已签署本任务 Task Contract；已完成第一轮高风险入口诊断报告；已识别 T0 级禁区包括 `tools/terminal_tool.py`、`hermes_cli/uninstall.py` / `hermes_cli/profiles.py`、配置与凭据写入链（`cli.py` / `gateway/run.py` / `hermes_cli/memory_setup.py` / `hermes_cli/config.py`）；已判断应新建 `docs/agents/runtime-risk-index.md`，并保持 `guardrails.md` 作为规则入口。  
- 未完成 / 当前阻塞：本任务专属 Verification Chain 尚未建立；`guardrails.md` 与 `runtime-risk-index.md` 还未起草；“触碰高风险锚点前最少必须执行的拦截动作”尚未固化进正式验证闸门。  
- 当前判断：未完成

**Evidence Logged (证据登记)**  
- 已有证据：已定位多处真实高风险物理锚点，包括任意命令执行、递归删除、配置写入、`.env` 重写、定时脚本执行、桥接进程杀端口、全局状态污染点；已形成按文件路径、风险分类、致命后果、触碰前验证动作组织的诊断清单；已完成“新建 `runtime-risk-index.md` 而非继续写胖 `guardrails.md`”的主控裁定。  
- 证据对应结论：本轮任务不是抽象防御宣言，而是建立在真实代码入口上的物理级风控；高风险锚点数量已超过适合直接塞进 `guardrails.md` 本体的范围，需要规则入口与风险索引分层。  
- 证据缺口：尚无本任务专属 Verification Chain；尚无更新后的 `guardrails.md` 与新建 `runtime-risk-index.md` 的正式草稿、落盘与回读证据；尚无“高风险锚点触碰前强制回查验证链”的正式文案落点。

**Next Handoff (下一步 / 接管指令)**  
- 接手后第一步：建立本任务专属的 Verification Chain，并把“高风险锚点触碰前最少必须执行的拦截与验证动作”写成硬规则。  
- 立即核查：核对后续 Verification Actions 是否真正包含实质性拦截动作，而不是空泛地写“注意安全”；核对文档拆分方案是否仍然坚持 `guardrails.md` 入口化、`runtime-risk-index.md` 承接物理锚点细节。  
- 若受阻先排查：如果后续文档方案开始膨胀成安全百科，立即收回到“规则入口 + 风险索引”双层结构；如果把普通操作点误纳入高风险清单，立即按误操作后果重新裁剪。  
