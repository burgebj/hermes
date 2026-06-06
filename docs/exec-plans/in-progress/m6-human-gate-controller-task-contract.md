## Task Contract（任务合同）

**Objective (目标)**  
实现 `M6: Human Gate Controller`，使其成为 `safe-refactor-loop` 中唯一合法的终审保险丝：只有当 M5 完成自动审计、自愈循环，并输出 `APPROVE_CANDIDATE` 后，系统才允许物理停机并向北冥发出精简《北冥裁决请示书》，等待显式 `Y` / `Confirm` 信号后再进入最终合并或放行步骤。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 定义并实现 M6 的输入/输出、等待态、信号格式、超时/取消行为；明确 M6 与 M5 的交界面；明确没有北冥签字任何代码都不准合并；更新战时文档与 Skill 状态机说明。  
OUT: 不实现真正的 git merge / deploy；不绕过现有人工审批；不把 M6 变成聊天式模糊确认；不降低高危代码的审批门槛。  
WATCHOUTS: 最大风险是把 M6 做成软提示而非硬停机保险丝；第二风险是把任何 `WARN` 或未完成自愈循环的结果送进人工终审；第三风险是把自然语言回复误当成确认信号，导致误放行。

**Inputs (输入)**  
当前 `safe-refactor-loop` Skill、M3 审计引擎、M5 Review Orchestrator、AR-1 战时台账与验证链、自动裁决标准文档。M6 只接收来自 M5 的结构化结果，不直接读取执行体原始输出作为放行依据。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：M6 合同、M6 设计/接口说明、状态机与 Skill/台账更新。  
证据：明确写死只有 `APPROVE_CANDIDATE` 才能进入 M6；M6 输出精简战报并等待 `Y` / `Confirm`；无确认不放行；战时台账与 Skill 已回写该硬规则。

**Done (完成标准)**  
以下条件同时成立才算完成：  
1. M6 被正式定义为唯一合法终审官；  
2. M5 只有在完成全部自愈循环且输出 `APPROVE_CANDIDATE` 后才能进入 M6；  
3. M6 明确要求物理停机并等待北冥显式确认；  
4. 已写死“没有北冥签字，任何代码都不准合并”；  
5. 相关状态机、Skill、Status Ledger 已同步更新。  
