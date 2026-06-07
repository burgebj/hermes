# Hermes Visibility OS Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. Do not execute external/public write actions without explicit human approval through the Action Queue.

**Goal:** Build Hermes Visibility OS: a Hermes-native plugin and dashboard extension that finds real engineering opportunities, prepares evidence-backed artifacts, and queues all reputation-sensitive write actions for human approval.

**Architecture:** Implement as a Hermes dashboard plugin plus core Python modules under `plugins/visibility_os/`. Use profile-aware SQLite for MVP persistence. The dashboard exposes a news-feed/action-queue UI; backend routes live under `/api/plugins/visibility-os/...`; scheduled work uses Hermes cron. External writes are deny-by-default and can only happen through approved action items with audit logging.

**Tech Stack:** Python, FastAPI `APIRouter`, SQLite, Pydantic, Hermes dashboard plugin system, React/Vite dashboard frontend, Hermes cron, `gh` CLI for GitHub MVP.

---

## Non-Negotiable Product Rules

1. **SQLite first.** Use profile-aware SQLite via `get_hermes_home()`; do not introduce Postgres in MVP.
2. **Read freely, write through approval.** Scanners may read GitHub/Slack/Linear/docs/CI, but all external write-actions must be queued.
3. **No unapproved reputation-sensitive actions.** Slack posts, GitHub comments, PR creation, branch pushes, docs publication, deployments, incident updates, and ticket changes require human approval.
4. **Hard-block high-risk actions.** Merge PR, production deploy, delete branch, mute alert, permission change, close customer ticket, and executive-channel message are manual-only unless a future explicit override flow is added.
5. **No fake impact.** Completion claims require evidence and executed/shipped status.
6. **Audit everything.** Every approval transition and execution attempt writes an audit-log row.

---

## Data Model Overview

SQLite database path:

```python
get_hermes_home() / "visibility_os.db"
```

Initial tables:

- `schema_migrations`
- `opportunities`
- `action_queue`
- `audit_log`
- `daily_summaries`
- `weekly_summaries`
- `scan_runs`
- `connector_state`

JSON fields are stored as encoded `TEXT` in SQLite.

---

## Task 1: Create plugin skeleton

**Objective:** Add the minimal plugin structure so Hermes can discover Visibility OS.

**Files:**
- Create: `plugins/visibility_os/plugin.yaml`
- Create: `plugins/visibility_os/__init__.py`
- Create: `plugins/visibility_os/core/__init__.py`
- Create: `plugins/visibility_os/dashboard/plugin_api.py`
- Create: `tests/plugins/visibility_os/test_plugin_api.py`

**Step 1: Create plugin manifest**

Create `plugins/visibility_os/plugin.yaml`:

```yaml
name: visibility-os
display_name: Hermes Visibility OS
description: Evidence-backed engineering impact feed and human approval queue.
version: 0.1.0
kind: dashboard
sidebar:
  label: Visibility OS
  path: /plugins/visibility-os
api: plugin_api.py
```

**Step 2: Create minimal API router**

Create `plugins/visibility_os/dashboard/plugin_api.py`:

```python
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"ok": "true", "plugin": "visibility-os"}
```

**Step 3: Add test**

Create `tests/plugins/visibility_os/test_plugin_api.py`:

```python
from fastapi.testclient import TestClient
from fastapi import FastAPI

from plugins.visibility_os.dashboard.plugin_api import router


def test_visibility_os_health_endpoint():
    app = FastAPI()
    app.include_router(router, prefix="/api/plugins/visibility-os")
    client = TestClient(app)

    res = client.get("/api/plugins/visibility-os/health")

    assert res.status_code == 200
    assert res.json() == {"ok": "true", "plugin": "visibility-os"}
```

**Step 4: Run test**

Run:

```bash
python -m pytest tests/plugins/visibility_os/test_plugin_api.py -q -o 'addopts='
```

Expected: `1 passed`.

**Step 5: Commit**

```bash
git add plugins/visibility_os tests/plugins/visibility_os
git commit -m "feat: add visibility os plugin skeleton"
```

---

## Task 2: Add profile-aware SQLite database layer

**Objective:** Create an idempotent SQLite initialization layer.

