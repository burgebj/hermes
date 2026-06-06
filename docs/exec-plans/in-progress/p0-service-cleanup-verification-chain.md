## Verification Chain（默认验证链）

**Verification Target (验证目标)**  
- 目标 1：证明 `profiles` 与 `uninstall` 路径已共享同一套 service cleanup 核心语义，而不是名义统一。  
- 目标 2：证明本轮未新增高危删除路径，也未扩大 cleanup 副作用范围。  
- 目标 3：证明本轮未越界到 wrapper 双实现、active profile 解析链或 uninstall 参数语义。  
- 目标 4：证明最小相关测试真实覆盖了 profile 删除路径与 uninstall 路径的共享 cleanup 行为。  

**Verification Actions (验证动作)**  
- 动作 1：Diff 审计——检查是否新增 `rmtree` / 删除路径 / 新 cleanup helper 分叉。  
- 动作 2：调用链回读——确认 `delete_profile()` 通过 `profiles._cleanup_gateway_service()` 委托到 `hermes_cli.uninstall.cleanup_gateway_service(profile_dir)`；确认 `run_uninstall()` 通过 `uninstall_gateway_service()` 委托到同一 helper。  
- 动作 3：越界审计——检查是否改了 wrapper 大范围逻辑、active profile 解析链、uninstall 参数语义、文档文件。  
- 动作 4：测试审计——运行最小相关测试并核对 `4 passed`。  

**Verification Result (验证结果)**  
- 目标 1：通过 —— `profiles._cleanup_gateway_service()` 已删除本地重复实现并委托 `hermes_cli.uninstall.cleanup_gateway_service(profile_dir)`；`uninstall_gateway_service()` 也委托到该共享 helper。  
- 目标 2：通过 —— diff grep 未发现新增 `rmtree`；仅保留原有 `unlink(missing_ok=True)` 清理语义，没有引入新的删除路径。  
- 目标 3：通过 —— wrapper 逻辑未被收敛；active profile 解析链未修改；uninstall 参数语义未修改；文档未改。  
- 目标 4：通过 —— `uv run --extra dev python -m pytest tests/hermes_cli/test_profiles.py::TestDeleteProfile::test_cleanup_wrapper_uses_shared_service_cleanup tests/hermes_cli/test_profiles.py::TestDeleteProfile::test_removes_directory tests/hermes_cli/test_uninstall.py -q` 返回 `4 passed in 0.51s`。  

**Release / Handoff Gate (放行 / 接管闸门)**  
- 当前判断：通过 / 可收口  
- 当前缺口：无  
- 接手后第一步：如进入合并前复核，先做更大范围平台行为检查；若发现 wrapper 相关新问题，按 TDB-2 新开战役，不回卷当前 P0。  
- 接手入口：先看本验证链，再看 `git diff -- hermes_cli/profiles.py hermes_cli/uninstall.py tests/hermes_cli/test_profiles.py tests/hermes_cli/test_uninstall.py`。  
