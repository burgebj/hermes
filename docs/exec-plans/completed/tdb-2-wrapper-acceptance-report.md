# TDB-2 Wrapper 双实现收敛结案报告

## 任务名称
TDB-2：wrapper 删除 / 识别规则双实现收敛

## Task Contract（任务合同）

**Objective (目标)**  
将 Profile 删除路径与 uninstall 路径中的 wrapper 识别与删除双实现收敛为一套统一、可复用、边界清晰的受控逻辑，在不误伤当前活跃实例、非目标 profile 或用户命令入口的前提下，消除 wrapper 处理行为分叉。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理 wrapper 识别与删除双实现相关代码路径；允许提炼统一 wrapper helper 或统一调用链；允许最小必要测试；不改 active profile 解析链；不修 uninstall 参数语义；不扩展到 shell rc / PATH / install 体系重构；不改文档文件。  
OUT: 不顺手改 active profile 解析链；不顺手修 uninstall 参数语义；不扩展到 shell rc / PATH / install 体系重构；不改文档文件。  
WATCHOUTS: 最大风险是误删当前活跃 profile 的 wrapper、误删非目标 profile 的 wrapper、误删用户命令入口；第二风险是把 wrapper 收敛扩大成 install / shell 集成重构；第三风险是只统一删除动作，不统一识别规则，导致“统一错了”。

**Inputs (输入)**  
`docs/exec-plans/tech-debt-tracker.md` 中的 `TDB-2`；`controlled-entry-index.md` 中 Profile / Uninstall 第二组样板；P0 已完成的 service cleanup 收敛结果；已坐实的风险包括 wrapper 双实现、识别规则不一致、profile 删除与 uninstall 表现分叉。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：代码改动、最小必要测试、简短改动报告。  
证据：Profile 删除与 uninstall 路径复用统一 wrapper 识别/删除语义；未误伤当前活跃实例、非目标 profile 或用户命令入口；测试通过；未越界进入 uninstall 参数语义或 active profile 链。

**Done (完成标准)**  
统一 wrapper 识别/删除核心链成立；行为不回归；最小相关测试通过；未越界进入 shell rc / PATH / install 体系、active profile 解析链与 uninstall 参数语义；报告可审计。

---

## 最终 Status Ledger（状态台账）

**Task Contract Snapshot (合同快照)**  
- 目标：收敛 Profile / Uninstall 路径中的 wrapper 双实现，且不误伤当前活跃实例、非目标 profile 或用户命令入口。  
- 范围边界：只打 wrapper 识别/删除这一个点；不改 active profile 解析链；不改 uninstall 参数语义；不扩展到 shell rc / PATH / install 体系。  
- 完成标准：两条路径复用统一 wrapper 核心链；Dummy Profile 沙盒测试通过；无 shell/PATH 回归；无越界。

**Current State (当前状态)**  
- 当前停点：玄麟已交卷，主控已按 4 步复审法完成裁决。  
- 已完成：Diff 审计、调用链回读、测试审计、报告复核全部通过；判定为真赢。  
- 未完成 / 当前阻塞：无阻塞项；仅剩结案归档与账本平账。  
- 当前判断：可收口。

**Evidence Logged (证据登记)**  
- 已有证据：`profiles.py` 与 `uninstall.py` 共享 wrapper 识别/删除核心；6 项最小相关测试通过；未碰 shell rc / PATH / install 体系；Dummy Profile 沙盒纪律满足。  
- 证据对应结论：TDB-2 在合同边界内完成，未误伤活跃实例、非目标 profile 或用户命令入口。  
- 证据缺口：无。

**Next Handoff (下一步 / 接管指令)**  
- 接手后第一步：在 `tech-debt-tracker.md` 中将 TDB-2 标为已解决，并锁定下一战 TDB-3。  
- 立即核查：保留关键 diff、调用链统一与 Dummy Profile 测试证据。  
- 若受阻先排查：若后续发现 shell/PATH 隐性回归证据，立即撤回“可收口”并重审。

---

## 最终 Verification Chain（验证链）

**Verification Target (验证目标)**  
- 目标 1：证明 Profile 删除路径与 uninstall 路径已复用统一 wrapper 识别/删除核心链。  
- 目标 2：证明没有误伤当前活跃实例、非目标 profile 或用户命令入口。  
- 目标 3：证明没有越界到 active profile 解析链、uninstall 参数语义、shell rc / PATH / install 体系。  
- 目标 4：证明测试在 Dummy Profile 沙盒中完成，没有对当前真实 active profile 做测试操作。

**Verification Actions (验证动作)**  
- 动作 1：Diff 审计：检查是否新增高危删除路径、是否改动文档、是否触碰 active profile / uninstall 参数语义 / shell rc / PATH。  
- 动作 2：调用链回读：确认 `profiles.py` 与 `uninstall.py` 都走统一 wrapper helper 或统一调用链，而不是复制实现。  
- 动作 3：测试审计：确认测试覆盖 profile 删除路径、uninstall 路径、非目标 wrapper 保护；确认测试对象是 Dummy Profile，而不是当前真实 active profile。  
- 动作 4：报告复核：确认玄麟承认未处理哪些技术债，且如有 service 最小联动修正已明确说明原因与范围。  
- 动作 5：越界审计：若出现 wrapper 全面收敛、install / shell 集成改造、active profile 链调整、参数语义修复，直接判定不通过。

**Verification Result (验证结果)**  
- 目标 1：通过。  
- 目标 2：通过。  
- 目标 3：通过。  
- 目标 4：通过。

**Release / Handoff Gate (放行 / 接管闸门)**  
- 当前判断：通过 / 可收口。  
- 当前缺口：无。  
- 接手后第一步：执行结案归档与 tech-debt 平账，再开启下一战。  
- 接手入口：先看本报告，再看 `tech-debt-tracker.md` 中的后续优先级。

---

## shell / PATH 专项防爆复核结论

已专项复核 `hermes_cli/profiles.py`、`hermes_cli/uninstall.py` 与本轮测试改动，确认：

- 本轮 diff **没有新增** shell rc / PATH 处理逻辑
- 本轮 diff **没有修改** `find_shell_configs()` / `remove_path_from_shell_configs()` 等 shell 清理函数的行为
- 本轮改动集中在 wrapper 识别/删除核心链，不涉及 `.bashrc`、`.zshrc`、`.profile`、`PATH` 注入或移除路径
- 测试使用 Dummy Profile / 临时 home 环境，没有对当前真实 active profile 或真实 shell 环境做销毁演练

**安全担保：本轮改动未发现对系统 shell / PATH 链路的隐性回归或副作用证据。**

---

## 三条铁证（永久保留）

### 铁证 1：共享 wrapper 核心链成立
`profiles.py` 的 wrapper 删除逻辑不再单独维护一套核心实现，而是复用共享的 `_remove_managed_wrapper_script(...)` 语义。

### 铁证 2：uninstall 路径同样接入共享链
`uninstall.py` 改为复用来自 `profiles.py` 的共享 wrapper 核心链，而不是继续维持第二套独立删除语义。

### 铁证 3：Dummy Profile 沙盒测试与非目标保护测试通过
最小相关测试 6 项通过，其中明确覆盖：
- 只删除 Dummy Profile 对应 wrapper
- 非目标 wrapper 不受影响
- uninstall 路径 wrapper 清理命中当前 install，而不误伤其他 install

---

## 结论

**TDB-2：wrapper 删除 / 识别规则双实现收敛，已完成并正式结案。**  
**Gate：通过 / 可收口。**
