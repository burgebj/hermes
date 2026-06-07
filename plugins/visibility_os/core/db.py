from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from hermes_constants import get_hermes_home

DB_FILENAME = "visibility_os.db"
SCHEMA_VERSION = 2


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
        conn.executescript("""
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
            suggested_artifacts TEXT NOT NULL DEFAULT '[]',
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_visibility_opportunity_source
            ON opportunities(source_system, source_url, category);

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
        CREATE INDEX IF NOT EXISTS idx_visibility_action_status ON action_queue(status);

        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            action_id TEXT REFERENCES action_queue(id),
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            before_state TEXT,
            after_state TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_visibility_audit_action ON audit_log(action_id);

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

        CREATE TABLE IF NOT EXISTS workstreams (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT REFERENCES opportunities(id),
            root_action_id TEXT REFERENCES action_queue(id),
            lane_kind TEXT NOT NULL,
            title TEXT NOT NULL,
            repo TEXT,
            source_url TEXT,
            stage TEXT NOT NULL,
            status TEXT NOT NULL,
            started_at TEXT,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            completed_at TEXT,
            agent_session_id TEXT,
            summary TEXT NOT NULL DEFAULT '',
            current_step TEXT NOT NULL DEFAULT '',
            progress_percent INTEGER NOT NULL DEFAULT 0,
            result_payload TEXT NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_visibility_workstreams_status ON workstreams(status);
        CREATE INDEX IF NOT EXISTS idx_visibility_workstreams_opportunity ON workstreams(opportunity_id);
        CREATE INDEX IF NOT EXISTS idx_visibility_workstreams_root_action ON workstreams(root_action_id);

        CREATE TABLE IF NOT EXISTS workstream_events (
            id TEXT PRIMARY KEY,
            workstream_id TEXT NOT NULL REFERENCES workstreams(id),
            event_type TEXT NOT NULL,
            stage TEXT,
            actor TEXT NOT NULL,
            message TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_visibility_workstream_events_ws ON workstream_events(workstream_id, created_at);

        CREATE TABLE IF NOT EXISTS workstream_artifacts (
            id TEXT PRIMARY KEY,
            workstream_id TEXT NOT NULL REFERENCES workstreams(id),
            artifact_type TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL DEFAULT '',
            payload TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_visibility_workstream_artifacts_ws ON workstream_artifacts(workstream_id, artifact_type);

        CREATE TABLE IF NOT EXISTS board_item_states (
            item_kind TEXT NOT NULL,
            item_id TEXT NOT NULL,
            board_state TEXT NOT NULL,
            actor TEXT NOT NULL DEFAULT 'human',
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY(item_kind, item_id)
        );
        CREATE INDEX IF NOT EXISTS idx_visibility_board_state ON board_item_states(board_state);
        """)
        conn.execute("INSERT OR IGNORE INTO schema_migrations(version) VALUES (?)", (SCHEMA_VERSION,))