**Files:**
- Create: `plugins/visibility_os/core/db.py`
- Create: `tests/plugins/visibility_os/test_db.py`

**Step 1: Write failing tests**

Create `tests/plugins/visibility_os/test_db.py`:

```python
import sqlite3

from plugins.visibility_os.core import db


def test_init_db_creates_required_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "get_db_path", lambda: tmp_path / "visibility_os.db")

    db.init_db()

    conn = sqlite3.connect(tmp_path / "visibility_os.db")
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    names = {row[0] for row in rows}

    assert "schema_migrations" in names
    assert "opportunities" in names
    assert "action_queue" in names
    assert "audit_log" in names
    assert "daily_summaries" in names
    assert "weekly_summaries" in names
    assert "scan_runs" in names
    assert "connector_state" in names


def test_init_db_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "get_db_path", lambda: tmp_path / "visibility_os.db")

    db.init_db()
    db.init_db()

    conn = sqlite3.connect(tmp_path / "visibility_os.db")
    row = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()
    assert row[0] >= 1
```

**Step 2: Implement database module**

Create `plugins/visibility_os/core/db.py`:

```python
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator
from contextlib import contextmanager

from hermes_constants import get_hermes_home

DB_FILENAME = "visibility_os.db"
SCHEMA_VERSION = 1


def get_db_path() -> Path:
    return Path(get_hermes_home()) / DB_FILENAME


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                source_system TEXT NOT NULL,
                source_url TEXT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                impact_score INTEGER NOT NULL,
                visibility_score INTEGER NOT NULL,
                effort_score INTEGER NOT NULL,
                safety_score INTEGER NOT NULL,
                risk_penalty INTEGER NOT NULL DEFAULT 0,
                priority_score INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                metadata TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS action_queue (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT REFERENCES opportunities(id),
                proposed_by_agent TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target_system TEXT NOT NULL,
                target_location TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                proposed_payload TEXT NOT NULL,
                final_payload TEXT,
                evidence_links TEXT NOT NULL DEFAULT '[]',
                risk_level TEXT NOT NULL,
                impact_score INTEGER,
                visibility_score INTEGER,
                effort_score INTEGER,
                approval_required INTEGER NOT NULL DEFAULT 1,
                approval_reason TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                approved_at TEXT,
                executed_at TEXT,
                approved_by TEXT,
                execution_result TEXT
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id TEXT PRIMARY KEY,
                action_id TEXT REFERENCES action_queue(id),
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                before_state TEXT,
                after_state TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS daily_summaries (
                id TEXT PRIMARY KEY,
                date TEXT NOT NULL,
                summary_payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS weekly_summaries (
                id TEXT PRIMARY KEY,
                week_start TEXT NOT NULL,
                week_end TEXT NOT NULL,
                summary_payload TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS scan_runs (
                id TEXT PRIMARY KEY,
                scanner_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL DEFAULT (datetime('now')),
                finished_at TEXT,
                result_payload TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS connector_state (
                connector_name TEXT PRIMARY KEY,
                state_payload TEXT NOT NULL DEFAULT '{}',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )
        conn.execute(
            "INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
```

**Step 3: Run test**

```bash
python -m pytest tests/plugins/visibility_os/test_db.py -q -o 'addopts='
```

Expected: `2 passed`.

**Step 4: Commit**

```bash
git add plugins/visibility_os/core/db.py tests/plugins/visibility_os/test_db.py
git commit -m "feat: add visibility os sqlite store"
```

---

## Task 3: Implement scoring engine

**Objective:** Implement deterministic priority scoring from the JSON spec.

**Files:**
- Create: `plugins/visibility_os/core/scoring.py`
- Create: `tests/plugins/visibility_os/test_scoring.py`

**Step 1: Write tests**

Create `tests/plugins/visibility_os/test_scoring.py`:

