## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应本次法典瘦身二次手术的交付物、证据与完成标准。
- 目标 1：证明 `docs/agents/mainline-integration-protocol.md` 只剩主线收编固定法则、固定检查项、固定红线与模板索引。
- 目标 2：证明 `~/.hermes/skills/safe-refactor-loop/SKILL.md` 只剩状态机、模式、硬门槛、调用关系与一键启动方式。
- 目标 3：证明 `docs/agents/law-casebook.md` 真实承接了迁出的战史经验、失败先例与法典淬炼案例。
- 目标 4：证明本次改动没有削弱既有红线，也没有改变任何执行逻辑。
- 目标 5：证明宪章、协议、状态机、战史经验、汇报模板五层分离比改动前更清晰。

**Verification Actions (验证动作)**
- 动作 1：回读抽脂后的协议、Skill、casebook、AGENTS 与北冥汇报模板，逐项核对层级职责是否清晰。
- 动作 2：用 `git diff --stat` 与目标文件 diff 回读，识别哪些内容是纯迁移、哪些是重写、哪些是删除。
- 动作 3：逐条核对红线：TTY 降级、常量绕过、参数别名漂移、shell/PATH 保护、主线四类验收、M6 物理停机与北冥签字权。
- 动作 4：对照《规则迁移清单》做逻辑一致性检查，确认所有新增表达均可追溯，所有删除都有去向或属于非规则冗余说明。

**Verification Result (验证结果)**
- 目标 1：通过 —— 回读后的 `mainline-integration-protocol.md` 只保留主线收编固定法则、固定检查项、固定红线与模板索引，且搜索未再命中 PAC / AR-1 / TDB 战史词条。
- 目标 2：通过 —— 回读后的 `safe-refactor-loop/SKILL.md` 保留状态机、模式、固定硬门槛、固定调用关系与一键启动；搜索未再命中 PAC / AR-1 等具体战役经验。
- 目标 3：通过 —— `law-casebook.md` 已扩编为 19 个案例，明确承接 PAC / AR / TDB 战史经验、失败先例与法典淬炼案例。
- 目标 4：通过 —— 红线关键词与 M6 物理停机签字权仍在 Skill / 协议中可回读，且本次只修改文档与 Skill 文本，未触碰 M3 / M5 / M6 执行逻辑文件。
- 目标 5：通过 —— AGENTS 仍只做地图入口；宪章、协议、状态机、战史经验、汇报模板各自有单独入口并互相索引。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：无。
- 接手后第一步：若需复核，先回读 `docs/exec-plans/in-progress/empire-law-slimming-second-task-contract.md` 的《规则迁移清单》，再对照最终汇报中的《法典演进 Diff》。
- 接手入口：先看本任务合同、状态台账、验证链与三个目标文件的回读结果。 
