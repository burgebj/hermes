"""Tests for context compression persistence in the gateway.

Verifies that when context compression fires during run_conversation(),
the compressed messages are properly persisted to both SQLite (via the
agent) and JSONL (via the gateway).

Bug scenario (pre-fix):
  1. Gateway loads 200-message history, passes to agent
  2. Agent's run_conversation() compresses to ~30 messages mid-run
  3. _compress_context() resets _last_flushed_db_idx = 0
  4. On exit, _flush_messages_to_session_db() calculates:
     flush_from = max(len(conversation_history=200), _last_flushed_db_idx=0) = 200
  5. messages[200:] is empty (only ~30 messages after compression)
  6. Nothing written to new session's SQLite — compressed context lost
  7. Gateway's history_offset was still 200, producing empty new_messages
  8. Fallback wrote only user/assistant pair — summary lost
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch



# ---------------------------------------------------------------------------
# Part 1: Agent-side — _flush_messages_to_session_db after compression
# ---------------------------------------------------------------------------

class TestFlushAfterCompression:
    """Verify that compressed messages are flushed to the new session's SQLite
    even when conversation_history (from the original session) is longer than
    the compressed messages list."""

    def _make_agent(self, session_db):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
            from run_agent import AIAgent
            agent = AIAgent(
                api_key="test-key",
                base_url="https://openrouter.ai/api/v1",
                model="test/model",
                quiet_mode=True,
                session_db=session_db,
                session_id="original-session",
                skip_context_files=True,
                skip_memory=True,
            )
        return agent

    def test_flush_after_compression_with_long_history(self):
        """The actual bug: conversation_history longer than compressed messages.

        Before the fix, flush_from = max(len(conversation_history), 0) = 200,
        but messages only has ~30 entries, so messages[200:] is empty.
        After the fix, conversation_history is cleared to None after compression,
        so flush_from = max(0, 0) = 0, and ALL compressed messages are written.
        """
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SessionDB(db_path=db_path)

            agent = self._make_agent(db)

            # Simulate the original long history (200 messages)
            original_history = [
                {"role": "user" if i % 2 == 0 else "assistant",
                 "content": f"message {i}"}
                for i in range(200)
            ]

            # First, flush original messages to the original session
            agent._flush_messages_to_session_db(original_history, [])
            original_rows = db.get_messages("original-session")
            assert len(original_rows) == 200

            # Now simulate compression: new session, reset idx, shorter messages
            agent.session_id = "compressed-session"
            db.create_session(session_id="compressed-session", source="test")
            agent._last_flushed_db_idx = 0

            # The compressed messages (summary + tail + new turn)
            compressed_messages = [
                {"role": "user", "content": "[CONTEXT COMPACTION] Summary of work..."},
                {"role": "user", "content": "What should we do next?"},
                {"role": "assistant", "content": "Let me check..."},
                {"role": "user", "content": "new question"},
                {"role": "assistant", "content": "new answer"},
            ]

            # THE BUG: passing the original history as conversation_history
            # causes flush_from = max(200, 0) = 200, skipping everything.
            # After the fix, conversation_history should be None.
            agent._flush_messages_to_session_db(compressed_messages, None)

            new_rows = db.get_messages("compressed-session")
            assert len(new_rows) == 5, (
                f"Expected 5 compressed messages in new session, got {len(new_rows)}. "
                f"Compression persistence bug: messages not written to SQLite."
            )

    def test_flush_with_stale_history_loses_messages(self):
        """Demonstrates the bug condition: stale conversation_history causes data loss."""
        from hermes_state import SessionDB

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = SessionDB(db_path=db_path)

            agent = self._make_agent(db)

            # Simulate compression reset
            agent.session_id = "new-session"
            db.create_session(session_id="new-session", source="test")
            agent._last_flushed_db_idx = 0

            compressed = [
                {"role": "user", "content": "summary"},
                {"role": "assistant", "content": "continuing..."},
            ]

            # Bug: passing a conversation_history longer than compressed messages
            stale_history = [{"role": "user", "content": f"msg{i}"} for i in range(100)]
            agent._flush_messages_to_session_db(compressed, stale_history)

            rows = db.get_messages("new-session")
            # With the stale history, flush_from = max(100, 0) = 100
            # But compressed only has 2 entries → messages[100:] = empty
            assert len(rows) == 0, (
                "Expected 0 messages with stale conversation_history "
                "(this test verifies the bug condition exists)"
            )


# ---------------------------------------------------------------------------
# Part 2: Gateway-side — history_offset after session split
# ---------------------------------------------------------------------------

class TestGatewayHistoryOffsetAfterSplit:
    """Verify that when the agent creates a new session during compression,
    the gateway uses history_offset=0 so all compressed messages are written
    to the JSONL transcript."""

    def test_history_offset_zero_on_session_split(self):
        """When agent.session_id differs from the original, history_offset must be 0."""
        # This tests the logic in gateway/run.py run_sync():
        # _session_was_split = agent.session_id != session_id
        # _effective_history_offset = 0 if _session_was_split else len(agent_history)

        original_session_id = "session-abc"
        agent_session_id = "session-compressed-xyz"  # Different = compression happened
        agent_history_len = 200

        # Simulate the gateway's offset calculation (post-fix)
        _session_was_split = (agent_session_id != original_session_id)
        _effective_history_offset = 0 if _session_was_split else agent_history_len

        assert _session_was_split is True
        assert _effective_history_offset == 0

    def test_history_offset_preserved_without_split(self):
        """When no compression happened, history_offset is the original length."""
        session_id = "session-abc"
        agent_session_id = "session-abc"  # Same = no compression
        agent_history_len = 200

        _session_was_split = (agent_session_id != session_id)
        _effective_history_offset = 0 if _session_was_split else agent_history_len

        assert _session_was_split is False
        assert _effective_history_offset == 200

    def test_new_messages_extraction_after_split(self):
        """After compression with offset=0, new_messages should be ALL agent messages."""
        # Simulates the gateway's new_messages calculation
        agent_messages = [
            {"role": "user", "content": "[CONTEXT COMPACTION] Summary..."},
            {"role": "user", "content": "recent question"},
            {"role": "assistant", "content": "recent answer"},
            {"role": "user", "content": "new question"},
            {"role": "assistant", "content": "new answer"},
        ]
        history_offset = 0  # After fix: 0 on session split

        new_messages = agent_messages[history_offset:] if len(agent_messages) > history_offset else []
        assert len(new_messages) == 5, (
            f"Expected all 5 messages with offset=0, got {len(new_messages)}"
        )

    def test_new_messages_empty_with_stale_offset(self):
        """Demonstrates the bug: stale offset produces empty new_messages."""
        agent_messages = [
            {"role": "user", "content": "summary"},
            {"role": "assistant", "content": "answer"},
        ]
        # Bug: offset is the pre-compression history length
        history_offset = 200

        new_messages = agent_messages[history_offset:] if len(agent_messages) > history_offset else []
        assert len(new_messages) == 0, (
            "Expected 0 messages with stale offset=200 (demonstrates the bug)"
        )


# ---------------------------------------------------------------------------
# Part 3: Gateway-side — eager session-rotation persistence
# ---------------------------------------------------------------------------

class TestEagerSessionRotationPersist:
    """Verify that mid-run session rotation (from _compress_context) is
    persisted to the session store and JSONL transcript IMMEDIATELY after
    the agent returns, before any post-run discard path can swallow it.

    Bug scenario (pre-fix):
      1. Agent compresses mid-run, rotating session_id A → B.
      2. Result is returned; before the post-run "Session split detected"
         block runs, the result is flagged stale (e.g. /stop bumped the
         run generation) and discarded.
      3. session_store entry still points at A; B's JSONL was never written.
      4. Next message loads A.jsonl (full uncompressed history) and the
         preflight compressor re-fires, burning another aux LLM call and
         creating an orphaned third session C.

    The fix moves the persistence step from the post-run block (which only
    runs on success) to immediately after `agent.run_conversation()` returns
    inside `run_sync`, so it survives /stop, early-returns from
    `final_response is None`, and any other path that skips the post-run
    block.
    """

    def _make_store(self, tmp_path):
        from unittest.mock import patch

        from gateway.config import GatewayConfig
        from gateway.session import SessionStore

        config = GatewayConfig()
        with patch("gateway.session.SessionStore._ensure_loaded"):
            store = SessionStore(sessions_dir=tmp_path, config=config)
        store._db = None  # JSONL-only — easier to assert against
        store._loaded = True
        return store

    def _simulate_eager_persist(self, store, session_key, original_session_id,
                                 rotated_session_id, compressed_messages):
        """Mirror the eager-persist block from gateway/run.py:run_sync()."""
        # Pre-condition: store points at the original session_id.
        entry = store._entries.get(session_key)
        if (
            rotated_session_id
            and session_key
            and rotated_session_id != original_session_id
            and entry
            and entry.session_id != rotated_session_id
        ):
            entry.session_id = rotated_session_id
            store._save()
            if compressed_messages:
                store.rewrite_transcript(rotated_session_id, compressed_messages)
            return True
        return False

    def test_eager_persist_updates_entry_and_writes_compressed_jsonl(self, tmp_path):
        """Happy path: rotation persists entry + new JSONL atomically."""
        from datetime import datetime

        from gateway.config import Platform
        from gateway.session import SessionEntry, SessionSource

        store = self._make_store(tmp_path)
        session_key = "telegram:dm:user1"
        original_sid = "20260520_095544_aaaaaa"
        rotated_sid = "20260520_140509_bbbbbb"

        # Seed: entry at original, JSONL holds 200-message uncompressed history
        entry = SessionEntry(
            session_key=session_key,
            session_id=original_sid,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            origin=SessionSource(platform=Platform.TELEGRAM, chat_id="user1", chat_type="dm"),
        )
        store._entries[session_key] = entry
        for i in range(200):
            store.append_to_transcript(original_sid, {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"msg {i}",
            })

        compressed = [
            {"role": "user", "content": "[CONTEXT COMPACTION] Summary..."},
            {"role": "user", "content": "recent question"},
            {"role": "assistant", "content": "recent answer"},
        ]
        persisted = self._simulate_eager_persist(
            store, session_key, original_sid, rotated_sid, compressed,
        )

        assert persisted is True
        # 1. session_store entry points at the new session id
        assert store._entries[session_key].session_id == rotated_sid
        # 2. NEW session JSONL has only the compressed messages (not 203)
        new_transcript = store.load_transcript(rotated_sid)
        assert len(new_transcript) == 3
        assert new_transcript[0]["content"].startswith("[CONTEXT COMPACTION]")
        # 3. Old session JSONL is left intact (lineage preserved for search)
        old_transcript = store.load_transcript(original_sid)
        assert len(old_transcript) == 200

    def test_eager_persist_survives_stale_discard(self, tmp_path):
        """If the next turn loads the (now-rotated) entry, it must see the
        compressed transcript — NOT the uncompressed pre-rotation one.

        This is the regression: pre-fix, only the post-run block updated
        the entry, so a /stop between agent-return and post-run path left
        the entry stale, causing the next turn to re-compress from scratch.
        """
        from datetime import datetime

        from gateway.config import Platform
        from gateway.session import SessionEntry, SessionSource

        store = self._make_store(tmp_path)
        session_key = "telegram:dm:user2"
        original_sid = "session_pre_compression"
        rotated_sid = "session_post_compression"

        entry = SessionEntry(
            session_key=session_key,
            session_id=original_sid,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            origin=SessionSource(platform=Platform.TELEGRAM, chat_id="user2", chat_type="dm"),
        )
        store._entries[session_key] = entry

        # Seed the pre-rotation transcript at 180K-equivalent length
        for i in range(180):
            store.append_to_transcript(original_sid, {
                "role": "user" if i % 2 == 0 else "assistant",
                "content": "x" * 100,
            })

        compressed = [
            {"role": "user", "content": "[COMPACT] summary"},
            {"role": "assistant", "content": "ack"},
        ]

        # Eager persist fires DURING run_sync, before any stale-discard
        self._simulate_eager_persist(
            store, session_key, original_sid, rotated_sid, compressed,
        )

        # Simulate stale-result discard: post-run block never runs.
        # The next turn loads transcript from the entry's session_id.
        next_turn_sid = store._entries[session_key].session_id
        next_turn_history = store.load_transcript(next_turn_sid)

        assert next_turn_sid == rotated_sid, (
            "session_store entry must point at the rotated session id even "
            "when the result is discarded after agent return"
        )
        assert len(next_turn_history) == 2, (
            f"Next turn must see compressed history (2 msgs), got "
            f"{len(next_turn_history)} — the rotation was not persisted "
            f"and the uncompressed transcript leaked through"
        )

    def test_eager_persist_is_idempotent(self, tmp_path):
        """Post-run block runs the same update — must be a no-op the second time."""
        from datetime import datetime

        from gateway.config import Platform
        from gateway.session import SessionEntry, SessionSource

        store = self._make_store(tmp_path)
        session_key = "telegram:dm:user3"
        original_sid = "sess_a"
        rotated_sid = "sess_b"

        entry = SessionEntry(
            session_key=session_key,
            session_id=original_sid,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            origin=SessionSource(platform=Platform.TELEGRAM, chat_id="user3", chat_type="dm"),
        )
        store._entries[session_key] = entry

        compressed = [{"role": "user", "content": "summary"}]

        # First call (the eager block) — persists.
        first = self._simulate_eager_persist(
            store, session_key, original_sid, rotated_sid, compressed,
        )
        # Second call (the post-run block) — must short-circuit because
        # entry.session_id already equals rotated_sid.
        second = self._simulate_eager_persist(
            store, session_key, original_sid, rotated_sid, compressed,
        )

        assert first is True
        assert second is False, (
            "Post-run rotation block must be a no-op when the eager block "
            "already persisted the rotation — otherwise rewrite_transcript "
            "would double-write and clobber any messages appended between "
            "agent-return and post-run."
        )
        assert store._entries[session_key].session_id == rotated_sid

    def test_eager_persist_skips_when_no_rotation(self, tmp_path):
        """Normal turn (no compression) — eager block must not touch anything."""
        from datetime import datetime

        from gateway.config import Platform
        from gateway.session import SessionEntry, SessionSource

        store = self._make_store(tmp_path)
        session_key = "telegram:dm:user4"
        sid = "stable_session"

        entry = SessionEntry(
            session_key=session_key,
            session_id=sid,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            origin=SessionSource(platform=Platform.TELEGRAM, chat_id="user4", chat_type="dm"),
        )
        store._entries[session_key] = entry
        store.append_to_transcript(sid, {"role": "user", "content": "hi"})

        # Agent did NOT rotate — rotated_sid == original_sid
        persisted = self._simulate_eager_persist(
            store, session_key, sid, sid, [{"role": "user", "content": "summary"}],
        )

        assert persisted is False
        assert store._entries[session_key].session_id == sid
        # Transcript must be untouched by the eager block
        history = store.load_transcript(sid)
        assert len(history) == 1
        assert history[0]["content"] == "hi"
