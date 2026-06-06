---
name: skillhub-install
description: Install skills from ClawHub and SkillHub marketplaces into Hermes. Downloads zip packages, converts SKILL.md format, maps categories, and handles dependencies.
tags: [skills, marketplace, clawhub, skillhub, install]
---
name: skillhub-install
description: Install skills from SkillHub (skillhub.cn) marketplace into Hermes. Downloads zip packages, converts SKILL.md format, maps categories, and handles dependencies.
tags: [skills, marketplace, skillhub, install]
---

# SkillHub Install

Install skills from SkillHub (skillhub.cn) into Hermes. Handles the full pipeline: discover, download, convert, install.

> **注意**: 统一使用 SkillHub (skillhub.cn) 作为唯一技能来源，不再从 ClawHub 下载。

## API 信息

- **API 基础 URL**: `https://api.skillhub.cn`
- **技能详情**: `GET /api/v1/skills/{slug}`
- **下载 ZIP**: `GET /api/v1/download?slug={slug}`
- **技能列表**: `GET /api/skills?page=1&pageSize=20&keyword=xxx&category=xxx`
- **网站地址**: https://skillhub.cn

## Workflow

### 1. Discover Skills

Browse or search SkillHub:

```
# Browse all skills
browser_navigate: https://skillhub.cn/

# Search skills
browser_navigate: https://skillhub.cn/skills?keyword=关键词

# View skill detail page
browser_navigate: https://skillhub.cn/skills/{slug}
```

### 2. Download Skill Package

Direct download via API (no browser needed):

```python
import urllib.request

slug = "baidu-search"  # skill slug from URL
url = f"https://api.skillhub.cn/api/v1/download?slug={slug}"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=30)
# resp.read() returns a zip file
```

### 3. Get Skill Details (optional)

```python
url = f"https://api.skillhub.cn/api/v1/skills/{slug}"
# Returns JSON with: name, slug, displayName, summary, version, source, stats, etc.
```

### 4. Inspect Package Structure

Extract and inspect the zip:
```python
import zipfile, os, json

tmpdir = "/tmp/skill-install"
with zipfile.ZipFile(zip_path) as z:
    z.extractall(tmpdir)
    for name in z.namelist():
        print(name)
    skill_md = z.read("SKILL.md").decode("utf-8")
    if "_meta.json" in z.namelist():
        meta = json.loads(z.read("_meta.json"))
```

### 5. Convert SKILL.md

OpenClaw frontmatter → Hermes frontmatter conversion:
```python
import re

def convert_frontmatter(md_content):
    fm_match = re.match(r'^---\n(.*?)\n---', md_content, re.DOTALL)
    if not fm_match:
        return md_content

    old_fm = fm_match.group(1)
    name_match = re.search(r'name:\s*(.+)', old_fm)
    desc_match = re.search(r'description:\s*(.+)', old_fm)

    tags = []
    meta_match = re.search(r'metadata.*?"env".*?\[(.*?)\]', old_fm, re.DOTALL)
    if meta_match:
        env_vars = [v.strip().strip('"').strip("'") for v in meta_match.group(1).split(',')]
        tags.extend([v.lower().replace('_', '-') for v in env_vars[:3]])

    bins_match = re.search(r'"bins".*?\[(.*?)\]', old_fm, re.DOTALL)
    if bins_match:
        bins = [v.strip().strip('"').strip("'") for v in bins_match.group(1).split(',')]
        tags.extend([f"requires-{b.lower()}" for b in bins[:2]])

    name = name_match.group(1).strip() if name_match else "unknown"
    desc = desc_match.group(1).strip() if desc_match else ""
    desc = re.sub(r'OpenClaw', 'Hermes', desc)

    new_fm = f'---\nname: {name}\ndescription: {desc}\ntags: [{", ".join(tags)}]\n---'
    body = md_content[fm_match.end():]
    body = re.sub(r'OpenClaw', 'Hermes', body)
    body = re.sub(r'openclaw skills install', 'skill_manage', body)
    return new_fm + body
```

### 6. Determine Category

Map skill to Hermes category:

| Keyword Pattern | Hermes Category |
|----------------|-----------------|
| web, search, baidu, google | productivity |
| github, git, code, dev | github / software-development |
| mlops, ml, train, model | mlops |
| creative, art, image, video | creative |
| data, analysis, jupyter | data-science |
| email, mail | email |
| game, minecraft | gaming |
| smart-home, hue, light | smart-home |
| social, twitter, xurl | social-media |
| note, obsidian | note-taking |
| research, paper, arxiv | research |
| Otherwise | productivity (default) |

### 7. Install to Hermes

Use the skill_manage tool:
```
skill_manage:
  action: create (new) or edit (existing)
  name: <converted-name>
  content: <converted-SKILL.md>
  category: <mapped-category>

skill_manage:
  action: write_file
  name: <skill-name>
  file_path: scripts/<script-name>
  file_content: <script-content>
```

### 8. Handle Dependencies

Check for required tools/env vars:
```python
for bin in meta.get("requires", {}).get("bins", []):
    result = terminal(f"which {bin}")
    if result["exit_code"] != 0:
        print(f"Missing binary: {bin} — please install it")

for env in meta.get("requires", {}).get("env", []):
    if not os.getenv(env):
        print(f"Missing env var: {env} — please set it")
```

## Complete Installation Flow

When user says "install <skill> from SkillHub":

1. **Get slug** from user or SkillHub URL (e.g., `baidu-search`)
2. **Download** zip from `https://api.skillhub.cn/api/v1/download?slug={slug}`
3. **Extract** to `/tmp/skill-install/`
4. **Read** `SKILL.md` and `_meta.json`
5. **Convert** frontmatter format
6. **Determine** Hermes category
7. **Create** the skill via `skill_manage(action='create')`
8. **Write** each script file via `skill_manage(action='write_file')`
9. **Check** dependencies (bins, env vars)
10. **Report** success/failure

## Important Notes

- **统一来源**: 所有技能从 SkillHub (skillhub.cn) 下载，不再使用 ClawHub。
- **直接下载**: 使用 API 端点直接下载 ZIP，无需浏览器操作。
- **Slug 获取**: 从 SkillHub 页面 URL 中提取 slug，如 `skillhub.cn/skills/baidu-search` → `baidu-search`。
- **Script compatibility**: OpenClaw scripts using `requests` library work fine in Hermes. Scripts using OpenClaw-specific tools need manual adaptation.
- **Category mapping**: When in doubt, use `productivity` as the default category.
- **Name conflicts**: If a skill with the same name already exists in Hermes, ask the user before overwriting.
- **Security**: Always inspect `SKILL.md` and scripts before installing. Check for suspicious network calls or file operations.
- **Size limit**: Hermes skills over 8000 chars in SKILL.md may be truncated. Keep the converted SKILL.md concise.
