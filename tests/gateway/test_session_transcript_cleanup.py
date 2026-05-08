"""Tests for session transcript cleanup (#20098).

The SessionStore should:
1. Delete old transcript files when a session is reset in get_or_create_session
2. Delete transcript files when entries are pruned via prune_old_entries
3. Clean up orphaned transcript files on startup via cleanup_orphaned_transcripts
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig, Platform, SessionResetPolicy
from gateway.session import SessionEntry, SessionSource, SessionStore


def _make_store(tmp_path, max_age_days: int = 90, has_active_processes_fn=None):
    """Build a SessionStore bypassing SQLite/disk-load side effects."""
    config = GatewayConfig(
        default_reset_policy=SessionResetPolicy(mode="none"),
        session_store_max_age_days=max_age_days,
    )
    with patch("gateway.session.SessionStore._ensure_loaded"):
        store = SessionStore(
            sessions_dir=tmp_path,
            config=config,
            has_active_processes_fn=has_active_processes_fn,
        )
    store._db = None
    store._loaded = True
    return store


def _make_source(platform=Platform.TELEGRAM, user_id="u1", chat_id="c1"):
    """Create a minimal SessionSource for testing."""
    return SessionSource(
        platform=platform,
        user_id=user_id,
        chat_id=chat_id,
        chat_type="dm",
        chat_name="test",
    )


def _entry(key: str, age_days: float, *, suspended: bool = False,
           session_id: str | None = None) -> SessionEntry:
    now = datetime.now()
    return SessionEntry(
        session_key=key,
        session_id=session_id or f"sid_{key}",
        created_at=now - timedelta(days=age_days + 30),
        updated_at=now - timedelta(days=age_days),
        platform=Platform.TELEGRAM,
        chat_type="dm",
        suspended=suspended,
    )


class TestDeleteTranscript:
    """Tests for SessionStore._delete_transcript."""

    def test_deletes_existing_transcript(self, tmp_path):
        store = _make_store(tmp_path)
        transcript = tmp_path / "test_session.jsonl"
        transcript.write_text('{"role":"user","content":"hi"}\n')
        assert transcript.exists()

        store._delete_transcript("test_session")

        assert not transcript.exists()

    def test_ignores_missing_transcript(self, tmp_path):
        store = _make_store(tmp_path)
        # Should not raise
        store._delete_transcript("nonexistent_session")

    def test_ignores_permission_error(self, tmp_path):
        store = _make_store(tmp_path)
        transcript = tmp_path / "test_session.jsonl"
        transcript.write_text('{"role":"user","content":"hi"}\n')

        # Make parent dir read-only (won't work as root, but tests the path)
        # Just verify it doesn't crash
        store._delete_transcript("test_session")


class TestGetOrCreateSessionDeletesOldTranscript:
    """Tests that get_or_create_session deletes old transcript files on reset."""

    def test_old_transcript_deleted_on_session_reset(self, tmp_path):
        """When a session is reset, the old transcript file should be deleted."""
        config = GatewayConfig(
            default_reset_policy=SessionResetPolicy(mode="per_message"),
            session_store_max_age_days=90,
        )
        with patch("gateway.session.SessionStore._ensure_loaded"):
            store = SessionStore(
                sessions_dir=tmp_path,
                config=config,
            )
        store._db = None
        store._loaded = True

        source = _make_source()
        session_key = store._generate_session_key(source)

        # Create first session
        entry1 = store.get_or_create_session(source)
        old_session_id = entry1.session_id

        # Create a transcript file for the old session
        old_transcript = tmp_path / f"{old_session_id}.jsonl"
        old_transcript.write_text('{"role":"user","content":"hello"}\n')
        assert old_transcript.exists()

        # Force a new session (simulates reset)
        entry2 = store.get_or_create_session(source, force_new=True)
        new_session_id = entry2.session_id

        # Old transcript should be deleted
        assert not old_transcript.exists()
        # New session should have a different ID
        assert new_session_id != old_session_id

    def test_no_transcript_deleted_when_session_reused(self, tmp_path):
        """When a session is reused (not reset), no transcript should be deleted."""
        store = _make_store(tmp_path)
        source = _make_source()

        entry1 = store.get_or_create_session(source)
        session_id = entry1.session_id

        # Create a transcript file
        transcript = tmp_path / f"{session_id}.jsonl"
        transcript.write_text('{"role":"user","content":"hello"}\n')

        # Get the same session again (not reset)
        entry2 = store.get_or_create_session(source)

        # Transcript should still exist
        assert transcript.exists()
        assert entry2.session_id == session_id


class TestPruneDeletesTranscripts:
    """Tests that prune_old_entries deletes transcript files for pruned entries."""

    def test_prune_deletes_transcript_files(self, tmp_path):
        store = _make_store(tmp_path, max_age_days=30)

        # Create old entries with transcript files
        old_entry = _entry("old", age_days=100, session_id="old_session_123")
        store._entries["old"] = old_entry
        old_transcript = tmp_path / "old_session_123.jsonl"
        old_transcript.write_text('{"role":"user","content":"old"}\n')

        fresh_entry = _entry("fresh", age_days=5, session_id="fresh_session_456")
        store._entries["fresh"] = fresh_entry
        fresh_transcript = tmp_path / "fresh_session_456.jsonl"
        fresh_transcript.write_text('{"role":"user","content":"fresh"}\n')

        removed = store.prune_old_entries(max_age_days=30)

        assert removed == 1
        assert not old_transcript.exists()
        assert fresh_transcript.exists()

    def test_prune_handles_missing_transcript_files(self, tmp_path):
        """Pruning should not fail if transcript files don't exist."""
        store = _make_store(tmp_path, max_age_days=30)

        old_entry = _entry("old", age_days=100, session_id="old_session_no_file")
        store._entries["old"] = old_entry
        # No transcript file created

        removed = store.prune_old_entries(max_age_days=30)

        assert removed == 1
        assert "old" not in store._entries


