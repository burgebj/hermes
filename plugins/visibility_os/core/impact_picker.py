from __future__ import annotations

import json
import uuid
from datetime import date
from typing import Any

from . import db
from .opportunities import list_opportunities


def generate_daily_plan() -> dict[str, Any]:
    opportunities = [o for o in list_opportunities(limit=50) if o.get("risk_penalty", 0) < 8]
    main = opportunities[0] if opportunities else None
    side = opportunities[1:3]
    comm = next((o for o in opportunities if o.get("visibility_score", 0) >= 4), main)
    plan = {
        "main_task": main,
        "side_quests": side,
        "communication_artifact": comm,
        "rationale": "Selected by priority score while excluding high reputation-risk work.",
    }
    db.init_db()
    with db.connect() as conn:
        conn.execute("INSERT INTO daily_summaries(id, date, summary_payload) VALUES (?, ?, ?)", (f"daily_{uuid.uuid4().hex}", date.today().isoformat(), json.dumps(plan, sort_keys=True)))
    return plan
