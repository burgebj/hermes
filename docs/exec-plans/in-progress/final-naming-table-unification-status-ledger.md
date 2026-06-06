**Task Contract Snapshot (合同快照)**
- 目标：按《最终命名表》对北冥法典主干做逐文件语义统一收口，并在必要时完成文件重命名与引用修复。
- 范围边界：只改法典主干文档、相关账本/现场文档与 `~/.hermes/skills/safe-refactor-loop/SKILL.md`；不改任何代码、测试、执行逻辑与 Git 工作流。
- 完成标准：正式称呼统一落地，必要引用已修复，旧称呼不再作为当前正式称呼保留，且 `AGENTS.md` 仍是地图型入口。

**Current State (当前状态)**
- 当前停点：已完成主干术语统一、宪章文件重命名与关键引用修复，正在做最终搜索与 git 边界验收。
- 已完成：已回读用户点名文件、safe-refactor-loop Skill 与 tech-debt-tracker；已将 `docs/agents/empire-constitution.md` 重命名为 `docs/agents/beiming-constitution.md`；已统一 AGENTS、北冥宪章、casebook、Skill 与账本文案中的正式称呼；已建立迁移状态文件与备份。
- 未完成 / 当前阻塞：无执行阻塞；仅剩最终证据回写与汇报输出。代码与测试中的历史字符串命中按红线保持不改。
- 当前判断：可收口

**Evidence Logged (证据登记)**
- 已有证据：目标文件回读结果、旧称呼搜索命中、`docs/exec-plans/tech-debt-tracker.md` 活跃战役信息、`docs/exec-plans/in-progress/final-naming-table-unification-migration-state.json` 备份与回滚信息。
- 证据对应结论：法典主干的正式称呼已统一到《最终命名表》口径，且宪章文件名与关键引用已完成收口。
- 证据缺口：无当前阶段缺口；仅保留汇报所需汇总整理。

**Next Handoff (下一步 / 接管指令)**
- 接手后第一步：若需复核，先回读 `AGENTS.md`、`docs/agents/beiming-constitution.md`、`docs/agents/law-casebook.md` 与 `~/.hermes/skills/safe-refactor-loop/SKILL.md`，确认正式称呼已统一。
- 立即核查：所有改动必须停留在文档、Skill 文本与任务现场文档，不得进入代码或测试。
- 若受阻先排查：若搜索结果只剩代码或历史存档命中，则保持不改并在最终汇报中说明边界原因。