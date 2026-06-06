# Controlled Entry Index / 受控入口索引

> 定位：这里回答“如果高风险点非碰不可，应该从哪条受控入口进去”。  
> 它不是风险清单。  
> 风险清单看 `runtime-risk-index.md`。  
> 这里的职责是把“危险点”与“推荐进入路径”成对钉死，防止 Agent 走旁路直改。

## 1. 使用方式

只有在以下条件同时成立时，才进入本索引：

- 已确认当前任务必须触碰高风险写入或高副作用入口
- 已有正式 `Task Contract`
- 已有对应 `Verification Chain`
- 当前任务不是在做抽象讨论，而是要找“应从哪条受控路径进入”

硬规则：

- 本索引只给“推荐受控入口”，不等于自动放行
- 进入受控入口前，仍必须回查当前任务的 `Verification Chain`
- Gate 未关闭前，不得执行
- 发现推荐入口与代码现实不一致时，先修索引，不要脑补执行

## 2. 配置写入链（首批样板）

### 2.1 设计结论

配置写入链的统一收敛目标，优先指向：

- `hermes_cli.config.load_config()`
- 修改内存中的配置对象
- `hermes_cli.config.save_config()`

也就是说：

**`hermes_cli.config.save_config()` 是当前最应该被视为全局 YAML 配置持久化出口的受控入口。**

CLI 层的 `save_config_value(...)` 可以保留为场景化 helper，  
但 `gateway` 不应继续复制局部写入逻辑，而应优先向配置中心收敛。

---

### 2.2 危险点 -> 受控入口 对照表

| 危险点 | 当前物理入口 | 推荐受控入口 | 主控裁定 | 禁止的旁路 | 触碰前最少验证 |
|---|---|---|---|---|---|
| CLI 场景下改 `config.yaml` 中单个 key | `cli.py::save_config_value(key_path, value)` | 短期可继续走 `save_config_value(...)`；中长期应保持其底层语义与 `hermes_cli.config.save_config()` 一致 | 允许作为 CLI 层便捷入口，但不得偏离配置中心语义 | 在 CLI 命令代码中直接打开 `config.yaml` 手写字典并覆盖保存 | 写前回读目标 key；确认只改目标项；写后回读；确认未污染其他 section |
| gateway 聊天命令持久化改配置 | `gateway/run.py` 中局部 `_save_config_key(...)` / 手工 YAML 写入 | **优先收敛到 `hermes_cli.config.save_config()` 所代表的统一配置中心路径** | 这是当前最需要治理的分叉区；不应继续复制 gateway 局部 helper | 在各聊天 handler 中继续新增局部 `_save_config_key()` 变体；手工 `atomic_yaml_write(...)` 各写各的 | 写前回读；确认平台影响范围；写后回读；确认只改目标 key；确认与 CLI 语义一致 |
| memory provider 配置写入 | `hermes_cli/memory_setup.py::save_config(config)` | 继续通过 `memory_setup.py` 的集中流程推进，但其 YAML 持久化部分应服从配置中心语义 | 允许作为 memory 配置场景入口，但不应演变成独立配置体系 | 绕开 memory setup 流程，到多个地方分别改 provider 配置 | 明确改哪个 provider；写前回读；写后回读；确认未连带污染其他 provider 配置 |
| `.env` secrets / env vars 写入 | `hermes_cli/memory_setup.py::_write_env_vars(...)` | **`hermes_cli.config.save_env_value()` / `save_env_value_secure()`** | `_write_env_vars(...)` 直接定性为**绝对禁止的高风险旁路** | 直接 `write_text()` 覆盖整个 `.env`；在业务代码中手工拼接字符串重写敏感配置 | 写前回读关键 env 键；写后回读；敏感值掩码；确认未删除无关键；确认只改目标 env var |
| 配置 schema / env 定义源 | `hermes_cli/config.py::DEFAULT_CONFIG` / `OPTIONAL_ENV_VARS` | 将这里视为“配置定义源”，新增配置必须先改定义源，再进入受控写入链 | 这里是配置合法性的上游，不是任意写入点 | 先在运行时各处偷偷写新 key，再回头补 schema | 先确认目标 key 已在定义源存在；确认消费点存在；再进入 YAML / env 受控写入入口 |

---

### 2.3 绝对禁止的高风险旁路

#### A. gateway 局部配置写入旁路
以下行为应直接视为高风险旁路：

