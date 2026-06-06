## Verification Chain（默认验证链）

**Verification Target (验证目标)**
- 对应合同项：对应本轮 live repo 最小运行健康、文档口径纠偏与完成标准。
- 目标 1：证明 `hermes_cli/safe_refactor_audit.py` 与 `hermes_cli/human_gate_controller.py` 在当前 live repo 中可被 Python 正常编译与导入。
- 目标 2：证明两个目标文件中不再存在 `***` 等残留占位或明显语法损坏。
- 目标 3：证明两份直接相关最小测试通过。
- 目标 4：证明文档已明确本轮不是主线收编证明、不是相对 `origin/main` 的纯类型标注小修，且目标文件仍处于未跟踪状态。

**Verification Actions (验证动作)**
- 动作 1：在 `/Users/beiming/.hermes/hermes-agent` 运行 `python -m py_compile hermes_cli/safe_refactor_audit.py hermes_cli/human_gate_controller.py`。
- 动作 2：在当前 live repo 运行直接导入脚本，分别导入 `hermes_cli.safe_refactor_audit` 与 `hermes_cli.human_gate_controller`。
- 动作 3：扫描两个目标文件中的 `***`、`PLACEHOLDER`、`TODO`、`NotImplemented`、`pass  #`。
- 动作 4：运行 `python -m pytest -o addopts='' tests/hermes_cli/test_safe_refactor_audit.py tests/hermes_cli/test_human_gate_controller.py -q`。
- 动作 5：运行 `git status --short` 与 `git rev-list --left-right --count main...origin/main`，确认跟踪状态与分支落后状态。
- 动作 6：对比 `origin/main` 中两个目标文件与当前工作区文件，确认差异性质不是纯类型标注小修。

**Verification Result (验证结果)**
- 目标 1：通过 —— 编译命令退出码 0，直接导入脚本退出码 0，并输出两个模块 import ok。
- 目标 2：通过 —— 残留占位扫描输出 `hermes_cli/safe_refactor_audit.py: residuals=[]` 与 `hermes_cli/human_gate_controller.py: residuals=[]`。
- 目标 3：通过 —— 定向 pytest 输出 `8 passed in 0.03s`。
- 目标 4：通过 —— `git status --short` 显示两个目标文件仍为 `??` 未跟踪；`git rev-list --left-right --count main...origin/main` 输出 `0	214`；相对 `origin/main` 的 diff 显示 `human_gate_controller.py` 存在 `audit_report` 到 `audit_result` 口径变化，`safe_refactor_audit.py` 存在大范围实现差异；本文档已移除“只增加类型标注”的放行口径。

**Release / Handoff Gate (放行 / 接管闸门)**
- 当前判断：可收口
- 当前缺口：未做全仓测试、第三刀验收、主线收编候选验证或干净 `origin/main` worktree 收编复验；目标文件仍未跟踪。
- 接手后第一步：若继续推进 AR-1，请先确认下一任务是否为主线收编或候选提交；若是，必须另开任务并重新做收编边界验证。
- 接手入口：`docs/exec-plans/in-progress/ar-1-live-repo-infrastructure-repair-task-contract.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`、`docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`。
