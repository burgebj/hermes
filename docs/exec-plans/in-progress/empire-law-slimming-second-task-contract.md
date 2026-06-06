## Task Contract（任务合同）

**Objective (目标)**  
在不改动任何核心执行逻辑与红线判定条件的前提下，完成北冥法典“瘦身二次手术”，把主线收编固定法则、状态机固定门槛与战史经验重新分层，使未来 CLI 更稳定地区分北冥宪章、协议、状态机、战史经验与北冥汇报模板。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只修改 `docs/agents/mainline-integration-protocol.md`、`~/.hermes/skills/safe-refactor-loop/SKILL.md`、`docs/agents/law-casebook.md`，并为本次任务新增任务合同、状态台账、验证链；允许对表达进行抽脂重写与规则重归类，但必须保持逻辑等价。  
OUT: 不修改 M3 / M5 / M6 执行逻辑；不修改任何 `REJECT_HARD` / `FAKE_WIN` / `APPROVE_CANDIDATE` 判定条件；不修改业务代码、测试代码、调度器逻辑；不把 `AGENTS.md` 写胖；不新建平台级框架。  
WATCHOUTS: 最大风险是把“迁移位置”误做成“改变法律”；第二风险是删除红线却不给去向；第三风险是把战史案例继续残留在协议或 Skill 中；第四风险是为了瘦身删除未来 CLI 仍需读取的固定门槛。

**Inputs (输入)**  
`~/.hermes/hermes-agent/AGENTS.md`、`docs/agents/beiming-constitution.md`、`docs/agents/mainline-integration-protocol.md`、`docs/agents/beiming-report-template-v2.md`、`docs/agents/law-casebook.md`、`~/.hermes/skills/safe-refactor-loop/SKILL.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`、`docs/exec-plans/tech-debt-tracker.md`；北冥签字红线：TTY 降级必死、常量绕过拦截、参数别名漂移、shell/PATH 保护、主线收编四类验收、M6 物理停机与北冥签字权必须保留。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：抽脂后的 `mainline-integration-protocol.md` 与 `safe-refactor-loop/SKILL.md`，承接战史经验后的 `law-casebook.md`，以及本次任务的合同 / 台账 / 验证链。  
证据：文件回读证明协议仅保留固定法则、检查项、红线与模板索引；Skill 仅保留状态机、模式、硬门槛、调用关系与一键启动；`law-casebook.md` 承接了迁出的战史经验与失败先例；`git diff` 与回读结果能解释每一类迁移、新增、删除；逻辑一致性检查证明没有改动执行逻辑与红线强度。

**Done (完成标准)**  
1. `mainline-integration-protocol.md` 已抽脂为主线收编固定法则文档；  
2. `safe-refactor-loop/SKILL.md` 已抽脂为状态机与硬门槛文档；  
3. `law-casebook.md` 已承接迁出的 PAC / AR / TDB 战史经验、失败先例与红线淬炼案例；  
4. 没有任何法典红线被删弱，没有任何执行逻辑被改动；  
5. 能以证据证明宪章、协议、状态机、战史经验、汇报模板五层已清晰分离。

## M1 附件：规则迁移清单

| 编号 | 规则 / 内容 | 原文件 | 目标文件 | 迁移类型 |
| --- | --- | --- | --- | --- |
| 1 | 主线收编前先校验“任务对象一致 + 协议对象一致 + 分支祖先干净” | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/mainline-integration-protocol.md` | 固定法则上收 |
| 2 | 主线收编时同时比对 `git show --stat --summary HEAD` 与 `git diff --name-status main..HEAD` 的候选边界检查 | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/mainline-integration-protocol.md` | 固定检查项上收 |
| 3 | 主线收编 push 被远端抢先时，先 `fetch` 判定远端已吸收哪一层战果，再决定 rebase / closure commit | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/mainline-integration-protocol.md` | 固定红线上收 |
| 4 | 新战役收编前先确认协议已切到当前战役，且候选已形成单一可审计提交 | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/mainline-integration-protocol.md` | 固定法则上收 |
| 5 | M3→调用链→pytest→报告 的固定复审顺序 | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | 保留并抽脂重写 |
| 6 | TTY 降级必死、常量绕过拦截、参数别名漂移、shell/PATH 保护、测试通过不免罪、M6 物理停机签字权 | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | 保留并抽脂重写 |
| 7 | 脏工作树隔离 worktree、白名单测试文件误判、`--yes` 不得绕过 typed confirmation、共享 helper、pytest 解释器 / addopts、未跟踪文件不进 worktree | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/law-casebook.md` | 战史经验迁移 |
| 8 | 未跟踪新文件 diff 要用 `git diff --no-index -- /dev/null <path>`、坏 diff / 策略冲突 fail-closed | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/law-casebook.md` | 战史经验迁移 |
| 9 | 合同 fail-closed、台账 / 验证链可恢复；账本按 section 选战役；假批准器禁止；按 battle_name 更新 tracker | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/law-casebook.md` | 战史经验迁移 |
| 10 | PAC vs AR-1 任务对象错位、远端抢先、协议滞后 / 候选未提交三类主线事故 | `~/.hermes/skills/safe-refactor-loop/SKILL.md` | `docs/agents/law-casebook.md` | 战史经验迁移 |
| 11 | 现有 `FAKE_WIN`、TTY 降级、`rm` 拦截、PAC vs AR-1 错位案例的承接与扩编 | `docs/agents/law-casebook.md` | `docs/agents/law-casebook.md` | 原位扩编 |
| 12 | `mainline-integration-protocol.md` 的命令示例段 | `docs/agents/mainline-integration-protocol.md` | 无（删除） | 冗余说明删除，非规则 |