```python
from plugins.visibility_os.core.scoring import score_opportunity


def test_score_opportunity_uses_visibility_formula():
    result = score_opportunity(
        impact=4,
        visibility=5,
        effort=4,
        safety=5,
        risk_penalty=0,
    )

    assert result.priority_score == 31


def test_risk_penalty_reduces_priority():
    safe = score_opportunity(impact=4, visibility=5, effort=4, safety=5, risk_penalty=0)
    risky = score_opportunity(impact=4, visibility=5, effort=4, safety=5, risk_penalty=10)

    assert risky.priority_score == safe.priority_score - 10


def test_scores_are_clamped():
    result = score_opportunity(
        impact=99,
        visibility=-1,
        effort=99,
        safety=-1,
        risk_penalty=99,
    )

    assert result.impact == 5
    assert result.visibility == 0
    assert result.effort == 5
    assert result.safety == 1
    assert result.risk_penalty == 10
```

**Step 2: Implement scoring**

Create `plugins/visibility_os/core/scoring.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    impact: int
    visibility: int
    effort: int
    safety: int
    risk_penalty: int
    priority_score: int


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def score_opportunity(
    *,
    impact: int,
    visibility: int,
    effort: int,
    safety: int,
    risk_penalty: int,
) -> ScoreResult:
    impact = _clamp(impact, 0, 5)
    visibility = _clamp(visibility, 0, 5)
    effort = _clamp(effort, 1, 5)
    safety = _clamp(safety, 1, 5)
    risk_penalty = _clamp(risk_penalty, 0, 10)
    priority_score = (impact * 3) + (visibility * 2) + effort + safety - risk_penalty
    return ScoreResult(
        impact=impact,
        visibility=visibility,
        effort=effort,
        safety=safety,
        risk_penalty=risk_penalty,
        priority_score=priority_score,
    )
```

**Step 3: Run tests**

```bash
python -m pytest tests/plugins/visibility_os/test_scoring.py -q -o 'addopts='
```

Expected: `3 passed`.

**Step 4: Commit**

```bash
git add plugins/visibility_os/core/scoring.py tests/plugins/visibility_os/test_scoring.py
git commit -m "feat: add visibility scoring engine"
```

---

## Task 4: Implement action queue state machine

**Objective:** Create, list, approve, edit, reject, and guard execution of queued actions.

**Files:**
- Create: `plugins/visibility_os/core/actions.py`
- Create: `plugins/visibility_os/core/audit.py`
- Create: `plugins/visibility_os/core/policies.py`
- Create: `tests/plugins/visibility_os/test_action_queue.py`

**Step 1: Define policy constants**

Create `plugins/visibility_os/core/policies.py`:

```python
WRITE_ACTIONS_REQUIRE_APPROVAL = {
    "slack_message",
    "slack_thread_reply",
    "github_issue_comment",
    "github_pr_comment",
    "github_pr_creation",
    "github_pr_merge",
    "github_branch_push",
    "jira_ticket_update",
    "jira_ticket_creation",
    "docs_publication",
    "incident_update",
    "release_note",
    "deployment",
    "production_config_change",
}

HARD_BLOCKED_ACTIONS = {
    "merge_pull_request",
    "production_deploy",
    "delete_branch",
    "close_customer_ticket",
    "mute_alert",
    "change_permissions",
    "send_message_to_executive_channel",
}

VALID_STATUSES = {
    "drafted",
    "queued",
    "needs_review",
    "approved",
    "rejected",
    "edited_by_human",
    "executed",
    "failed",
    "cancelled",
    "expired",
}

VALID_TRANSITIONS = {
    "drafted": {"queued", "cancelled"},
    "queued": {"approved", "rejected", "needs_review", "edited_by_human", "cancelled", "expired"},
    "needs_review": {"queued", "rejected", "cancelled"},
    "edited_by_human": {"approved", "queued", "rejected", "cancelled"},
    "approved": {"executed", "failed", "cancelled"},
    "rejected": set(),
    "executed": set(),
    "failed": set(),
    "cancelled": set(),
    "expired": set(),
}
```

**Step 2: Implement audit helper**

Create `plugins/visibility_os/core/audit.py`:

```python
from __future__ import annotations

import json
import uuid
from typing import Any

from .db import connect


def record_event(
    *,
    action_id: str | None,
    event_type: str,
    actor: str,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
) -> str:
    event_id = f"audit_{uuid.uuid4().hex}"
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO audit_log(id, action_id, event_type, actor, before_state, after_state)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                action_id,
                event_type,
                actor,
                json.dumps(before_state) if before_state is not None else None,
                json.dumps(after_state) if after_state is not None else None,
            ),
        )
    return event_id
```

