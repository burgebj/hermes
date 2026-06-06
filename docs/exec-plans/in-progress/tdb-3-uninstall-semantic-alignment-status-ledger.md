**Task Contract Snapshot (合同快照)**
- 目标：在不放松 `uninstall` 的 TTY / 人工确认安全边界的前提下，使 `hermes uninstall` 的 CLI 参数语义与真实执行行为对齐，并通过 `safe-refactor-loop` 首航流程完成首轮自动接管。
- 范围边界：只处理 `hermes_cli/main.py`、`hermes_cli/uninstall.py` 与直接相关最小测试；使用隔离 worktree、M3、M5-v2、M6；禁止触碰 `hermes_cli/profiles.py`、shell / PATH / wrapper 链与任何非 TDB-3 业务代码。
- 完成标准：隔离 worktree 中的 TDB-3 改动通过 M3 与 M5-v2 审计并给出 `APPROVE_CANDIDATE`；随后进入 M6 物理停机等待北冥显式 `Y / Confirm`；未到该节点前一律不算完成。

**Current State (当前状态)**
- 当前停点：北冥已在 M6 给出 `Y`；主控已在隔离分支 `tdb-3-safe-refactor-flight` 完成最终复验与提交，当前停在“待后续择机 cherry-pick / 集成 main”的归档态。
- 已完成：确认当前中央账本位于 `/Users/beiming/.hermes/hermes-agent/docs/exec-plans/`；确认 `TDB-3` 已从挂起切换为自动接管并完成首航；确认 `m3-audit-rules-checklist.md` 已把文件范围、TTY 降级、shell / PATH、常量绕过、参数别名漂移写成硬规则；确认 M3/M5/M6 代码与最小测试在主仓可用；已创建隔离 worktree；玄麟已完成两轮施工并写入 JSON 留痕；第二轮真实 diff 已收敛到 `hermes_cli/main.py`、`hermes_cli/uninstall.py`、`tests/hermes_cli/test_uninstall.py`；M3 裁决 `APPROVE`，M5-v2 裁决 `APPROVE_CANDIDATE`，最小 pytest 结果 `3 passed in 0.04s`；最终已在隔离分支提交 `a520f70e`。
- 未完成 / 当前阻塞：成果尚未并入主仓 `main`；主仓当前工作树较脏，若要集成，需另开一次安全 cherry-pick / 复审动作。
- 当前判断：可收口

**Evidence Logged (证据登记)**
- 已有证据：`tech-debt-tracker.md` 明确 TDB-3 的现状是参数语义与实现不一致；`main.py` 显示存在 `--full / --yes` 参数声明且 `cmd_uninstall()` 保留 `_require_tty("uninstall")`；`uninstall.py` 当前仍使用纯交互式选项输入而未消费 `args.full / args.yes`；`/tmp/hermes-tdb3-autopilot` 已从 `422f2866e60daa617688043fd9758c6380711d43` 创建；M3/M5/M6 相关测试已在主仓用 `python -m pytest -o addopts='' ...` 验证 `18 passed`。
- 证据对应结论：TDB-3 缺口真实存在；现有自动监理底座已具备首航条件；为避免脏工作树污染，必须在隔离 worktree 中施工与审计。
- 证据缺口：缺少玄麟首轮 diff、玄麟执行留痕 JSON、M5-v2 对 TDB-3 候选变更的结构化裁决结果。

**Next Handoff (下一步 / 接管指令)**
- 接手后第一步：在 `/tmp/hermes-tdb3-autopilot` 向玄麟下发只允许修改 `hermes_cli/main.py`、`hermes_cli/uninstall.py`、直接相关最小测试的施工单，并要求优先保持 `_require_tty("uninstall")` 不变。
- 立即核查：提交前先看 `git diff --name-only` 是否越界，再跑 M3、指定 pytest 与 M5-v2 自愈审计。
- 若受阻先排查：先区分是参数语义设计问题、测试环境问题（如 `pytest -n` 配置）、还是越界问题；任何 TTY 放松迹象直接打回，不进入 M6。