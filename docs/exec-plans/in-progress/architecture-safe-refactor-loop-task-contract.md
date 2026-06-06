## Task Contract（任务合同）

**Objective (目标)**  
设计并实现一个可复用的自动化防爆重构 Skill（暂定名 `safe-refactor-loop`），把当前成功的人类主控流程固化为状态机，使系统未来能够在严格边界、可回查验证链和必要人工审批的约束下，连续自动安全执行重构任务，并优先接管 `TDB-3` 的执行。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 设计 `safe-refactor-loop` 的状态机、战时文档生成逻辑、自动审计顺序、人工审批点、归档平账流程；明确它如何接入现有的 Task Contract / Status Ledger / Verification Chain / 风险索引 / 受控入口索引体系；先以 `TDB-3` 作为目标任务进行适配设计。  
OUT: 不在本轮直接全面重构 Hermes 执行框架；不立即实现 Hook 级强制拦截器；不让 Skill 直接绕过人工审批点；不把整套系统做成“大而全自治代理平台”；不同时推进多个技术债自动执行。  
WATCHOUTS: 最大风险是把 `safe-refactor-loop` 做成“自动改代码工具”，而不是“自动监理状态机”；第二风险是过早移除人工审批点，导致高危动作无保险丝；第三风险是把状态机写得过重、过复杂，反而不如当前人工主控稳；第四风险是只描述流程，不把它接到现有物理文档体系中，最后无法落地。

**Inputs (输入)**  
当前已落地的：`hermes-harness-task-contract`、`hermes-harness-status-ledger`、`hermes-harness-verification-chain`、`hermes-harness-skill-change-loop`、`AGENTS.md`、`runtime-risk-index.md`、`controlled-entry-index.md`、`tech-debt-tracker.md`；以及已实战验证成功的流程：`立合同与沙盒纪律 -> 派玄麟下场 -> Diff 审计 -> 调用链回读 -> 最小相关测试 -> 越界裁决`。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：`safe-refactor-loop` 的状态机设计文档；人工审批点剥离表；自动/人工边界说明；面向 `TDB-3` 的适配方案；必要时的 Skill 草案与配套模板。  
证据：状态机能清晰描述每一步输入/输出/失败转移；能够明确哪些检查自动化、哪些必须人工批准；能证明它与现有 Hermes 骨架兼容；能说明如何安全接管 `TDB-3`，而不是口头上“以后可以自动化”。

**Done (完成标准)**  
以下条件同时成立才算完成：
1. `safe-refactor-loop` 的核心状态机被清晰定义；
2. 自动审计与人工审批的边界被明确切开；
3. 至少能对 `TDB-3` 给出一套可执行的接管方案；
4. 不移除高危动作的人工保险丝；
5. 设计结果可直接转化为 Skill 与配套文档，而不是停留在口头构想。
