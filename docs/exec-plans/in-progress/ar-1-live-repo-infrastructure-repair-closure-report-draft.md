# AR-1 live repo 基础设施修复结案报告草案

Session ID：20260424_083641_0722cc

## 结论

本轮只确认当前 live repo 的最小运行健康已通过：`hermes_cli/safe_refactor_audit.py` 与 `hermes_cli/human_gate_controller.py` 在 `/Users/beiming/.hermes/hermes-agent` 中可编译、可导入、残留占位扫描为空，且两份直接相关定向 pytest 通过。

这不是主线收编证明。当前 `main` 落后 `origin/main` 214 个提交，且两个目标文件在当前工作区显示为未跟踪文件。

这也不是相对 `origin/main` 的纯类型标注小修。相对 `origin/main`，`human_gate_controller.py` 包含 `audit_report` 到 `audit_result` 的接口口径变化；`safe_refactor_audit.py` 存在大范围实现差异。

## 已保留证据

- `python -m py_compile hermes_cli/safe_refactor_audit.py hermes_cli/human_gate_controller.py`：通过。
- `hermes_cli.safe_refactor_audit` 与 `hermes_cli.human_gate_controller`：可直接导入。
- 残留占位扫描：`residuals=[]`。
- `python -m pytest -o addopts='' tests/hermes_cli/test_safe_refactor_audit.py tests/hermes_cli/test_human_gate_controller.py -q`：`8 passed in 0.03s`。
- `git rev-list --left-right --count main...origin/main`：`0	214`。
- `git status --short`：两个目标文件仍为 `??` 未跟踪。
- 相对 `origin/main` 的文件对比：存在非纯类型标注差异。

## 明确未做事项

- 未改代码。
- 未改 M3 / M5 / M6 代码语义。
- 未做第三刀验收。
- 未做全仓测试承诺。
- 未做主线收编候选验证。
- 未在干净 `origin/main` worktree 做收编复验。
- 未 `git add`。
- 未 `commit`。
- 未 `push`。
- 未 `merge`。

## 后续唯一建议

若北冥要把 `hermes_cli/safe_refactor_audit.py` 与 `hermes_cli/human_gate_controller.py` 收编进主线，必须另开“主线收编 / 候选提交任务”，以 `origin/main` 为基线重新做文件范围审查、代码与文档一致性审查、测试复验、Git 收编边界审查，并单独裁决 `audit_report -> audit_result` 接口口径变化与 `safe_refactor_audit.py` 大范围实现差异是否允许进入候选提交。
