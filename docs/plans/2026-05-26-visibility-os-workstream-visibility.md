# Visibility OS Workstream Visibility Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make Visibility OS clearly show what agentic opportunities exist, what workstreams agents are currently working on, what they have already worked on, where each workstream is in the lane lifecycle, and what code or review changes the agent proposes before any external GitHub side effect.

**Architecture:** Add a first-class `workstreams` model that ties together an opportunity, its lane action, agent session/run metadata, progress events, produced artifacts, reviews, proposed PRs, and final GitHub side effects. Keep `action_queue` as the approval/execution state machine, but stop using it as the only user-visible progress surface. Add API endpoints that return workstream timelines and artifact summaries, then upgrade the dashboard from a feed of cards into a workbench with Kanban/status views, live-ish progress, and human-friendly diff/review visualisations.

**Tech Stack:** Python/FastAPI plugin backend, SQLite profile-scoped storage, existing `actions`, `audit_log`, `opportunities`, `executors/hermes.py`, GitHub CLI integration, dashboard `dist/index.js` React bundle using Hermes plugin SDK.

---

## Product principles

- One opportunity equals one trackable workstream once an agent starts acting on it.
- The dashboard must answer four questions at a glance:
  1. What is available for agents to work on?
  2. What is currently being worked on?
  3. What has the agent already done?
  4. What does Barney need to approve, reject, or inspect?
- Internal agent steps should be visible without requiring extra user clicks.
- External side effects remain separately approved: push branch, post review/comment, merge, deploy.
- Proposed changes should be understandable without opening a terminal.
- PR review/audit output should feel like a review workspace, not raw JSON.

---

## Target lifecycle model

Use these workstream stages consistently in backend and UI:

1. `opportunity_open`
   - Opportunity exists, no agent lane has started.
2. `queued`
   - A lane action has been created but not started.
3. `agent_starting`
   - Hermes process/session is launching.
4. `gathering_context`
   - Agent is reading issue/PR/CI evidence and repo context.
5. `editing`
   - Agent is making local code/docs/test changes.
6. `verifying`
   - Agent is running tests/checks.
7. `self_auditing`
   - Agent is reviewing its own diff.
8. `independent_reviewing`
   - Fresh session review is running with no fix context.
9. `ready_for_push`
   - Proposed PR branch passed gates and waits for Barney's push approval.
10. `push_queued`
    - Push action exists but is not executed yet.
11. `pushed`
    - Branch/PR has been pushed/opened.
12. `review_ready`
    - PR audit/review findings are ready for Barney.
13. `comment_queued`
    - Review/comment action exists but is not posted yet.
14. `completed`
    - Workstream reached its intended terminal state.
15. `failed`
    - Lane failed with useful evidence and retry guidance.
16. `cancelled`
    - Human or system cancelled it.

---

## Data model tasks

### Task 1: Add workstream tables

**Objective:** Persist agentic work as first-class trackable workstreams instead of inferring everything from actions.