**Step 3: Implement action service**

Create `plugins/visibility_os/core/actions.py` with functions:

```python
create_action(...)
get_action(action_id)
list_actions(status=None)
transition_action(action_id, to_status, actor, reason=None)
approve_action(action_id, actor)
edit_action(action_id, actor, final_payload)
reject_action(action_id, actor, reason)
execute_action_guard(action_id)
```

Required behavior:

- Call `init_db()` before database operations.
- Use IDs like `act_<uuidhex>`.
- Store `proposed_payload`, `final_payload`, `evidence_links`, and `execution_result` as JSON text.
- Reject invalid status transitions.
- `execute_action_guard()` raises if status is not `approved`.
- `execute_action_guard()` raises if action type is hard-blocked.
- Every mutation records an audit event.

**Step 4: Tests**

Create tests for:

- creating an action defaults to `queued`
- approving queued action changes status to `approved`
- rejecting queued action changes status to `rejected`
- invalid transition raises
- execute guard rejects non-approved action
- execute guard rejects hard-blocked action
- audit rows are written

**Step 5: Run tests**

```bash
python -m pytest tests/plugins/visibility_os/test_action_queue.py -q -o 'addopts='
```

**Step 6: Commit**

```bash
git add plugins/visibility_os/core/actions.py plugins/visibility_os/core/audit.py plugins/visibility_os/core/policies.py tests/plugins/visibility_os/test_action_queue.py
git commit -m "feat: add visibility action queue"
```

---

## Task 5: Add feed and action queue API routes

**Objective:** Expose the action queue through dashboard plugin API routes.

**Files:**
- Modify: `plugins/visibility_os/dashboard/plugin_api.py`
- Create: `tests/plugins/visibility_os/test_visibility_api.py`

**Routes:**

```text
GET  /feed
GET  /actions
GET  /actions/{action_id}
POST /actions/{action_id}/approve
POST /actions/{action_id}/edit
POST /actions/{action_id}/reject
POST /actions/{action_id}/execute
GET  /audit-log
```

**API behavior:**

- `/feed` returns mixed cards: queued actions, opportunities, summaries, risk warnings.
- `/actions` supports optional `status` query.
- `/approve` changes status only unless body has `execute_immediately: true`.
- `/edit` stores final payload and moves to `edited_by_human`.
- `/reject` requires a reason.
- `/execute` calls guard only in this task; actual external execution comes later.

**Step: Run tests**

```bash
python -m pytest tests/plugins/visibility_os/test_visibility_api.py -q -o 'addopts='
```

**Commit:**

```bash
git add plugins/visibility_os/dashboard/plugin_api.py tests/plugins/visibility_os/test_visibility_api.py
git commit -m "feat: expose visibility action queue api"
```

---

## Task 6: Add language guard

**Objective:** Prevent overclaiming and misleading updates.

**Files:**
- Create: `plugins/visibility_os/core/language_guard.py`
- Create: `tests/plugins/visibility_os/test_language_guard.py`

**Blocked terms when status is not executed:**

```text
fixed
shipped
resolved
completed
deployed
```

**Allowed unfinished-work language:**

```text
I am investigating
I found a likely cause
I opened a draft
I am testing a fix
I proposed a follow-up
```

**Tests:**

- non-executed action with “Fixed” fails
- executed action with “Fixed” passes if evidence exists
- team-channel post without evidence fails
- progress update with “likely cause” passes

**Commit:**

```bash
git add plugins/visibility_os/core/language_guard.py tests/plugins/visibility_os/test_language_guard.py
git commit -m "feat: add visibility language guard"
```

---

## Task 7: Add evidence package builder

**Objective:** Standardize the evidence required for PRs, comments, Slack updates, and weekly summaries.

**Files:**
- Create: `plugins/visibility_os/core/evidence.py`
- Create: `tests/plugins/visibility_os/test_evidence.py`

**Evidence fields:**

```text
problem_statement
affected_users_or_systems
root_cause
fix_summary
before_after_behaviour
tests_run
logs_or_screenshots
risk_assessment
follow_up_tasks
```

**Required for completion updates:**

- PR URL or issue URL
- test result or explanation
- clear actual status

