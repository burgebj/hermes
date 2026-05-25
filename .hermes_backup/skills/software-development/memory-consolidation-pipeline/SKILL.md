---
name: memory-consolidation-pipeline
description: "Design and implement a periodic background pipeline (a 'dream cycle') that scans new conversation sessions, extracts important signals, merges them into MEMORY.md/USER.md with conflict resolution, budget management, and relative-to-absolute date conversion."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [memory, consolidation, pipeline, dream-cycle, background, cron]
    related_skills: [writing-plans, hermes-agent, cron-job-troubleshooting, codex-session]
    references:
      - references/codex-session.md: Codex session continuity details (absorbed from standalone codex-session skill)
---

# Memory Consolidation Pipeline (Dream Cycle)

## Overview

A periodic background pipeline that consolidates new conversation sessions into durable memory (MEMORY.md / USER.md). Modeled after the biological "dream" process — offline replay of recent experience to extract and integrate important signals while discarding noise.

## When to Use

Use this skill when the user wants:
- A background agent that "sleeps" and reviews its day
- Periodic memory consolidation / summarization
- A cron job that processes conversation sessions offline
- Automatic extraction of important facts from chat history
- Budget management for MEMORY.md (char limit overflow)
- Conflict resolution between existing memory entries and new signals
- Conversion of relative dates ("yesterday", "last week") to absolute dates

## Architecture

The pipeline has 4 mandatory phases executed sequentially:

```
Phase 1: Calibrate  ─►  Phase 2: Collect  ─►  Phase 3: Merge  ─►  Phase 4: Index
     │                      │                       │                     │
     ▼                      ▼                       ▼                     ▼
  Scan existing         Pre-filter + LLM        Resolve dates,          Final write,
  memory files +        extract signals,        contradictions,         state file
  find new sessions     detect conflicts        budget mgmt             update
```

## Key System Details

### Memory File Format (`~/.hermes/memories/`)

```
MEMORY.md     — agent's personal notes (default: 2200 char limit)
USER.md       — user profile (default: 1375 char limit)

Entry delimiter: § (section sign, "\n§\n")
Format: plain text entries separated by §
Atomic write: temp file + os.replace() for race-free updates
```

### Session File Format (`~/.hermes/sessions/`)

```json
{
  "session_id": "20260501_090239_fd11ef",
  "session_start": "2026-05-01T09:02:39.027358",
  "last_updated": "2026-05-01T09:04:50.336711",
  "platform": "cli|weixin|cron|...",
  "model": "model-name",
  "messages": [
    {"role": "user|assistant|tool", "content": "...", "tool_calls": [...]}
  ]
}
```

### State Tracking

Use `.dream_state.json` in the `memories/` directory:
```json
{
  "last_processed_session": "20260501_211739_2439a368",
  "last_run": "2026-05-01T21:30:00+08:00",
  "total_runs": 12,
  "phases_executed": ["calibrate", "collect", "merge", "index"],
  "stats_summary": {
    "sessions_scanned": 3,
    "fragments_collected": 2,
    "entries_added": 1,
    "entries_removed": 0,
    "contradictions_found": 0
  }
}
```

## Implementation Guide

### Phase 1: Calibrate

**Goal:** Read existing MEMORY.md/USER.md, build dedup index, find unprocessed sessions.

Steps:
1. Read both files and split by `"\n§\n"` into entry lists
2. Build a `known_index = {normalized_key: entry_text}` for fast dedup lookup
3. Normalization: lowercase + strip whitespace + collapse runs of spaces
4. Read `.dream_state.json` to get `last_processed_session`
5. Scan `~/.hermes/sessions/session_*.json` sorted by mtime
6. Skip sessions older than or equal to `last_processed_session`
7. **First run guard:** if no `last_processed_session`, cap at 7 days or 20 sessions

### Critical: Skip Cron Sessions

Before scanning sessions, **skip all sessions with `platform == "cron"`**. Cron sessions are tool execution dumps from scheduled tasks, not conversational exchanges. They are large (often >500KB), full of JSON tool outputs, and never contain user preferences or corrections worth extracting.

### Phase 2: Collect

