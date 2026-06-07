from __future__ import annotations

import json
import uuid
from typing import Any

from . import db


def _decode(v: str | None, default: Any) -> Any:
    if not v:
        return default
    try:
        return json.loads(v)
    except Exception:
        return default


def row_to_opportunity(row) -> dict[str, Any]:
    d = dict(row)
    d["suggested_artifacts"] = _decode(d.get("suggested_artifacts"), [])
    d["metadata"] = _decode(d.get("metadata"), {})
    return d


def upsert_opportunity(*, source_system: str, source_url: str | None, title: str, description: str, category: str, impact_score: int, visibility_score: int, effort_score: int, safety_score: int, risk_penalty: int, priority_score: int, suggested_artifacts: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    db.init_db()
    oid = f"opp_{uuid.uuid4().hex}"
    suggested_artifacts = suggested_artifacts or []
    metadata = metadata or {}
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO opportunities(id, source_system, source_url, title, description, category, impact_score, visibility_score, effort_score, safety_score, risk_penalty, priority_score, suggested_artifacts, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_system, source_url, category) DO UPDATE SET
              title=excluded.title, description=excluded.description, impact_score=excluded.impact_score,
              visibility_score=excluded.visibility_score, effort_score=excluded.effort_score, safety_score=excluded.safety_score,
              risk_penalty=excluded.risk_penalty, priority_score=excluded.priority_score,
              suggested_artifacts=excluded.suggested_artifacts, metadata=excluded.metadata,
              updated_at=datetime('now')
            """,
            (oid, source_system, source_url, title, description, category, impact_score, visibility_score, effort_score, safety_score, risk_penalty, priority_score, json.dumps(suggested_artifacts), json.dumps(metadata, sort_keys=True)),
        )
        row = conn.execute("SELECT * FROM opportunities WHERE source_system = ? AND source_url IS ? AND category = ?", (source_system, source_url, category)).fetchone()
    return row_to_opportunity(row)


def get_opportunity(opportunity_id: str) -> dict[str, Any]:
    db.init_db()
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE id = ?", (opportunity_id,)).fetchone()
    if not row:
        raise KeyError(f"Opportunity not found: {opportunity_id}")
    return row_to_opportunity(row)


def mark_opportunity_resolved_by_source(source_system: str, source_url: str | None, category: str, *, reason: str) -> dict[str, Any] | None:
    if not source_url:
        return None
    db.init_db()
    with db.connect() as conn:
        row = conn.execute("SELECT * FROM opportunities WHERE source_system = ? AND source_url IS ? AND category = ?", (source_system, source_url, category)).fetchone()
        if not row:
            return None
        metadata = row_to_opportunity(row).get("metadata") or {}
        metadata["resolved_reason"] = reason
        conn.execute(
            "UPDATE opportunities SET status = ?, metadata = ?, updated_at = datetime('now') WHERE id = ?",
            ("resolved", json.dumps(metadata, sort_keys=True), row["id"]),
        )
        updated = conn.execute("SELECT * FROM opportunities WHERE id = ?", (row["id"],)).fetchone()
    return row_to_opportunity(updated)


def list_opportunities(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    db.init_db()
    with db.connect() as conn:
        if status:
            rows = conn.execute("SELECT * FROM opportunities WHERE status = ? ORDER BY priority_score DESC, updated_at DESC LIMIT ?", (status, limit)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM opportunities ORDER BY priority_score DESC, updated_at DESC LIMIT ?", (limit,)).fetchall()
    return [row_to_opportunity(r) for r in rows]
