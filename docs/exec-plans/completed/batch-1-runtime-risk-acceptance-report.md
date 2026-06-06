# Batch 1 Runtime Risk Acceptance Report / 批次 1 任务 2 结案报告

## 任务名称
批次 1 任务 2：防御工事深化——运行时高风险锚点梳理

## 结案结论
**【通过 / 可收口】**

本次任务已完成以下闭环：
- 已梳理并分级运行时高风险物理锚点
- 已建立 `docs/agents/runtime-risk-index.md`
- 已对 `docs/agents/guardrails.md` 完成最小补丁接线
- 已验证 `AGENTS.md -> guardrails.md -> runtime-risk-index.md` 导航链路顺畅
- 已通过任务专属 Verification Chain 与最终 Release Gate 审校

---

## Task Contract（任务合同）

**Objective (目标)**  
梳理仓库中所有一旦被 AI 误操作就可能导致系统崩盘、数据丢失、配置污染、权限越界或不可逆副作用的高风险操作入口，并建立一套可回查、可导航、可触发验证链的防御索引。

**Scope / Watchouts (范围 / 警戒线)**  
IN: 系统性盘点仓库中的高风险物理落点，包括但不限于危险文件删除/覆盖入口、核心配置写入点、持久化状态写入点、敏感环境变量消费点、外部系统/平台 API 调用点、跨环境执行入口、可能破坏 prompt caching 或全局状态的关键调用点；将这些高风险锚点按类型整理进 `docs/agents/guardrails.md` 或其直接配套索引中；明确以后 Agent 触碰这些点之前必须先回查 Verification Chain。  
OUT: 不在本轮直接修改危险实现逻辑本身；不直接引入 Hook、自动拦截器、运行时 kill-switch 或批次 1 之后的自动防御机制；不把整个仓库做成安全审计报告大全；不为了“看起来完整”把所有普通写文件操作都膨胀成高风险入口。  
WATCHOUTS: 最大风险是“为了防御而防御”，列出一堆抽象禁令，却找不到真实代码落点；第二风险是把普通改动点和高风险入口混为一谈，导致 guardrails 失去警报价值；第三风险是只写“禁止”不写“怎么回查验证链”，结果后续 Agent 仍然可能直接误碰；第四风险是误把调查任务做成代码改造任务，导致 scope 漂移；第五风险是把高风险索引写成长篇百科，违背渐进式披露原则。

**Inputs (输入)**  
当前已落地的 `AGENTS.md` 与 `docs/agents/guardrails.md`；批次 0 三大骨架与 `hermes-harness-skill-change-loop` 的闭环纪律；当前仓库中的高风险线索包括但不限于路径写入规则（`get_hermes_home()` / `display_hermes_home()`）、全局状态点（如 `_last_resolved_tool_names`）、工具与 schema 注册链、gateway / CLI / cron / batch_runner / ACP 等运行入口、用户配置与环境文件（`~/.hermes/config.yaml`、`~/.hermes/.env`）及其消费点；本轮目标是建立“高风险锚点防御索引”，不是直接修代码。

**Deliverables / Evidence (交付物 / 证据)**  
交付物：一份高风险操作入口清单；按风险类型分组的防御索引；更新后的 `docs/agents/guardrails.md`（或其直接引用的最小配套索引文档），明确哪些锚点触发“先回查 Verification Chain”；必要时补一个专门的二级文档入口，例如 `docs/agents/runtime-risk-index.md`，但只有在内容确实无法保持 guardrails 简洁时才允许创建。  
证据：已通过搜索/回读定位到真实代码物理落点；每个高风险项都有路径、风险类型、误操作后果、触碰前应做的验证回查说明；更新后的 guardrails 能把后续 Agent 明确导向“先查哪份合同/台账/验证链，再碰哪个入口”；不存在大面积空泛禁令、无路径风险项或计划外目录膨胀。

**Done (完成标准)**  
仓库中的高风险操作入口已被分类型梳理并能回溯到真实文件或调用点；`guardrails.md` 已完成防御索引化增强，且仍保持“规则入口”而不是百科；后续 Agent 读完 `AGENTS.md` 和 `guardrails.md` 后，能够知道哪些点是高风险锚点、为什么危险、触碰前必须回查哪类 Verification Chain；本轮没有越界成代码改造、Hook 体系或全面安全重构；所有新增文档或索引路径都可回读、可验证、无计划外空壳结构。

