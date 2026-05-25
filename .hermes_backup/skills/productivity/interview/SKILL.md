---
name: interview
description: Manage interview timetables, candidates, resumes, and onboard timelines for WarpDriveAI hiring.
---

# Interview Management Skill

Manages candidate resumes, interview schedules, onboard timelines, and candidate archives for WarpDriveAI.

## How to Invoke

The skill is available as the slash command **`/interview`**. Type it directly to load the skill.

> **Note:** Slash command registration is automatic — it comes from the skill's `name` in the frontmatter above (`interview` → `/interview`). The skill becomes available after any hermes restart. There is no `trigger:` field needed or used.

> **Important:** `_skill_commands` is populated once at hermes startup. If you create or update a skill while hermes is already running, the changes won't take effect — you must restart hermes first.

## ⚠️ Critical: Direct Execution Rule

**When the user gives a command with a candidate name + action, execute immediately. Do not ask clarifying questions.**

The most common failure mode is asking unnecessary questions when the action is already clear:

| ❌ Bad (don't do this) | ✅ Good (do this instead) |
|---|---|
| User: `/interview 介绍一下刘子铭情况` → Assistant: "请问您是已经下载了简历还是..." | → 直接去 `候选人档案/` 找，找到就读，找不到再去 `简历/` 找 |
| User: `/interview 帮我把李明简历归档` → Assistant: "请问简历在哪里？" | → 先去 `Downloads/` 搜，找到就确认移动，找不到再问 |
| User: `/interview 安排顾婧一面` → Assistant: "请问要安排什么？" | → 先读 `面试时间表.md`，检查是否已有记录，再问具体信息 |

### Default Action Chain for "介绍一下/查一下"

当用户说"介绍一下[某人]"或"查一下[某人]情况"时，按此顺序自动执行，**不要提前问问题**：

1. **Step 1:** `find "$ARCHIVE_DIR" -name "*姓名*"` — 搜候选人档案
   - ✅ 找到 → 直接读取并展示，不需要问"找到了，要我看吗？"
   - ❌ 没找到 → Step 2
2. **Step 2:** `find "$RESUME_DIR" -name "*姓名*"` — 搜简历目录
   - ✅ 找到 → 读取简历内容，做摘要展示，询问是否要创建档案
   - ❌ 没找到 → Step 3
3. **Step 3:** `find "$DOWNLOADS_DIR" -name "*姓名*"` — 搜下载目录
   - ✅ 找到 → 展示文件路径，询问是否归档
   - ❌ 没找到 → 告知未找到该候选人

### Default Action Chain for "安排面试"

当用户说"安排[某人]面试"时：
1. 先读 `面试时间表.md`，查看该候选人是否已有面试记录
2. 展示已有记录（如果有）
3. 要求用户补充: 轮次、日期、时间、形式、面试官

---

## File Paths

```bash
RESUME_DIR="/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/简历"
DOWNLOADS_DIR="/mnt/c/Users/liuch/Downloads"
ARCHIVE_DIR="/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/候选人档案"
SCHEDULE_FILE="/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/面试时间表.md"
ONBOARD_FILE="/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/入职时间表.md"
```

All paths contain spaces — **always quote them** in shell commands.

---

## Feature 1: Move Resume from Downloads to Official Folder

**Trigger:** User says a candidate's name and the resume needs to be filed.

### Step 1: Find the resume

Search Downloads for files matching the candidate's name (Chinese or English), prioritizing PDF/DOCX files:

```bash
find "/mnt/c/Users/liuch/Downloads" -maxdepth 2 -type f \( -iname "*李明*" -o -iname "*liming*" -o -iname "*li*ming*" \) 2>/dev/null
```

Also check subdirectories (some candidates are in subfolders by date):

```bash
find "/mnt/c/Users/liuch/Downloads" -type f \( -iname "*李明*" -o -iname "*liming*" \) 2>/dev/null
```

### Step 2: Confirm with user

Show the found file path and ask for confirmation before moving:

```
Found: /mnt/c/Users/liuch/Downloads/李明_简历.pdf
Move to: /mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/简历/
Confirm? (yes/no)
```

If user confirms, move with:

```bash
mv "/mnt/c/Users/liuch/Downloads/李明_简历.pdf" "/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/简历/"
```

### Step 3: Create candidate archive stub

After moving, create an archive file using `write_file` (auto-creates parent dirs):

```
路径: /mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/简历/李明_简历.pdf

## 面试反馈

## 入职时间线
```

> **Note:** The `候选人档案/` directory is auto-created by `write_file`. If using `terminal` with heredoc, first run: `mkdir -p "/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/候选人档案"`

---

## Feature 2: Summarize Candidate Resume (Pros & Cons)

**Trigger:** User provides a candidate's name and wants a summary.

### Workflow

1. Find the candidate's resume in `RESUME_DIR`:
```bash
find "$RESUME_DIR" -type f \( -iname "*李明*" -o -iname "*liming*" \) 2>/dev/null
```

2. Read the resume content using `execute_code` with `pypdf` (avoids `pdftotext` which is not always available):
```python
import pypdf
reader = pypdf.PdfReader("/path/to/resume.pdf")
for i, page in enumerate(reader.pages):
    print(f"--- Page {i+1} ---")
    print(page.extract_text())
```
If `pypdf` is not installed: `pip install pypdf -q`

For DOCX:
```python
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile('/path/to/resume.docx') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        root = tree.getroot()
        texts = [t.text for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]
        print(' '.join(texts))
```

3. Analyze and present:

**Output format:**
```
## 简历摘要 — [候选人姓名]

**优势:**
- [Point 1]
- [Point 2]
- [Point 3]

**劣势/风险:**
- [Point 1]
- [Point 2]

**综合评价:** 一句话总结
```

---

## Feature 3: Write Interview Schedule

**Trigger:** User provides a candidate's name and interview details.

### Schedule File Format (`面试时间表.md`)

```markdown
# 面试时间表

## [候选人姓名]

| 轮次 | 日期 | 时间 | 形式 | 面试官 | 状态 | 备注 |
|------|------|------|------|--------|------|------|
| 一面 | 2025-06-01 | 14:00 | 线上 | 张三 | 已安排 | 技术面 |
| 二面 | 2025-06-05 | 15:00 | 线下 | 李四 | 待确认 | 综合面 |

---
```

### Workflow

1. If SCHEDULE_FILE doesn't exist, create it with header
2. Check if candidate already exists in the table
3. If yes, update the row; if no, append new candidate
4. Use sed or python to update the table

```python
import re
from datetime import date

schedule_path = "/mnt/c/Users/liuch/My Documents/warpdriveai/制度/招聘/面试时间表.md"
candidate = "李明"
round_num = "一面"
interview_date = "2025-06-01"
interview_time = "14:00"
format_type = "线上"
interviewer = "张三"
status = "已安排"
note = "技术面"

# Read existing file
with open(schedule_path, "r", encoding="utf-8") as f:
    content = f.read()

new_row = f"| {round_num} | {interview_date} | {interview_time} | {format_type} | {interviewer} | {status} | {note} |"

# Check if candidate section exists
candidate_pattern = rf"(?## {candidate}\n\| 轮次.*?\n)((?:\|.*?\n)*)"
match = re.search(candidate_pattern, content)
if match:
    # Append to existing section
    section = match.group(0)
    new_section = section + new_row + "\n"
    content = content.replace(section, new_section)
else:
    # Add new section before "---"
    new_section = f"\n## {candidate}\n\n| 轮次 | 日期 | 时间 | 形式 | 面试官 | 状态 | 备注 |\n|------|------|------|------|--------|------|------|\n{new_row}\n\n---\n"
    content = content.replace("\n---\n", new_section, 1) if content.endswith("\n---\n") else content + new_section

with open(schedule_path, "w", encoding="utf-8") as f:
    f.write(content)
```

---

## Feature 4: Write Onboard Timeline

**Trigger:** User provides a candidate's name and onboard plan details.

### Onboard File Format (`入职时间表.md`)

```markdown
# 入职时间表

## [候选人姓名]

| 阶段 | 日期 | 内容 | 负责人 | 状态 |
|------|------|------|--------|------|
| Offer发送 | 2025-06-10 | 发送Offer及合同 | HR | 已完成 |
| 背景调查 | 2025-06-12 | 第三方背调 | HR | 进行中 |
| 入职日 | 2025-07-01 | 第一天上班 | — | 待确认 |

### 注意事项
- [ ]
```

### Workflow

Same update pattern as Feature 3, using the onboard table structure.

---

## Feature 5: Build Candidate Archive

**Trigger:** User asks to build or update a candidate's archive file.

### Archive File Format (`候选人档案/<姓名>.md`)

```markdown
---
name: [候选人姓名]
status: [状态: 面试中/待入职/已入职/已淘汰]
created: [YYYY-MM-DD]
updated: [YYYY-MM-DD]
---

# [候选人姓名] 档案

## 基本信息
- **姓名:** [姓名]
- **应聘岗位:** [岗位]
- **简历路径:** `...`
- **简历归档时间:** YYYY-MM-DD

## 面试记录

### 一面 (YYYY-MM-DD)
- **面试官:** [姓名]
- **评价:** 
- **结果:** 通过/未通过

### 二面 (YYYY-MM-DD)
- ...

## 综合反馈
[多轮面试的综合评价，优势与不足]

## 入职时间线
| 阶段 | 日期 | 内容 | 状态 |
|------|------|------|------|
| Offer | YYYY-MM-DD | 发送Offer | ✓ |

## 备注
[其他重要信息]
```

### Workflow

1. Check if archive exists:
```bash
find "$ARCHIVE_DIR" -name "*李明*" 2>/dev/null
```

2. If exists, read it and update with new information
3. If not, create new archive file from scratch
4. Always update the `updated:` field

---

---

## meeting-record: 会议记录管理

记录和归档会议笔记、生成纪要、追踪待办事项。

### File Paths

```bash
MEETING_DIR="/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record"
INDEX_FILE="/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record/会议索引.md"
```

所有路径含空格 — **始终加引号**。

### 模板

```markdown
# [YYYY-MM-DD] 会议主题

## 基本信息
- **日期:** YYYY-MM-DD
- **时间:** HH:MM - HH:MM
- **地点/形式:** 线下/线上
- **参会人:** 张三, 李四
- **主持人:** [姓名]
- **记录人:** [姓名]

## 会议议程
1. [议程项1]

## 讨论内容
### 1. [议程项1]
[讨论内容]

**结论:**
- [结论1]

## 会议决议
- ✅ [决议1]

## 待办事项 (Action Items)

| # | 事项 | 负责人 | 截止日期 | 状态 |
|---|------|--------|----------|------|
| 1 | [事项] | @姓名 | YYYY-MM-DD | ⬜ 待办 |

## 下次会议
- **时间:** [日期时间]
- **待确认议题:** [议题列表]
```

### Workflows

1. **创建会议记录**: 确认字段 → `mkdir -p` 目录 → `write_file` 生成 `YYYY-MM-DD_简短主题.md` → 更新 `会议索引.md`
2. **记录讨论**: 识别当前会议文件 → 添加内容到对应章节 → 用 `patch` 或 Python 插入
3. **完成并归档**: 检查完整性 → 提示缺失章节 → 更新索引状态
4. **查找历史会议**: `grep -rl "关键词" "$MEETING_DIR"` 或 `ls -t` 按日期查找
5. **更新待办状态**: 用 `patch` 将 `⬜ 待办` 改为 `✅ 已完成` / `🔄 进行中` / `❌ 已取消`

### 索引文件格式

`会议索引.md`:
```markdown
| 日期 | 主题 | 文件 | 状态 |
|------|------|------|------|
| 2026-04-30 | 产品评审 | [2026-04-30_产品评审.md](./2026-04-30_产品评审.md) | ✅ 已完成 |
```

### 约定

- 文件名: `YYYY-MM-DD_主题关键词.md`
- 日期格式: 始终 `YYYY-MM-DD`
- 参会人: Action items 中用 @ 前缀标识责任人
- 状态值: `📝 待完成` | `✅ 已完成` | `📅 已归档`
- 编码: UTF-8

---

## Conventions

- **Candidate name matching:** Always search with both Chinese characters and pinyin variants
- **Resume file types:** Support `.pdf`, `.docx`, `.doc`
- **Status values:** `简历待归档` | `面试中` | `待发Offer` | `待入职` | `已入职` | `已淘汰`
- **File encoding:** Always UTF-8 for all markdown files
- **Paths:** Always quote paths with spaces — use `"/path/with spaces/"` syntax

---

## Important Safeguards

### Always verify current date before writing dates
Run `date "+%Y-%m-%d"` before every file write that involves dates. System clocks vary between environments — never assume the date.

### Safe patching — anchor on unique context
When updating a section in `面试时间表.md` (which has multiple candidates in one file), always anchor patches on the candidate's name section header. For example, instead of just patching `| 一面 | 2026-04-23 |`, include the surrounding `## 顾婧` header so the patch is unambiguous and won't accidentally affect another candidate's row.

Wrong (matches all rows with that date):
```
old_string = "| 一面 | 2026-04-23 |"
```
Right (anchored to one candidate):
```
old_string = "## 顾婧\n\n| 轮次 | 日期 | ...\n| 一面 | 2026-04-23 |"
```

### Never fabricate or infer information
Only record what the user explicitly tells you. Do not invent names (candidates, interviewers), dates, times, formats, or any other details — even if they seem like reasonable guesses. If the user did not provide it, mark it as `[待补充]`. This applies to:
- Interviewer names
- Interview dates, times, formats
- Candidate background or resume content
- Interview feedback or evaluations
- Any relationship between candidates and interviewers

When in doubt, leave it blank rather than fill it in.

### Resume PDF extraction
If `pdftotext` is unavailable, use `pypdf`:
```python
import pypdf
reader = pypdf.PdfReader("/path/to/resume.pdf")
for i, page in enumerate(reader.pages):
    print(f"--- Page {i+1} ---")
    print(page.extract_text())
```
Install with: `pip install pypdf -q`

Note: Some PDFs may have font encoding issues in extracted text — key data (education, experience, projects) usually remains readable even if decorative text is garbled.
- **Confirmation:** Always confirm before moving files or overwriting existing archive entries