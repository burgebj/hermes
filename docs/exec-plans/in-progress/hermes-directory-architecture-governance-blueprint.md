# Hermes 目录架构治理蓝图

## 1. 当前问题总览

### 1.1 当前问题不是“看起来乱”，而是路径治理开始失去主干
目前仓库已经同时存在以下几类对象：
- 运行入口与 packaging 入口
- 北冥法典与接管入口文档
- 执行现场文档
- 历史 release 文档
- 一次性计划 / 蓝图 / 备忘文
- 本地状态文件与临时产物

这些对象正在共享根目录与若干相邻层级，导致“入口”“现场”“历史”“临时物”之间的边界变弱。

### 1.2 已出现的结构性信号
1. 根目录同时放着正式入口、历史文档、营销型文章、状态文件与本地产物。  
2. `plans/`、`docs/plans/`、`.plans/` 三处分裂，计划类文档没有唯一锚点。  
3. `docs/exec-plans/in-progress/` 同时承载合同、状态台账、验证链、blueprint、battle packet、备份、迁移状态文件。  
4. 用户期望中的 `policies/` 还没有形成正式目录，导致部分治理规则只能散落在 `docs/agents/`、`docs/exec-plans/` 与任务文档中。  
5. 根目录存在未纳入治理边界的本地状态对象，如 `migration_state.json`、`tts_chinese_migration.json`、`pip_list_backup.txt`、`node_modules/`、`venv_backup_20260416_034059/`、`.plans/` 等，容易污染人和自动化对“仓库结构”的直觉。

### 1.3 为什么这会拖累自动化与法典执行
- 自动接管时，很难快速判断“先读哪个路径才是正式入口”。
- 若自动化只按文件名搜索，`task-contract`、`blueprint`、`battle-packet`、`backup` 混在一层，会降低路径预测稳定性。
- 根目录一旦长期吸纳历史文档与临时物，后续很难建立稳定 allowlist；任何基于根目录扫描的工具都更容易误抓无关文件。
- 北冥法典强调“地图、协议、现场、证据”的分层；目录混层会削弱这一分层，使后续法典执行更依赖人工解释而不是固定路径。

---

## 2. 现状目录审计

### 2.1 根目录当前哪些对象最混乱

#### A. 明显不应长期占根的文档对象
- `hermes-already-has-routines.md`：更像文章 / 备忘 / 对外材料，不是仓库正式入口。
- `RELEASE_v0.2.0.md` ～ `RELEASE_v0.9.0.md`：属于历史 release 文档，批量堆在根目录会稀释根入口层。
- `plans/gemini-oauth-provider.md`：说明存在“计划文档落在根 plans/”的分流现象。
- `.plans/streaming-support.md`、`.plans/openai-api-server.md`：进一步证明计划类文档没有唯一锚点。

#### B. 明显不应作为仓库结构一部分的本地状态 / 临时物
- `migration_state.json`
- `tts_chinese_migration.json`
- `pip_list_backup.txt`
- `node_modules/`
- `venv/`、`.venv/`、`venv_backup_20260416_034059/`
- `__pycache__/`、`.pytest_cache/`

这些对象不一定都被跟踪，但它们真实占据根目录心智空间，会影响人工审计与自动化规则设计。

#### C. 边界模糊但暂不应直接动的对象
- `shiba_inu_white_background.png`
- `shiba_inu_white_background.svg`

它们大概率属于品牌 / 资产类材料，应下沉到 `assets/` 或专门资产目录，但是否存在外部引用尚未核查，不能先搬。

### 2.2 哪些属于“正式入口”，应继续留在根目录

#### A. 仓库元入口
- `README.md`
- `LICENSE`
- `CONTRIBUTING.md`
- `AGENTS.md`
- `pyproject.toml`
- `requirements.txt`
- `MANIFEST.in`
- `Dockerfile`
- `flake.nix`
- `flake.lock`
- `package.json`
- `package-lock.json`
- `cli-config.yaml.example`
- `constraints-termux.txt`
- 各类 Git / shell 配置文件：`.gitignore`、`.gitattributes`、`.gitmodules`、`.dockerignore`、`.env.example`

#### B. 当前运行入口 / 打包入口
这些文件目前直接参与脚本入口、import 或 setuptools `py-modules` 装配，短期内不应因目录治理直接迁移：
- `run_agent.py`
- `cli.py`
- `model_tools.py`
- `toolsets.py`
- `toolset_distributions.py`
- `batch_runner.py`
- `mcp_serve.py`
- `mini_swe_runner.py`
- `rl_cli.py`
- `hermes_constants.py`
- `hermes_logging.py`
- `hermes_state.py`
- `hermes_time.py`
- `trajectory_compressor.py`
- `utils.py`
- `hermes`

