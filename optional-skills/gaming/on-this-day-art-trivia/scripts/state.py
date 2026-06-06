"""SQLite-backed state for the on-this-day-art-trivia skill.

All persistent state lives at ``$HERMES_HOME/data/on-this-day-art-trivia/trivia.db``.
The module exposes a thin connection helper (:func:`get_conn`) plus high-level
helpers for the two surfaces that need them: the skill engine (which writes
challenges, guesses, achievements) and the gateway plugin (which reads the
active challenge for a chat and records guesses).

The schema is migrated forward in :func:`migrate`. Migrations are idempotent
and additive — never drop a column. Tests instantiate this module with a
custom path via :func:`set_db_path` so the production DB is not touched.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

# --------------------------------------------------------------------------- #
# Path resolution
# --------------------------------------------------------------------------- #

_DEFAULT_HOME = Path.home() / ".hermes"
_HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(_DEFAULT_HOME)))
_DEFAULT_DB_PATH = _HERMES_HOME / "data" / "on-this-day-art-trivia" / "trivia.db"

_db_path_override: Optional[Path] = None
_path_lock = threading.Lock()


def set_db_path(path: Path | str) -> None:
    """Override the database location. Tests use this; production never does."""
    global _db_path_override
    with _path_lock:
        _db_path_override = Path(path)


def get_db_path() -> Path:
    """Resolve the active database path, honouring any test override."""
    with _path_lock:
        return _db_path_override or _DEFAULT_DB_PATH


# --------------------------------------------------------------------------- #
# Schema
# --------------------------------------------------------------------------- #

SCHEMA_STATEMENTS: Tuple[str, ...] = (
    """
    CREATE TABLE IF NOT EXISTS schema_version (
        version INTEGER PRIMARY KEY
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
        user_id              TEXT NOT NULL,
        platform             TEXT NOT NULL,
        display_name         TEXT,
        current_streak       INTEGER NOT NULL DEFAULT 0,
        longest_streak       INTEGER NOT NULL DEFAULT 0,
        last_correct_date    TEXT,
        total_correct        INTEGER NOT NULL DEFAULT 0,
        total_attempts       INTEGER NOT NULL DEFAULT 0,
        countries_correct    TEXT NOT NULL DEFAULT '[]',
        created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (platform, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS challenges (
        challenge_id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id              TEXT,
        chat_id              TEXT NOT NULL,
        platform             TEXT NOT NULL,
        scope                TEXT NOT NULL,
        event_date           TEXT NOT NULL,
        event_year           INTEGER,
        location             TEXT,
        country              TEXT,
        canonical_answer     TEXT NOT NULL,
        short_summary        TEXT,
        full_description     TEXT,
        source               TEXT,
        hint_history         TEXT NOT NULL DEFAULT '[]',
        attempts_used        INTEGER NOT NULL DEFAULT 0,
        max_attempts         INTEGER NOT NULL DEFAULT 3,
        status               TEXT NOT NULL DEFAULT 'active',
        telegram_message_id  TEXT,
        created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        resolved_at          TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_challenges_active
        ON challenges (chat_id, platform, status)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_challenges_msg
        ON challenges (platform, telegram_message_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS acceptable_answers (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_id         INTEGER NOT NULL REFERENCES challenges(challenge_id) ON DELETE CASCADE,
        alias                TEXT NOT NULL,
        alias_normalized     TEXT NOT NULL,
        precision_tier       INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_acceptable_lookup
        ON acceptable_answers (challenge_id, alias_normalized)
    """,
    """
    CREATE TABLE IF NOT EXISTS guesses (
        guess_id             INTEGER PRIMARY KEY AUTOINCREMENT,
        challenge_id         INTEGER NOT NULL REFERENCES challenges(challenge_id) ON DELETE CASCADE,
        user_id              TEXT NOT NULL,
        platform             TEXT NOT NULL,
        guess_text           TEXT NOT NULL,
        outcome              TEXT NOT NULL,
        created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS achievements (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        platform             TEXT NOT NULL,
        user_id              TEXT NOT NULL,
        achievement_key      TEXT NOT NULL,
        awarded_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (platform, user_id, achievement_key)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS subscriptions (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        platform             TEXT NOT NULL,
        user_id              TEXT NOT NULL,
        chat_id              TEXT NOT NULL,
        scope                TEXT NOT NULL,
        enabled              INTEGER NOT NULL DEFAULT 1,
        created_at           TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (platform, user_id, chat_id)
    )
    """,
)

CURRENT_SCHEMA_VERSION = 1


# --------------------------------------------------------------------------- #
# Connection helper
# --------------------------------------------------------------------------- #

@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """Yield a sqlite3 connection with WAL + FK + row-factory configured.

    Always commits on clean exit and rolls back on exception. Callers can rely
    on the connection being closed regardless.
    """
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10.0, isolation_level=None)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        conn.execute("BEGIN IMMEDIATE")
        try:
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


@contextmanager
def get_readonly_conn() -> Iterator[sqlite3.Connection]:
    """Yield a read-only connection (no transaction)."""
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=5.0)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA query_only = ON")
        yield conn
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Migration
# --------------------------------------------------------------------------- #

def migrate() -> int:
    """Bring the schema up to :data:`CURRENT_SCHEMA_VERSION`. Returns the active version."""
    with get_conn() as conn:
        for stmt in SCHEMA_STATEMENTS:
            conn.execute(stmt)
        row = conn.execute("SELECT MAX(version) AS v FROM schema_version").fetchone()
        current = row["v"] if row and row["v"] is not None else 0
        if current < CURRENT_SCHEMA_VERSION:
            conn.execute(
                "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
                (CURRENT_SCHEMA_VERSION,),
            )
            current = CURRENT_SCHEMA_VERSION
        return current


# --------------------------------------------------------------------------- #
# User helpers
# --------------------------------------------------------------------------- #

def upsert_user(platform: str, user_id: str, display_name: Optional[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO users (platform, user_id, display_name)
            VALUES (?, ?, ?)
            ON CONFLICT(platform, user_id) DO UPDATE
                SET display_name = COALESCE(excluded.display_name, users.display_name)
            """,
            (platform, user_id, display_name),
        )


def get_user(platform: str, user_id: str) -> Optional[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE platform = ? AND user_id = ?",
            (platform, user_id),
        ).fetchone()
    return dict(row) if row else None


def update_streak_after_correct(
    platform: str,
    user_id: str,
    today: str,
    country: Optional[str],
) -> Dict[str, Any]:
    """Bump streak/longest/total_correct/countries. Returns the post-update row."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE platform = ? AND user_id = ?",
            (platform, user_id),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO users (platform, user_id) VALUES (?, ?)",
                (platform, user_id),
            )
            current_streak = 0
            longest = 0
            last_date = None
            total_correct = 0
            total_attempts = 0
            countries: List[str] = []
        else:
            current_streak = int(row["current_streak"] or 0)
            longest = int(row["longest_streak"] or 0)
            last_date = row["last_correct_date"]
            total_correct = int(row["total_correct"] or 0)
            total_attempts = int(row["total_attempts"] or 0)
            try:
                countries = list(json.loads(row["countries_correct"] or "[]"))
            except (TypeError, ValueError):
                countries = []

        # Streak rule: contiguous days. Same-day repeats don't bump.
        new_streak = _next_streak(last_date, today, current_streak)
        new_longest = max(longest, new_streak)
        new_total_correct = total_correct + 1
        new_total_attempts = total_attempts + 1

        if country:
            country = country.strip()
            if country and country not in countries:
                countries.append(country)

        conn.execute(
            """
            UPDATE users SET
                current_streak    = ?,
                longest_streak    = ?,
                last_correct_date = ?,
                total_correct     = ?,
                total_attempts    = ?,
                countries_correct = ?
            WHERE platform = ? AND user_id = ?
            """,
            (
                new_streak, new_longest, today,
                new_total_correct, new_total_attempts,
                json.dumps(countries),
                platform, user_id,
            ),
        )
        return {
            "current_streak": new_streak,
            "longest_streak": new_longest,
            "total_correct": new_total_correct,
            "total_attempts": new_total_attempts,
            "countries": countries,
        }


def update_after_wrong(platform: str, user_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO users (platform, user_id) VALUES (?, ?)",
            (platform, user_id),
        )
        conn.execute(
            "UPDATE users SET total_attempts = total_attempts + 1 WHERE platform = ? AND user_id = ?",
            (platform, user_id),
        )


def reset_streak(platform: str, user_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET current_streak = 0 WHERE platform = ? AND user_id = ?",
            (platform, user_id),
        )


def _next_streak(last_correct_date: Optional[str], today: str, current_streak: int) -> int:
    """Compute the new streak count based on yesterday/today logic.

    last_correct_date and today are ISO YYYY-MM-DD strings. A gap of 1 day
    increments; same day keeps; gap of >1 resets to 1.
    """
    if not last_correct_date:
        return 1
    from datetime import date
    try:
        prev = date.fromisoformat(last_correct_date)
        cur = date.fromisoformat(today)
    except ValueError:
        return 1
    delta = (cur - prev).days
    if delta == 0:
        return current_streak if current_streak > 0 else 1
    if delta == 1:
        return current_streak + 1
    return 1


# --------------------------------------------------------------------------- #
# Challenge helpers
# --------------------------------------------------------------------------- #

def create_challenge(
    *,
    platform: str,
    chat_id: str,
    scope: str,
    user_id: Optional[str],
    event_date: str,
    event_year: Optional[int],
    location: Optional[str],
    country: Optional[str],
    canonical_answer: str,
    short_summary: Optional[str],
    full_description: Optional[str],
    source: Optional[str],
    aliases: Iterable[Tuple[str, int]],
    max_attempts: int = 3,
) -> int:
    """Create an active challenge and its acceptable answers. Returns challenge_id."""
    from .guess_matcher import normalize  # local import avoids circular

    with get_conn() as conn:
        # Mark any prior active challenge in this chat as expired.
        conn.execute(
            """
            UPDATE challenges SET status = 'expired', resolved_at = CURRENT_TIMESTAMP
            WHERE platform = ? AND chat_id = ? AND status = 'active'
            """,
            (platform, chat_id),
        )
        cur = conn.execute(
            """
            INSERT INTO challenges (
                user_id, chat_id, platform, scope,
                event_date, event_year, location, country,
                canonical_answer, short_summary, full_description, source,
                max_attempts
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id, chat_id, platform, scope,
                event_date, event_year, location, country,
                canonical_answer, short_summary, full_description, source,
                max_attempts,
            ),
        )
        challenge_id = int(cur.lastrowid)
        for alias, tier in aliases:
            conn.execute(
                "INSERT INTO acceptable_answers (challenge_id, alias, alias_normalized, precision_tier) VALUES (?, ?, ?, ?)",
                (challenge_id, alias, normalize(alias), int(tier)),
            )
        return challenge_id


def attach_telegram_message_id(challenge_id: int, message_id: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE challenges SET telegram_message_id = ? WHERE challenge_id = ?",
            (str(message_id), int(challenge_id)),
        )


def get_challenge(challenge_id: int) -> Optional[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        row = conn.execute(
            "SELECT * FROM challenges WHERE challenge_id = ?",
            (int(challenge_id),),
        ).fetchone()
    return dict(row) if row else None


def get_active_challenge_for_chat(platform: str, chat_id: str) -> Optional[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        row = conn.execute(
            """
            SELECT * FROM challenges
            WHERE platform = ? AND chat_id = ? AND status = 'active'
            ORDER BY created_at DESC LIMIT 1
            """,
            (platform, chat_id),
        ).fetchone()
    return dict(row) if row else None


def get_challenge_by_message_id(platform: str, message_id: str) -> Optional[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        row = conn.execute(
            "SELECT * FROM challenges WHERE platform = ? AND telegram_message_id = ?",
            (platform, str(message_id)),
        ).fetchone()
    return dict(row) if row else None


def list_acceptable_answers(challenge_id: int) -> List[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        rows = conn.execute(
            "SELECT alias, alias_normalized, precision_tier FROM acceptable_answers WHERE challenge_id = ?",
            (int(challenge_id),),
        ).fetchall()
    return [dict(r) for r in rows]


def record_guess(
    challenge_id: int,
    platform: str,
    user_id: str,
    guess_text: str,
    outcome: str,
) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO guesses (challenge_id, platform, user_id, guess_text, outcome) VALUES (?, ?, ?, ?, ?)",
            (int(challenge_id), platform, user_id, guess_text, outcome),
        )


def increment_attempts(challenge_id: int) -> int:
    with get_conn() as conn:
        conn.execute(
            "UPDATE challenges SET attempts_used = attempts_used + 1 WHERE challenge_id = ?",
            (int(challenge_id),),
        )
        row = conn.execute(
            "SELECT attempts_used, max_attempts FROM challenges WHERE challenge_id = ?",
            (int(challenge_id),),
        ).fetchone()
    return int(row["attempts_used"]) if row else 0


def append_hint(challenge_id: int, hint_text: str) -> List[str]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT hint_history FROM challenges WHERE challenge_id = ?",
            (int(challenge_id),),
        ).fetchone()
        try:
            history = list(json.loads(row["hint_history"] or "[]")) if row else []
        except (TypeError, ValueError):
            history = []
        history.append(hint_text)
        conn.execute(
            "UPDATE challenges SET hint_history = ? WHERE challenge_id = ?",
            (json.dumps(history), int(challenge_id)),
        )
        return history


def resolve_challenge(challenge_id: int, status: str) -> None:
    if status not in {"solved", "failed", "revealed", "expired"}:
        raise ValueError(f"Invalid status: {status!r}")
    with get_conn() as conn:
        conn.execute(
            "UPDATE challenges SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE challenge_id = ?",
            (status, int(challenge_id)),
        )


def count_wrong_guesses(challenge_id: int, user_id: str) -> int:
    with get_readonly_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM guesses WHERE challenge_id = ? AND user_id = ? AND outcome IN ('wrong', 'close')",
            (int(challenge_id), user_id),
        ).fetchone()
    return int(row["n"]) if row else 0


def count_hints_used(challenge_id: int) -> int:
    with get_readonly_conn() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM guesses WHERE challenge_id = ? AND outcome = 'hint'",
            (int(challenge_id),),
        ).fetchone()
    return int(row["n"]) if row else 0


# --------------------------------------------------------------------------- #
# Achievement helpers
# --------------------------------------------------------------------------- #

def award_achievement(platform: str, user_id: str, key: str) -> bool:
    """Award an achievement. Returns True if newly awarded."""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO achievements (platform, user_id, achievement_key) VALUES (?, ?, ?)",
            (platform, user_id, key),
        )
        return cur.rowcount > 0


def list_achievements(platform: str, user_id: str) -> List[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        rows = conn.execute(
            "SELECT achievement_key, awarded_at FROM achievements WHERE platform = ? AND user_id = ? ORDER BY awarded_at",
            (platform, user_id),
        ).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #
# Subscription helpers
# --------------------------------------------------------------------------- #

def add_subscription(platform: str, user_id: str, chat_id: str, scope: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO subscriptions (platform, user_id, chat_id, scope, enabled)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(platform, user_id, chat_id) DO UPDATE SET enabled = 1, scope = excluded.scope
            """,
            (platform, user_id, chat_id, scope),
        )


def remove_subscription(platform: str, user_id: str, chat_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE subscriptions SET enabled = 0 WHERE platform = ? AND user_id = ? AND chat_id = ?",
            (platform, user_id, chat_id),
        )
        return cur.rowcount > 0


def list_active_subscriptions() -> List[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        rows = conn.execute(
            "SELECT platform, user_id, chat_id, scope FROM subscriptions WHERE enabled = 1"
        ).fetchall()
    return [dict(r) for r in rows]


# --------------------------------------------------------------------------- #
# Leaderboard
# --------------------------------------------------------------------------- #

def leaderboard_top(platform: str, limit: int = 10) -> List[Dict[str, Any]]:
    with get_readonly_conn() as conn:
        rows = conn.execute(
            """
            SELECT user_id, display_name, current_streak, longest_streak, total_correct
            FROM users WHERE platform = ?
            ORDER BY total_correct DESC, longest_streak DESC, current_streak DESC
            LIMIT ?
            """,
            (platform, int(limit)),
        ).fetchall()
    return [dict(r) for r in rows]
