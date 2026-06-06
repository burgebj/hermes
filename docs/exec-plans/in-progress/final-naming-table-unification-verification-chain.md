## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应本轮交付物、证据与完成标准。
- 目标 1：证明法典主干中的正式总称已统一为“北冥法典”，正式顶层原则层已统一指向“北冥宪章”。
- 目标 2：证明“北冥汇报模板”“北冥裁决请示书”“Harness Engineering”“safe-refactor-loop”等正式称呼在主干中与《最终命名表》一致。
- 目标 3：证明若发生文件重命名，相关引用已修复且 `AGENTS.md` 仍保持地图型入口。
- 目标 4：证明本轮改动只涉及文档、Skill 文本与任务现场文档，没有触碰执行逻辑、判定逻辑、Git 工作流与业务代码。

**Verification Actions (验证动作)**
- 动作 1：逐文件回读 `AGENTS.md`、宪章、主线协议、casebook、北冥汇报模板、tech-debt-tracker 与 `~/.hermes/skills/safe-refactor-loop/SKILL.md`，核对正式称呼是否按语义统一。
- 动作 2：搜索法典主干中的“统帅”“帝国法典”“北冥帝国法典”“统帅汇报模板”“统帅裁决请示书”“empire-constitution.md”。
- 动作 3：如发生重命名，检查旧路径引用与新路径命中，确认关键引用全部切换。
- 动作 4：查看 `git diff --name-only` 与 `git diff --stat`，确认改动范围只落在允许文件。

**Verification Result (验证结果)**
- 目标 1：通过 —— `AGENTS.md`、`docs/agents/beiming-constitution.md`、`docs/agents/law-casebook.md` 与 `~/.hermes/skills/safe-refactor-loop/SKILL.md` 已统一使用“北冥法典 / 北冥宪章”等正式称呼。
- 目标 2：通过 —— 北冥汇报模板、北冥裁决请示书、Harness Engineering、safe-refactor-loop 等正式称呼在主干与 Skill 中均已按《最终命名表》落地。
- 目标 3：通过 —— 宪章文件已重命名为 `docs/agents/beiming-constitution.md`，关键文档与任务现场中的主干路径引用已同步修复。
- 目标 4：通过 —— 当前 git 变更边界只涉及文档、Skill 文本与任务现场文档；代码与测试命中项未被修改。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：无。
- 接手后第一步：若需复核，先按改动文件清单回读，再执行针对主干的旧称呼搜索与 git 边界检查。
- 接手入口：先看本任务合同、状态台账、迁移状态文件、以及 `docs/agents/beiming-constitution.md` 的重命名结果。