**不能马上动的原因：** `pyproject.toml` 的 `[project.scripts]` 与 `[tool.setuptools].py-modules` 已把这些 root 文件视为当前架构的一部分；目录治理任务本身不应升级成 Python 包结构重构任务。

#### C. 顶层职责明确的目录
这些目录已基本形成稳定职责，不是本轮治理的首要混乱源：
- `agent/`
- `tools/`
- `hermes_cli/`
- `gateway/`
- `cron/`
- `tests/`
- `docs/`
- `website/`
- `web/`
- `assets/`
- `scripts/`
- `docker/`
- `packaging/`
- `plugins/`
- `skills/`
- `optional-skills/`
- `environments/`
- `nix/`
- `acp_adapter/`

### 2.3 哪些属于“应下沉”的对象

#### 优先应下沉到文档或归档层
- `hermes-already-has-routines.md` → 应归入 `docs/archive/` 或 `docs/memos/` 一类历史 / 对外材料层。
- `RELEASE_v*.md` → 应归入 `docs/archive/releases/` 或 `docs/releases/`。
- `plans/`、`.plans/` 中的计划文档 → 应统一归并到一个正式计划目录，建议以 `docs/plans/` 为唯一入口。

#### 需要单独治理但不能先搬的对象
- 根目录图片资产 → 等引用关系核实后再统一入 `assets/branding/` 或等效目录。
- 根目录状态 JSON / 备份 TXT → 应纳入 `.gitignore` / 本地状态规范，不应占据正式仓库入口层；但是否删除或迁移，属于执行批次事项。

### 2.4 哪些目录已经形成稳定职责，哪些还混层

#### 已形成稳定职责的目录
- `docs/agents/`：已经形成“地图下钻、结构、工作流、规则、宪章、协议、战史、模板”的法典入口层。
- `docs/specs/`：虽然文件少，但职责清晰，适合存放专题规格。
- `docs/migration/`：职责明确，适合迁移与兼容说明。
- `tools/`、`hermes_cli/`、`gateway/`、`tests/`：代码职责较稳定。

#### 仍然混层的目录
- 根目录：入口、历史、文章、状态物混层。
- `docs/exec-plans/in-progress/`：执行现场与临时辅助物混层。
- `docs/` 顶层：除 `agents/`、`exec-plans/`、`specs/`、`migration/` 外，还夹有零散 html/md 文档，未来若继续增长，会再次出现入口漂移。
- 计划层：`plans/`、`.plans/`、`docs/plans/` 三分裂。

### 2.5 当前目录结构会如何拖累后续自动化与法典执行
1. **根目录 allowlist 难建立**：因为根目录不再只承载入口级对象。  
2. **自动发现链不稳定**：计划文档和执行文档散落多处，新会话很难靠固定路径接管。  
3. **执行现场难以 fail-closed**：`docs/exec-plans/in-progress/` 没有“任务级容器”，工具若只按文件名抓取，容易拿到旧 battle packet 或无关 blueprint。  
4. **治理规则难机器化**：`policies/` 尚未形成稳定落点，很多“规则”仍是 prose，而不是稳定、可引用、可校验的治理对象。  
5. **战时接管成本上升**：接手方需要先辨认哪些是正式入口、哪些只是历史材料或临时产物，违背北冥法典“固定入口、固定证据、固定接管”的方向。

---

## 3. 目标目录蓝图

## 3.1 根目录应保留什么
根目录只保留四类对象：
1. **仓库元入口**：README、LICENSE、CONTRIBUTING、AGENTS、构建与包管理文件。  
2. **当前架构硬入口**：被脚本入口、import、setuptools 明确绑定的 root 级 Python 文件。  
3. **顶层代码目录**：`agent/`、`tools/`、`hermes_cli/`、`gateway/`、`tests/`、`docs/`、`website/` 等。  
4. **少量确有必要的顶层资产或脚手架目录**：如 `assets/`、`docker/`、`scripts/`、`packaging/`。

**根目录不应长期保留：**
- 历史 release 文档
- 单次战役蓝图
- 文章 / 宣传稿 / 备忘
- 临时计划文档
- 迁移状态文件、备份文件、环境产物

### 3.1.1 建议的根目录治理原则
- 用“根目录 allowlist”定义允许长期存在的对象。  
- 不在本任务内移动 root Python 入口层。  
- 先清掉文档和临时物，再考虑更深层包结构调整。  
- 根目录新增文件必须先判断：它是入口，还是应该下沉？