**Files:**
- Modify: `plugins/visibility_os/core/db.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Schema additions:**

```sql
CREATE TABLE IF NOT EXISTS workstreams (
    id TEXT PRIMARY KEY,
    opportunity_id TEXT REFERENCES opportunities(id),
    root_action_id TEXT REFERENCES action_queue(id),
    lane_kind TEXT NOT NULL,
    title TEXT NOT NULL,
    repo TEXT,
    source_url TEXT,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    completed_at TEXT,
    agent_session_id TEXT,
    summary TEXT NOT NULL DEFAULT '',
    current_step TEXT NOT NULL DEFAULT '',
    progress_percent INTEGER NOT NULL DEFAULT 0,
    result_payload TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_visibility_workstreams_status ON workstreams(status);
CREATE INDEX IF NOT EXISTS idx_visibility_workstreams_opportunity ON workstreams(opportunity_id);

CREATE TABLE IF NOT EXISTS workstream_events (
    id TEXT PRIMARY KEY,
    workstream_id TEXT NOT NULL REFERENCES workstreams(id),
    event_type TEXT NOT NULL,
    stage TEXT,
    actor TEXT NOT NULL,
    message TEXT NOT NULL,
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_visibility_workstream_events_ws ON workstream_events(workstream_id, created_at);

CREATE TABLE IF NOT EXISTS workstream_artifacts (
    id TEXT PRIMARY KEY,
    workstream_id TEXT NOT NULL REFERENCES workstreams(id),
    artifact_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    payload TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_visibility_workstream_artifacts_ws ON workstream_artifacts(workstream_id, artifact_type);
```

**Test:** Assert the new tables and indexes are created by `db.init_db()`.

---

### Task 2: Add workstream core module

**Objective:** Provide a small API for creating workstreams, moving stages, recording events, and attaching artifacts.

**Files:**
- Create: `plugins/visibility_os/core/workstreams.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Required functions:**

```python
def create_workstream(*, opportunity_id: str | None, root_action_id: str | None, lane_kind: str, title: str, repo: str | None = None, source_url: str | None = None, actor: str = "visibility_os") -> dict[str, Any]: ...

def get_workstream(workstream_id: str) -> dict[str, Any]: ...

def list_workstreams(*, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]: ...

def update_stage(workstream_id: str, *, stage: str, status: str | None = None, current_step: str = "", progress_percent: int | None = None, actor: str = "system", payload: dict[str, Any] | None = None) -> dict[str, Any]: ...

def record_workstream_event(workstream_id: str, *, event_type: str, message: str, actor: str = "system", stage: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]: ...

def add_workstream_artifact(workstream_id: str, *, artifact_type: str, title: str, summary: str = "", payload: dict[str, Any] | None = None) -> dict[str, Any]: ...
```

**Test:** Create a workstream, transition through two stages, add an artifact, and assert `get_workstream()` returns events and artifacts ordered chronologically.

---

### Task 3: Connect lane actions to workstreams

**Objective:** Starting any agentic lane should create or reuse a workstream linked to the opportunity and action.

**Files:**
- Modify: `plugins/visibility_os/core/opportunity_actions.py`
- Modify: `plugins/visibility_os/core/actions.py` if needed
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Implementation notes:**

- For `ci_fix_lane`, `github_issue_fix_lane`, `pr_ci_fix_lane`, `wip_handoff_lane`, and `github_pr_review_lane`, create a workstream when the action is drafted.
- Include `workstream_id` in the action `proposed_payload`.
- If the same open opportunity already has an active workstream for the same lane, reuse it or return a clear conflict instead of silently creating duplicates.
- Workstream title should be human-readable, e.g. `Fix bug: Negative add support` or `Review PR #123: Improve vault accounting`.

**Test:** Draft a fix issue lane and assert one workstream exists, linked to the action and opportunity.

---

## Agent progress tracking tasks

### Task 4: Emit progress events from Hermes lane executor

**Objective:** The dashboard should show where the agent is while the lane runs.

**Files:**
- Modify: `plugins/visibility_os/core/executors/hermes.py`
- Modify: `plugins/visibility_os/core/workstreams.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Implementation notes:**

- Before launching Hermes: `agent_starting`.
- After prompt/context is prepared: `gathering_context`.
- Before applying/expecting local changes: `editing`.
- Before verification parsing: `verifying`.
- Before self-audit parsing: `self_auditing`.
- Before fresh session review: `independent_reviewing`.
- If review passes and push action is queued: `ready_for_push`.
- If review fails: `failed` with blockers surfaced.

Because the current Hermes subprocess output may not provide structured streaming events, start with coarse deterministic events around known executor milestones. Do not fake fine-grained progress.

**Test:** Mock Hermes execution and assert stage events are recorded in the expected order for a successful lane and a failed review lane.

---

### Task 5: Store agent artifacts as structured workstream artifacts

**Objective:** Proposed PRs and reviews should be durable and inspectable from the workstream, not buried in raw action payloads.

**Files:**
- Modify: `plugins/visibility_os/core/executors/hermes.py`
- Modify: `plugins/visibility_os/core/executors/github.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Artifacts to capture:**

- `proposed_pr`
  - branch
  - commit message
  - PR title/body
  - changed files
  - verification evidence
  - self audit
  - independent review
- `diff_summary`
  - files changed
  - additions/deletions if available
  - human summary by file
- `review_findings`
  - severity counts
  - findings by file/line
  - copyable comments
- `github_result`
  - pushed branch URL
  - PR URL
  - posted comment URL

**Test:** Successful branch prep creates `proposed_pr` and `diff_summary`; successful push adds `github_result` and moves stage to `pushed` or `completed`.

---

## API tasks

### Task 6: Add workstream API endpoints

**Objective:** The dashboard can fetch current, historical, and detailed workstream state directly.

**Files:**
- Modify: `plugins/visibility_os/dashboard/plugin_api.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Endpoints:**

```text
GET /api/plugins/visibility-os/workstreams
GET /api/plugins/visibility-os/workstreams?status=active
GET /api/plugins/visibility-os/workstreams/{workstream_id}
GET /api/plugins/visibility-os/opportunities/{opportunity_id}/workstreams
```

**Response shape for list endpoint:**

```json
{
  "workstreams": [
    {
      "id": "ws_...",
      "title": "Fix bug: negative add support",
      "lane_kind": "github_issue_fix_lane",
      "stage": "independent_reviewing",
      "status": "active",
      "current_step": "Fresh review agent is checking the local diff",
      "progress_percent": 70,
      "repo": "org/repo",
      "source_url": "https://github.com/org/repo/issues/2",
      "updated_at": "...",
      "pending_human_action": null
    }
  ]
}
```

**Test:** List endpoint returns active and completed workstreams with summary fields; detail endpoint returns events and artifacts.

---

### Task 7: Upgrade feed to include workstream rollups

**Objective:** Existing feed cards should show whether an opportunity is untouched, active, done, or waiting on Barney.

**Files:**
- Modify: `plugins/visibility_os/dashboard/plugin_api.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Feed additions:**

- `workstream_status`
- `workstream_stage`
- `workstream_id`
- `agent_has_worked_on_this`
- `last_agent_activity_at`
- `pending_human_action`

**Test:** Feed item for an opportunity with active workstream includes these fields.

---

## Dashboard UX tasks

### Task 8: Add Overview sections

**Objective:** Make the landing dashboard immediately show queue and progress.

**Files:**
- Modify: `plugins/visibility_os/dashboard/dist/index.js`

**Sections:**

1. **Needs decision**
   - Push branch
   - Post review/comment
   - Failed lane needing retry or discard
2. **Agent working now**
   - Active workstreams with stage pill and progress bar
3. **Open opportunities**
   - Unstarted opportunities
4. **Completed recently**
   - Pushed PRs, posted reviews, closed/resolved opportunities

**No backend test required**, but add API-level tests already covered above.

---

### Task 9: Add Workstream detail drawer/page

**Objective:** Clicking a workstream should show a readable timeline and artifacts.

**Files:**
- Modify: `plugins/visibility_os/dashboard/dist/index.js`

**UI content:**

- Header: title, repo, source link, lane kind, current stage.
- Progress stepper with lifecycle stages.
- Timeline of events:
  - queued
  - agent started
  - context gathered
  - files changed
  - tests run
  - self-audit complete
  - independent review complete
  - push/comment queued
  - pushed/commented/completed
- Artifact tabs:
  - Summary
  - Changes
  - Verification
  - Self-audit
  - Independent review
  - Raw JSON fallback

---

### Task 10: Improve Proposed PR visualisation

**Objective:** Proposed code changes should be inspectable without reading raw JSON or opening GitHub first.

**Files:**
- Modify: `plugins/visibility_os/dashboard/dist/index.js`
- Optional backend support: `plugins/visibility_os/core/executors/hermes.py`

**UI content for `proposed_pr` artifact:**

- Branch name and commit message.
- PR title/body preview.
- Changed file list grouped by type:
  - code
  - tests
  - docs
  - config/CI
- Per-file summaries from agent output where available.
- Verification commands with pass/fail badge.
- Self-audit summary:
  - status
  - issues found
  - fixes applied
- Independent review summary:
  - status
  - blockers
  - non-blocking findings
- Clear call to action:
  - **Push branch** if safe and queued
  - **Reject/discard** if not wanted
  - **Retry with note** as a later enhancement

---

### Task 11: Add human-friendly diff artifact

**Objective:** Show meaningful code change previews even before a PR exists on GitHub.

**Files:**
- Modify: `plugins/visibility_os/core/executors/hermes.py`
- Modify: `plugins/visibility_os/dashboard/dist/index.js`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Backend approach:**

- After the agent prepares the branch, run a local git diff summary for the branch vs base.
- Store a safe summarized artifact:
  - file path
  - change type
  - additions/deletions if available
  - first N changed hunks, capped to avoid huge payloads
- Do not store secrets or huge diffs blindly. Cap by file and total payload size.

**UI approach:**

- File tree on left or stacked file cards.
- Each file card shows:
  - path
  - additions/deletions
  - agent explanation
  - expandable diff hunk preview
- Link to local branch metadata and GitHub PR once pushed.

**Test:** Mock diff collection and assert artifact is capped and attached to the workstream.

---

### Task 12: Upgrade PR audit/review visualisation

**Objective:** Reviews should be actionable and skimmable.

**Files:**
- Modify: `plugins/visibility_os/dashboard/dist/index.js`
- Possibly modify: `plugins/visibility_os/core/pr_audit.py`
- Test: `tests/plugins/visibility_os/test_visibility_os_core.py`

**UI content:**

- Summary counts: blockers, warnings, suggestions.
- Group findings by file.
- Each finding card:
  - severity
  - file and line
  - short casual explanation
  - technical detail expandable
  - suggested fix
  - copyable GitHub comment
  - mark checked / needs follow-up local UI status
- Separate deterministic findings from agentic findings.
- Show final recommended decision:
  - approve
  - request changes
  - comment only
  - no action

**Test:** Ensure review artifact payload supports severity counts and grouped findings.

---

## History and filters tasks

### Task 13: Add filters and tabs

**Objective:** Barney can quickly answer what agents are doing or have done.

**Files:**
- Modify: `plugins/visibility_os/dashboard/dist/index.js`

**Filters:**

- Status: active, waiting on me, completed, failed, unstarted.
- Lane: Fix Docs, Fix Bug, Deflake, Fix CI, Fix PR CI, Review PR, Handoff.
- Repo.
- Time: today, 7 days, all.
- Outcome: PR opened, review posted, failed, rejected.

---

### Task 14: Add opportunity history trail

**Objective:** Each opportunity card should show if the agent has previously worked on it.

**Files:**
- Modify: `plugins/visibility_os/dashboard/dist/index.js`
- Backend covered by Task 7.

**UI content:**

- `Not started`
- `Agent working: independent review`
- `Waiting for you: Push branch`
- `Worked on: PR #10 opened`
- `Failed: independent review found blocker`

---

## Verification tasks

### Task 15: Add regression tests for workstream tracking

**Objective:** Prevent future regressions where agent work becomes invisible again.

**Files:**
- Modify: `tests/plugins/visibility_os/test_visibility_os_core.py`

**Test cases:**

- Starting a fix lane creates a workstream.
- Duplicate clicks do not create duplicate active workstreams for the same opportunity/lane.
- Hermes executor records stage transitions.
- Successful fix lane attaches proposed PR, diff summary, self-audit, and independent review artifacts.
- Failed independent review leaves workstream failed and no push action queued.
- Pushing branch attaches GitHub result and marks workstream completed/pushed.
- Review PR lane attaches review findings and queues comment action.
- Feed returns workstream rollups.

---

### Task 16: Manual lab verification

**Objective:** Prove the UX with the existing `visibility-os-flow-lab` repo.

**Manual checks:**

- Start Fix Docs and see workstream move from queued to ready for push.
- Start Fix PR CI and see self-audit plus independent review in the workstream detail.
- Push branch and see PR URL attached to the same workstream.
- Run Review PR and see findings grouped by file with copyable comments.
- Confirm the LAN dashboard view shows the same information Barney uses, not just localhost.

---

## MVP cut

If implementing in phases, ship in this order:

1. Workstream tables/module/API.
2. Coarse stage events from lane executor.
3. Dashboard sections: Needs decision, Agent working now, Open opportunities, Completed recently.
4. Proposed PR artifact view.
5. PR review artifact view.
6. Local diff preview.
7. Filters and history polish.

This gives immediate visibility first, then richer code/review visualisation.
