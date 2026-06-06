**Task Contract Snapshot (合同快照)**
- 目标：确认并收口当前 live repo 中两个基础设施文件的最小运行健康，同时修正文档口径，防止误写成主线收编证明或相对 `origin/main` 的纯类型标注小修。
- 范围边界：只修正文档口径并保留最小运行健康证据；不改代码，不改 M3 / M5 / M6 代码语义，不做第三刀验收，不 push，不 merge，不 commit，不 git add，不做主线收编。
- 完成标准：两个目标模块在当前 live repo 中可编译、可导入、残留扫描为空、定向测试通过；文档明确目标文件仍未跟踪、本轮不是主线收编证明、也不是相对 `origin/main` 的纯类型标注小修。

**Current State (当前状态)**
- 当前停点：本轮 live repo 最小运行健康已通过，正在做文档口径收口复核。
- 已完成：已确认当前仓库根为 `/Users/beiming/.hermes/hermes-agent`；已在当前 live repo 直接执行编译、导入、占位扫描与定向 pytest；已确认当前 `main` 落后 `origin/main` 214 个提交；已确认 `hermes_cli/safe_refactor_audit.py` 与 `hermes_cli/human_gate_controller.py` 在当前工作区仍为未跟踪文件；已确认相对 `origin/main` 存在非纯类型标注差异。
- 未完成 / 当前阻塞：未执行 push、merge、commit、git add 或主线收编；未运行无关测试战线；未做第三刀验收；未处理仓库中既有其他脏文件。
- 当前判断：可收口（仅限 live repo 最小运行健康与文档口径纠偏）

**Evidence Logged (证据登记)**
- 已有证据：`python -m py_compile hermes_cli/safe_refactor_audit.py hermes_cli/human_gate_controller.py` 退出码 0；两个模块直接导入退出码 0；残留占位扫描显示两个目标文件 `residuals=[]`；`python -m pytest -o addopts='' tests/hermes_cli/test_safe_refactor_audit.py tests/hermes_cli/test_human_gate_controller.py -q` 输出 `8 passed in 0.03s`；`git rev-list --left-right --count main...origin/main` 输出 `0	214`；`git status --short` 显示两个目标文件为 `??`；相对 `origin/main` 的 diff 显示 `human_gate_controller.py` 有 `audit_report` 到 `audit_result` 口径变化，`safe_refactor_audit.py` 有大范围实现差异。
- 证据对应结论：当前 live repo 本地主控基础设施达到最小可运行状态；该结论不等于主线收编通过，也不等于相对 `origin/main` 的纯类型标注小修。
- 证据缺口：未做全仓测试、第三刀验收、主线收编候选验证或干净 `origin/main` worktree 收编复验；目标文件仍未进入当前工作区跟踪状态。

**Next Handoff (下一步 / 接管指令)**
- 接手后第一步：先查看 `docs/exec-plans/in-progress/ar-1-live-repo-infrastructure-repair-task-contract.md`，确认本轮边界只是 live repo 最小运行健康与文档口径纠偏。
- 立即核查：重跑 `git status --short`、`git rev-list --left-right --count main...origin/main`、`python -m py_compile hermes_cli/safe_refactor_audit.py hermes_cli/human_gate_controller.py` 与两份定向 pytest。
- 若受阻先排查：先检查是否误用了 pytest 默认 `addopts` 中的 `-n`；当前环境未装 pytest-xdist，定向测试需使用 `python -m pytest -o addopts='' ... -q`；若要收编，必须另开主线收编或候选提交任务。
