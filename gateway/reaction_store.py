"""SQLite-backed sink for :class:`gateway.reactions.ReactionEvent` (issue #27438).

Keeps reaction history in a dedicated ``reactions.db`` under ``HERMES_HOME``
rather than co-locating with ``state.db``.  Rationale:

* state.db's schema is owned by :mod:`hermes_state` and has its own
  versioned migration machinery; touching it for an opt-in feature would
  add migration risk for every user.
* A separate file means cleanup is trivial (delete one file) and the data
  is profile-scoped automatically via the existing HERMES_HOME alignment
  (issue #27250).

The WAL/fallback pattern, schema-version table and ``apply_wal_with_fallback``
helper are re-used from :mod:`hermes_state` so behaviour on NFS/SMB matches
the rest of Hermes.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from gateway.reactions import (
    DEFAULT_REACTION_WEIGHTS,
    ReactionEvent,
    ReactionPolarity,
    ReactionSignal,
)
from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)


SCHEMA_VERSION = 1


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS reaction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    actor_user_id TEXT NOT NULL,
    target_message_id TEXT NOT NULL,
    emoji TEXT NOT NULL,
    label TEXT NOT NULL,
    weight REAL NOT NULL,
    polarity TEXT NOT NULL,
    added INTEGER NOT NULL DEFAULT 1,
    ts REAL NOT NULL,
    platform_data TEXT
);

CREATE INDEX IF NOT EXISTS idx_reaction_events_target
    ON reaction_events(platform, channel_id, target_message_id);
CREATE INDEX IF NOT EXISTS idx_reaction_events_actor
    ON reaction_events(platform, actor_user_id, ts);
CREATE INDEX IF NOT EXISTS idx_reaction_events_ts
    ON reaction_events(ts);
"""


def default_reactions_db_path() -> Path:
    """Resolved on every call so profile switches at startup are respected."""
    return get_hermes_home() / "reactions.db"


def _apply_wal_with_fallback(conn: sqlite3.Connection, db_label: str) -> str:
    """Local copy of :func:`hermes_state.apply_wal_with_fallback`.

    We delegate to :mod:`hermes_state` when it's importable but inline a
    fallback so this module stays usable from contexts that haven't
    imported the full session-DB module yet (e.g. lightweight CLI
    smoke tests).
    """
    try:
        from hermes_state import apply_wal_with_fallback
    except Exception:
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            return "wal"
        except sqlite3.OperationalError:
            conn.execute("PRAGMA journal_mode=DELETE")
            return "delete"
    return apply_wal_with_fallback(conn, db_label=db_label)