**Commit:**

```bash
git add plugins/visibility_os/core/evidence.py tests/plugins/visibility_os/test_evidence.py
git commit -m "feat: add visibility evidence packages"
```

---

## Task 8: Implement communications drafter

**Objective:** Generate concise, factual message drafts that always become queued actions.

**Files:**
- Create: `plugins/visibility_os/core/communications.py`
- Create: `tests/plugins/visibility_os/test_communications.py`

**Formats:**

Progress update:

```text
Problem → current diagnosis → action underway → expected next step
```

Completion update:

```text
Problem → fix → evidence → impact → follow-up
```

Weekly update:

```text
Outcomes shipped → systems improved → blockers removed → next risks
```

**Behavior:**

- Run language guard before queueing.
- Require evidence links for team-visible messages.
- Create `slack_message`, `github_issue_comment`, or `weekly_update_draft` action items.

**Commit:**

```bash
git add plugins/visibility_os/core/communications.py tests/plugins/visibility_os/test_communications.py
git commit -m "feat: draft evidence-backed visibility updates"
```

---

## Task 9: Implement GitHub read-only scanner

**Objective:** Find initial opportunities from GitHub without writing anything.

**Files:**
- Create: `plugins/visibility_os/core/connectors/__init__.py`
- Create: `plugins/visibility_os/core/connectors/github.py`
- Create: `plugins/visibility_os/core/scanner.py`
- Create: `tests/plugins/visibility_os/test_github_scanner.py`

**Use `gh` CLI:**

```bash
gh issue list --json number,title,url,labels,updatedAt,assignees

gh pr list --json number,title,url,updatedAt,reviewDecision,statusCheckRollup

gh run list --json databaseId,status,conclusion,displayTitle,workflowName,url,createdAt
```

**MVP opportunity categories:**

- flaky tests / CI failures
- stale PRs
- issues labelled bug/test/docs
- PRs awaiting review
- docs/runbook gaps inferred from labels/title

**Scanner output:** normalized opportunity rows with score and suggested artifacts.

**Tests:** mock `subprocess.run` output from `gh`.

**Commit:**

```bash
git add plugins/visibility_os/core/connectors plugins/visibility_os/core/scanner.py tests/plugins/visibility_os/test_github_scanner.py
git commit -m "feat: scan github visibility opportunities"
```

---

## Task 10: Implement impact picker

**Objective:** Create a daily plan from ranked opportunities.

**Files:**
- Create: `plugins/visibility_os/core/impact_picker.py`
- Create: `tests/plugins/visibility_os/test_impact_picker.py`

**Rules:**

- Pick 1 main task.
- Pick 2 side quests.
- Pick 1 communication artifact.
- Avoid high-risk/unbounded/private/no-artifact work.

**Output:** daily feed card stored in `daily_summaries`.

**Commit:**

```bash
git add plugins/visibility_os/core/impact_picker.py tests/plugins/visibility_os/test_impact_picker.py
git commit -m "feat: select daily visibility plan"
```

---

## Task 11: Add dashboard UI page

**Objective:** Add a news-feed interface to review opportunities and action items.

**Files:**
- Create: `web/src/pages/VisibilityOSPage.tsx`
- Create: `web/src/components/visibility/ActionCard.tsx`
- Create: `web/src/components/visibility/ApprovalControls.tsx`
- Create: `web/src/components/visibility/EvidenceLinks.tsx`
- Create: `web/src/components/visibility/FeedFilters.tsx`
- Create: `web/src/components/visibility/ScoreBadges.tsx`
- Modify: routing/sidebar registration files after inspecting current dashboard route pattern.
- Modify: `web/src/lib/api.ts` to add Visibility OS API client functions.

**UI card fields:**

- title
- agent name
- target system
- target location
- proposed action
- generated text/diff
- risk level
- impact score
- visibility score
- evidence links
- approval buttons
- audit history

**Controls:**

- Approve & Execute
- Edit & Execute
- Reject
- Ask Hermes to Revise
- Save for Later
- Mark Done Manually

**Verification:**

```bash
cd web
npm run build
```

**Commit:**