---

## Status Ledger / Progress Doc（状态台账 / 进度文档）

**Task Contract Snapshot (合同快照)**  
- 目标：梳理仓库中所有一旦被 AI 误操作就可能导致系统崩盘、数据丢失、配置污染、权限越界或不可逆副作用的高风险操作入口，并建立一套可回查、可导航、可触发验证链的防御索引。  
- 范围边界：本轮只做高风险锚点的物理梳理、防御索引设计与文档入口规划；不直接修改危险实现逻辑本身；不引入 Hook、自动拦截器、运行时 kill-switch；不把普通写文件操作膨胀成高风险入口；不把任务扩成全仓库安全重构。  
- 完成标准：高风险操作入口已按类型梳理并能回溯到真实文件或调用点；`guardrails.md` 的增强方案与是否拆出 `runtime-risk-index.md` 已定稿；后续 Agent 能明确知道哪些点是高风险锚点、为什么危险、触碰前必须回查哪类 Verification Chain；新增文档路径可回读、可验证、无计划外空壳结构。

**Current State (当前状态)**  
- 当前停点：任务已完成物理索引落盘、规则接线、导航实测与最终 Gate 审校，进入结案归档。  
- 已完成：第一轮高风险锚点物理扫描；T0 / 首批 T1 分级裁定；`docs/agents/runtime-risk-index.md` 建立；`docs/agents/guardrails.md` 最小补丁接线；导航链路实测；任务专属 Verification Chain 放行结论闭合。  
- 未完成 / 当前阻塞：无。  
- 当前判断：可收口

**Evidence Logged (证据登记)**  
- 已有证据：`docs/agents/runtime-risk-index.md` 已落盘并回读；`docs/agents/guardrails.md` 已完成接线并回读；任务专属 Verification Chain 已回写为“可收口”；未新增计划外目录或空壳结构；`AGENTS.md -> guardrails.md -> runtime-risk-index.md` 导航链路已实测顺畅。  
- 证据对应结论：本轮防御索引不是抽象禁令，而是建立在真实代码物理入口上的可回查防线；规则入口与风险索引分层成立；后续 Agent 触碰高风险锚点前已存在明确停手与回查门槛。  
- 证据缺口：无。

**Next Handoff (下一步 / 接管指令)**  
- 接手后第一步：若进入下一批任务，应在不破坏“guardrails 入口化、runtime-risk-index 承接细节”结构的前提下，继续推进高风险写入路径的受控修改入口梳理。  
- 立即核查：先确认新任务是否会触碰本轮定义的 T0 / T1 高风险锚点；若会，必须先建立新的 Verification Chain。  
- 若受阻先排查：如果后续文档开始膨胀成百科，立即收回到“规则入口 + 风险索引”双层结构。

---

## Verification Chain（默认验证链）

**Verification Target (验证目标)**  
- 对应合同项：直接对应本次 Task Contract 的交付物 / 证据与完成标准。  
- 目标 1：证明高风险锚点索引中的每一项都能回溯到真实文件路径或调用点，而不是抽象禁令。  
- 目标 2：证明更新后的 `docs/agents/guardrails.md` 仍然是规则入口，不会被写成运行时风险百科；若风险项过多，则通过 `docs/agents/runtime-risk-index.md` 承接细节。  
- 目标 3：证明后续 Agent 触碰 T0 级禁区或其他高风险锚点前，必须先执行最少必要的拦截与验证动作，而不是直接调用工具或改文件。  
- 目标 4：证明新增的风险索引与规则文档可回读、可导航、可接管，不会新增计划外目录或空壳结构。