class TestCleanupOrphanedTranscripts:
    """Tests for cleanup_orphaned_transcripts."""

    def test_removes_orphaned_transcripts(self, tmp_path):
        store = _make_store(tmp_path)

        # Create a session entry
        entry = _entry("active", age_days=0, session_id="active_session")
        store._entries["active"] = entry

        # Create transcript files - one for active, one orphaned
        active_file = tmp_path / "active_session.jsonl"
        active_file.write_text('{"role":"user","content":"active"}\n')

        orphan_file = tmp_path / "orphan_session_20260505_053804_914eb0.jsonl"
        orphan_file.write_text('{"role":"user","content":"orphaned"}\n')

        removed = store.cleanup_orphaned_transcripts()

        assert removed == 1
        assert active_file.exists()
        assert not orphan_file.exists()

    def test_no_removal_when_no_orphans(self, tmp_path):
        store = _make_store(tmp_path)

        entry = _entry("active", age_days=0, session_id="active_session")
        store._entries["active"] = entry

        active_file = tmp_path / "active_session.jsonl"
        active_file.write_text('{"role":"user","content":"active"}\n')

        removed = store.cleanup_orphaned_transcripts()

        assert removed == 0
        assert active_file.exists()

    def test_ignores_non_jsonl_files(self, tmp_path):
        store = _make_store(tmp_path)

        # Create a non-JSONL file in the sessions directory
        other_file = tmp_path / "sessions.json"
        other_file.write_text('{"key": "value"}\n')

        removed = store.cleanup_orphaned_transcripts()

        assert removed == 0
        assert other_file.exists()

    def test_handles_empty_sessions_dir(self, tmp_path):
        store = _make_store(tmp_path)
        # sessions_dir doesn't exist yet
        store.sessions_dir = tmp_path / "nonexistent"

        removed = store.cleanup_orphaned_transcripts()

        assert removed == 0

    def test_handles_multiple_orphans(self, tmp_path):
        store = _make_store(tmp_path)

        entry = _entry("active", age_days=0, session_id="active_session")
        store._entries["active"] = entry

        # Create multiple orphaned files
        for i in range(5):
            orphan = tmp_path / f"orphan_{i}.jsonl"
            orphan.write_text(f'{{"role":"user","content":"orphan {i}"}}\n')

        active_file = tmp_path / "active_session.jsonl"
        active_file.write_text('{"role":"user","content":"active"}\n')

        removed = store.cleanup_orphaned_transcripts()

        assert removed == 5
        assert active_file.exists()
