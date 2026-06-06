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
