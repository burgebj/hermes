from __future__ import annotations

import json
import uuid
from typing import Any

from . import db

ACTIVE_STATUSES = {"active", "queued"}
TERMINAL_STAGES = {"completed", "failed", "cancelled", "pushed"}


def _json(value: Any) -> str:
    return json.dumps(value or {}, sort_keys=True)


def _decode(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _row_to_workstream(row) -> dict[str, Any]:
    d = dict(row)
    d["result_payload"] = _decode(d.get("result_payload"), {})
    return d


def _row_to_event(row) -> dict[str, Any]:
    d = dict(row)
    d["payload"] = _decode(d.get("payload"), {})
    return d


def _row_to_artifact(row) -> dict[str, Any]:
    d = dict(row)
    d["payload"] = _decode(d.get("payload"), {})
    return d


def _events(conn, workstream_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM workstream_events WHERE workstream_id = ? ORDER BY created_at, rowid",
        (workstream_id,),
    ).fetchall()
    return [_row_to_event(row) for row in rows]


def _artifacts(conn, workstream_id: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM workstream_artifacts WHERE workstream_id = ? ORDER BY created_at, rowid",
        (workstream_id,),
    ).fetchall()
    return [_row_to_artifact(row) for row in rows]


def _hydrate(conn, row) -> dict[str, Any]:
    ws = _row_to_workstream(row)
    ws["events"] = _events(conn, ws["id"])
    ws["artifacts"] = _artifacts(conn, ws["id"])
    ws["pending_human_action"] = _pending_human_action(conn, ws)
    return ws


def _pending_human_action(conn, ws: dict[str, Any]) -> dict[str, Any] | None:
    rows = conn.execute(
        """
        SELECT id, action_type, title, status, target_system
        FROM action_queue
        WHERE opportunity_id IS ?
          AND status IN ('queued', 'needs_review', 'drafted')
          AND action_type IN ('github_push_branch', 'github_pr_comment', 'github_issue_comment')
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (ws.get("opportunity_id"),),
    ).fetchall()
    if not rows:
        return None
    return dict(rows[0])


def create_workstream(
    *,
    opportunity_id: str | None,
    root_action_id: str | None,
    lane_kind: str,
    title: str,
    repo: str | None = None,
    source_url: str | None = None,
    actor: str = "visibility_os",
    summary: str = "",
) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        if opportunity_id:
            row = conn.execute(
                """
                SELECT * FROM workstreams
                WHERE opportunity_id = ? AND lane_kind = ? AND status = 'active'
                ORDER BY updated_at DESC LIMIT 1
                """,
                (opportunity_id, lane_kind),
            ).fetchone()
            if row:
                ws = _hydrate(conn, row)
                if root_action_id and not ws.get("root_action_id"):
                    conn.execute("UPDATE workstreams SET root_action_id = ?, updated_at = datetime('now') WHERE id = ?", (root_action_id, ws["id"]))
                    row = conn.execute("SELECT * FROM workstreams WHERE id = ?", (ws["id"],)).fetchone()
                    ws = _hydrate(conn, row)
                return ws
        workstream_id = f"ws_{uuid.uuid4().hex}"
        conn.execute(
            """
            INSERT INTO workstreams(id, opportunity_id, root_action_id, lane_kind, title, repo, source_url, stage, status, started_at, summary, current_step, progress_percent)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', 'active', datetime('now'), ?, 'Queued for agent work', 0)
            """,
            (workstream_id, opportunity_id, root_action_id, lane_kind, title, repo, source_url, summary),
        )
        conn.execute(
            """
            INSERT INTO workstream_events(id, workstream_id, event_type, stage, actor, message, payload)
            VALUES (?, ?, 'created', 'queued', ?, ?, '{}')
            """,
            (f"wse_{uuid.uuid4().hex}", workstream_id, actor, f"Created workstream for {lane_kind}"),
        )
        row = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        return _hydrate(conn, row)


def bind_root_action(workstream_id: str, action_id: str) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        conn.execute("UPDATE workstreams SET root_action_id = ?, updated_at = datetime('now') WHERE id = ?", (action_id, workstream_id))
        row = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        if not row:
            raise KeyError(f"Workstream not found: {workstream_id}")
        return _hydrate(conn, row)


def get_workstream(workstream_id: str) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        if not row:
            raise KeyError(f"Workstream not found: {workstream_id}")
        return _hydrate(conn, row)


def list_workstreams(*, status: str | None = None, opportunity_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    db.init_db()
    clauses = []
    values: list[Any] = []
    if status:
        if status == "active":
            clauses.append("status = 'active'")
        else:
            clauses.append("status = ?")
            values.append(status)
    if opportunity_id:
        clauses.append("opportunity_id = ?")
        values.append(opportunity_id)
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    values.append(limit)
    with db.connect() as conn:
        rows = conn.execute(f"SELECT * FROM workstreams{where} ORDER BY updated_at DESC LIMIT ?", tuple(values)).fetchall()
        return [_hydrate(conn, row) for row in rows]


def update_stage(
    workstream_id: str,
    *,
    stage: str,
    status: str | None = None,
    current_step: str = "",
    progress_percent: int | None = None,
    actor: str = "system",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db.init_db()
    payload = payload or {}
    if status is None:
        status = "completed" if stage in {"completed", "pushed"} else "failed" if stage == "failed" else "active"
    progress = max(0, min(100, int(progress_percent if progress_percent is not None else 0)))
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        if not row:
            raise KeyError(f"Workstream not found: {workstream_id}")
        if progress_percent is None:
            progress = int(row["progress_percent"] or 0)
        completed_at_sql = ", completed_at = datetime('now')" if status in {"completed", "failed", "cancelled"} else ""
        conn.execute(
            f"""
            UPDATE workstreams
            SET stage = ?, status = ?, current_step = ?, progress_percent = ?, updated_at = datetime('now') {completed_at_sql}
            WHERE id = ?
            """,
            (stage, status, current_step, progress, workstream_id),
        )
        conn.execute(
            """
            INSERT INTO workstream_events(id, workstream_id, event_type, stage, actor, message, payload)
            VALUES (?, ?, 'stage_changed', ?, ?, ?, ?)
            """,
            (f"wse_{uuid.uuid4().hex}", workstream_id, stage, actor, current_step or stage.replace("_", " ").title(), _json(payload)),
        )
        updated = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        return _hydrate(conn, updated)


def record_workstream_event(
    workstream_id: str,
    *,
    event_type: str,
    message: str,
    actor: str = "system",
    stage: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        ws = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        if not ws:
            raise KeyError(f"Workstream not found: {workstream_id}")
        conn.execute(
            """
            INSERT INTO workstream_events(id, workstream_id, event_type, stage, actor, message, payload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (f"wse_{uuid.uuid4().hex}", workstream_id, event_type, stage or ws["stage"], actor, message, _json(payload or {})),
        )
        conn.execute("UPDATE workstreams SET updated_at = datetime('now') WHERE id = ?", (workstream_id,))
        return _hydrate(conn, conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone())


def add_workstream_artifact(
    workstream_id: str,
    *,
    artifact_type: str,
    title: str,
    summary: str = "",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        ws = conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone()
        if not ws:
            raise KeyError(f"Workstream not found: {workstream_id}")
        conn.execute(
            """
            INSERT INTO workstream_artifacts(id, workstream_id, artifact_type, title, summary, payload)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (f"wsa_{uuid.uuid4().hex}", workstream_id, artifact_type, title, summary, _json(payload or {})),
        )
        conn.execute("UPDATE workstreams SET updated_at = datetime('now') WHERE id = ?", (workstream_id,))
        return _hydrate(conn, conn.execute("SELECT * FROM workstreams WHERE id = ?", (workstream_id,)).fetchone())


def latest_for_opportunity(opportunity_id: str) -> dict[str, Any] | None:
    streams = list_workstreams(opportunity_id=opportunity_id, limit=1)
    return streams[0] if streams else None
