## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应本次角色术语去幻觉清理任务的交付物、证据与完成标准。
- 目标 1：证明目标文档中明确指向用户本人的“统帅”称呼已按语义改为“北冥”体系表述。
- 目标 2：证明“等待统帅输入 Y / Confirm”类表达已统一改为“等待北冥输入 Y / Confirm”。
- 目标 3：证明汇报模板已在需要时完成重命名，且旧路径引用已同步修复。
- 目标 4：证明本次改动只涉及文档、协议、模板、Skill 文本与任务文档，没有触碰执行逻辑与业务代码。

**Verification Actions (验证动作)**
- 动作 1：逐文件回读 `AGENTS.md`、宪章、主线协议、北冥汇报模板、casebook、safe-refactor-loop Skill、相关台账 / 验证链，核对术语替换是否符合上下文语义。
- 动作 2：搜索 `docs/` 与 `~/.hermes/skills/safe-refactor-loop/SKILL.md` 中的“统帅”“commander-report-template-v2.md”“等待统帅输入”。
- 动作 3：查看 `git diff --stat` 与 `git diff --name-status`，确认改动范围仅为文档、模板、Skill 文本与任务文档。
- 动作 4：对命中但未改动的条目做边界判定，确认其属于业务代码或非本轮允许范围。

**Verification Result (验证结果)**
- 目标 1：通过 —— 目标文档与相关战时文档中明确指向用户本人的“统帅”称呼已按语义改为“北冥”体系表述；剩余命中仅存在于本任务文档中，作为清理对象说明。
- 目标 2：通过 —— 业务文档中的“等待统帅输入 Y / Confirm”类表达已清理为“等待北冥输入 Y / Confirm”；剩余命中仅存在于本任务文档中，作为验证目标描述。
- 目标 3：通过 —— 汇报模板已重命名为 `docs/agents/beiming-report-template-v2.md`，仓库中的旧路径仅保留在本任务文档与迁移状态文件中，用于记录旧新映射。
- 目标 4：通过 —— 本轮改动只落在文档、模板、Skill 文本与任务文档；业务代码中的历史字符串命中已按红线保持不改。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：无。
- 接手后第一步：若需复核，先按最终汇报中的改动文件清单逐一回读，再对照本验证链的 4 项结果。
- 接手入口：先看本任务合同、状态台账、验证链，以及重命名后的 `docs/agents/beiming-report-template-v2.md`。
