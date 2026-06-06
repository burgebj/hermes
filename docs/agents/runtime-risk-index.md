# Runtime Risk Index / 运行时高风险锚点索引

> 定位：这里记录真实存在的高风险物理入口。  
> 它不是总规则入口。  
> 总规则、放行纪律、交接纪律仍以 `guardrails.md` 为准。  
> 这里的职责只有一个：告诉 Agent 哪些点不能直接碰、为什么危险、触碰前必须先补什么验证。  
> 本文件当前只收录 **T0 禁区** 与 **首批 T1 高风险入口**，不追求一次性穷举全仓库风险。

## 1. 使用方式

读到这里时，默认说明你已经确认任务会触碰高风险锚点。

**风险索引只负责报警，不授予执行许可；凡触碰高风险锚点，仍必须回到当前任务的 Verification Chain，Gate 未关闭前一律不得动手。**

硬规则：

- 先有 `Task Contract`
- 再有对应的 `Verification Chain`
- 没有“误伤排除”动作，不得执行
- 没有执行前状态回读，不得执行
- 没有执行后结果回读，不得宣称完成
- Gate 未关闭前，不得放行

**缺任一项，视为未获授权执行。**

---

## 2. T0 禁区（绝对禁止直碰）

### 2.1 `tools/terminal_tool.py`

- **Physical Entry（物理入口）**：`tools/terminal_tool.py`
- **Risk（风险）**：终端破坏性命令执行，直接落到真实系统。
- **Fatal Consequence（致命后果）**：误删文件、覆盖状态、污染环境、不可逆系统破坏。
- **Minimum Pre-touch Requirements（触碰前最少要求）**：
  - 已有正式 `Task Contract`
  - 已有对应 `Verification Chain`
  - 已明确目标命令、工作目录、影响范围
  - 已包含“误伤排除”动作
  - 已执行前状态回读
  - 已定义执行后结果回读
  - Gate 未明确前，不得执行

### 2.2 `hermes_cli/uninstall.py` / `hermes_cli/profiles.py`

- **Physical Entry（物理入口）**：`hermes_cli/uninstall.py`；`hermes_cli/profiles.py`
- **Risk（风险）**：环境卸载、profile 切换/删除、用户态数据破坏。
- **Fatal Consequence（致命后果）**：配置丢失、profile 误删、真实 `HERMES_HOME` 被清空或错写、gateway/service 中断。
- **Minimum Pre-touch Requirements（触碰前最少要求）**：
  - 已有正式 `Task Contract`
  - 已有对应 `Verification Chain`
  - 已明确目标 profile 或目标安装目录
  - 已确认当前 active profile 与服务状态
  - 已包含“误伤排除”动作
  - 已定义删后或切换后回读动作
  - 缺任一项，一律不放行

### 2.3 `cli.py` / `gateway/run.py` / `hermes_cli/memory_setup.py` / `hermes_cli/config.py`

- **Physical Entry（物理入口）**：`cli.py`；`gateway/run.py`；`hermes_cli/memory_setup.py`；`hermes_cli/config.py`
- **Risk（风险）**：配置与凭据写入链，入口多点联动，容易静默改写用户状态。
- **Fatal Consequence（致命后果）**：凭据泄漏、配置损坏、启动链失配、后续运行全面失真、跨会话持续异常。
- **Minimum Pre-touch Requirements（触碰前最少要求）**：
  - 已有正式 `Task Contract`
  - 已有对应 `Verification Chain`
  - 已明确只改哪个 key / env var / 配置项
  - 已执行写前状态回读
  - 已定义写后结果回读
  - 敏感值不得明文回显
  - Gate 未关闭前，不得执行

---

## 3. T1 高风险入口（首批）

### 3.1 `tools/code_execution_tool.py`

- **Physical Entry（物理入口）**：`tools/code_execution_tool.py`
- **Risk（风险）**：沙箱/远端执行与清理，可能误清真实资源。
- **Fatal Consequence（致命后果）**：错误清理会话、目录或远端资产，导致环境破坏与证据链断裂。
- **Minimum Pre-touch Requirements（触碰前最少要求）**：
  - 已有正式 `Task Contract`
  - 已有对应 `Verification Chain`
  - 已确认 sandbox 或远端边界
  - 已包含“误伤排除”动作
  - 已执行前状态回读
  - 已定义清理后结果回读
  - Gate 未关闭前，不得执行

### 3.2 `tools/skill_manager_tool.py`

- **Physical Entry（物理入口）**：`tools/skill_manager_tool.py`
- **Risk（风险）**：技能删除与覆盖，可能直接抹掉可运行能力。
- **Fatal Consequence（致命后果）**：技能资产丢失、调用链断裂、行为回归、后续 Agent 失去流程能力。
- **Minimum Pre-touch Requirements（触碰前最少要求）**：
  - 已有正式 `Task Contract`
  - 已有对应 `Verification Chain`
  - 已回读目标 skill 路径
  - 已确认 skill 名称与目标精确匹配
  - 已包含“误伤排除”动作
  - 已定义删后或覆盖后回读
  - Gate 未关闭前，不得执行

### 3.3 `gateway/platforms/whatsapp.py`

- **Physical Entry（物理入口）**：`gateway/platforms/whatsapp.py`
- **Risk（风险）**：kill port / bridge process，直接打断桥接进程。
- **Fatal Consequence（致命后果）**：端口误杀、桥接中断、消息链路掉线、恢复失败。
- **Minimum Pre-touch Requirements（触碰前最少要求）**：
  - 已有正式 `Task Contract`
  - 已有对应 `Verification Chain`
  - 已确认端口归属与目标进程身份
  - 已写明恢复路径
  - 已包含“误伤排除”动作
  - 已定义执行前后状态回读
  - Gate 未关闭前，不得执行

---

## 4. 高风险锚点的统一拦截动作

所有高风险锚点一律先过这 5 刀：

1. 目标确认  
2. 非目标范围排除  
3. 执行前状态回读  
4. 执行后结果回读  
5. Verification Chain Gate 明确放行

**少一刀，都不算可执行。**

---

## 5. 分类型补充动作

### 5.1 删除 / 覆盖类
额外要求：

- 明确目标路径
- 明确当前工作目录
- 明确是否存在递归或批量影响
- 必要时先做只读枚举或 dry-run 替代检查
- 删后验证非目标未受影响

### 5.2 配置 / 凭据写入类
额外要求：

- 精确到 key / env var
- 敏感值不回显
- 写前后比对关键字段
- 核对是否影响 CLI / gateway / service / memory 行为

### 5.3 进程 / bridge / service 类
额外要求：

- 确认端口归属
- 确认目标进程身份
- 写明停机影响范围
- 写明恢复路径或回滚动作

### 5.4 全局状态 / 上下文污染类
额外要求：

- 确认当前是否处于子代理 / 恢复流程
- 比较操作前后状态一致性
- 证明不会污染父流程或历史上下文

---

## 6. 使用边界

- 这里不替代 `guardrails.md`
- 这里不定义完整验证模板
- 这里不承载执行现场
- 这里不承载历史复盘
- 这里只记录：物理入口、风险、后果、触碰前验证要求

发现内容开始变成安全百科时，应回收范围。