class ReactionStore:
    """Thread-safe writer + reader for ``reactions.db``.

    Designed for single-process gateway use (one writer, many readers).
    All write methods serialise on an internal lock so callers can fan out
    concurrent reaction handlers without worrying about ``database is
    locked``.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = Path(db_path) if db_path else default_reactions_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(
            str(self.db_path),
            isolation_level=None,  # autocommit; we use explicit BEGIN where needed
            timeout=10.0,
        )
        conn.row_factory = sqlite3.Row
        try:
            _apply_wal_with_fallback(conn, db_label="reactions.db")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            row = conn.execute("SELECT version FROM schema_version LIMIT 1").fetchone()
            if row is None:
                conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
            elif row["version"] != SCHEMA_VERSION:
                # Future-proofing.  v1 has no migration logic yet.
                logger.warning(
                    "reactions.db schema_version=%s but code expected %s; "
                    "future versions will migrate.",
                    row["version"], SCHEMA_VERSION,
                )

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    def record(self, event: ReactionEvent) -> int:
        """Persist ``event``.  Returns the row id.

        Idempotent at the row level: every reaction tap creates a new row,
        which is the right model because Telegram/Discord/Slack each emit
        separate add and remove events that we want to preserve as a full
        engagement timeline.  Aggregations are computed at read time via
        :meth:`aggregate_for_message`.
        """
        platform_data_json = (
            json.dumps(event.platform_data, separators=(",", ":")) if event.platform_data else None
        )
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO reaction_events (
                    platform, channel_id, actor_user_id, target_message_id,
                    emoji, label, weight, polarity, added, ts, platform_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.platform,
                    event.channel_id,
                    event.actor_user_id,
                    event.target_message_id,
                    event.emoji,
                    event.signal.label,
                    event.weight,
                    event.polarity.value,
                    1 if event.added else 0,
                    event.timestamp.timestamp(),
                    platform_data_json,
                ),
            )
            return int(cursor.lastrowid)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    def aggregate_for_message(
        self,
        *,
        platform: str,
        channel_id: str,
        target_message_id: str,
        since: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Return summed weight and counts for one message.

        ``added=0`` rows (removals) subtract a prior add of the same emoji
        from the same user.  This matches user intent ("I changed my mind")
        without trying to reconstruct full per-user state per emoji.
        """
        params: List[Any] = [platform, channel_id, target_message_id]
        clauses = "platform = ? AND channel_id = ? AND target_message_id = ?"
        if since is not None:
            clauses += " AND ts >= ?"
            params.append(since.timestamp())
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT emoji, label, polarity, weight, added, actor_user_id
                FROM reaction_events
                WHERE {clauses}
                ORDER BY ts ASC
                """,
                params,
            ).fetchall()
        net_weight = 0.0
        positive = 0
        negative = 0
        neutral = 0
        unique_users: set[str] = set()
        for r in rows:
            sign = 1 if r["added"] else -1
            net_weight += sign * r["weight"]
            polarity = r["polarity"]
            if r["added"]:
                if polarity == ReactionPolarity.POSITIVE.value:
                    positive += 1
                elif polarity == ReactionPolarity.NEGATIVE.value:
                    negative += 1
                else:
                    neutral += 1
                unique_users.add(r["actor_user_id"])
        return {
            "platform": platform,
            "channel_id": channel_id,
            "target_message_id": target_message_id,
            "net_weight": net_weight,
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "unique_users": len(unique_users),
            "sample_count": len(rows),
        }

    def recent_for_user(
        self,
        *,
        platform: str,
        actor_user_id: str,
        limit: int = 50,
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Most-recent reactions tapped by a single user (newest first)."""
        params: List[Any] = [platform, actor_user_id]
        clauses = "platform = ? AND actor_user_id = ?"
        if since is not None:
            clauses += " AND ts >= ?"
            params.append(since.timestamp())
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT id, platform, channel_id, actor_user_id,
                       target_message_id, emoji, label, weight, polarity,
                       added, ts
                FROM reaction_events
                WHERE {clauses}
                ORDER BY ts DESC
                LIMIT ?
                """,
                params + [int(limit)],
            ).fetchall()
        return [dict(r) for r in rows]

    def prune_older_than(self, days: int) -> int:
        """Delete rows older than ``days``.  Returns the number deleted.

        Called by callers honouring :attr:`ReactionConfig.decay_days`.  We
        don't auto-run this on every write -- the housekeeping cadence is
        the caller's choice.
        """
        if days <= 0:
            return 0
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).timestamp()
        with self._lock, self._connect() as conn:
            cursor = conn.execute("DELETE FROM reaction_events WHERE ts < ?", (cutoff,))
            return cursor.rowcount or 0

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS n FROM reaction_events").fetchone()
            return int(row["n"])


# ---------------------------------------------------------------------------
# Process-global singleton (lazy)
# ---------------------------------------------------------------------------


_store_lock = threading.Lock()
_store_instance: Optional[ReactionStore] = None


def get_reaction_store(db_path: Optional[Path] = None) -> ReactionStore:
    """Return the per-process :class:`ReactionStore`.

    Created on first use and cached.  Pass ``db_path`` only in tests --
    in production the path is resolved from ``HERMES_HOME`` and we want a
    single shared store so the gateway and slash-commands see the same
    history.
    """
    global _store_instance
    with _store_lock:
        if _store_instance is None or db_path is not None:
            _store_instance = ReactionStore(db_path=db_path)
        return _store_instance


def reset_reaction_store_for_tests() -> None:
    """Drop the cached singleton.  Tests only."""
    global _store_instance
    with _store_lock:
        _store_instance = None


__all__ = [
    "ReactionStore",
    "default_reactions_db_path",
    "get_reaction_store",
    "reset_reaction_store_for_tests",
    # Re-exports for callers that want one import.
    "ReactionEvent",
    "ReactionSignal",
    "ReactionPolarity",
    "DEFAULT_REACTION_WEIGHTS",
]
