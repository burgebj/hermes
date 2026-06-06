"""Tests for state persistence module."""

import json
import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock


class TestStatePersistence:
    def test_save_and_load(self):
        from tools.state_persistence import save_conversation_state, load_conversation_state, discard_recovery_state
        session_id = "test_session_1"
        messages = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
        
        result = save_conversation_state(session_id, messages, metadata={"model": "test"})
        assert result is True
        
        state = load_conversation_state(session_id)
        assert state is not None
        assert len(state["messages"]) == 2
        assert state["metadata"]["model"] == "test"
        
        discard_recovery_state(session_id)
        loaded = load_conversation_state(session_id)
        assert loaded is None

    def test_has_recovery_state(self):
        from tools.state_persistence import save_conversation_state, has_recovery_state, discard_recovery_state
        session_id = "test_has_state"
        save_conversation_state(session_id, [{"role": "user", "content": "test"}])
        assert has_recovery_state(session_id) is True
        discard_recovery_state(session_id)
        assert has_recovery_state(session_id) is False

    def test_load_nonexistent(self):
        from tools.state_persistence import load_conversation_state
        state = load_conversation_state("nonexistent_session_xyz")
        assert state is None

    def test_list_recovery_sessions(self):
        from tools.state_persistence import save_conversation_state, list_recovery_sessions
        session_id = "test_list_session"
        save_conversation_state(session_id, [{"role": "user", "content": "t"}])
        sessions = list_recovery_sessions()
        assert session_id in sessions

    def test_save_with_metadata(self):
        from tools.state_persistence import save_conversation_state, load_conversation_state, discard_recovery_state
        session_id = "test_meta"
        meta = {"provider": "anthropic", "model": "claude-sonnet-4", "iteration": 5}
        save_conversation_state(session_id, [{"role": "user", "content": "x"}], metadata=meta)
        state = load_conversation_state(session_id)
        assert state["metadata"]["provider"] == "anthropic"
        assert state["metadata"]["iteration"] == 5
        discard_recovery_state(session_id)

    def test_prune_stale_snapshots(self):
        from tools.state_persistence import save_conversation_state
        from tools.state_persistence import _prune_stale_snapshots
        from tools.state_persistence import STATE_DIR
        
        for i in range(7):
            save_conversation_state(f"prune_test_{i}", [{"role": "user", "content": str(i)}])
        
        _prune_stale_snapshots()
        remaining = len([f for f in STATE_DIR.iterdir() if f.suffix == ".json"])
        assert remaining <= 5