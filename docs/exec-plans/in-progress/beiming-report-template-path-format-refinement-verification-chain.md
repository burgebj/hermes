## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应本任务关于路径写法统一、11 个顶层字段稳定输出、“未暴露”边界、Session ID 兼容规则与最小必要引用同步的交付物 / 证据 / 完成标准。
- 目标 1：证明汇报模板已明确规定仓库内文件使用仓库相对路径，仓库外 Skill 可使用绝对路径并标明仓库外。
- 目标 2：证明汇报模板已稳定保留 11 个顶层字段，并明确哪些字段必须始终输出、哪些子字段允许写“未暴露”。
- 目标 3：证明 Session ID 规则已固定为“可读则真实值，不可读则固定兜底句式”，且仍明确禁止编造或留空不解释。
- 目标 4：证明主线协议、宪章与账本中与模板直接相关的引用口径已同步一致，且本轮改动未越界到执行逻辑或测试逻辑。

**Verification Actions (验证动作)**
- 动作 1：回读 `docs/agents/beiming-report-template-v2.md`，核对路径写法、字段清单、“未暴露”规则与 Session ID 规则是否全部落地。
- 动作 2：回读 `docs/agents/mainline-integration-protocol.md`、`docs/agents/beiming-constitution.md` 与 `docs/exec-plans/tech-debt-tracker.md`，核对与模板直接相关的引用口径是否一致。
- 动作 3：搜索目标文件，确认仓库内未混入 `.hermes/hermes-agent/...` 这类投影式路径；若出现该字样，仅作为禁止示例存在，而非实际文件引用。
- 动作 4：检查 `git status --short`、`git rev-parse --show-toplevel`、`git branch --show-current` 与环境变量，确认本轮改动范围仍局限于文档，且运行时未暴露当前会话 Session ID。

**Verification Result (验证结果)**
- 目标 1：通过 —— `docs/agents/beiming-report-template-v2.md` 已写明仓库内路径统一使用仓库相对路径，仓库外 Skill / 系统文件可写绝对路径并标注“仓库外”。
- 目标 2：通过 —— 模板已固定 11 个顶层字段，并把 `Session ID`、`当前分支`、`当前候选提交（如有）` 列为仅在运行时确实无法读取时允许写“未暴露”的字段。
- 目标 3：通过 —— 模板与主线协议都已固定 Session ID 的真实值 / 指定兜底句式规则；环境变量检查未提供当前会话 Session ID，因此本轮最终汇报必须使用固定兜底句式。
- 目标 4：通过 —— 主线协议、宪章与账本已同步引用口径；`git status --short` 显示本轮涉及文件均为文档路径；未见执行逻辑或测试逻辑改动被纳入本轮范围。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：无。
- 接手后第一步：若需复核，先按结案报告列出的文件清单逐一回读，再对照本验证链的 4 项结果。
- 接手入口：先看本任务合同、状态台账、验证链、结案报告，以及 `docs/agents/beiming-report-template-v2.md` 当前正文。