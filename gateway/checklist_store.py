"""Emulated Telegram checklist system for the multi-agent workspace.

Native Telegram bot checklists are business-gated, so this module implements
an equivalent using persistent JSON state + inline keyboard buttons.

Checklists are stored under ``$HERMES_HOME/checklists/<id>.json`` so they
survive gateway restarts and can be toggled across sessions.

Callback data format (always ≤ 64 bytes):
  ``chk:t:<checklist_id>:<item_index>``  — toggle item done/undone
  ``chk:close:<checklist_id>``           — dismiss / close keyboard
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any, Optional


# --------------------------------------------------------------------------
# Standard checklists
# --------------------------------------------------------------------------

STANDARD_AGENT_CHECKLIST: list[str] = [
    "📥 Intake",
    "🔀 Route",
    "▶️  Run",
    "✔️  Verify",
    "📋 Summarize",
    "✅ Done",
]

STANDARD_REVIEW_CHECKLIST: list[str] = [
    "📖 Read context",
    "🔍 Identify issues",
    "💬 Draft feedback",
    "✅ Approve / request changes",
]


# --------------------------------------------------------------------------
# Storage helpers
# --------------------------------------------------------------------------

def _checklist_dir() -> Path:
    try:
        from hermes_cli.config import get_hermes_home
        d = get_hermes_home() / "checklists"
    except Exception:
        d = Path.home() / ".hermes" / "checklists"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_id(checklist_id: str) -> str:
    """Return a filesystem-safe version of *checklist_id*."""
    return re.sub(r"[^a-zA-Z0-9\-]", "", checklist_id)[:48]


def _path_for(checklist_id: str) -> Path:
    return _checklist_dir() / f"{_safe_id(checklist_id)}.json"


# --------------------------------------------------------------------------
# CRUD operations
# --------------------------------------------------------------------------

def create_checklist(
    title: str,
    items: list[str],
    chat_id: str,
    thread_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> str:
    """Persist a new checklist and return its ID."""
    checklist_id = uuid.uuid4().hex[:12]
    data: dict[str, Any] = {
        "id": checklist_id,
        "title": title,
        "items": list(items),
        "done": [False] * len(items),
        "chat_id": str(chat_id),
        "thread_id": str(thread_id) if thread_id else None,
        "user_id": str(user_id) if user_id else None,
        "created_at": time.time(),
    }
    _path_for(checklist_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return checklist_id


def get_checklist(checklist_id: str) -> Optional[dict[str, Any]]:
    """Load a checklist by ID. Returns None if not found or corrupted."""
    path = _path_for(checklist_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def toggle_item(checklist_id: str, idx: int) -> Optional[dict[str, Any]]:
    """Toggle item *idx* done/undone. Returns updated checklist or None."""
    data = get_checklist(checklist_id)
    if data is None:
        return None
    done: list[bool] = data.get("done", [])
    # Extend done list if shorter than items (defensive)
    items_len = len(data.get("items", []))
    while len(done) < items_len:
        done.append(False)
    if 0 <= idx < items_len:
        done[idx] = not done[idx]
    data["done"] = done
    _path_for(checklist_id).write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return data


def delete_checklist(checklist_id: str) -> bool:
    """Delete a persisted checklist. Returns True if deleted."""
    path = _path_for(checklist_id)
    if path.exists():
        path.unlink()
        return True
    return False


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def render_checklist_text(data: dict[str, Any]) -> str:
    """Render checklist as Markdown-compatible text for a Telegram message."""
    title = data.get("title", "Checklist")
    items: list[str] = data.get("items", [])
    done: list[bool] = data.get("done", [False] * len(items))

    lines: list[str] = [f"**{title}**", ""]
    for i, item in enumerate(items):
        is_done = i < len(done) and done[i]
        mark = "✅" if is_done else "☐"
        lines.append(f"{mark} {item}")

    completed = sum(bool(d) for d in done)
    lines.append(f"\n*{completed}/{len(items)} complete*")
    return "\n".join(lines)


def build_checklist_keyboard_rows(
    data: dict[str, Any],
) -> list[list[dict[str, str]]]:
    """Build inline-keyboard rows (as dicts) for the checklist.

    Each row is a single button that toggles one item.  A final row has a
    Close button.  All callback_data values are ≤ 64 bytes.
    """
    checklist_id: str = data["id"]
    items: list[str] = data.get("items", [])
    done: list[bool] = data.get("done", [False] * len(items))

    rows: list[list[dict[str, str]]] = []
    for i, item in enumerate(items):
        is_done = i < len(done) and done[i]
        mark = "✅" if is_done else "☐"
        short = item[:22]
        # e.g. "chk:t:abc123456789:5" = 21 bytes
        cb = f"chk:t:{checklist_id}:{i}"
        rows.append([{"text": f"{mark} {short}", "callback_data": cb}])

    # Close row
    rows.append([{"text": "✗ Close", "callback_data": f"chk:close:{checklist_id}"}])
    return rows
