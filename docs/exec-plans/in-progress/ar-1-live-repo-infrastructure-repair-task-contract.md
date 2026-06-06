## Task Contract（任务合同）

**Objective (目标)**  
确认并收口当前 live repo 本地工作区中 `safe_refactor_audit.py` 与 `human_gate_controller.py` 的最小运行健康，同时修正文档口径，防止把 live repo 健康误写成主线收编证明或相对 `origin/main` 的纯类型标注小修。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只回读并修正本轮现场文档口径；保留已取得的编译、导入、残留扫描与定向 pytest 证据；明确当前目标文件在 live repo 中仍是未跟踪文件。  
OUT: 不改代码；不改 M3 / M5 / M6 代码语义；不做第三刀验收；不运行或承诺全仓验收；不 push；不 merge；不 commit；不 git add；不把本轮扩大成主线收编任务或候选提交任务。  
WATCHOUTS: 当前分支 `main` 落后 `origin/main` 214 个提交，且 `hermes_cli/safe_refactor_audit.py` 与 `hermes_cli/human_gate_controller.py` 在当前工作区显示为未跟踪文件；相对 `origin/main`，`human_gate_controller.py` 包含 `audit_report` 到 `audit_result` 的接口口径变化，`safe_refactor_audit.py` 存在大范围实现差异，因此不得描述为“只增加类型标注”。本轮只能证明当前 live repo 最小运行健康，不能证明主线已收编、可合并或相对 `origin/main` 是纯类型标注小修。

**Inputs (输入)**  
- `hermes_cli/safe_refactor_audit.py`  
- `hermes_cli/human_gate_controller.py`  
- `tests/hermes_cli/test_safe_refactor_audit.py`  
- `tests/hermes_cli/test_human_gate_controller.py`  
- `docs/exec-plans/tech-debt-tracker.md`  
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-status-ledger.md`  
- `docs/exec-plans/in-progress/architecture-safe-refactor-loop-verification-chain.md`  
- `~/.hermes/skills/safe-refactor-loop/SKILL.md`

**Deliverables / Evidence (交付物 / 证据)**  
交付物：修正后的本轮任务合同、状态台账、验证链、tech-debt tracker 口径，以及一份结案报告草案。  
证据：`python -m py_compile` 成功；两个模块可被 Python 直接导入；目标文件中无 `***`、`PLACEHOLDER`、`TODO`、`NotImplemented`、`pass  #` 等残留占位；`tests/hermes_cli/test_safe_refactor_audit.py` 与 `tests/hermes_cli/test_human_gate_controller.py` 定向 pytest 通过；`git status --short` 显示两个目标文件仍为 `??` 未跟踪；`git rev-list --left-right --count main...origin/main` 输出 `0\t214`；相对 `origin/main` 的 diff 显示上述两类非纯类型标注差异。

**Done (完成标准)**  
以下条件必须同时成立：两个目标模块在当前 live repo 中可编译、可导入；残留占位扫描为空；两份直接相关测试通过；文档已明确本轮不是主线收编证明、不是相对 `origin/main` 的纯类型标注小修、目标文件仍处于未跟踪状态；本轮不改代码、不改变 M3 / M5 / M6 代码语义、不做第三刀验收、不 push、不 merge、不 commit、不 git add。