## 3.2 `docs/agents/` 应放什么
`docs/agents/` 作为**长期稳定的人类 / Agent 协议入口层**，只放：
- 总导航与阅读顺序
- 系统结构图与入口地图
- 工作流入口
- 风险边界与验证纪律
- 宪章 / 角色定义 / 主权原则
- 主线收编协议
- 战史案例库
- 固定模板
- 固定索引（如受控入口索引、运行时风险索引）

**不应放入：**
- 某一场战役的临时合同、状态台账、验证链
- 单次执行蓝图
- 临时 checklist
- 迁移状态文件
- 备份文件

## 3.3 `docs/exec-plans/` 应放什么
`docs/exec-plans/` 应被收敛为**执行现场层**，只承载任务级证据链与结案物。

### 建议的目标形态
```text
docs/exec-plans/
  in-progress/
    <task-slug>/
      task-contract.md
      status-ledger.md
      verification-chain.md
      execution-notes.md        # 如确有必要
      migration-state.json      # 仅当任务确实需要
  completed/
    <task-slug>/
      acceptance-report.md
      references/              # 可选，仅存本任务完成后的补充证据
  tech-debt-tracker.md
```

### 设计理由
- 把“任务级容器”引入 `in-progress/`，避免所有 battle 文件平铺在同一层。  
- 让自动化可以按 `task-slug` 进入现场，而不是先做文件名猜谜。  
- 让 `completed/` 成为清晰的归档层，而不是零散 acceptance report 平铺。

### `docs/exec-plans/` 不应长期承载的对象
- 仓库级通用 blueprint
- 对外文章
- 广义研究计划
- 无关备份与 `.bak`
- 与某个任务弱关联的零散 checklist

## 3.4 `policies/` 应放什么
`policies/` 当前不存在，**不建议为了“好看”立刻新建空目录**；但从蓝图角度，它适合作为**机器可引用、治理可校验的规则层**。

### `policies/` 适合承载的内容
- 根目录 allowlist / denylist
- 文档落点规则
- 命名规则
- 归档规则
- 执行现场文件命名矩阵
- 自动化工具读取的结构约束 YAML / JSON / Markdown 规则文档

### `policies/` 不应承载的内容
- 北冥宪章本身
- 战史案例
- 主线收编协议正文
- 执行现场文档
- 临时说明文

**原因：** `policies/` 是治理规则的“机器层”，不是主权法典的“叙事层”。北冥法典现有层级仍应保留在 `docs/agents/`。

## 3.5 哪些内容应归档
建议建立 `docs/archive/`（或等效归档层），承接以下对象：
- 历史 release 文档：`RELEASE_v*.md`
- 对外文章 / 备忘 / 非入口型长文：如 `hermes-already-has-routines.md`
- 废弃或被新路径取代的计划文档
- 历史战时材料的补充附件（若不再属于活跃执行现场）

## 3.6 哪些应是长期稳定入口
长期稳定入口建议固定为：
- 根：`README.md`、`AGENTS.md`、`pyproject.toml`、当前 root 运行入口
- 人类 / Agent 法典入口：`docs/agents/README.md`
- 执行现场入口：`docs/exec-plans/tech-debt-tracker.md` + 目标任务目录
- 规格入口：`docs/specs/`
- 迁移入口：`docs/migration/`
- 计划入口：`docs/plans/`
- 规则入口（未来如落地）：`policies/`

## 3.7 哪些属于战时文件，不应长期占主入口层
- task contract
- status ledger
- verification chain
- battle packet
- 单次 checklist
- migration-state.json
- task-specific blueprint
- 临时备份

这些都不应长期停留在根目录，也不应与法典主入口抢层级。

---

## 4. 分批治理路线

## 批次 1：根目录入口清理
### 目标
先把“显然不属于根入口层”的对象识别出来，建立根目录 allowlist 与待迁移清单。

### 影响范围
- 根目录文档类文件
- 根目录历史 release 文档
- 根目录一次性文章 / 备忘
- 根目录本地状态物与临时产物识别规则

### 风险
- 误把仍被引用的文档、资产或脚本当成可迁移对象。  
- 把“根目录整理”升级成 Python 包结构重构。  
- 把本地未跟踪文件和仓库正式对象混为一谈。

### 验证方法
- 建立根目录 allowlist。  
- 回读 `pyproject.toml`、脚本入口、README、现有引用关系。  
- 输出“保留 / 下沉 / 暂不动”三张清单。  
- 验证执行后根目录是否只剩入口级对象，没有破坏脚本入口与引用路径。

## 批次 2：文档层整理
### 目标
把计划层、法典层、执行现场层、规格层、迁移层的边界重新拉直，消除 `plans/`、`.plans/`、`docs/plans/` 的三分裂。

