## Status Ledger / Progress Doc（状态台账 / 进度文档）

**Task Contract Snapshot (合同快照)**  
- 目标：将 Profile 删除路径与 uninstall 路径中的 wrapper 识别与删除双实现收敛为一套统一、可复用、边界清晰的受控逻辑，在不误伤当前活跃实例、非目标 profile 或用户命令入口的前提下，消除 wrapper 处理行为分叉。  
- 范围边界：只处理 wrapper 识别与删除双实现相关代码路径；允许提炼统一 wrapper helper 或统一调用链；允许最小必要测试；不改 active profile 解析链；不修 uninstall 参数语义；不扩展到 shell rc / PATH / install 体系重构；不改文档文件。  
- 完成标准：Profile 删除与 uninstall 路径复用统一 wrapper 识别/删除语义；未误伤当前活跃实例、非目标 profile 或用户命令入口；测试通过；未越界进入 uninstall 参数语义或 active profile 链。

**Current State (当前状态)**  
- 当前停点：玄麟已完成 TDB-2 代码改造并交卷；主控已完成 4 步复审：看 Diff -> 查调用链 -> 看测试 -> 读报告。  
- 已完成：P0 已结案并归档；TDB-2 风险推演、正式合同、测试清单、最终派工单与 TL;DR 已定稿；已增加 Dummy Profile 沙盒测试纪律；玄麟已完成 wrapper 识别/删除双实现收敛的首轮代码改造；首轮裁决结果为真赢。  
- 未完成 / 当前阻塞：本轮范围内无阻塞性未完成项；TDB-2 的结案归档与账本平账尚未执行。  
- 当前判断：可收口

**Evidence Logged (证据登记)**  
- 已有证据：`controlled-entry-index.md` 已存在 Profile / Uninstall 第二组样板；`tech-debt-tracker.md` 已将 TDB-2 列为未解决项；diff 证明 `profiles.py` 与 `uninstall.py` 已共享 wrapper 核心链；最小相关测试 6 项通过；未触碰 active profile 解析链、uninstall 参数语义、shell rc / PATH；Dummy Profile 沙盒测试纪律得到满足。  
- 证据对应结论：TDB-2 在合同边界内完成了 wrapper 双实现收敛；当前没有发现越界、误伤活跃实例或误碰用户 shell 入口的证据。  
- 证据缺口：结案报告与 tech-debt 账本平账尚未完成。

**Next Handoff (下一步 / 接管指令)**  
- 接手后第一步：将 TDB-2 首轮真赢结果整理为结案报告，并在 `tech-debt-tracker.md` 中将 TDB-2 标记为已解决。  
- 立即核查：归档时要保留关键 diff、调用链统一证据与 Dummy Profile 沙盒测试证据。  
- 若受阻先排查：若归档前发现隐藏的 shell/PATH 触碰或 wrapper 误伤证据，立即撤回“可收口”判定并重新开审。 
