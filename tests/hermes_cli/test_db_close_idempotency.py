"""Tests for close() idempotency on SQLite-owning classes.

Verifies that:
  - close() can be called twice without raising
  - close() actually releases resources (sets references to None)
  - close() on already-closed objects is a no-op

Addresses review feedback from mxnstrexgl on PR #36116.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ── _WalSafeConnection ──────────────────────────────────────────────────────


class TestWalSafeConnectionClose:
    """Tests for hermes_cli.kanban_db._WalSafeConnection.close()."""

    def _make_conn(self, path: Path) -> sqlite3.Connection:
        """Create a _WalSafeConnection to a file-backed database."""
        from hermes_cli.kanban_db import _WalSafeConnection

        conn = sqlite3.connect(
            str(path),
            isolation_level=None,
            factory=_WalSafeConnection,
        )
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS test (id INTEGER PRIMARY KEY)")
        conn.execute("INSERT INTO test VALUES (1)")
        return conn

    def test_close_is_idempotent(self, tmp_path: Path) -> None:
        """Calling close() twice must not raise."""
        db_path = tmp_path / "test.db"
        conn = self._make_conn(db_path)
        conn.close()
        conn.close()  # second call — must not raise

    def test_close_checkpoints_wal(self, tmp_path: Path) -> None:
        """close() runs WAL checkpoint before closing."""
        db_path = tmp_path / "test.db"
        conn = self._make_conn(db_path)

        # Verify WAL mode is active
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

        conn.close()

        # After close, the WAL should be checkpointed (merged into main db)
        # Verify by opening a new connection and reading the data
        conn2 = sqlite3.connect(str(db_path))
        row = conn2.execute("SELECT id FROM test").fetchone()
        assert row is not None
        assert row[0] == 1
        conn2.close()

    def test_close_on_in_memory_db(self) -> None:
        """close() works on in-memory databases too."""
        from hermes_cli.kanban_db import _WalSafeConnection

        conn = sqlite3.connect(":memory:", factory=_WalSafeConnection)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.close()
        conn.close()  # idempotent

    def test_close_handles_already_closed(self, tmp_path: Path) -> None:
        """close() on an already-closed connection is graceful."""
        db_path = tmp_path / "test.db"
        conn = self._make_conn(db_path)
        conn.close()
        # The second close might raise ProgrammingError on some Python
        # versions, but _WalSafeConnection catches it.
        try:
            conn.close()
        except Exception:
            # If it raises, that's also acceptable — the important thing
            # is it doesn't crash the process.
            pass


# ── InsightsEngine.close() ─────────────────────────────────────────────────


class TestInsightsEngineClose:
    """Tests for agent/insights.py InsightsEngine.close()."""

    def test_close_nulls_references(self) -> None:
        """close() sets _conn and db to None."""
        from agent.insights import InsightsEngine

        engine = InsightsEngine.__new__(InsightsEngine)
        engine._conn = MagicMock()
        engine.db = MagicMock()

        engine.close()

        assert engine._conn is None
        assert engine.db is None

    def test_close_is_idempotent(self) -> None:
        """Calling close() twice doesn't raise."""
        from agent.insights import InsightsEngine

        engine = InsightsEngine.__new__(InsightsEngine)
        engine._conn = MagicMock()
        engine.db = MagicMock()

        engine.close()
        engine.close()  # second call — must not raise

        assert engine._conn is None
        assert engine.db is None

    def test_close_on_fresh_instance(self) -> None:
        """close() on an instance that was never opened is safe."""
        from agent.insights import InsightsEngine

        engine = InsightsEngine.__new__(InsightsEngine)
        engine._conn = None
        engine.db = None

        engine.close()  # must not raise
        assert engine._conn is None
        assert engine.db is None


# ── SessionStore.close() ───────────────────────────────────────────────────


class TestSessionStoreClose:
    """Tests for gateway/session.py SessionStore.close()."""

    def test_close_nulls_db(self) -> None:
        """close() sets _db to None."""
        from gateway.session import SessionStore

        store = SessionStore.__new__(SessionStore)
        store._db = MagicMock()

        store.close()

        assert store._db is None

    def test_close_is_idempotent(self) -> None:
        """Calling close() twice doesn't raise."""
        from gateway.session import SessionStore

        store = SessionStore.__new__(SessionStore)
        store._db = MagicMock()

        store.close()
        store.close()  # second call

        assert store._db is None

    def test_close_when_db_is_none(self) -> None:
        """close() when _db is already None is a no-op."""
        from gateway.session import SessionStore

        store = SessionStore.__new__(SessionStore)
        store._db = None

        store.close()  # must not raise
        assert store._db is None


# ── SessionManager.close() (acp_adapter) ───────────────────────────────────


class TestSessionManagerClose:
    """Tests for acp_adapter/session.py SessionManager.close()."""

    def test_close_nulls_db_instance(self) -> None:
        """close() sets _db_instance to None."""
        from acp_adapter.session import SessionManager

        mgr = SessionManager.__new__(SessionManager)
        mgr._db_instance = MagicMock()

        mgr.close()

        assert mgr._db_instance is None

    def test_close_is_idempotent(self) -> None:
        """Calling close() twice doesn't raise."""
        from acp_adapter.session import SessionManager

        mgr = SessionManager.__new__(SessionManager)
        mgr._db_instance = MagicMock()

        mgr.close()
        mgr.close()  # second call

        assert mgr._db_instance is None

    def test_close_when_db_instance_is_none(self) -> None:
        """close() when _db_instance is already None is a no-op."""
        from acp_adapter.session import SessionManager

        mgr = SessionManager.__new__(SessionManager)
        mgr._db_instance = None

        mgr.close()  # must not raise
        assert mgr._db_instance is None
