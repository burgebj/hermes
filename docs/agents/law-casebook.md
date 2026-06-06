# Law Casebook / 北冥法典战史与淬炼案例

> 定位：这里承接北冥法典在实战中淬炼出的案例、失败先例与制度性教训。
> 它不是宪章、不是协议、不是状态机。
> 它只回答：哪些历史战役证明了哪些红线必须存在，以及哪些事故不能再发生。

## 1. 使用边界

- 宪章原则看 `docs/agents/beiming-constitution.md`
- 主线收编固定法则看 `docs/agents/mainline-integration-protocol.md`
- 执行状态机与固定硬门槛看 `~/.hermes/skills/safe-refactor-loop/SKILL.md`
- 本文件只沉淀战史经验、失败先例与法典淬炼案例

## 2. 通用法典案例

### Case 1：`FAKE_WIN` 战例
- 现象：测试通过、报告好看，但控制流没有真实对齐。
- 法典结论：`FAKE_WIN` 不是胜利，必须继续打回。
- 对应淬炼：M5 不得被“测试全绿”诱导误判。

### Case 2：TTY 降级必死战例
- 现象：执行体试图通过显性或隐性方式放宽 `_require_tty("uninstall")` 或确认边界。
- 法典结论：一律 `REJECT_HARD`。
- 对应淬炼：M3 必须把 TTY 降级视为契约级越界，而不是普通优化。

### Case 3：`rm` 拦截事件
- 现象：任务推进中出现潜在危险删除动作，系统选择停手而非暴力绕过。
- 法典结论：红线面前宁可停止，不靠聪明和侥幸赌过去。
- 对应淬炼：自动系统必须具备“不会为完成任务背叛法典”的底层品格。

### Case 4：PAC vs AR-1 收编错位
- 现象：主线收编任务对象错位，PAC 候选被误当作 AR-1 收编对象。
- 法典结论：任务对象错位时必须先纠偏，不得强推。
- 对应淬炼：主线收编模式必须优先保护对象边界与候选纯度。

## 3. Skill 状态机淬炼案例

### Case 5：主仓工作树脏时，必须先切隔离 worktree
- 事故：TDB-3 首轮前线若直接在脏主仓派执行体，历史改动会混入候选 diff。
- 法典结论：候选 diff 必须纯净可归因；脏工作树先切隔离 worktree。
- 对应淬炼：safe-refactor-loop 把“先记录 branch / HEAD，再基于该 SHA 新建隔离 worktree”固化为实战纪律。

### Case 6：M3 白名单未放开的测试文件，不得擅自新建同类新文件
- 事故：TDB-3 首轮把最小测试写进新文件 `tests/hermes_cli/test_uninstall_flags.py`，语义虽正确，仍被 `FILE_SCOPE` 打回。
- 法典结论：当审计器仍按具体白名单放行时，执行体必须优先复用白名单内既有测试文件。
- 对应淬炼：测试语义正确不等于文件范围合规。

### Case 7：`--yes` 语义对齐不得顺手放松最终 typed confirmation
- 事故：TDB-3 首轮曾让 `--yes` 直接接受最终确认，虽然 `_require_tty("uninstall")` 仍在，依然被视为 `TTY_DOWNGRADE / REJECT_HARD`。
- 法典结论：只要任务合同仍把 TTY / 人工确认边界列为红线，`--yes` 只能做兼容占位，不得获得更宽松确认能力。
- 对应淬炼：参数对齐任务不能借“兼容”之名降安全门槛。

### Case 8：参数对齐不能只改 help，必须有真实共享 helper
- 事故：TDB-3 发现仅改 help 文案，无法让 M5 的调用链证据达到 `approval_ready`。
- 法典结论：需要真实共享 helper 把入口与执行层接到同一控制流。
- 对应淬炼：`normalize_uninstall_args(...)` 这类共享接线，比分散改动更能证明语义真实落地。

### Case 9：pytest 必须用已知可运行解释器，并必要时清空默认 `addopts`
- 事故：TDB-3 曾因系统 `python3` 没有 pytest 被误打成 `FAKE_WIN`；AR-1 dogfood 又因默认 `-n` addopts 缺插件而失败。
- 法典结论：先区分“代码失败”与“测试环境失败”，再裁决候选。
- 对应淬炼：优先使用已知有 pytest 的解释器；必要时加 `-o addopts=''` 跑最小测试子集。

### Case 10：主仓未跟踪原型文件不会自动进入基于 HEAD 的隔离 worktree
- 事故：AR-1 dogfood 时，主仓里已有的未跟踪模块与测试，在隔离 worktree 中全部缺失。
- 法典结论：主仓“看起来有”不等于隔离战场“真实存在”。
- 对应淬炼：进入 worktree 后必须重新核查模块、测试、战时文档是否真实存在；缺失就按已落盘合同与技能重建最小骨架。