- 在 `gateway/run.py` 或各聊天 handler 中继续新增局部 `_save_config_key()` 变体
- 在 gateway 侧直接手工拼装 YAML 并写回
- 不经过统一配置中心语义就持久化用户配置

主控裁定：

**gateway 配置写入应优先向 `hermes_cli.config.save_config()` 这一配置中心收敛。**

---

#### B. `.env` 整文件重写旁路
以下行为应直接视为高风险旁路：

- `hermes_cli/memory_setup.py::_write_env_vars(...)` 这种直接 `write_text()` 重写 `.env`
- 任何业务代码自行打开 `.env` 拼接字符串后整体覆盖保存

主控裁定：

**`memory_setup.py::_write_env_vars(...)` 是绝对禁止的高风险旁路。**  
正确入口应为：

- `hermes_cli.config.save_env_value()`
- `hermes_cli.config.save_env_value_secure()`

---

### 2.4 配置写入链的最低放行条件

凡触碰配置写入链，最少必须满足：

1. 已明确目标 key / env var / provider
2. 已回读当前状态
3. 已确认不是通过旁路直写
4. 已定义写后回读动作
5. 已确认不会连带污染其他配置
6. 敏感值不明文回显
7. `Verification Chain` Gate 已明确放行

少任一项，不得执行。

---

## 3. Profile / Uninstall 环境目录操作链

### 3.1 设计结论

Profile / Uninstall 相关危险动作，不是单纯“删一个目录”或“改一个状态文件”。  
它们通常同时涉及：

- active profile 切换
- `HERMES_HOME` 作用域
- gateway/service 停启与清理
- wrapper / symlink / shell 集成
- profile 目录与用户态数据删除

因此，这一组动作必须优先通过**上游封装入口**推进，不得旁路直碰底层状态文件、目录、service 文件或 pid 控制点。

当前最接近受控入口的函数链包括：

- `hermes_cli/profiles.py::delete_profile()`
- `hermes_cli/profiles.py::set_active_profile()`
- `hermes_cli/main.py::_apply_profile_override()`
- `hermes_cli/profiles.py::resolve_profile_env()`
- `hermes_cli/uninstall.py::run_uninstall()`

主控裁定：

- Profile 删除、active profile 切换、环境卸载，必须优先从这些上游封装入口理解和推进。
- 底层目录删除、状态文件写入、service 文件清理、pid 处理，不得被 Agent 视为“可直接操作的主入口”。

### 3.2 危险点 -> 受控入口 对照表

| 危险点 | 当前物理入口 | 推荐受控入口 | 主控裁定 | 禁止的旁路 | 触碰前最少验证 |
|---|---|---|---|---|---|
| 删除某个 profile | `hermes_cli/profiles.py::delete_profile()` 最终会清 service、停 gateway、删 wrapper、`rmtree(profile_dir)` | 只允许围绕 `delete_profile()` 这条封装链理解和推进 | 允许作为删除 profile 的受控入口；不得绕开它只删目录 | 直接 `shutil.rmtree(profile_dir)`、直接删 `profiles/<name>/`、只删数据不清 service/wrapper | 删前回读 profile 绝对路径；确认目标 profile 名；确认 active profile；确认 gateway/service 状态；删后回读目录、active profile、service 状态 |
| 切换 active profile | `hermes_cli/profiles.py::set_active_profile()` | 只允许围绕 `set_active_profile()` 及启动期 profile override 链推进 | active profile 切换必须走封装入口，不得直接改状态文件 | 直接写/删 `active_profile` 文件；绕开校验手工切换 profile 状态 | 写前回读当前 active profile；确认目标 profile 存在；写后回读 active profile；确认 `HERMES_HOME` 解析结果一致 |
| 启动时应用 profile 环境 | `hermes_cli/main.py::_apply_profile_override()` + `hermes_cli/profiles.py::resolve_profile_env()` | 启动期 profile / `HERMES_HOME` 作用域必须只认这条链 | 这是启动期环境作用域的受控入口，不允许业务代码私造 profile home 解析 | 直接手写 `HERMES_HOME`；手工拼接 profile 路径替代统一解析链 | 执行前回读当前 profile 解析逻辑；确认目标 profile home；执行后确认 `HERMES_HOME` 生效范围 |
| 卸载 Hermes / 清理环境目录 | `hermes_cli/uninstall.py::run_uninstall()` | 只允许围绕 `run_uninstall()` 这条封装链理解和推进 | 卸载是环境级高危操作，必须走集中入口，不得拆散执行 | 直接删安装目录；直接删 `~/.hermes`；直接删 wrapper / shell rc / service 文件 | 执行前回读 `project_root`、`hermes_home`、wrapper/service 状态；确认是否 full uninstall；执行后回读残留状态 |
| 清理 gateway service / wrapper | `profiles.py::_cleanup_gateway_service()`、`uninstall.py::uninstall_gateway_service()` 等辅助链 | 这类 helper 只可作为受控入口的内部组成，不得被 Agent 直接当主入口 | service / wrapper 清理当前存在双实现技术债；本轮只宣示入口主权，不直接重构 | 直接删 plist/service 文件；直接删 wrapper；直接 kill pid 代替封装链 | 回读目标 service 名称、wrapper 路径、profile 归属；执行后回读 service 是否已卸载、wrapper 是否清理正确 |

