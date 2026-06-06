## Task Contract（任务合同）

**Objective (目标)**  
在不改动任何执行逻辑、判定逻辑与 Git 工作流的前提下，按《最终命名表》对北冥法典主干进行逐文件语义统一收口，并在必要时完成文件重命名与引用修复。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只修改 `AGENTS.md`、`docs/agents/` 法典主干文档、`docs/exec-plans/tech-debt-tracker.md`、本轮任务现场文档，以及 `~/.hermes/skills/safe-refactor-loop/SKILL.md`；逐文件按语义把正式称呼统一为“北冥 / 有鱼 / 玄麟 / 北冥法典 / 北冥宪章 / 北冥汇报模板 / 北冥裁决请示书 / safe-refactor-loop / Harness Engineering”；必要时重命名仍带旧正式称呼的法典主干文件并同步修复引用。  
OUT: 不修改任何业务代码、运行时代码、测试代码；不改 M3 / M5 / M6 判定逻辑；不改 Git 工作流；不改任何 `REJECT_HARD` / `FAKE_WIN` / `APPROVE_CANDIDATE` 条件；不新增宏大叙事称呼；不做无脑全局替换。  
WATCHOUTS: 最大风险是把命名统一误做成法律含义改写；第二风险是文件重命名后遗漏引用；第三风险是把历史存档中的旧称呼误当成本轮正式称呼继续传播；第四风险是越界修改代码或测试中的历史字符串。

**Inputs (输入)**  
`AGENTS.md`、`docs/agents/beiming-constitution.md`、`docs/agents/mainline-integration-protocol.md`、`docs/agents/law-casebook.md`、`docs/agents/beiming-report-template-v2.md`、`~/.hermes/skills/safe-refactor-loop/SKILL.md`、`docs/exec-plans/tech-debt-tracker.md`；用户给出的《最终命名表》与红线：正式称呼统一到“北冥法典 / 北冥宪章 / 北冥汇报模板 / 北冥裁决请示书”，且仅做主干收口，不改执行逻辑。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：完成术语统一后的法典主干文档、必要的文件重命名与引用修复、本轮任务合同 / 状态台账 / 验证链 / 迁移状态文件。  
证据：逐文件回读显示正式称呼已统一；搜索结果证明旧称呼不再作为当前正式称呼留在法典主干；若发生重命名，旧路径引用已切换；`git diff --name-only` 显示只改文档与 Skill 文本；可明确说明未触碰执行逻辑。

**Done (完成标准)**  
1. 用户指定的 8 个最终正式称呼已在法典主干中统一落地；  
2. “统帅 / 帝国 / 帝国法典 / 统帅汇报模板 / 统帅裁决请示书”等旧称呼不再作为当前正式称呼继续存在；  
3. 如有文件重命名，旧路径引用已全部修复；  
4. 未改动任何业务代码、执行逻辑、判定逻辑与 Git 工作流；  
5. `AGENTS.md` 仍保持地图型入口，没有写胖。