---
name: meeting-record
description: Record general meeting notes, generate minutes, track action items, and manage meeting archives for WarpDriveAI.
---

# Meeting Record Skill

Records meeting content as structured markdown notes, tracks action items and decisions, and archives meeting records for future reference.

## File Paths

```bash
MEETING_DIR="/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record"
INDEX_FILE="/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record/会议索引.md"
```

All paths contain spaces — **always quote them**.

## Meeting Note Template

Each meeting is saved as a separate markdown file named `YYYY-MM-DD_简短主题.md`:

```markdown
# [YYYY-MM-DD] 会议主题

## 基本信息
- **日期:** YYYY-MM-DD (星期X)
- **时间:** HH:MM - HH:MM
- **地点/形式:** 线下/线上(腾讯会议/Zoom等)
- **参会人:** 张三, 李四, 王五...
- **主持人:** [姓名]
- **记录人:** [姓名]

## 会议议程
1. [议程项1]
2. [议程项2]
3. [议程项3]

## 讨论内容

### 1. [议程项1]
[详细讨论内容]

**结论:**
- [结论1]
- [结论2]

### 2. [议程项2]
...

## 会议决议
- ✅ [决议1]
- ✅ [决议2]

## 待办事项 (Action Items)

| # | 事项 | 负责人 | 截止日期 | 状态 |
|---|------|--------|----------|------|
| 1 | [事项描述] | @姓名 | YYYY-MM-DD | ⬜ 待办 |
| 2 | [事项描述] | @姓名 | YYYY-MM-DD | ⬜ 待办 |

## 下次会议
- **时间:** [日期时间]
- **待确认议题:** [议题列表]

## 备注
[其他补充信息]
```

---

## Workflows

### Workflow 1: 创建会议记录 (Create Meeting Record)

**Trigger:** User says "记录会议" / "create meeting record" / "会议纪要"

**Steps:**

1. Ask for or confirm the following fields:
   - 会议主题 (meeting topic)
   - 日期 (default: today via `date "+%Y-%m-%d"`)
   - 时间范围
   - 地点/形式
   - 参会人列表
   - 主持人
   - 会议议程

2. Create the directory if it doesn't exist:
```bash
mkdir -p "/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record"
```

3. Generate the markdown file using `write_file`:
   - File name: `YYYY-MM-DD_简短主题.md` (e.g., `2026-04-30_产品评审.md`)
   - Use the template above, filled with provided info
   - Leave discussion sections empty as placeholders

4. Update the index file:
   - If `会议索引.md` doesn't exist, create it
   - Append a new entry with date, topic, and file link

---

### Workflow 2: 记录会议讨论 (Record Discussion During Meeting)

**Trigger:** User says "记录讨论" / "add notes" / "记一下" during a meeting

**Steps:**

1. Identify which meeting file is active (most recently created/modified in the meeting directory)
2. Ask the user which section to add to (讨论内容 / 决议 / 待办事项 / 备注)
3. Append content to the appropriate section using `patch` or `execute_code` with targeted string insertion

For adding action items efficiently:
```python
import re
from datetime import date

meeting_file = "/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record/2026-04-30_产品评审.md"

with open(meeting_file, "r", encoding="utf-8") as f:
    content = f.read()

# Find the action items table and add a new row
new_item = "| 3 | 完成竞品分析报告 | @张三 | 2026-05-07 | ⬜ 待办 |\n"

# Insert before the "## 下次会议" section
content = content.replace("## 下次会议", new_item + "\n## 下次会议")

with open(meeting_file, "w", encoding="utf-8") as f:
    f.write(content)
```

---

### Workflow 3: 完成并归档会议记录 (Finalize & Archive)

**Trigger:** User says "完成会议记录" / "finalize" / "发布会议纪要"

**Steps:**

1. Read the meeting file and check for completeness
2. Prompt for missing sections:
   - 结论 (conclusions)
   - 待办事项 (action items with owners)
   - 下次会议时间
3. Fill in any gaps by asking the user
4. Update the `会议索引.md` to mark as 已完成
5. Optionally output a summary for sharing

---

### Workflow 4: 查找历史会议 (Search Past Meetings)

**Trigger:** User asks "查一下上次的会议" / "找关于XX的会议" / "search meetings"

**Steps:**

1. Search meeting files by topic keyword:
```bash
grep -rl "关键词" "/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record/" --include="*.md" 2>/dev/null
```

2. Or search by attendee:
```bash
grep -rl "参会人.*张三" "/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record/" --include="*.md" 2>/dev/null
```

3. Or list by date range:
```bash
ls -t "/mnt/c/Users/liuch/My Documents/warpdriveai/meeting_record/"*.md 2>/dev/null | head -10
```

4. Read the matching file(s) and present a summary

---

### Workflow 5: 更新待办事项状态 (Update Action Items)

**Trigger:** User says "更新待办" / "mark action item done" / "XXX完成了"

**Steps:**

1. Find the meeting file containing the action item
2. Search for the action item text in the table
3. Update the status column:
   - ⬜ 待办 → ✅ 已完成
   - ⬜ 待办 → 🔄 进行中
   - ⬜ 待办 → ❌ 已取消

Use `patch` with the old/new string anchored to unique context:
```
old_string: "| 1 | 完成竞品分析报告 | @张三 | 2026-05-07 | ⬜ 待办 |"
new_string: "| 1 | 完成竞品分析报告 | @张三 | 2026-05-07 | ✅ 已完成 |"
```

---

## 会议索引文件 Format

`会议索引.md` serves as a master index of all meetings:

```markdown
# 会议索引

| 日期 | 主题 | 文件 | 状态 |
|------|------|------|------|
| 2026-04-30 | 产品评审 | [2026-04-30_产品评审.md](./2026-04-30_产品评审.md) | ✅ 已完成 |
| 2026-04-28 | 周例会 | [2026-04-28_周例会.md](./2026-04-28_周例会.md) | 📝 待完成 |
```

---

## Conventions

- **File naming:** `YYYY-MM-DD_主题关键词.md` — consistent, sortable, searchable
- **Date format:** Always `YYYY-MM-DD` throughout the file (front matter, headings, tables)
- **Attendees:** List with @ prefix in action items to identify responsible persons
- **Status values:** `📝 待完成` | `✅ 已完成` | `📅 已归档`
- **Encoding:** Always UTF-8
- **Paths:** Always quote paths with spaces

## Related Skills

- **interview** — for candidate interview records (separate workflow)
