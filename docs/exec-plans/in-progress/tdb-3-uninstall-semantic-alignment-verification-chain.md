## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：直接对应 TDB-3 的交付物 / 证据与完成标准。
- 目标 1：证明候选 diff 只触碰 `hermes_cli/main.py`、`hermes_cli/uninstall.py` 与直接相关最小测试，没有越界到 `profiles.py`、`docs/`、shell / PATH / wrapper 链。
- 目标 2：证明 `_require_tty("uninstall")` 没有被放松，`--yes` 没有获得非 TTY 绕过能力，TTY / 人工确认边界仍然存在。
- 目标 3：证明 `--full / --yes` 的 CLI 语义真实接入 `run_uninstall(...)` 控制流，而不是只改 help 文案或参数表面映射。
- 目标 4：证明指定 pytest 真实通过，且 M5-v2 的裁决结果为 `APPROVE_CANDIDATE`，不是 `FAKE_WIN / OUT_OF_SCOPE / REJECT_HARD`。
- 目标 5：证明只有在目标 1-4 满足后，系统才允许进入 M6 物理停机等待北冥签字。

**Verification Actions (验证动作)**
- 动作 1：对隔离 worktree 执行 `git diff --name-only` 与 `git diff -- ...`，核对改动文件范围与关键控制流变更，必要时回读 `main.py` / `uninstall.py` 关键片段。
- 动作 2：用 `hermes_cli.safe_refactor_audit.audit_tdb3_diff(...)` 或等价入口对候选 diff 执行 M3 审计，重点核查 `FILE_SCOPE`、`TTY_DOWNGRADE`、`TTY_POLICY_INDIRECT_RELAXATION`、`SHELL_PATH_TOUCH`、`CONTRACT_CONSISTENCY`、`ARG_ALIAS_SEMANTIC_DRIFT`。
- 动作 3：执行指定 pytest（需要覆盖仓库默认 `-n` 配置时使用 `-o addopts=''`），验证 TDB-3 相关最小测试与 M3/M5/M6 回归测试是否通过，并记录 exit code。
- 动作 4：对候选 diff 运行 M5-v2 自愈审计；若非 `APPROVE_CANDIDATE`，提取纠错指令回灌玄麟，最多 3 次；未出真赢候选不得请求北冥确认。
- 动作 5：仅当 M5-v2 输出 `APPROVE_CANDIDATE` 后，生成精简《裁决请示书》，由 M6 物理停机等待北冥显式 `Y / Confirm`。

**Verification Result (验证结果)**
- 目标 1：通过 —— 第二轮真实 diff 只触碰 `hermes_cli/main.py`、`hermes_cli/uninstall.py`、`tests/hermes_cli/test_uninstall.py`，越界新文件 `tests/hermes_cli/test_uninstall_flags.py` 已撤销，M3 对最终候选未报 `FILE_SCOPE`。
- 目标 2：通过 —— `cmd_uninstall()` 仍保留 `_require_tty("uninstall")`；最终候选保留 typed confirmation；M3 对最终候选给出 `APPROVE`，未触发 `TTY_DOWNGRADE` 或 `TTY_POLICY_INDIRECT_RELAXATION`。
- 目标 3：通过 —— `main.py` 改为 `run_uninstall(normalize_uninstall_args(args))`，`uninstall.py` 中同一 helper `normalize_uninstall_args` 真实接入控制流；`--full` 仅用于 TTY 内预选 full uninstall 模式，`--yes` 的帮助文本已改为兼容占位且不再宣称可跳过最终 typed confirmation。
- 目标 4：通过 —— M5-v2 在使用可用解释器 `/opt/homebrew/bin/python3.11 -m pytest -q -o addopts='' tests/hermes_cli/test_uninstall.py` 后，给出 `APPROVE_CANDIDATE`；pytest 结果为 `3 passed in 0.04s`。
- 目标 5：通过 —— 当前已到 M6 人工闸门；尚未收到北冥 `Y / Confirm` 前，系统保持物理停机，不做任何提交、合并或放行。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：仅剩是否把隔离提交 `a520f70e` 集成回主仓 `main` 的后续工程动作；本轮首航本身已闭环。
- 接手后第一步：若要集成，先在干净上下文中对 `a520f70e` 做 cherry-pick / 再复审；若暂不集成，则保持当前隔离提交作为已验收成果。
- 接手入口：先看隔离分支 `tdb-3-safe-refactor-flight`、提交 `a520f70e`、`~/.hermes/runtime/agents/xuanlin/latest.json`、以及本验证链与状态台账。