**Verification Actions (验证动作)**  
- 动作 1：在起草风险索引前，使用 file / search 工具再次回读并核对每个高风险锚点的真实物理落点，至少确认路径、危险动作、误操作后果三者一致，防止把抽象风险写成没有代码落点的空警告。  
- 动作 2：在更新 `guardrails.md` 与创建 `runtime-risk-index.md` 后，使用 file 工具回读两份文档，核对 `guardrails.md` 是否只保留规则入口、风险分组、跳转索引与“先回查 Verification Chain 再触碰入口”的硬规则；核对 `runtime-risk-index.md` 是否承接真实锚点、后果与验证动作。  
- 动作 3：对 T0 级禁区的放行标准执行最少拦截动作核查：必须先有正式 Task Contract；必须有对应高风险项的 Verification Chain；必须写出受影响路径/对象的精确确认；必须包含至少一条“误伤排除”动作；必须包含回读或状态核验动作；必须在 Release / Handoff Gate 中明确当前缺口关闭前不得执行。  
- 动作 4：对涉及删除、覆盖、配置写入、`.env` 修改、杀进程、外部脚本执行等高风险动作，逐项核查是否包含以下最少验证：目标对象确认、非目标范围排除、执行前当前状态回读、执行后结果回读、未通过时不放行。缺任一项，则判定该高风险动作验证链不合格。  
- 动作 5：使用 search / file 工具核查新增路径，仅允许出现已拍板的文档落点；确认没有新增计划外目录、没有空壳文件夹、没有把高风险索引写进错误目录。  
- 动作 6：在文档落盘后，把“真实路径已核对、规则入口与风险索引职责已分层、T0 禁区拦截动作已明确、目录洁净度已通过”逐项写回本验证链，并据此给出最终 Gate 结论。

**Verification Result (验证结果)**  
- 目标 1：通过 —— `docs/agents/runtime-risk-index.md` 已落盘并回读；T0 与首批 T1 项均保留真实物理入口、风险、致命后果与触碰前最少要求，可回溯到真实代码路径。  
- 目标 2：通过 —— `docs/agents/guardrails.md` 已完成最小补丁接线并回读；其仍保持规则入口角色，只增加了高风险入口索引、验证链回查硬规则与最低放行条件，没有被写成运行时风险百科。  
- 目标 3：通过 —— `runtime-risk-index.md` 与 `guardrails.md` 均已写入“先有 Task Contract、再有 Verification Chain、最少五刀拦截动作、Gate 未关闭前不得执行”的硬规则，后续 Agent 触碰高风险锚点前已具备明确的停手与回查门槛。  
- 目标 4：通过 —— 新增文档仅为 `docs/agents/runtime-risk-index.md`；`AGENTS.md` → `docs/agents/guardrails.md` → `docs/agents/runtime-risk-index.md` 的导航链路清晰；未新增计划外目录或空壳结构，文档可回读、可导航、可接管。

**Release / Handoff Gate (放行 / 接管闸门)**  
- 当前判断：可收口  
- 当前缺口：无。  
- 接手后第一步：后续若继续扩展高风险锚点，只能在不破坏“guardrails 入口化、runtime-risk-index 承接物理细节”结构的前提下增量补充。  
- 接手入口：先看 `AGENTS.md`，再看 `docs/agents/guardrails.md`，需要真实锚点与前置验证要求时再进入 `docs/agents/runtime-risk-index.md`。

---

## 最终 Release Gate 判定

**【通过 / 可收口】**

### 判定依据
- 风险索引已落盘并回读
- guardrails 已完成最小补丁接线并回读
- 导航链路 `AGENTS.md -> guardrails.md -> runtime-risk-index.md` 已实测顺畅
- 未新增计划外目录或空壳结构
- T0 与首批 T1 风险入口均有真实物理落点
- “触碰前必须回查 Verification Chain”与“五刀最少拦截动作”已写成硬规则

---

## 物理落点
- `docs/agents/runtime-risk-index.md`
- `docs/agents/guardrails.md`
- `docs/exec-plans/in-progress/batch-1-runtime-risk-status-ledger.md`
- `docs/exec-plans/in-progress/batch-1-runtime-risk-verification-chain.md`
- `docs/exec-plans/completed/batch-1-runtime-risk-acceptance-report.md`

---

## 结案声明

批次 1 任务 2 已完成物理落盘、规则接线、导航实测与总放行审校。  
本任务现已具备归档条件，可作为后续批次 1 任务 3 的防御基础设施输入。