### Case 11：未跟踪新文件的候选 diff 不能只跑普通 `git diff`
- 事故：PAC-CORE-001 首轮 M5 审计时，对未跟踪新文件跑普通 `git diff -- <paths>` 得到空结果，险些把“未审候选”误当成通过。
- 法典结论：对未跟踪新文件，必须用 `git diff --no-index -- /dev/null <path>` 生成真实候选 diff。
- 对应淬炼：M5 证据里必须区分真实候选 diff、攻击样本 diff 与自愈后安全 diff。

### Case 12：Policy-as-Code 审计器必须对坏 diff 与策略冲突双重 fail-closed
- 事故：PAC-CORE-001 第二轮独立审查发现，空 diff / 畸形 diff 会被旧实现当成“干净候选”，而 allowlist 与 restricted scope 的冲突也可能让敏感路径被重新放行。
- 法典结论：坏 diff 拒绝、策略冲突拒绝，两类都必须 fail-closed。
- 对应淬炼：`parse_valid`、`policy.diff_parse_invalid` 与 scope consistency 校验必须存在，且覆盖多 override 顺序绕过场景。

### Case 13：战时文档接线必须“合同 fail-closed，台账 / 验证链可恢复”
- 事故：AR-1 首版 runtime 曾把 Task Contract、Status Ledger、Verification Chain 三份文档都走“缺了就补造”。
- 法典结论：合同是任务边界锚点，缺失时必须直接失败；只有台账与验证链可以在合同存在的前提下恢复。
- 对应淬炼：自动恢复能力不能掩盖真正的任务边界丢失。

### Case 14：一键启动从账本选战役时，不能用跨段正则硬抓
- 事故：AR-1 首版 `select_active_battle(...)` 曾把 `TDB-9` 误抓成活跃战役，只因为后文 section 里出现了“最高优先级活跃战役”。
- 法典结论：先按 `^### ` 分段，再在每个 section 内独立解析 battle name 与状态。
- 对应淬炼：账本解析必须 section-aware，不能靠跨段 `re.S` 侥幸命中。

### Case 15：M6 人工闸门不得允许外部注入假批准器
- 事故：AR-1 第二轮独立复审指出，首版 pipeline 只要传入永远 `approved=True` 的 `human_gate` 就能跳过真实人审并触发归档。
- 法典结论：生产默认路径必须强制走 `HumanGateController`；测试替身只有显式白名单时才允许生效。
- 对应淬炼：人工审批闸门属于主权锚点，不得因可测试性被默认旁路。

### Case 16：归档同步器更新 tracker 时，必须按当前 `battle_name` 定点改 section
- 事故：AR-1 首版 `_update_tracker_for_stage_closure(...)` 把匹配逻辑硬编码成 `AR-1`，导致非 AR battle 虽然归档成功，账本却不更新。
- 法典结论：tracker 更新必须按当前战役名定位 section，找不到就 fail-closed。
- 对应淬炼：归档成功与账本平账必须绑定在同一战役对象上。

## 4. 主线收编淬炼案例

### Case 17：主线收编前必须先校验“战役身份一致 + 分支祖先干净”
- 事故：用户点名的是 AR-1 主线收编，现场恢复出的却是 PAC-CORE-001；同时候选分支叠在别的未入主线分支之上，`main..HEAD` 还额外带出无关文件。
- 法典结论：任务对象错位或祖先不干净时，直接打回，不得继续推送。
- 对应淬炼：主线收编协议必须把“对象一致性 + 候选纯度”列为固定检查项。

### Case 18：主线收编 push 被远端抢先时，先 fetch 判定远端已含哪一层战果
- 事故：PAC-CORE-001 本地已生成主线收编提交，但 `git push origin main` 被远端抢先；如果直接强推或重做，会误覆盖 closure 文档与真实状态。
- 法典结论：先 `fetch`，再判断远端已吸收的是核心代码还是 closure 文档，之后再决定 rebase 或补 closure commit。
- 对应淬炼：主线收编不是“谁先 push 谁赢”，而是先分层识别战果已落到哪里。

### Case 19：新战役主线收编时，协议仍写死前一战役或候选尚未形成提交，只能直接打回
- 事故：AR-1 工程化接线收口时，worktree 里已有代码、测试与战时文档，但主线协议仍指向 PAC，且 `origin/main..HEAD` 为空，说明候选还只存在于 worktree 脏改动中。
- 法典结论：协议不新鲜、候选未形成单一可审计提交时，不得进入 `git add/commit/push`。
- 对应淬炼：协议 freshness 与候选 commit existence 都是主线收编前置条件。

## 5. 记录原则

未来新增案例时，优先写清：
- 事故或冲突是什么
- 法典最终如何裁决
- 这条裁决后来沉淀成了哪条固定规则

不要把具体战役的所有流水账都堆进这里。
这里只保留足以淬炼法典的先例级事实。
