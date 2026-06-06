## Verification Chain（默认验证链）

**Verification Target (验证目标)**  
- 对应合同项：直接对应本次 Task Contract 的交付物 / 证据与完成标准。  
- 目标 1：证明本轮锁定的首战标杆组与 P1 样板组都已正式落入 `docs/agents/controlled-entry-index.md`，且保持“危险点 -> 受控入口”映射，而不是抽象建议。  
- 目标 2：证明“把警报器误当通行证”的风险已被正式打断：后续 Agent 会被明确导向“先回查 Verification Chain，再进入受控入口”。  
- 目标 3：证明本轮产物保持入口化、可回读、可接管，没有把 `controlled-entry-index.md` 写成百科，也没有新增计划外目录。  
- 目标 4：证明本轮阶段性成果边界已经被明确写死：文档治理已完成，代码治理尚未开始；下一战 P0 只是已立项、未开工。  

**Verification Actions (验证动作)**  
- 动作 1：回读 `docs/agents/controlled-entry-index.md`，核对首批配置写入链样板与第二组 Profile / Uninstall 样板同时存在，且第二组包含 5 个“绝对禁止的高风险旁路”、最低放行条件与使用边界。  
- 动作 2：回读 `docs/agents/runtime-risk-index.md`，核对防误导提示已正式落盘，并确认语义是“风险索引只负责报警，不授予执行许可；凡触碰高风险锚点，仍必须回到当前任务的 Verification Chain，Gate 未关闭前一律不得动手。”  
- 动作 3：回读 `docs/exec-plans/tech-debt-tracker.md`，核对技术债账本已按 P0 / P1 / P2 分级，且 P0 仅为“service cleanup 双实现收敛”，P1/P2 排序与当前主控判断一致。  
- 动作 4：回读本任务 Status Ledger，核对其已记录两组样板落盘、账本已建立，并明确下一战是 P0（service cleanup 双实现收敛）。  
- 动作 5：核对目录洁净度：本轮只允许新增 `docs/agents/controlled-entry-index.md` 与 `docs/exec-plans/tech-debt-tracker.md` 这两个新落点，不得出现计划外目录或空壳结构。  
- 动作 6：在最终 Gate 中明确边界：本轮只收口文档治理与账本治理；代码层 service cleanup 双实现收敛尚未开始，不得误宣称已完成代码治理。  

**Verification Result (验证结果)**  
- 目标 1：通过 —— `docs/agents/controlled-entry-index.md` 已正式落盘并回读；配置写入链样板与 Profile / Uninstall 第二组样板均存在，第二组已包含 5 个绝对禁止旁路、最低放行条件与使用边界。  
- 目标 2：通过 —— `docs/agents/runtime-risk-index.md` 中的防误导提示已正式落盘并回读；当前链路已明确打断“看到风险索引就获得执行许可”的幻觉。  
- 目标 3：通过 —— `controlled-entry-index.md` 仍保持索引形态，没有写成百科；本轮未污染 `workflows.md`，也未新增计划外目录。  
- 目标 4：通过 —— 本任务台账、技术债账本与下一战派工单已经同时建立；边界明确为“文档治理已完成，代码治理尚未开始”，不存在误把 P0 代码战成果提前算入本轮的情况。  

**Release / Handoff Gate (放行 / 接管闸门)**  
- 当前判断：可收口  
- 当前缺口：无  
- 接手后第一步：若要进入代码治理，必须新开 P0 任务合同，并以 `docs/exec-plans/tech-debt-tracker.md` 中的 P0 条目为唯一代码战入口；不得沿用本轮文档治理 Gate 直接动代码。  
- 接手入口：先看本任务 Status Ledger，再看 `docs/agents/controlled-entry-index.md` 与 `docs/exec-plans/tech-debt-tracker.md`，最后依据新的 P0 合同与 Verification Chain 开工。  
