from __future__ import annotations

import json
import uuid
from typing import Any

from . import db
from .audit import record_event
from .policies import HARD_BLOCKED_ACTIONS, ActionPolicyError, VALID_STATUSES, validate_transition


def _json(v: Any) -> str:
    return json.dumps(v, sort_keys=True)


def _decode(v: str | None, default: Any = None) -> Any:
    if v is None:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default


def _row_to_action(row) -> dict[str, Any]:
    d = dict(row)
    d["approval_required"] = bool(d.get("approval_required"))
    d["proposed_payload"] = _decode(d.get("proposed_payload"), {})
    d["final_payload"] = _decode(d.get("final_payload"), None)
    d["evidence_links"] = _decode(d.get("evidence_links"), [])
    d["execution_result"] = _decode(d.get("execution_result"), None)
    return d


def create_action(*, proposed_by_agent: str, action_type: str, target_system: str, target_location: str, title: str, summary: str, proposed_payload: dict[str, Any], evidence_links: list[dict[str, Any]] | None = None, risk_level: str = "low", opportunity_id: str | None = None, impact_score: int | None = None, visibility_score: int | None = None, effort_score: int | None = None, approval_reason: str | None = None, status: str = "queued") -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ActionPolicyError(f"Unknown initial action status {status!r}")
    if status not in {"drafted", "queued", "needs_review"}:
        raise ActionPolicyError("Actions cannot be created directly in approved/executed terminal states; use the approval state machine")
    db.init_db()
    action_id = f"act_{uuid.uuid4().hex}"
    evidence_links = evidence_links or []
    approval_reason = approval_reason or "External or reputation-sensitive write action"
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO action_queue(id, opportunity_id, proposed_by_agent, action_type, target_system, target_location, title, summary, proposed_payload, evidence_links, risk_level, impact_score, visibility_score, effort_score, approval_required, approval_reason, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (action_id, opportunity_id, proposed_by_agent, action_type, target_system, target_location, title, summary, _json(proposed_payload), _json(evidence_links), risk_level, impact_score, visibility_score, effort_score, approval_reason, status),
        )
    action = get_action(action_id)
    record_event(action_id=action_id, event_type="created", actor=proposed_by_agent, after_state=action)
    return action


def get_action(action_id: str) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM action_queue WHERE id = ?", (action_id,)).fetchone()
    if not row:
        raise KeyError(f"Action not found: {action_id}")
    return _row_to_action(row)


def list_actions(status: str | None = None) -> list[dict[str, Any]]:
    db.init_db()
    with db.connect() as conn:
        if status:
            rows = conn.execute("SELECT * FROM action_queue WHERE status = ? ORDER BY created_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM action_queue ORDER BY created_at DESC").fetchall()
    return [_row_to_action(r) for r in rows]


def transition_action(action_id: str, to_status: str, *, actor: str, event_type: str | None = None, updates: dict[str, Any] | None = None) -> dict[str, Any]:
    before = get_action(action_id)
    validate_transition(before["status"], to_status)
    updates = dict(updates or {})
    updates["status"] = to_status
    assignments = []
    values = []
    for key, value in updates.items():
        assignments.append(f"{key} = ?")
        if key in {"final_payload", "execution_result"}:
            values.append(_json(value))
        else:
            values.append(value)
    values.append(action_id)
    with db.connect() as conn:
        conn.execute(f"UPDATE action_queue SET {', '.join(assignments)} WHERE id = ?", tuple(values))
    after = get_action(action_id)
    record_event(action_id=action_id, event_type=event_type or to_status, actor=actor, before_state=before, after_state=after)
    return after


def approve_action(action_id: str, *, actor: str = "human") -> dict[str, Any]:
    return transition_action(action_id, "approved", actor=actor, event_type="approved", updates={"approved_by": actor, "approved_at": _now_sql()})


def edit_action(action_id: str, *, final_payload: dict[str, Any], actor: str = "human") -> dict[str, Any]:
    return transition_action(action_id, "edited_by_human", actor=actor, event_type="edited_by_human", updates={"final_payload": final_payload})


def reject_action(action_id: str, *, reason: str, actor: str = "human") -> dict[str, Any]:
    return transition_action(action_id, "rejected", actor=actor, event_type="rejected", updates={"execution_result": {"reason": reason}})


def mark_executed(action_id: str, *, actor: str, execution_result: dict[str, Any]) -> dict[str, Any]:
    return transition_action(action_id, "executed", actor=actor, event_type="executed", updates={"executed_at": _now_sql(), "execution_result": execution_result})


def mark_failed(action_id: str, *, actor: str, error: str) -> dict[str, Any]:
    return transition_action(action_id, "failed", actor=actor, event_type="failed", updates={"execution_result": {"error": error}})


def save_for_later(action_id: str, *, actor: str = "human") -> dict[str, Any]:
    before = get_action(action_id)
    record_event(action_id=action_id, event_type="saved_for_later", actor=actor, before_state=before, after_state=before)
    return before


def execute_action_guard(action_id: str) -> dict[str, Any]:
    action = get_action(action_id)
    if action["status"] != "approved":
        record_event(action_id=action_id, event_type="execution_blocked", actor="system", before_state=action, after_state={"reason": "not approved"})
        raise ActionPolicyError("Action must be approved before execution")
    if action["action_type"] in HARD_BLOCKED_ACTIONS:
        record_event(action_id=action_id, event_type="execution_blocked", actor="system", before_state=action, after_state={"reason": "hard blocked"})
        raise ActionPolicyError(f"Action type {action['action_type']} is hard-blocked and must be done manually")
    return action


def list_audit_log(action_id: str | None = None) -> list[dict[str, Any]]:
    db.init_db()
    with db.connect() as conn:
        if action_id:
            rows = conn.execute("SELECT * FROM audit_log WHERE action_id = ? ORDER BY rowid", (action_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM audit_log ORDER BY rowid DESC").fetchall()
    out = []
    for row in rows:
        d = dict(row)
        d["before_state"] = _decode(d.get("before_state"), None)
        d["after_state"] = _decode(d.get("after_state"), None)
        out.append(d)
    return out


def _now_sql() -> str:
    # Keep timestamps SQLite-compatible and deterministic enough for tests.
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
