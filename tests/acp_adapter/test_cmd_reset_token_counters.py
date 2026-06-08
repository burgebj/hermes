"""Tests for ACP adapter _cmd_reset token counter reset (fixes #35823).

After /new or /reset in an ACP session, the agent's session token counters
must be zeroed so the context usage bar shows a clean slate.
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Ensure repo root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from acp_adapter.session import SessionState
from acp_adapter.server import HermesACPAgent


def _make_state():
    """Create a minimal SessionState with a mock agent."""
    agent = MagicMock()
    agent.reset_session_state = MagicMock()
    state = SessionState(
        session_id="test-session",
        agent=agent,
        history=[{"role": "user", "content": "hello"}],
    )
    return state, agent


def _make_server():
    """Create a minimal HermesACPAgent-like object with _cmd_reset."""
    server = MagicMock(spec=HermesACPAgent)
    server.session_manager = MagicMock()
    server._cmd_reset = lambda args, st: HermesACPAgent._cmd_reset(server, args, st)
    return server


class TestCmdResetTokenCounters:
    """_cmd_reset must zero session token counters via reset_session_state()."""

    def test_clears_history(self):
        """History must be empty after reset."""
        state, agent = _make_state()
        server = _make_server()
        result = server._cmd_reset("", state)
        assert state.history == []
        assert "cleared" in result.lower()

    def test_calls_reset_session_state(self):
        """reset_session_state() must be called to zero token counters."""
        state, agent = _make_state()
        server = _make_server()
        server._cmd_reset("", state)
        agent.reset_session_state.assert_called_once()

    def test_saves_session(self):
        """Session must be persisted after reset."""
        state, agent = _make_state()
        server = _make_server()
        server._cmd_reset("", state)
        server.session_manager.save_session.assert_called_once_with("test-session")

    def test_graceful_without_reset_method(self):
        """If agent lacks reset_session_state, reset still works (no crash)."""
        state, _ = _make_state()
        state.agent = MagicMock(spec=[])  # no attributes at all
        server = _make_server()
        result = server._cmd_reset("", state)
        assert state.history == []
        assert "cleared" in result.lower()
