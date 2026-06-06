## Status Ledger / Progress Doc（状态台账 / 进度文档）

**Task Contract Snapshot (合同快照)**  
- 目标：将 `hermes_cli/profiles.py` 与 `hermes_cli/uninstall.py` 中的 service cleanup 双实现收敛为一条统一、可复用、语义一致的受控清理链，在不扩大副作用范围的前提下，消除 profile 删除与 uninstall 路径在 service cleanup 行为上的分叉。  
- 范围边界：只处理与 service cleanup 双实现直接相关的代码路径；允许提炼统一 cleanup helper 或统一调用链；允许最小必要测试补充；如服务于 cleanup 正确性，仅允许最小必要 wrapper 联动修正。禁止顺手收敛 wrapper 双实现、active profile 解析链、uninstall 参数语义、Hook/新框架与文档改动。  
- 完成标准：两条上层路径共享同一套 cleanup 核心语义；相关测试通过；未新增高危删除路径；未扩大 wrapper 改动范围；未触碰 active profile 解析链与 uninstall 参数语义；改动可审计。  

**Current State (当前状态)**  
- 当前停点：玄麟已提交首轮代码改动；主控已按“先看 diff → 再查调用链 → 再看测试 → 最后读报告”的顺序完成首轮裁决。  
- 已完成：确认 `profiles._cleanup_gateway_service()` 已改为委托 `hermes_cli.uninstall.cleanup_gateway_service(profile_dir)`；`uninstall_gateway_service()` 已统一委托 `cleanup_gateway_service(get_hermes_home())`；最小相关测试 `4 passed`；未发现新增 `rmtree` 调用；未改文档、未改 active profile 解析链、未改 uninstall 参数语义。  
- 未完成 / 当前阻塞：本轮首审已判定为可通过；如需最终合并前复核，可追加更大范围回归，但不属于首轮裁决阻塞项。  
- 当前判断：首轮真赢  

**Evidence Logged (证据登记)**  
- 已有证据：diff 显示 `profiles.py` 删除了本地 Linux/macOS service cleanup 逻辑，改为调用统一 helper；`uninstall.py` 新增 `cleanup_gateway_service(service_home: Path)` 作为共享 cleanup 核心；`tests/hermes_cli/test_profiles.py` 增加委托测试；`tests/hermes_cli/test_uninstall.py` 新增共享 cleanup 测试；`uv run --extra dev python -m pytest ... -q` 结果为 `4 passed in 0.51s`。  
- 证据对应结论：本轮已实现 service cleanup 双实现收敛；改动范围受控；无新增高危删除路径；wrapper 未被扩大改动。  
- 证据缺口：无首轮裁决级缺口。  

**Next Handoff (下一步 / 接管指令)**  
- 接手后第一步：如进入最终合并前复核，先复看统一 helper 的 service 目标识别语义，再决定是否需要扩一层集成测试。  
- 立即核查：确认 wrapper 逻辑确未被扩大修改；确认未来下一战仍按账本顺序先打 TDB-2（wrapper 双实现收敛）。  
- 若受阻先排查：若后续发现平台特定 service 名称解析存在差异，单开新合同处理，不要回卷当前已通过的 P0 范围。  