### 影响范围
- `docs/`
- `docs/plans/`
- `plans/`
- `.plans/`
- 零散顶层文档的目标落点

### 风险
- 文档引用链接失效。  
- 新旧计划路径并存，导致过渡期更乱。  
- 把“通用架构蓝图”继续留在执行现场层。

### 验证方法
- 定义唯一计划入口：`docs/plans/`。  
- 用搜索回查旧路径引用是否已修复。  
- 随机挑选 2~3 个计划文档，验证新会话能否直接按固定路径接管。

## 批次 3：法典 / 模板 / 蓝图归位
### 目标
明确 `docs/agents/` 与未来 `policies/` 的分工，让法典叙事层与机器规则层分离，但不破坏现有北冥法典主干。

### 影响范围
- `docs/agents/`
- 未来可能新增的 `policies/`
- 与法典治理相关的固定模板与索引

### 风险
- 把宪章、协议、战史错误抽走到 `policies/`，导致法典层断裂。  
- 为了追求规则机器化而制造空壳目录。  
- 在未完成命名矩阵前就批量重定路径。

### 验证方法
- 明确“法典叙事层”与“机器规则层”对象清单。  
- 若落地 `policies/`，至少先放一项真正会被自动化读取的治理规则，不允许空目录。  
- 验证 `AGENTS.md -> docs/agents/README.md -> 具体法典文档` 的接管链仍成立。

## 批次 4：历史材料归档
### 目标
把 release 文档、历史文章、废弃计划与非活跃战时材料迁入归档层，恢复主入口清爽度。

### 影响范围
- `RELEASE_v*.md`
- `hermes-already-has-routines.md`
- 已失去入口价值的旧计划 / 旧说明文
- 可能的旧 battle 附件

### 风险
- 外部引用断裂。  
- 历史材料被“归档即失踪”。  
- 归档层规则不清，后续又继续堆乱。

### 验证方法
- 建立归档目录说明。  
- 为迁移对象保留可搜索命名与必要索引。  
- 搜索全仓引用并修复。  
- 验证 README / AGENTS / docs 入口不再直接依赖归档层对象。

---

## 5. 风险与验证方法

### 5.1 总风险
1. **误伤正式入口**：尤其是 root Python 模块与 packaging 入口。  
2. **引用链断裂**：文档跳转、AGENTS 地图、执行现场引用、README 链接都可能受影响。  
3. **自动化路径漂移**：如果只移动文件而不先定义固定路径，治理后反而更难预测。  
4. **过度治理**：把目录治理升级成代码重构或法典改写。  
5. **空壳化**：新建 `policies/`、`archive/` 等目录却没有真实治理对象，造成结构看似规范、实则更空。

### 5.2 全程验证原则
- 每一批都先有“保留 / 下沉 / 暂不动”清单。  
- 每一批都做引用搜索回读。  
- 每一批都验证自动接管入口是否比之前更短、更稳。  
- 每一批都只动一层边界，不同时触发代码入口重构。  
- 每一批结束后更新状态台账与验证链，证明目录治理不是“整理癖”，而是真正提升路径稳定性。

### 5.3 明确暂时不能动的对象
- root Python 入口层：受 `pyproject.toml` 脚本入口与 `py-modules` 绑定约束，当前任务不动。  
- `AGENTS.md`：必须留在根目录，作为项目上下文与接管总地图入口。  
- `docs/agents/` 主干法典文档：当前已形成稳定接管链，只能做边界收紧，不能轻易迁层。  
- `docs/exec-plans/` 现有战时文档：在建立任务级容器与引用修复方案前，不应直接大搬迁。  
- 根目录图片资产：需先核查引用关系，再决定是否下沉。

---

## 6. 建议先从哪一批开始

**建议先从批次 1：根目录入口清理开始。**

原因不是因为它“最简单”，而是因为它对后续三批都有基础性价值：
1. 先立住根目录 allowlist，后续任何治理才有“什么叫入口层”的判据。  
2. 先识别哪些对象只是历史 / 计划 / 临时物，后面文档层和归档层才不会继续混搬。  
3. 它几乎不需要碰代码入口，风险最低，但对长期自动化稳定性收益最大。  
4. 只有先把根目录边界拉直，`docs/agents`、`docs/exec-plans`、未来 `policies/` 才能在一个稳定主干上归位。

### 建议的起手动作
- 先做根目录 allowlist 审核表。  
- 把根目录对象分成：**保留 / 应下沉 / 暂不动 / 本地污染物** 四类。  
- 在不移动代码入口的前提下，优先收敛明显的文档与历史材料目标路径。  
- 等批次 1 证据成立后，再启动批次 2 的文档层归并。
