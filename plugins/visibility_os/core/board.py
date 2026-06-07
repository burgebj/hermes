from __future__ import annotations

from typing import Any

from . import db

VALID_BOARD_STATES = {"todo", "in_progress", "in_review", "done", "archived"}


def set_board_state(*, item_kind: str, item_id: str, board_state: str, actor: str = "human") -> dict[str, Any]:
    if item_kind not in {"opportunity", "action"}:
        raise ValueError(f"Unsupported board item kind {item_kind!r}")
    if board_state not in VALID_BOARD_STATES:
        raise ValueError(f"Unsupported board state {board_state!r}")
    db.init_db()
    with db.connect() as conn:
        conn.execute(
            """
            INSERT INTO board_item_states(item_kind, item_id, board_state, actor, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(item_kind, item_id) DO UPDATE SET
              board_state=excluded.board_state,
              actor=excluded.actor,
              updated_at=datetime('now')
            """,
            (item_kind, item_id, board_state, actor),
        )
        row = conn.execute(
            "SELECT item_kind, item_id, board_state, actor, updated_at FROM board_item_states WHERE item_kind = ? AND item_id = ?",
            (item_kind, item_id),
        ).fetchone()
    return dict(row)


def get_board_states() -> dict[tuple[str, str], dict[str, Any]]:
    db.init_db()
    with db.connect() as conn:
        rows = conn.execute("SELECT item_kind, item_id, board_state, actor, updated_at FROM board_item_states").fetchall()
    return {(row["item_kind"], row["item_id"]): dict(row) for row in rows}
