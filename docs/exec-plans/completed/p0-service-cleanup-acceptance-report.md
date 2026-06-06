# P0 Service Cleanup Acceptance Report / P0 service cleanup 双实现收敛结案报告

## 1. 任务合同（Task Contract）

**Objective (目标)**  
将 `hermes_cli/profiles.py` 与 `hermes_cli/uninstall.py` 中的 service cleanup 双实现收敛为一条统一、可复用、语义一致的受控清理链，在不扩大副作用范围的前提下，消除 profile 删除与 uninstall 路径在 service cleanup 行为上的分叉。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理与 service cleanup 双实现直接相关的代码路径；允许提炼统一 cleanup helper 或统一调用链；允许最小必要测试补充；如服务于 cleanup 正确性，仅允许最小必要 wrapper 联动修正。  
OUT: 不顺手收敛 wrapper 双实现；不修改 active profile 解析链；不修 uninstall 参数语义；不引入 Hook、自动拦截器或新框架；不改 `AGENTS.md` / `guardrails.md` / `runtime-risk-index.md` / `controlled-entry-index.md`。  
WATCHOUTS: 防止以“统一 cleanup”为名扩大 wrapper 改动范围、改变 profile 删除或 uninstall 的行为顺序、引入新的高危删除路径或新增 cleanup 分叉。

**Inputs (输入)**  
`docs/exec-plans/tech-debt-tracker.md` 中的 `TDB-1`；`controlled-entry-index.md` 中 Profile / Uninstall 第二组样板；已识别高风险链路包括 `hermes_cli/profiles.py::delete_profile()`、`hermes_cli/uninstall.py::run_uninstall()` 及各自的 service cleanup 辅助实现。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：代码改动、最小必要测试、改动报告。  
证据：两条上层路径复用同一套 service cleanup 语义；相关测试通过；未新增计划外高危删除路径；未扩大 wrapper 改动范围；关键文件回读可证明没有越界。

**Done (完成标准)**  
1. `profiles` 与 `uninstall` 路径共享同一套 service cleanup 核心语义。  
2. profile 删除与 uninstall 路径行为未回归。  
3. 最小相关测试通过。  
4. 未越界：未改文档、未新增 `rmtree` / 删除路径、未顺手收敛 wrapper 双实现、未改 active profile 解析链、未改 uninstall 参数语义。  
5. 改动可审计。

---

## 2. 状态台账（Status Ledger）最终状态

**Task Contract Snapshot (合同快照)**  
- 目标：统一 `profiles.py` 与 `uninstall.py` 的 service cleanup 核心语义。  
- 范围边界：仅处理 service cleanup 双实现相关路径；仅允许最小必要测试与极小 wrapper 联动；不碰 wrapper 双实现本身、active profile 解析链与 uninstall 参数语义。  
- 完成标准：共享核心链成立、测试通过、无新增高危删除路径、无越界。

**Current State (当前状态)**  
- 当前停点：P0 首轮代码战已完成主控复审。  
- 已完成：玄麟提交统一 cleanup 改动；主控完成 diff 审计、调用链回读、测试审计、报告复读。  
- 未完成 / 当前阻塞：当前阶段无阻塞；若继续推进，为下一战 `TDB-2` 新开合同，不回卷本轮。  
- 当前判断：通过 / 可收口。

**Evidence Logged (证据登记)**  
- 已有证据：`profiles.py` 改为委托 `hermes_cli.uninstall.cleanup_gateway_service(profile_dir)`；`uninstall_gateway_service()` 统一委托 `cleanup_gateway_service(get_hermes_home())`；最小相关测试 `4 passed in 0.51s`；未发现新增 `rmtree`；未改文档、active profile 解析链与 uninstall 参数语义。  
- 证据对应结论：service cleanup 双实现已收敛；本轮为边界内真赢。  
- 证据缺口：无当前阶段缺口。

**Next Handoff (下一步 / 接管指令)**  
- 接手后第一步：把 `TDB-1` 从技术债账本中标记为已解决。  
- 立即核查：下一战按既定顺序推进 `TDB-2：wrapper 删除 / 识别规则双实现收敛`。  
- 若受阻先排查：若发现 service 名称解析平台差异，单开新合同处理，不回卷本轮 P0。

---

## 3. 验证链（Verification Chain）最终状态

**Verification Target (验证目标)**  
- 目标 1：证明 `profiles` 与 `uninstall` 路径已共享同一套 service cleanup 核心语义。  
- 目标 2：证明未新增高危删除路径，也未扩大 cleanup 副作用范围。  
- 目标 3：证明未越界到 wrapper 双实现、active profile 解析链或 uninstall 参数语义。  
- 目标 4：证明最小相关测试真实覆盖了 profile 删除路径与 uninstall 路径的共享 cleanup 行为。

**Verification Actions (验证动作)**  
- 动作 1：Diff 审计——检查是否新增 `rmtree` / 删除路径 / 新 cleanup helper 分叉。  
- 动作 2：调用链回读——确认 `delete_profile()` 与 `run_uninstall()` 都委托到同一共享 helper。  
- 动作 3：越界审计——检查是否改了 wrapper 大范围逻辑、active profile 解析链、uninstall 参数语义、文档文件。  
- 动作 4：测试审计——运行最小相关测试并核对结果。

**Verification Result (验证结果)**  
- 目标 1：通过。  
- 目标 2：通过。  
- 目标 3：通过。  
- 目标 4：通过。

**Release / Handoff Gate (放行 / 接管闸门)**  
- 当前判断：通过 / 可收口。  
- 当前缺口：无。  
- 接手后第一步：进入 `TDB-2` 新合同，不回卷 P0。  
- 接手入口：优先查看 `tech-debt-tracker.md` 中 `TDB-2`，再查看 `controlled-entry-index.md` 中 Profile / Uninstall 样板。

---

## 4. 关键物理证据

### 4.1 关键 diff 证据
- `profiles.py` 删除了本地重复的 service cleanup 逻辑，改为统一委托共享 helper。  
- `uninstall.py` 新增 `cleanup_gateway_service(service_home: Path)` 作为共享 service cleanup 核心。  
- `uninstall_gateway_service()` 改为委托共享 helper。

### 4.2 关键测试证据
执行命令：

```bash
uv run --extra dev python -m pytest \
  tests/hermes_cli/test_profiles.py::TestDeleteProfile::test_cleanup_wrapper_uses_shared_service_cleanup \
  tests/hermes_cli/test_profiles.py::TestDeleteProfile::test_removes_directory \
  tests/hermes_cli/test_uninstall.py -q
```

结果：

```text
4 passed in 0.51s
```

---

## 5. 最终结论

**P0：service cleanup 双实现收敛，结论为【真赢】。**  
**本轮文档与代码边界均保持干净，无越界。**  
**TDB-1 已具备从技术债账本中正式划掉的条件。**