### 3.3 绝对禁止的高风险旁路

以下行为直接定性为**绝对禁止的高风险旁路**：

#### A. 直接写 `active_profile`
- 直接修改或删除 active profile 状态文件
- 绕开 `set_active_profile()` 手工切换当前 profile

主控裁定：

**active profile 只能通过受控入口切换，绝不允许旁路直写。**

#### B. 直接删除 profile 目录
- 直接 `shutil.rmtree(profile_dir)`
- 直接删 `profiles/<name>/`
- 不经 `delete_profile()` 只删目录本体

主控裁定：

**profile 删除绝不等于目录删除。**  
删 profile 必须同时受控处理 active profile、gateway/service、wrapper 与目录状态。  
任何“只删目录”的行为一律视为绝对禁止旁路。

#### C. 直接删除 service / plist / wrapper
- 手工删 launchd / service 文件
- 手工删 wrapper / symlink
- 不经封装链自行清理 gateway 相关系统集成物

主控裁定：

**service / wrapper 清理只能作为受控链的内部步骤，不得被单独当作主入口执行。**

#### D. 直接 kill gateway 相关进程
- 不经 profile / uninstall 封装链，直接 kill gateway pid
- 用粗暴 kill 代替受控停机与清理流程

主控裁定：

**直接 kill 进程不是 profile / uninstall 的合法替代路径。**

#### E. 直接手写 `HERMES_HOME`
- 在业务逻辑中手工改 `HERMES_HOME`
- 绕开 `_apply_profile_override()` / `resolve_profile_env()` 私自决定 profile home

主控裁定：

**`HERMES_HOME` 作用域只能通过启动期受控链解析与应用，绝不允许旁路直写。**

### 3.4 最低放行条件

凡触碰 Profile / Uninstall 环境目录操作链，最少必须满足：

1. 已明确目标 profile 名、目标目录或卸载范围
2. 已回读真实绝对路径  
   - profile 目录  
   - `project_root`  
   - `hermes_home`
3. 已确认当前 active profile
4. 已确认当前 gateway/service/wrapper 状态
5. 已明确是否会触发目录删除、service 清理、wrapper 清理、active profile 回退
6. 已包含“误伤排除”动作  
   - 非目标 profile 不受影响  
   - 非目标目录不受影响  
   - 当前用户真实环境不被误删
7. 已定义执行后回读动作  
   - 目录是否仍存在  
   - active profile 是否符合预期  
   - service / wrapper 是否处于正确状态
8. 已在 `Verification Chain` 中关闭 Gate

**少任一项，不得执行。**

### 3.5 使用边界

- 这里不替代 `runtime-risk-index.md`
- 这里不定义完整执行模板
- 这里不承载技术债分析全文
- 这里不授权直接执行 profile / uninstall 高危动作
- 这里只定义：受控入口、禁止旁路、最低放行条件

若未来代码层完成统一收敛，应优先更新这里的受控入口建议，而不是继续沿用已过时入口。

---

## 4. 使用边界

- 这里不替代 `runtime-risk-index.md`
- 这里不替代 `guardrails.md`
- 这里不承载执行现场
- 这里不定义完整模板
- 这里只做：“危险点 -> 推荐受控入口 -> 禁止旁路 -> 最低放行条件”的映射

当某一组受控入口已经脱离代码现实时，应优先修索引，而不是继续沿用过期建议。
