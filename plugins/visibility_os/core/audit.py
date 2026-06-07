from __future__ import annotations

import json
import uuid
from typing import Any

from . import db


def record_event(*, action_id: str | None, event_type: str, actor: str, before_state: dict[str, Any] | None = None, after_state: dict[str, Any] | None = None) -> str:
    db.init_db()
    event_id = f"audit_{uuid.uuid4().hex}"
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO audit_log(id, action_id, event_type, actor, before_state, after_state) VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, action_id, event_type, actor, json.dumps(before_state, sort_keys=True) if before_state is not None else None, json.dumps(after_state, sort_keys=True) if after_state is not None else None),
        )
    return event_id