**Goal:** Find important signals in new sessions, using regex pre-filter then LLM refinement.

#### Step A: Regex Pre-filter (Cheap, Fast)

Scan user messages for high-value patterns:

| Pattern | Category |
|---------|----------|
| `(错了\|不是\|不对\|错误\|纠正\|正确.*是\|实际.*是)` | correction |
| `(我喜欢\|我习惯\|我偏好\|prefer\|不要\|需要\|要求\|建议)` | preference |
| `(配置\|安装\|设置\|config\|setup\|环境\|版本\|路径\|端口)` | config |
| `(记住\|保存\|存到\|写入\|memory\|技能\|skill\|记下来)` | memory_signal |
| `(昨天\|今天\|明天\|上周\|last week\|next month)` | temporal |

On match, collect context: 2 messages before, 2 after, truncate each to ≤600 chars.

#### Step B: LLM Refinement (Expensive, Targeted)

For each candidate context, call the LLM with this prompt structure:

```
你是一个记忆精炼助手。分析以下对话片段，判断是否有值得永久记住的信息。

已知现有记忆：
{known_entries_truncated_2000chars}

对话片段：
{context_json}

以 JSON 格式回答（只输出 JSON）：
{
  "is_important": true/false,
  "target": "memory" 或 "user",
  "extracted_fact": "规范化的陈述句",
  "confidence": "high/medium/low",
  "contradicts_entry": "如果有矛盾，写被矛盾的旧条目原文（否则 null）",
  "contradiction_type": "correction/update/ambiguous/null",
  "reason": "为什么这个信息重要"
}
```

LLM call method: use `hermes chat -q` or direct HTTP POST to the configured API.

#### LLM Call Budget and Incremental Processing

Implement a hard cap on total LLM calls per run. Without this, the first run over 121 sessions with 30 candidates can take hours.

```python
MAX_LLM_CALLS = 30  # configurable, prevents runaway costs/slowdowns
```

**Critical: Track `last_scanned_session_id` correctly when hitting the cap.**

When `llm_calls >= MAX_LLM_CALLS` is reached mid-way, you must break out of the outer session loop too (not just the inner candidate loop), and set `last_processed_session` to the **last fully-scanned session** (the one whose LLM calls completed), NOT the very last session file.

```python
# In phase2_collect():
llm_calls = 0
last_scanned_session_id = None  # tracks the last session we finished scanning
llm_cap_hit = False

for spath in pending_sessions:
    # ... parse session, regex filter ...
    
    # LLM refinement loop
    for cand in candidates[:3]:
        if llm_calls >= MAX_LLM_CALLS:
            llm_cap_hit = True
            break       # break inner loop
        llm_calls += 1
        fact = llm.extract_fact(...)
        # ...
    
    if llm_cap_hit:
        print("⚠️ LLM cap hit, will resume next run")
        break          # ← BREAK OUTER LOOP too! Otherwise it wastefully scans remaining sessions

    # Only record checkpoint if session was fully processed
    last_scanned_session_id = data.get("session_id", ...)

# After the loop:
return all_fragments, last_scanned_session_id, llm_cap_hit
```

**In main(), only update last_processed_session if LLM cap wasn't hit:**

```python
fragments, last_scanned_id, llm_cap_hit = phase2_collect(...)

if llm_cap_hit and last_scanned_id:
    state["last_processed_session"] = last_scanned_id
elif not llm_cap_hit and ctx.get("last_session_id"):
    state["last_processed_session"] = ctx["last_session_id"]
```

Also ensure `phase4_index()` does NOT overwrite `last_processed_session` — that should be done exclusively by main(). Remove this line from phase4_index:

```python
# REMOVE from phase4_index:
if ctx.get("last_session_id"):
    state["last_processed_session"] = ctx["last_session_id"]
```

### Pitfall: `last_processed_session` Overwritten by `phase4_index`

