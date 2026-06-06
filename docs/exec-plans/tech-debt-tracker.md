# Tech Debt Tracker / 代码层收敛任务候选清单

> 定位：这里只记录已经被摸排坐实、但当前回合不直接重构的代码层收敛候选任务。  
> 它不是风险索引，也不是执行现场。  
> 这里的职责是把“后续应该单开任务治理的技术债”按优先级立账。

## 已解决

### TDB-1：service cleanup 双实现收敛 ✅
- **状态**：已解决（见 `docs/exec-plans/completed/p0-service-cleanup-acceptance-report.md`）
- **解决结果**：
  - `profiles` 与 `uninstall` 路径已共享同一套 service cleanup 核心语义
  - 相关最小测试通过
  - 未新增高危删除路径，未越界到 wrapper 双实现、active profile 解析链或 uninstall 参数语义

### TDB-2：wrapper 删除 / 识别规则双实现收敛 ✅
- **状态**：已解决（见 `docs/exec-plans/completed/tdb-2-wrapper-acceptance-report.md`）
- **解决结果**：
  - `profiles` 与 `uninstall` 路径已复用统一 wrapper 识别 / 删除核心链
  - Dummy Profile 沙盒测试通过，非目标 wrapper 与当前活跃实例未受误伤
  - 未触碰 shell rc / PATH / install 体系，未越界到 active profile 解析链或 uninstall 参数语义

## 架构级升维战役

### AR-1：`safe-refactor-loop` 自动化防爆重构 Skill / 调度器
- **状态**：最高优先级活跃战役（第一刀、第二刀已落地；第三刀为当前验收子阶段）
- **自动接管入口**：`docs/exec-plans/in-progress/ar-1-engineering-wiring-task-contract.md`
- **目标**：将当前成功的人类主控流程固化为可执行状态机。
- **当前重点**：AR-1 live repo 基础设施最小运行健康已通过；`safe_refactor_audit.py` 与 `human_gate_controller.py` 在当前 live repo 中已通过编译、导入、残留占位扫描与定向 pytest。此结论只证明 live repo 最小运行健康，不证明主线收编；当前 `main` 落后 `origin/main` 214 个提交，两个目标文件在当前工作区仍为未跟踪文件，且相对 `origin/main` 不是纯类型标注小修。第三刀归档同步器仍待北冥验收后再用于真实 M6 归档；若要收编这些目标文件，必须另开主线收编或候选提交任务。
- **归档目标路径**：`docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md`
- **参考历史验收**：`docs/exec-plans/completed/ar-1-engineering-wiring-acceptance-report.md` 仅作为归档目标路径与历史输入，不得直接当作第三刀当前完成证明。
- **最近完成的法典升级子任务**：`docs/agents/beiming-report-template-v2.md` 的路径表达与输出字段规范已完成一轮小范围精修，见 `docs/exec-plans/completed/beiming-report-template-path-format-refinement-acceptance-report.md`；本轮已继续推进最终命名表统一收口，统一正式称呼到“北冥法典 / 北冥宪章 / 北冥汇报模板 / 北冥裁决请示书”。
### TDB-3：`uninstall` CLI 参数语义与实现对齐
- **状态**：已批准并隔离提交（分支 `tdb-3-safe-refactor-flight`，提交 `a520f70e`；见 `docs/exec-plans/in-progress/tdb-3-uninstall-semantic-alignment-task-contract.md`）
- **现状**：CLI 暴露了 `--full / --yes` 等参数，但实现仍可能强依赖交互确认。
- **风险**：
  - 参数语义与实际行为不一致
  - Agent 或用户误以为“无交互可执行”
  - 自动化脚本行为不可预测
- **建议治理方向**：
  - 统一 CLI 宣称行为与真实执行行为
  - 明确自动化安全边界

### TDB-4：`rename_profile()` 的 service 清理条件不完整
- **现状**：只在 gateway 正在运行时才清理旧 service，可能导致残留。
- **风险**：
  - 旧 service 留存
  - profile rename 后环境状态不干净
  - 后续排障困难
- **建议治理方向**：
  - 将 rename 时的 service / wrapper 清理规则显式化并统一

## P2

### TDB-5：active profile 读取链轻量分叉
- **现状**：
  - `hermes_cli/main.py::_apply_profile_override()`
  - `hermes_cli/profiles.py::get_active_profile()` / `resolve_profile_env()`
  启动期与其他路径存在轻量分叉，没有完全复用一条主链。
- **风险**：
  - profile 解析逻辑不完全一致
  - 边缘情况下 `HERMES_HOME` 作用域漂移
  - 后续继续复制逻辑的概率变高
- **建议治理方向**：
  - 统一 active profile 与 `HERMES_HOME` 解析源
  - 减少启动期分叉
