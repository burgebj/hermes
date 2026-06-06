# M3 Audit Rules Checklist / M3 审计规则验收清单

> 定位：这是 `safe-refactor-loop` 的第一批“数字法律”。
> 当前优先服务对象：`TDB-3：uninstall CLI 参数语义与实现对齐`。
> 目标：在业务代码真正执行前，先把最危险、最隐蔽、最容易伪装成“优化”的越界拦下来。

## 1. 文件范围硬拦截

### 1.1 允许修改白名单
- `hermes_cli/main.py`
- `hermes_cli/uninstall.py`
- 直接相关最小测试文件

### 1.2 命中即报红
- `hermes_cli/profiles.py`
- `docs/`
- shell / PATH / wrapper 相关非目标文件
- 与 `TDB-3` 无直接关系的其他业务文件

### 验收项
- [ ] 审计器能识别白名单文件
- [ ] diff 命中 `hermes_cli/profiles.py` 时会报红
- [ ] diff 命中文档文件时会报红
- [ ] diff 命中非目标 shell / PATH / wrapper 文件时会报红

---

## 2. TTY 降级硬规则

### 2.1 红线定义
**只要涉及 TTY 降级，审计器必须报红，绝无商量余地。**

### 2.2 触发即 `REJECT_HARD`
- 修改 `_require_tty("uninstall")`
- 新增绕过 TTY 检查的条件分支
- 让 `--yes` 在非 TTY 场景获得更宽松执行能力
- 删除或弱化原有交互确认与 TTY 绑定关系

### 验收项
- [ ] 命中 `_require_tty("uninstall")` 改动时直接 `REJECT_HARD`
- [ ] 命中新增长/改写的非 TTY 放宽分支时直接 `REJECT_HARD`
- [ ] 命中 `--yes` 导致更宽松非交互执行能力时直接 `REJECT_HARD`
- [ ] 这类规则不会被后续“测试通过”覆盖

---

## 3. 高危删除 / 写入规则

### 3.1 审计模式
- `rmtree(`
- `unlink(`
- `remove(`
- `write_text(`

### 3.2 裁决原则
- 若新增高危删除 / 写入调用，默认至少高危告警
- 若该调用与 `TDB-3` 目标无直接关系，默认打回

### 验收项
- [ ] 能识别新增 `rmtree(`
- [ ] 能识别新增 `unlink(`
- [ ] 能识别新增 `remove(`
- [ ] 能识别新增 `write_text(`

---

## 4. shell / PATH 触碰保护规则

### 4.1 审计模式
- `.bashrc`
- `.zshrc`
- `.profile`
- `PATH=`
- `export PATH`
- `find_shell_configs`
- `remove_path_from_shell_configs`

### 4.2 裁决原则
- 命中 shell rc / PATH 清理逻辑，默认报红
- 若 diff 直接触碰 shell 环境集成链，默认视为越界

### 验收项
- [ ] 命中 shell rc 相关字符串时会报红
- [ ] 命中 PATH 相关逻辑时会报红
- [ ] shell / PATH 触碰结果不会被误判为普通变更

---

## 5. 契约一致性规则

### 5.1 风险定义
防止执行体只改 help / 文案 / 参数展示，而不改真实控制流，制造“假对齐”。

### 5.2 审计目标
- `add_argument(...)`
- 参数默认值
- 参数帮助文本
- 参数传递到 `run_uninstall(...)` 的映射关系
- 控制流是否真实使用了参数

### 验收项
- [ ] 能识别“只改 help 文案、不改真实控制流”的风险
- [ ] 能对参数声明与执行路径脱节给出告警

---

## 6. 隐蔽边界补强规则 A：常量 / 默认值间接绕过

### 6.1 风险定义
执行体不直接改 TTY 检查，而是通过修改默认值、常量、布尔开关、dataclass 默认字段等方式，间接放宽 uninstall 行为。

### 6.2 重点审计模式
- `DEFAULT_`
- `ASSUME_`
- `YES_`
- `CONFIRM_`
- `INTERACTIVE_`
- `NON_INTERACTIVE_`
- 函数默认参数中的布尔控制值
- dataclass / config object 中的默认交互开关

### 6.3 裁决建议
- 命中这些默认值且与 uninstall 进入条件相关：至少 `WARN`
- 若导致 TTY / 确认边界实质放松：升级为 `REJECT_HARD`

### 验收项
- [ ] 能识别默认值 / 常量层面的间接放宽风险
- [ ] 与 uninstall 进入条件相关时能升级严重级别

---

## 7. 隐蔽边界补强规则 B：参数别名语义漂移

### 7.1 风险定义
执行体通过修改参数别名、option strings、帮助文本或参数映射关系，制造“看起来语义对齐、实际控制流未对齐”的漂移。

### 7.2 重点审计目标
- `add_argument(...)`
- option strings / aliases
- 参数目标变量
- 参数传递到 `run_uninstall(...)` 的链路
- 交互 / 非交互分支是否真实使用该参数

### 7.3 裁决建议
- 参数定义变化但控制流未同步：至少 `WARN`
- 参数语义增强但实际未参与控制流：`REJECT_HARD`

### 验收项
- [ ] 能识别 alias / option string 变化
- [ ] 能识别参数映射与控制流不一致
- [ ] 能识别“参数看起来增强但不生效”的伪对齐

---

## 8. 误报控制

### 验收项
- [ ] 合法最小 diff 不会被全部打成高危
- [ ] 至少有 1 个正常样例证明规则不是“见啥都红”

---

## 9. 输出结构要求

审计结果至少包含：
- 规则名
- 严重级别
- 决策
- 提示文案

### 最低裁决级别
- `APPROVE`
- `WARN`
- `REJECT_HARD`

---

## 10. 当前主控结论

M3 在接管 `TDB-3` 前，至少必须通过以下硬标准：
- 文件范围能锁边界
- TTY 降级能一秒报红
- 高危删除 / 写入能被抓到
- shell / PATH 触碰能被抓到
- 常量绕过与参数别名漂移也能被抓到

达不到以上标准，不得宣称 M3 可接管 `TDB-3`。