```bash
git add web/src/pages/VisibilityOSPage.tsx web/src/components/visibility web/src/lib/api.ts
git commit -m "feat: add visibility os dashboard feed"
```

---

## Task 12: Add safe executors

**Objective:** Execute approved low-risk actions only.

**Files:**
- Create: `plugins/visibility_os/core/executors/__init__.py`
- Create: `plugins/visibility_os/core/executors/base.py`
- Create: `plugins/visibility_os/core/executors/github.py`
- Create: `plugins/visibility_os/core/executors/slack.py`
- Create: `tests/plugins/visibility_os/test_executors.py`

**First supported actions:**

- `github_issue_comment`
- `github_pr_comment`
- `slack_message`

**Do not implement in MVP:**

- merge PR
- production deploy
- mute alert
- permission change
- delete branch

**Pre-execution checks:**

- target system is valid
- user permissions are available
- status is `approved`
- final/reviewed payload exists or proposed payload is explicitly accepted
- no forbidden claims
- no obvious sensitive data leak
- evidence links exist when required
- audit log is written before and after execution

**Commit:**

```bash
git add plugins/visibility_os/core/executors tests/plugins/visibility_os/test_executors.py
git commit -m "feat: execute approved visibility actions"
```

---

## Task 13: Add scheduled jobs

**Objective:** Wire Visibility OS into Hermes cron without bypassing approval.

**Jobs:**

```text
Europe/London 08:30 scan_opportunities
Europe/London 09:00 generate_daily_plan
Europe/London 11:30 draft_progress_update
Europe/London 14:30 check_pr_and_ci_status
Europe/London 17:30 draft_end_of_day_summary
Europe/London Friday 16:00 generate_weekly_impact_summary
Europe/London Friday 16:30 generate_next_week_opportunity_backlog
```

**Implementation options:**

1. Add CLI entrypoints under `hermes_cli` for plugin operations, then cron calls those.
2. Add lightweight scripts under `plugins/visibility_os/scripts/` that invoke core functions.
3. Use Hermes cron prompts that instruct the agent to call Visibility OS routes/core code.

Preferred MVP: **scripts calling core functions**, because they are deterministic and do not rely on an LLM for simple scans.

**Acceptance criteria:**

- Scheduled jobs create feed cards/action items only.
- Scheduled jobs never execute external writes.
- The configured human approver receives a notification only when review items are waiting.

---

## Task 14: End-to-end safety tests

**Objective:** Prove the approval boundary cannot be bypassed.

**Files:**
- Create: `tests/plugins/visibility_os/test_safety_e2e.py`

**Test cases:**

1. Unapproved Slack action cannot execute.
2. Approved Slack action executes exactly final payload.
3. Draft claiming “Fixed” without executed status is rejected.
4. GitHub comment requires evidence link.
5. Hard-blocked deploy action cannot execute even if approved.
6. Every failed execution attempt has an audit event.

**Commit:**

```bash
git add tests/plugins/visibility_os/test_safety_e2e.py
git commit -m "test: enforce visibility os approval boundary"
```

---

## MVP Completion Criteria

MVP is complete when:

- Dashboard shows Visibility OS feed.
- SQLite action queue persists proposed actions.
- User can approve/edit/reject actions.
- Audit log records every state transition.
- GitHub scanner can produce scored opportunities.
- Communications drafter queues factual updates.
- No external write occurs unless action status is `approved`.
- Hard-blocked actions cannot execute through the agent.
- Tests pass for database, scoring, actions, API, language guard, and safety E2E.

---

## Verification Commands

Run focused tests:

```bash
python -m pytest tests/plugins/visibility_os -q -o 'addopts='
```

Run dashboard build:

```bash
cd web
npm run build
```

Run broader relevant tests:

```bash
python -m pytest tests/plugins tests/hermes_cli -q -o 'addopts='
```

---

## Recommended Implementation Order

1. Plugin skeleton
2. SQLite database
3. Scoring engine
4. Action queue state machine
5. API routes
6. Language guard
7. Evidence builder
8. Communications drafter
9. GitHub scanner
10. Impact picker
11. Dashboard UI
12. Safe executors
13. Cron jobs
14. End-to-end safety tests

The Action Queue must be implemented before any executor. The dashboard approval experience should exist before any external write integration is enabled.
