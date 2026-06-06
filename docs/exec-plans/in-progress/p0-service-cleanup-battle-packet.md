# P0 Service Cleanup Battle Packet / P0 Service Cleanup 战时包

## 1. Task Contract（任务合同）

**Objective (目标)**  
将 `hermes_cli/profiles.py` 与 `hermes_cli/uninstall.py` 中的 service cleanup 双实现收敛为一条统一、可复用、语义一致的受控清理链，在不扩大副作用范围的前提下，消除 profile 删除与 uninstall 路径在 service cleanup 行为上的分叉。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 只处理与 service cleanup 双实现直接相关的代码路径；允许提炼统一 cleanup helper 或统一调用链；允许补最小必要测试；如 service cleanup 正确性依赖一处 wrapper 联动修正，仅允许最小必要修正。  
OUT: 不顺手收敛 wrapper 双实现；不修改 active profile 解析链；不修 uninstall 参数语义；不引入 Hook、自动拦截器、新框架；不改 `AGENTS.md` / `guardrails.md` / `runtime-risk-index.md` / `controlled-entry-index.md`。  
WATCHOUTS: 最大风险是以 cleanup 收敛为名扩大 wrapper 改动或新增删除路径；第二风险是统一后改变行为顺序导致隐性回归；第三风险是抽象过度，形成第三套 cleanup 逻辑。

**Inputs (输入)**  
`docs/exec-plans/tech-debt-tracker.md` 中的 `TDB-1`；`controlled-entry-index.md` 中 Profile / Uninstall 受控入口样板；已知问题包括 service cleanup 双实现、wrapper 双实现、uninstall 参数语义问题与 active profile 读取链轻量分叉。当前只处理第一项。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：代码改动、最小必要测试、简短改动报告。  
证据：两条上层路径复用同一 cleanup 核心语义；相关测试通过；未新增高危删除路径；未扩大 wrapper 改动范围；关键文件回读可证明未越界。

**Done (完成标准)**  
1. `profiles` 路径与 `uninstall` 路径的 service cleanup 不再维护两套独立核心逻辑。  
2. profile 删除与 uninstall 的关键 cleanup 行为不回归。  
3. 通过本战 P0 回归测试清单中的核心项。  
4. 未越界：未修改文档文件；未新增新的 `rmtree` / 删除路径；未新增新的 service cleanup 分叉 helper；如有 wrapper 改动，仅为直接耦合的最小必要修正，并在报告中明确说明；未触碰 active profile 解析链与 uninstall 参数语义。  
5. 改动与测试可审计。

---

## 2. P0 回归测试 CheckList

### A. 结构与危险改动审计
- 检查 diff 是否新增：`rmtree(`、`unlink(`、`remove(`、新的删除路径
- 检查是否新增新的 cleanup helper 分叉

### B. Profile 删除路径回归
- 回读 `hermes_cli/profiles.py`，确认 `delete_profile()` 已走统一 cleanup 入口
- 运行与 profiles / hermes_cli 相关的最小测试子集
- 代码级确认删除路径仍处理 active profile / gateway / service / wrapper / 目录顺序

### C. Uninstall 路径回归
- 回读 `hermes_cli/uninstall.py`，确认 `run_uninstall()` 已走统一 cleanup 入口
- 运行与 uninstall / hermes_cli 相关的最小测试子集
- 代码级确认 uninstall 仍处理 wrapper / shell rc / project_root / hermes_home 逻辑

### D. Service 目标识别回归
- 回读统一 helper，确认两条路径对目标 service 的判断一致
- 确认 service 不存在时的容错行为

### E. Wrapper 联动越界检查
- 搜索 diff 中 wrapper 相关改动
- 若存在 wrapper 改动，确认仅为最小必要联动
- 如出现 wrapper 识别规则重写或全面收敛，直接判定越界

---

## 3. 越界规则

### 允许
- 提炼统一 service cleanup helper 或统一调用链
- 补最小必要测试
- 若不改一处 wrapper 直接耦合逻辑就无法让 cleanup 正确成立，允许最小必要联动修正

### 禁止
- 顺手收敛 wrapper 双实现
- 修改 active profile 解析链
- 修 uninstall 参数语义
- 改动任意文档文件
- 新增高危删除路径或新的 cleanup 分叉 helper
- 大面积风格重排或扩大战线

### 越界裁定
如 diff 通过测试但出现轻微越界（例如多删一行不该删的 wrapper 逻辑），仍判定为**不通过**；要求回退越界改动后重提，不以“测试过了”作为越界免责理由。