The `main()` function handles `last_processed_session` carefully (only sets it when the LLM cap wasn't hit). But if `phase4_index()` also sets `last_processed_session`, it will **overwrite** `main()`'s smarter logic.

**Remove this from `phase4_index()`:**

```python
# REMOVE these lines from phase4_index():
if ctx.get("last_session_id"):
    state["last_processed_session"] = ctx["last_session_id"]
```

Instead, let `main()` handle it exclusively:

```python
# In main(), after phase2_collect:
fragments, last_scanned_id, llm_cap_hit = phase2_collect(...)

if llm_cap_hit and last_scanned_id:
    state["last_processed_session"] = last_scanned_id
elif not llm_cap_hit and ctx.get("last_session_id"):
    state["last_processed_session"] = ctx["last_session_id"]
```

### Pitfall: CJK Char Count vs Byte Count Confusion

When inspecting the script's output, you may see a discrepancy:

```
# What the code reports:
Memory entries: 14 (1737 chars)   ← 1776 - some overhead

# What wc -c shows:
2838 MEMORY.md                      ← byte count, NOT char count
```

CJK characters (Chinese, Japanese, Korean) are **3-4 bytes each** in UTF-8. A file with 1776 CJK characters is **~2838 bytes**. This is expected and correct — the 2200 limit is measured in **characters**, not bytes.

Don't panic when `wc -c` shows values exceeding the limit. Always use `len(content)` (Python char count) for budget enforcement.

### Session ID Format Mismatch

Session filenames use the format `session_20260501_211739_2439a368.json` but the internal `session_id` field is `20260501_211739_2439a368` (no `session_` prefix). When tracking progress and filtering, **normalize by stripping the `session_` prefix**:

```python
last_id_clean = last_session_id.replace("session_", "")
```

Check both **filename** (fast) and **JSON `session_id` field** (accurate) when finding the cutoff:

```python
for s in sorted_sessions:
    # Quick filename check
    if last_id_clean in s.name:
        found = True
        continue
    # Accurate JSON check (handles edge cases)
    if not found:
        with open(s, 'rb') as f:
            chunk = f.read(2048)
        m = re.search(r'"session_id"\s*:\s*"([^"]+)"', chunk.decode())
        if m and m.group(1) == last_id_clean:
            found = True
            continue
    if found:
        newer.append(s)
```

### Pitfall: phase2_collect Return Signature Mismatch

When `phase2_collect` finds no pending sessions, it returns `[]` (a list). But the caller `main()` was refactored to expect a 3-tuple `(fragments, last_scanned_id, llm_cap_hit)`. **This will crash with a `cannot unpack non-iterable` error.**

Always return a consistent 3-tuple:

```python
if not pending_sessions:
    return [], None, False  # NOT `return []`
```

Also update the function's return type annotation:

```python
def phase2_collect(...) -> Tuple[List[Dict], Optional[str], bool]:
```

### Pitfall: LLM Cap Must Break Both Loops

When `llm_calls >= MAX_LLM_CALLS`, you must `break` **both** the inner `for cand` loop and the outer `for spath` loop. Breaking only the inner loop leaves the outer loop scanning hundreds of remaining sessions wastefully:

```python
for spath in pending_sessions:
    # ... parse, regex filter ...
    for cand in candidates[:3]:
        if llm_calls >= MAX_LLM_CALLS:
            llm_cap_hit = True
            break       # breaks inner loop
    
    if llm_cap_hit:
        print("⚠️ Cap hit, will resume next run")
        break            # ← MUST ALSO BREAK THE OUTER LOOP
```

### Pitfall: Track `last_scanned_session_id` After LLM Loop, Not Before

If you set `last_scanned_session_id` **before** the LLM loop, and the LLM cap is hit mid-session, the state file will record this session as fully processed — causing its remaining candidates to be lost forever.

```python
# WRONG: recorded even when cap hits mid-session
last_scanned_session_id = data.get("session_id")
for cand in candidates[:3]:  # cap might hit here
    ...

# RIGHT: only record after LLM work is complete
for cand in candidates[:3]:
    ...

if llm_cap_hit:
    break  # don't record; session will be re-scanned next run

# Only reach here if session was fully processed
last_scanned_session_id = data.get("session_id", ...)
```

### Pitfall: Session ID Format Mismatch

Session filenames use the format `session_20260501_211739_2439a368.json` but the internal `session_id` field is `20260501_211739_2439a368` (no `session_` prefix). When tracking progress and filtering, **normalize by stripping the `session_` prefix**:

```python
last_id_clean = last_session_id.replace("session_\", "")
```

Check both **filename** (fast) and **JSON `session_id` field** (accurate) when finding the cutoff:

```python
for s in sorted_sessions:
    # Quick filename check
    if last_id_clean in s.name:
        found = True
        continue
    # Accurate JSON check (handles edge cases)
    if not found:
        with open(s, 'rb') as f:
            chunk = f.read(2048)
        m = re.search(r'\"session_id\"\s*:\s*\"([^\"]+)\"', chunk.decode())
        if m and m.group(1) == last_id_clean:
            found = True
            continue  # ← continue MUST go here inside the if
    if found:
        newer.append(s)
```

Contradiction types:
- **correction**: user explicitly corrected something → old entry should be replaced
- **update**: new information supersedes old → old entry should be replaced with updated version
- **ambiguous**: unclear which is correct → keep both with a note

### Phase 3: Merge

**Goal:** Merge new fragments into memory files with date resolution, conflict handling, and budget enforcement.

#### Relative Date Resolution

```python
RELATIVE_DATE_PATTERNS = [
    (r'昨[天日]|yesterday', -1),
    (r'今[天日]|today', 0),
    (r'前[天日]', -2),
    (r'明[天日]|tomorrow', +1),
    (r'上[周个]|last week', -7),
    (r'下[周个]|next week', +7),
    (r'上个?月|last month', -30),
    (r'下个?月|next month', +30),
    (r'刚[才]', 0),
]
```

Use the session's `session_start` timestamp as the reference point.

#### Merge Logic

1. For each fragment (sorted by confidence, high first):
   - Skip if already in `known_index` (dedup)
   - Skip if `confidence == "low"` (optionally)
   - If `contradiction_type = "correction"|"update"` → replace old entry
   - If `contradiction_type = "ambiguous"` → add with append note
   - Otherwise → add as new entry
2. After all merges, run budget enforcement

#### Post-Merge: Near-Duplicate Dedup

After merging all fragments, run a **near-duplicate merging pass**. Without this, entries like these accumulate:

```
面试管理技能已创建，包含简历归档、简历摘要、面试时间表、入职时间表、候选人档案五个核心功能
面试管理技能包含5个核心功能：简历归档、简历摘要、面试时间表、入职时间表、候选人档案，并定义了相关文件路径
```

Use Jaccard similarity on word sets with a threshold of ~0.50:

```python
def merge_near_duplicates(entries: List[str]) -> List[str]:
    """Merge entries with >50% word overlap by keeping the longer entry."""
    if len(entries) < 2:
        return entries
    result, merged = [], set()
    
    for i in range(len(entries)):
        if i in merged:
            continue
        words_i = set(re.findall(r'\w+', entries[i].lower()))
        if len(words_i) < 3:
            result.append(entries[i])
            continue
        
        best_j, best_overlap = None, 0
        for j in range(i + 1, len(entries)):
            if j in merged:
                continue
            words_j = set(re.findall(r'\w+', entries[j].lower()))
            if len(words_j) < 3:
                continue
            intersection = words_i & words_j
            union = words_i | words_j
            overlap = len(intersection) / len(union) if union else 0
            if overlap > 0.50 and overlap > best_overlap:
                best_overlap, best_j = overlap, j
        
        if best_j is not None:
            # Keep longer entry
            result.append(max(entries[i], entries[best_j], key=len))
            merged.update([i, best_j])
        else:
            result.append(entries[i])
    
    return result
```

This should run **before** budget enforcement, so merged entries occupy less space.

#### Character Count vs Byte Count

CJK characters (Chinese, Japanese, Korean) are multi-byte in UTF-8. A memory file may show:
- **1776 characters** (what the code counts)
- **2838 bytes** (what `wc -c` reports)

The limits (2200 for MEMORY.md, 1375 for USER.md) are **character counts**, not byte counts. This is correct behavior—CJK-heavy entries use fewer characters but the same budget.

#### Budget Enforcement

**Use the full limit (not 95%).** The original design used `limit * 0.92` as the stop condition, which caused entries to be under-budget on disk but still reported as over-budget. Always trim until `total <= limit`:

```python
while len(separator.join(entries)) > limit and len(entries) > 1:
    entries.pop(0)  # remove lowest-priority entry
```

Also set `_find_replaceable` Jaccard threshold to **0.35** (not 0.50) to catch more similar entries during merge and reduce the need for budget eviction.

**Pitfall: LLM-extracted facts can contain near-duplicates.** Three fragments like "面试管理技能已创建，包含5个功能" from different sessions all pass the dedup check because they use slightly different wording. This is why a **near-duplicate merging pass** must run after all fragments are merged but before budget enforcement.

#### Character Count vs Byte Count

CJK characters (Chinese, Japanese, Korean) are multi-byte in UTF-8. A memory file may show:
- **1776 characters** (what the code counts)
- **2838 bytes** (what `wc -c` reports)

The limits (2200 for MEMORY.md, 1375 for USER.md) are **character counts**, not byte counts. This is correct behavior—CJK-heavy entries use fewer characters but the same budget.
def write_entries(path, entries):
    """Atomic write via temp file + rename (matching Hermes convention)."""
    content = "\n§\n".join(entries) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.rename(path)
```

#### Cross-file Conflict Resolution

Check if the same fact exists in both MEMORY.md and USER.md with different wording:
- USER.md takes priority for user-specific facts
- MEMORY.md keeps generalized versions
- If same fact is in both, keep only the more authoritative one

#### Output Summary

```
🌙 Dream Cycle Complete

📊 Stats: sessions_scanned=3, entries_added=1, entries_removed=0, contradictions=0
📝 Added: "User requires xhigh reasoning effort globally"
🗑️ Removed: (none)
💾 Memory: 2147/2200 → 2152/2200 (97%)
💾 User:   674/1375 → 674/1375 (49%)
```

## Cron Setup

```yaml
# Register via cronjob tool
schedule: "0 3 * * *"        # 3:00 AM daily
name: dream-cycle
prompt: |
  执行做梦精炼流水线：运行 ~/.hermes/scripts/dream_cycle.py，
  扫描新 session，提取重要信息，合并到 MEMORY.md/USER.md，
  解决矛盾，清理过时条目。静默执行，只报告结果摘要。
enabled_toolsets: [terminal, file]
deliver: local              # Use 'local' for silent operation (no weixin/telegram notify)
                            # Use 'origin' if you want results pushed to your messaging platform
```

### Maintenance-Only Runs

Even when there are no new sessions, the script should still run a **maintenance pass** that:
1. Runs `_merge_near_duplicates()` on existing entries
2. Runs `_enforce_budget()` to trim if memory has crept over limit

This keeps memory files tidy even without new session data, and ensures the pipeline is always active.

## Script Location

Place the script at: `~/.hermes/scripts/dream_cycle.py`

Run from cron context:
```bash
cd /home/jianliu/work/hermes-agent && source venv/bin/activate && python ~/.hermes/scripts/dream_cycle.py
```

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM calls too slow for many sessions | Strict pre-filter; cap at 20 sessions/first run; 60s timeout per LLM call |
| Memory budget overflow (97% full) | Must include budget enforcement; prefer replacement over adds |
| File corruption from concurrent writes | Atomic temp+rename; fcntl file lock on state file; session files are read-only |
| Accidental deletion of important memories | Only drop entries with stale keywords; never drop correction entries |
| LLM unavailable during cron window | Reserve final merge to write phase; skip LLM if API returns error; try again next cycle |
| First run processes too many sessions | Cap at last 7 days or 20 sessions, whichever is smaller |

## Verification

- [ ] Script runs without errors end-to-end
- [ ] State file is created and updated correctly
- [ ] Second run only sees new sessions (idempotent)
- [ ] Budget enforcement triggers when near limit
- [ ] Relative dates are converted to absolute
- [ ] Contradictory entries are properly handled
- [ ] Atomic writes survive kill -9 mid-write
- [ ] Cron job registers and fires at scheduled time
