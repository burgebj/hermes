## Task Contract（任务合同）

**Objective (目标)**  
在不改动任何执行逻辑、判定逻辑与法典含义的前提下，逐文件语义清理北冥法典相关文档中的“统帅”称呼，并将明确指向用户本人的表达统一改为更低歧义的“北冥”体系表述。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只修改文档、协议、模板、Skill 文本与本次任务文档；逐文件审查 `AGENTS.md`、`docs/agents/beiming-constitution.md`、`docs/agents/mainline-integration-protocol.md`、汇报模板、`docs/agents/law-casebook.md`、`~/.hermes/skills/safe-refactor-loop/SKILL.md`、相关台账/验证链/验收文档中的角色称呼；如重命名汇报模板文件，则同步修正全部引用。  
OUT: 不修改 M3 / M5 / M6 判定逻辑；不修改任何业务代码、运行时代码、测试代码；不改变法典规则含义；不做无脑全局替换。  
WATCHOUTS: 最大风险是把角色去幻觉清理误做成法律含义改写；第二风险是文件重命名后遗漏引用修复；第三风险是把历史文档中的用户本人语义误改成抽象职位语义；第四风险是触碰代码字符串而越过“只改文档/Skill 文本”的边界。

**Inputs (输入)**  
`AGENTS.md`、`docs/agents/beiming-constitution.md`、`docs/agents/mainline-integration-protocol.md`、`docs/agents/beiming-report-template-v2.md`（原 `commander-report-template-v2.md`）、`docs/agents/law-casebook.md`、`~/.hermes/skills/safe-refactor-loop/SKILL.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`、`docs/exec-plans/tech-debt-tracker.md`；用户给出的术语原则：明确指向用户本人时，统一改为“北冥 / 北冥（用户本人）/ 北冥签字 / 北冥审批 / 北冥汇报模板 / 北冥裁决请示书”。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：完成术语去幻觉清理后的目标文档、重命名后的北冥汇报模板文件、同步修正后的引用，以及本次任务的合同 / 台账 / 验证链。  
证据：逐文件回读显示“统帅”已按语义改为“北冥”体系表述；重命名后的模板路径引用已全部切换；搜索结果证明旧模板路径引用已清理；`git diff --stat` 仅显示文档与 Skill 文本改动；可明确说明未触碰执行逻辑。

**Done (完成标准)**  
1. 目标文档中的“统帅”称呼已按语义逐文件清理；  
2. “等待统帅输入 Y / Confirm”类表达已统一改为“等待北冥输入 Y / Confirm”；  
3. 若发生模板文件重命名，旧路径引用已全部修正；  
4. 未改动任何执行逻辑、业务代码与 M3 / M5 / M6 判定逻辑；  
5. 最终汇报可按文件列出术语变更摘要、重命名映射、关键引用修复与未改动逻辑声明。
