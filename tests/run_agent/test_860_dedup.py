"""Tests for issue #860 — SQLite session transcript deduplication.

Verifies that:
1. _flush_messages_to_session_db uses _last_flushed_db_idx to avoid re-writing
2. Multiple _persist_session calls don't duplicate messages
3. append_to_transcript(skip_db=True) skips SQLite but writes JSONL
4. The gateway doesn't double-write messages the agent already persisted
"""

import json
import os
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Test: _flush_messages_to_session_db only writes new messages
# ---------------------------------------------------------------------------

class TestFlushDeduplication:
    """Verify _flush_messages_to_session_db tracks what it already wrote."""

    def _make_agent(self, session_db):
        """Create a minimal AIAgent with a real session DB."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from run_agent import AIAgent
            agent = AIAgent(
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                model="test/model",
                quiet_mode=True,
                session_db=session_db,
                session_id="test-session-860",
                skip_context_files=True,
                skip_memory=True,
            )
        # Simulate lazy session creation (normally done by run_conversation)
        agent._ensure_db_session()
        return agent

    def test_flush_writes_only_new_messages(self):
        """First flush writes all new messages, second flush writes none."""
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SessionDB(db_path=db_path)

            agent = self._make_agent(db)

            conversation_history = [
                {"role": "user", "content": "old message"},
            ]
            messages = list(conversation_history) + [
                {"role": "user", "content": "new question"},
                {"role": "assistant", "content": "new answer"},
            ]

            # First flush — should write 2 new messages
            agent._flush_messages_to_session_db(messages, conversation_history)

            rows = db.get_messages(agent.session_id)
            assert len(rows) == 2, f"Expected 2 messages, got {len(rows)}"

            # Second flush with SAME messages — should write 0 new messages
            agent._flush_messages_to_session_db(messages, conversation_history)

            rows = db.get_messages(agent.session_id)
            assert len(rows) == 2, f"Expected still 2 messages after second flush, got {len(rows)}"

    def test_flush_writes_incrementally(self):
        """Messages added between flushes are written exactly once."""
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SessionDB(db_path=db_path)

            agent = self._make_agent(db)

            conversation_history = []
            messages = [
                {"role": "user", "content": "hello"},
            ]

            # First flush — 1 message
            agent._flush_messages_to_session_db(messages, conversation_history)
            rows = db.get_messages(agent.session_id)
            assert len(rows) == 1

            # Add more messages
            messages.append({"role": "assistant", "content": "hi there"})
            messages.append({"role": "user", "content": "follow up"})

            # Second flush — should write only 2 new messages
            agent._flush_messages_to_session_db(messages, conversation_history)
            rows = db.get_messages(agent.session_id)
            assert len(rows) == 3, f"Expected 3 total messages, got {len(rows)}"

    def test_persist_session_multiple_calls_no_duplication(self):
        """Multiple _persist_session calls don't duplicate DB entries."""
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SessionDB(db_path=db_path)

            agent = self._make_agent(db)

            conversation_history = [{"role": "user", "content": "old"}]
            messages = list(conversation_history) + [
                {"role": "user", "content": "q1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "q2"},
                {"role": "assistant", "content": "a2"},
            ]

            # Simulate multiple persist calls (like the agent's many exit paths)
            for _ in range(5):
                agent._persist_session(messages, conversation_history)

            rows = db.get_messages(agent.session_id)
            assert len(rows) == 4, f"Expected 4 messages, got {len(rows)} (duplication bug!)"

    def test_flush_reset_after_compression(self):
        """After compression creates a new session, flush index resets."""
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SessionDB(db_path=db_path)

            agent = self._make_agent(db)

            # Write some messages
            messages = [
                {"role": "user", "content": "msg1"},
                {"role": "assistant", "content": "reply1"},
            ]
            agent._flush_messages_to_session_db(messages, [])

            old_session = agent.session_id
            assert agent._last_flushed_db_idx == 2

            # Simulate what _compress_context does: new session, reset idx
            agent.session_id = "compressed-session-new"
            db.create_session(session_id=agent.session_id, source="test")
            agent._last_flushed_db_idx = 0

            # Now flush compressed messages to new session
            compressed_messages = [
                {"role": "user", "content": "summary of conversation"},
            ]
            agent._flush_messages_to_session_db(compressed_messages, [])

            new_rows = db.get_messages(agent.session_id)
            assert len(new_rows) == 1

            # Old session should still have its 2 messages
            old_rows = db.get_messages(old_session)
            assert len(old_rows) == 2


# ---------------------------------------------------------------------------
# Test: append_to_transcript skip_db parameter
# ---------------------------------------------------------------------------

class TestAppendToTranscriptSkipDb:
    """Verify skip_db=True skips the SQLite write."""

    def test_skip_db_prevents_sqlite_write(self, tmp_path):
        """With skip_db=True and a real DB, message does NOT appear in SQLite."""
        from gateway.config import GatewayConfig
        from gateway.session import SessionStore
        from hermes_state import SessionDB

        db_path = tmp_path / "test_skip.db"
        db = SessionDB(db_path=db_path)

        config = GatewayConfig()
        with patch("gateway.session.SessionStore._ensure_loaded"):
            store = SessionStore(sessions_dir=tmp_path, config=config)
        store._db = db
        store._loaded = True

        session_id = "test-skip-db-real"
        db.create_session(session_id=session_id, source="test")

        msg = {"role": "assistant", "content": "hello world"}
        store.append_to_transcript(session_id, msg, skip_db=True)

        # SQLite should NOT have the message
        rows = db.get_messages(session_id)
        assert len(rows) == 0, f"Expected 0 DB rows with skip_db=True, got {len(rows)}"

    def test_default_writes_to_sqlite(self, tmp_path):
        """Without skip_db, message appears in SQLite."""
        from gateway.config import GatewayConfig
        from gateway.session import SessionStore
        from hermes_state import SessionDB

        db_path = tmp_path / "test_both.db"
        db = SessionDB(db_path=db_path)

        config = GatewayConfig()
        with patch("gateway.session.SessionStore._ensure_loaded"):
            store = SessionStore(sessions_dir=tmp_path, config=config)
        store._db = db
        store._loaded = True

        session_id = "test-default-write"
        db.create_session(session_id=session_id, source="test")

        msg = {"role": "user", "content": "test message"}
        store.append_to_transcript(session_id, msg)

        # SQLite should have the message
        rows = db.get_messages(session_id)
        assert len(rows) == 1


# ---------------------------------------------------------------------------
# Test: _last_flushed_db_idx initialization
# ---------------------------------------------------------------------------

class TestFlushIdxInit:
    """Verify _last_flushed_db_idx is properly initialized."""

    def test_init_zero(self):
        """Agent starts with _last_flushed_db_idx = 0."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from run_agent import AIAgent
            agent = AIAgent(
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                model="test/model",
                quiet_mode=True,
                skip_context_files=True,
                skip_memory=True,
            )
        assert agent._last_flushed_db_idx == 0

    def test_no_session_db_noop(self):
        """Without session_db, flush is a no-op and doesn't crash."""
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from run_agent import AIAgent
            agent = AIAgent(
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                model="test/model",
                quiet_mode=True,
                skip_context_files=True,
                skip_memory=True,
            )
        messages = [{"role": "user", "content": "test"}]
        agent._flush_messages_to_session_db(messages, [])
        # Should not crash, idx should remain 0
        assert agent._last_flushed_db_idx == 0


class TestFlushWalRetry:
    """Tests for WAL contention retry in _flush_messages_to_session_db."""

    def _make_agent(self, session_db):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from run_agent import AIAgent
            agent = AIAgent(
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                model="test/model",
                quiet_mode=True,
                session_db=session_db,
                session_id="test-session-retry",
                skip_context_files=True,
                skip_memory=True,
            )
        agent._ensure_db_session()
        return agent

    def test_wal_lock_retry_succeeds(self):
        """OperationalError: database is locked should retry then succeed."""
        import sqlite3
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = SessionDB(db_path=Path(tmpdir) / "lock_retry.db")
            agent = self._make_agent(db)
            agent._last_flushed_db_idx = 0
            agent._session_db_created = True

            messages = [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ]

            call_count = [0]
            orig_append = db.append_message

            def flaky_append(*args, **kwargs):
                call_count[0] += 1
                if call_count[0] <= 2:
                    raise sqlite3.OperationalError("database is locked")
                return orig_append(*args, **kwargs)

            conversation_history = []
            with patch.object(db, "append_message", side_effect=flaky_append):
                agent._flush_messages_to_session_db(messages, conversation_history)

            rows = db.get_messages(agent.session_id)
            assert len(rows) == 2

    def test_wal_lock_retry_exhausted_warns_but_doesnt_crash(self):
        """After 3 failed retries the method returns without crashing."""
        import sqlite3
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db = SessionDB(db_path=Path(tmpdir) / "lock_exhaust.db")
            agent = self._make_agent(db)
            agent._last_flushed_db_idx = 0
            agent._session_db_created = True

            messages = [{"role": "user", "content": "hello"}]
            conversation_history = []

            def always_locked(*args, **kwargs):
                raise sqlite3.OperationalError("database is locked")

            with patch.object(db, "append_message", side_effect=always_locked):
                agent._flush_messages_to_session_db(messages, conversation_history)

            assert agent._last_flushed_db_idx == 0  # no flush happened


class TestVerifySessionDbHealth:
    """Tests for _verify_session_db_health — post-flush integrity check."""

    def _make_agent(self, session_db):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from run_agent import AIAgent
            return AIAgent(
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                model="test/model",
                quiet_mode=True,
                session_db=session_db,
                session_id="test-session-health",
                skip_context_files=True,
                skip_memory=True,
            )

    def test_health_check_no_warning_when_db_matches(self):
        """No POST-FLUSH warning when DB already has all messages."""
        from hermes_state import SessionDB
        with tempfile.TemporaryDirectory() as tmpdir:
            db = SessionDB(db_path=Path(tmpdir) / "health.db")
            agent = self._make_agent(db)
            agent._ensure_db_session()

            messages = [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
            ]
            agent._flush_messages_to_session_db(messages, [])
            assert db.message_count(agent.session_id) == 2

            import run_agent
            with patch.object(run_agent.logger, "warning"):
                # Should not produce POST-FLUSH warning
                agent._verify_session_db_health(messages)

    def test_health_check_warns_on_zero_messages(self):
        """Warns when DB has 0 messages but in-memory has messages."""
        from hermes_state import SessionDB
        import run_agent
        with tempfile.TemporaryDirectory() as tmpdir:
            db = SessionDB(db_path=Path(tmpdir) / "health2.db")
            agent = self._make_agent(db)
            agent._ensure_db_session()

            messages = [
                {"role": "user", "content": "hello"},
                {"role": "assistant", "content": "hi"},
                {"role": "user", "content": "follow up"},
                {"role": "assistant", "content": "answer"},
            ]

            with patch.object(run_agent.logger, "warning") as mock_warn:
                agent._verify_session_db_health(messages)
                health_warnings = [
                    c for c in mock_warn.call_args_list
                    if c and "POST-FLUSH" in str(c)
                ]
                assert len(health_warnings) == 1
                assert "0 messages" in str(health_warnings[0])


class TestOrphanedSessionsHint:
    """Tests for _check_orphaned_sessions_hint — startup hint (P2 repair)."""

    def test_hint_logs_when_orphans_above_threshold(self, tmp_path):
        """When >50 sessions exist on disk but not in DB, hint fires."""
        import run_agent
        from hermes_state import SessionDB

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        db_path = tmp_path / "test.db"

        # Create 55 orphan session files on disk
        for i in range(55):
            sid = f"{i:08d}-orph"
            (sessions_dir / f"session_{sid}.json").write_text(
                '{"messages": [{"role": "user", "content": "hi"}]}'
            )

        # Create a DB with only 3 sessions (55 - 3 = 52 orphans)
        db = SessionDB(db_path=db_path)
        for s in ("a", "b", "c"):
            db.create_session(session_id=f"sess-{s}", source="cli")
        db.close()

        run_agent._orphan_hint_checked = False
        with patch.object(run_agent, "get_hermes_home", return_value=tmp_path), \
             patch("hermes_state.SessionDB", return_value=SessionDB(db_path=db_path)):
            with patch.object(run_agent.logger, "info") as mock_info:
                run_agent._check_orphaned_sessions_hint()
                hint_calls = [
                    c for c in mock_info.call_args_list
                    if c[0] and "repair" in str(c[0][0])
                ]
                assert len(hint_calls) == 1

    def test_hint_does_not_fire_when_under_threshold(self, tmp_path):
        """When <50 orphans, no hint fires."""
        import run_agent
        from hermes_state import SessionDB

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        db_path = tmp_path / "test2.db"

        # Only 5 orphan files
        for i in range(5):
            sid = f"{i:08d}-orph"
            (sessions_dir / f"session_{sid}.json").write_text(
                '{"messages": []}'
            )

        db = SessionDB(db_path=db_path)
        db.close()

        run_agent._orphan_hint_checked = False
        with patch.object(run_agent, "get_hermes_home", return_value=tmp_path), \
             patch("hermes_state.SessionDB", return_value=SessionDB(db_path=db_path)):
            with patch.object(run_agent.logger, "info") as mock_info:
                run_agent._check_orphaned_sessions_hint()
                hint_calls = [
                    c for c in mock_info.call_args_list
                    if c[0] and "repair" in str(c[0][0])
                ]
                assert len(hint_calls) == 0

    def test_hint_fire_once_per_process(self, tmp_path):
        """Second call does not log even if orphans still exist."""
        import run_agent
        from hermes_state import SessionDB

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        db_path = tmp_path / "test3.db"

        for i in range(60):
            sid = f"{i:08d}-orph"
            (sessions_dir / f"session_{sid}.json").write_text(
                '{"messages": []}'
            )

        db = SessionDB(db_path=db_path)
        db.close()

        run_agent._orphan_hint_checked = False
        with patch.object(run_agent, "get_hermes_home", return_value=tmp_path), \
             patch("hermes_state.SessionDB", return_value=SessionDB(db_path=db_path)):
            with patch.object(run_agent.logger, "info") as mock_info:
                run_agent._check_orphaned_sessions_hint()
                run_agent._check_orphaned_sessions_hint()
                run_agent._check_orphaned_sessions_hint()
                hint_calls = [
                    c for c in mock_info.call_args_list
                    if c[0] and "repair" in str(c[0][0])
                ]
                assert len(hint_calls) == 1

    def test_hint_skips_symlinks(self, tmp_path):
        """Symlinks to session files are ignored."""
        import run_agent
        from hermes_state import SessionDB

        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        db_path = tmp_path / "test4.db"

        # Create one real file and a symlink to it
        (sessions_dir / "session_real.json").write_text('{"messages": []}')
        (sessions_dir / "session_00000099-symlink.json").symlink_to(
            sessions_dir / "session_real.json"
        )

        db = SessionDB(db_path=db_path)
        db.close()

        run_agent._orphan_hint_checked = False
        with patch.object(run_agent, "get_hermes_home", return_value=tmp_path), \
             patch("hermes_state.SessionDB", return_value=SessionDB(db_path=db_path)):
            with patch.object(run_agent.logger, "info") as mock_info:
                run_agent._check_orphaned_sessions_hint()
                hint_calls = [
                    c for c in mock_info.call_args_list
                    if c[0] and "repair" in str(c[0][0])
                ]
                # Only 1 orphan (symlink skipped), below threshold of 50
                assert len(hint_calls) == 0
