"""Tests for clarify text-intercept in _handle_active_session_busy_message.

When the agent is waiting for a clarify response and the user replies,
_handle_active_session_busy_message must route the reply to the clarify
handler instead of interrupting the running agent. This mirrors the same
interception in _handle_message which is unreachable for busy sessions
because the adapter calls the dedicated busy handler first.

See PR #27570, Issue #27564.
"""

import asyncio
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Repo root importable
_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)

# Import the module so patch target is resolvable
import tools.clarify_gateway as _clarify_mod

# ---------------------------------------------------------------------------
# Minimal stubs so we can import gateway code without heavy deps
# ---------------------------------------------------------------------------
import types as _types

_tg = _types.ModuleType("telegram")
_tg.constants = _types.ModuleType("telegram.constants")
_ct = MagicMock()
_ct.SUPERGROUP = "supergroup"
_ct.GROUP = "group"
_ct.PRIVATE = "private"
_tg.constants.ChatType = _ct
sys.modules.setdefault("telegram", _tg)
sys.modules.setdefault("telegram.constants", _tg.constants)
sys.modules.setdefault("telegram.ext", _types.ModuleType("telegram.ext"))

from gateway.platforms.base import (
    MessageEvent,
    MessageType,
    SessionSource,
    build_session_key,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_event(text="hello", chat_id="123", platform_val="telegram"):
    """Build a minimal MessageEvent."""
    source = SessionSource(
        platform=MagicMock(value=platform_val),
        chat_id=chat_id,
        chat_type="private",
        user_id="user1",
    )
    evt = MessageEvent(
        text=text,
        message_type=MessageType.TEXT,
        source=source,
        message_id="msg1",
    )
    return evt


def _make_runner():
    """Build a minimal GatewayRunner-like object for testing."""
    from gateway.run import GatewayRunner, _AGENT_PENDING_SENTINEL

    runner = object.__new__(GatewayRunner)
    runner._running_agents = {}
    runner._running_agents_ts = {}
    runner._busy_ack_ts = {}
    runner._draining = False
    runner.adapters = {}
    runner.config = MagicMock()
    runner.session_store = None
    runner.hooks = MagicMock()
    runner.hooks.emit = AsyncMock()
    runner.pairing_store = MagicMock()
    runner.pairing_store.is_approved.return_value = True
    runner._is_user_authorized = lambda _source: True
    runner._pending_messages = {}
    return runner, _AGENT_PENDING_SENTINEL


def _make_adapter(platform_val="telegram"):
    """Build a minimal adapter mock."""
    adapter = MagicMock()
    adapter._pending_messages = {}
    adapter._send_with_retry = AsyncMock()
    adapter.config = MagicMock()
    adapter.config.extra = {}
    adapter.platform = MagicMock(value=platform_val)
    return adapter


# ===========================================================================
# Tests
# ===========================================================================

class TestClarifyInterceptInBusyHandler:
    """User replies during a pending clarify while agent is busy."""

    @pytest.mark.asyncio
    async def test_pending_clarify_resolved_from_text(self):
        """Pending clarify + user text → resolve clarify, no interrupt."""
        from gateway.run import GatewayRunner

        runner, _sentinel = _make_runner()
        runner._busy_input_mode = "interrupt"
        adapter = _make_adapter()

        event = _make_event(text="my answer is 42")
        sk = build_session_key(event.source)

        agent = MagicMock()
        runner._running_agents[sk] = agent
        runner.adapters[event.source.platform] = adapter

        # Mock a pending clarify entry
        mock_entry = SimpleNamespace(clarify_id="cid_001")

        with (
            patch("tools.clarify_gateway") as mock_cg,
        ):
            mock_cg.get_pending_for_session.return_value = mock_entry
            mock_cg.resolve_gateway_clarify.return_value = True

            result = await runner._handle_active_session_busy_message(event, sk)

        # VERIFY: Clarify was resolved, agent was NOT interrupted
        assert result is True
        mock_cg.get_pending_for_session.assert_called_once_with(sk)
        mock_cg.resolve_gateway_clarify.assert_called_once_with("cid_001", "my answer is 42")
        agent.interrupt.assert_not_called()

    @pytest.mark.asyncio
    async def test_slash_command_during_clarify_falls_through(self):
        """Slash command during pending clarify → NOT resolved, normal interrupt."""
        from gateway.run import GatewayRunner

        runner, _sentinel = _make_runner()
        runner._busy_input_mode = "interrupt"
        adapter = _make_adapter()

        event = _make_event(text="/help")
        sk = build_session_key(event.source)

        agent = MagicMock()
        runner._running_agents[sk] = agent
        runner.adapters[event.source.platform] = adapter

        mock_entry = SimpleNamespace(clarify_id="cid_001")

        with (
            patch("tools.clarify_gateway") as mock_cg,
        ):
            mock_cg.get_pending_for_session.return_value = mock_entry

            result = await runner._handle_active_session_busy_message(event, sk)

        # VERIFY: Clarify was NOT resolved (slash command), agent was interrupted
        assert result is True
        mock_cg.resolve_gateway_clarify.assert_not_called()
        agent.interrupt.assert_called_once_with("/help")

    @pytest.mark.asyncio
    async def test_no_pending_clarify_falls_through(self):
        """No pending clarify → normal interrupt path."""
        from gateway.run import GatewayRunner

        runner, _sentinel = _make_runner()
        runner._busy_input_mode = "interrupt"
        adapter = _make_adapter()

        event = _make_event(text="what's up")
        sk = build_session_key(event.source)

        agent = MagicMock()
        runner._running_agents[sk] = agent
        runner.adapters[event.source.platform] = adapter

        with (
            patch("tools.clarify_gateway") as mock_cg,
        ):
            mock_cg.get_pending_for_session.return_value = None

            result = await runner._handle_active_session_busy_message(event, sk)

        # VERIFY: No clarify resolution, agent interrupted normally
        assert result is True
        mock_cg.resolve_gateway_clarify.assert_not_called()
        agent.interrupt.assert_called_once_with("what's up")

    @pytest.mark.asyncio
    async def test_clarify_resolve_failure_falls_through(self):
        """resolve_gateway_clarify returns False → falls through to interrupt."""
        from gateway.run import GatewayRunner

        runner, _sentinel = _make_runner()
        runner._busy_input_mode = "interrupt"
        adapter = _make_adapter()

        event = _make_event(text="my answer")
        sk = build_session_key(event.source)

        agent = MagicMock()
        runner._running_agents[sk] = agent
        runner.adapters[event.source.platform] = adapter

        mock_entry = SimpleNamespace(clarify_id="cid_001")

        with (
            patch("tools.clarify_gateway") as mock_cg,
        ):
            mock_cg.get_pending_for_session.return_value = mock_entry
            mock_cg.resolve_gateway_clarify.return_value = False

            result = await runner._handle_active_session_busy_message(event, sk)

        # VERIFY: Resolve was attempted but failed, falls through to interrupt
        assert result is True
        mock_cg.resolve_gateway_clarify.assert_called_once_with("cid_001", "my answer")
        agent.interrupt.assert_called_once_with("my answer")

    @pytest.mark.asyncio
    async def test_pending_clarify_skipped_in_non_interrupt_mode(self):
        """Clarify intercept only fires in interrupt mode — queue/steer unaffected."""
        from gateway.run import GatewayRunner

        runner, _sentinel = _make_runner()
        runner._busy_input_mode = "queue"  # NOT interrupt
        adapter = _make_adapter()

        event = _make_event(text="queue this")
        sk = build_session_key(event.source)

        agent = MagicMock()
        runner._running_agents[sk] = agent
        runner.adapters[event.source.platform] = adapter

        mock_entry = SimpleNamespace(clarify_id="cid_001")

        with (
            patch("tools.clarify_gateway") as mock_cg,
            patch("gateway.run.merge_pending_message_event") as mock_merge,
        ):
            mock_cg.get_pending_for_session.return_value = mock_entry

            result = await runner._handle_active_session_busy_message(event, sk)

        # VERIFY: Clarify NOT resolved (queue mode skips the clarify intercept block)
        assert result is True
        mock_cg.resolve_gateway_clarify.assert_not_called()
        agent.interrupt.assert_not_called()
        mock_merge.assert_called_once()
