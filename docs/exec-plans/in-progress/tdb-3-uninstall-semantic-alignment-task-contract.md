## Task Contract（任务合同）

**Objective (目标)**  
在不放松 `uninstall` 的 TTY / 人工确认安全边界的前提下，使 `hermes uninstall` 的 CLI 参数语义与真实执行行为对齐，并通过 `safe-refactor-loop` 首航流程完成首轮自动接管。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理 `hermes_cli/main.py`、`hermes_cli/uninstall.py` 与直接相关最小测试；允许对 `--full / --yes` 的参数语义、帮助文本、参数传递链与 `run_uninstall(...)` 控制流做最小必要对齐；允许使用隔离 worktree、M3 审计、M5-v2 自愈审计、M6 人工闸门。  
OUT: 不触碰 `hermes_cli/profiles.py`；不改 shell / PATH / wrapper 链；不把 `--yes` 扩展为非 TTY 绕过开关；不实现 Hook、自动 merge、自动 deploy、自动放行；不顺手处理其他技术债。  
WATCHOUTS: 最大风险是把“参数对齐”做成 TTY 降级；第二风险是只改 help 文案不改真实控制流，制造假对齐；第三风险是被当前主仓脏工作树污染，误把旧改动混进 TDB-3；第四风险是让 M5/M6 越权，未到 `APPROVE_CANDIDATE` 就请求人工签字。

**Inputs (输入)**  
`/Users/beiming/.hermes/hermes-agent/docs/exec-plans/tech-debt-tracker.md` 中的 `TDB-3`；`/Users/beiming/.hermes/hermes-agent/docs/exec-plans/in-progress/m3-audit-rules-checklist.md`；`/Users/beiming/.hermes/hermes-agent/docs/exec-plans/in-progress/m5-automated-judgment-criteria.md`；AR-1 战时文档；当前主仓存在大量无关未提交改动，因此本轮施工隔离在 `/tmp/hermes-tdb3-autopilot`；玄麟执行留痕目录为 `~/.hermes/runtime/agents/xuanlin/`。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：TDB-3 代码改动、最小测试、玄麟执行审计 JSON、M5-v2 裁决结果、必要时的 M6 裁决请示书。  
证据：Diff 只触碰允许文件；M3 审计结果满足红线要求；调用链能证明参数语义真实接入控制流；指定 pytest 通过；玄麟留痕文件可回读；若进入 M6，则《裁决请示书》明确显示 `APPROVE_CANDIDATE` 后才停机等签字。

**Done (完成标准)**  
只有当隔离 worktree 中的 TDB-3 改动通过 M3 与 M5-v2 审计、输出 `APPROVE_CANDIDATE`、并随后进入 M6 物理停机等待北冥显式 `Y / Confirm` 时，本轮才算到达请示节点；在此之前一律视为未完成。