"""Tests for Mattermost thread-mode fixes.

Covers three regressions that surface when Mattermost is configured with
``MATTERMOST_REPLY_MODE=thread`` (or similar reply-into-thread setups):

1. ``/approve`` and ``/deny`` typed inside a thread did not resolve pending
   approvals whose blocking entry had been registered against the parent
   channel's session key.  Verified via ``_handle_approve_command`` and
   ``_handle_deny_command`` plus the underlying
   ``_approval_fallback_session_key`` helper.

2. Tool-progress and final-status bubbles produced while the agent ran inside
   a channel thread were posted to the channel root instead of the thread.
   Verified by inspecting the routing decisions inside ``run_message`` —
   specifically that the adapter's ``send()`` honors ``metadata["thread_id"]``
   when no ``reply_to`` anchor is available.

3. ``MattermostAdapter._handle_ws_event`` now stamps ``source.message_id``
   with the post id so the gateway can fall back to it as the thread anchor
   for a channel ``@mention`` that has not yet been replied to.
"""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent
from gateway.session import SessionSource


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _make_mattermost_source(
    *,
    thread_id=None,
    message_id="post_root",
    chat_type="channel",
) -> SessionSource:
    return SessionSource(
        platform=Platform.MATTERMOST,
        chat_id="chan_1",
        chat_name="general",
        chat_type=chat_type,
        user_id="user_1",
        user_name="alice",
        thread_id=thread_id,
        message_id=message_id,
    )


def _make_event(text: str, source: SessionSource) -> MessageEvent:
    return MessageEvent(
        text=text,
        source=source,
        message_id=source.message_id,
    )


def _make_runner():
    """Build a minimal GatewayRunner sufficient for the approval handlers."""
    from gateway.run import GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(
        platforms={
            Platform.MATTERMOST: PlatformConfig(
                enabled=True,
                token="test",
                extra={"url": "https://mm.example.com"},
            )
        }
    )
    adapter = MagicMock()
    adapter.send = AsyncMock()
    adapter.resume_typing_for_chat = MagicMock()
    runner.adapters = {Platform.MATTERMOST: adapter}
    runner._voice_mode = {}
    runner.hooks = SimpleNamespace(emit=AsyncMock(), loaded_hooks=False)
    runner.session_store = MagicMock()
    # session_store.generate_session_key is consulted first by
    # _session_key_for_source; return a falsy value so the builder falls
    # through to the deterministic build_session_key() path.
    runner.session_store._generate_session_key = MagicMock(return_value=None)
    runner._running_agents = {}
    runner._pending_messages = {}
    runner._pending_approvals = {}
    runner._background_tasks = set()
    runner._session_db = None
    runner._reasoning_config = None
    runner._provider_routing = {}
    runner._fallback_model = None
    runner._show_reasoning = False
    runner._is_user_authorized = lambda _source: True
    runner._set_session_env = lambda _context: None
    return runner


def _clear_approval_state():
    from tools import approval as mod
    mod._gateway_queues.clear()
    mod._gateway_notify_cbs.clear()
    mod._session_approved.clear()
    mod._permanent_approved.clear()
    mod._pending.clear()


# ---------------------------------------------------------------------------
# _approval_fallback_session_key helper
# ---------------------------------------------------------------------------


class TestApprovalFallbackSessionKey:

    def test_returns_none_without_thread_id(self):
        runner = _make_runner()
        source = _make_mattermost_source(thread_id=None)
        assert runner._approval_fallback_session_key(source) is None

    def test_returns_non_thread_key_for_threaded_source(self):
        runner = _make_runner()
        threaded = _make_mattermost_source(thread_id="root_post")
        channel = _make_mattermost_source(thread_id=None, message_id=None)

        fallback_key = runner._approval_fallback_session_key(threaded)
        channel_key = runner._session_key_for_source(channel)

        assert fallback_key is not None
        assert fallback_key == channel_key
        # Sanity check: thread session key must include the thread fragment.
        assert runner._session_key_for_source(threaded) != fallback_key

    def test_returns_none_for_non_dataclass_source(self):
        """A duck-typed source that isn't a dataclass should not crash."""
        runner = _make_runner()
        fake = SimpleNamespace(thread_id="t1", message_id="m1")
        assert runner._approval_fallback_session_key(fake) is None


# ---------------------------------------------------------------------------
# /approve in a thread — falls back to parent-channel session key
# ---------------------------------------------------------------------------


class TestApproveThreadFallback:

    def setup_method(self):
        _clear_approval_state()

    @pytest.mark.asyncio
    async def test_approve_in_thread_resolves_channel_pending(self):
        """Approval was registered while the agent ran in the parent channel.

        The user typed /approve inside a thread under the agent's prompt —
        the session key derived from that event includes thread_id, but the
        pending entry lives under the channel-level session key.  The
        fallback should locate and resolve it.
        """
        from tools.approval import _ApprovalEntry, _gateway_queues

        runner = _make_runner()

        channel_source = _make_mattermost_source(thread_id=None, message_id=None)
        channel_key = runner._session_key_for_source(channel_source)

        # Agent registered the entry against the channel key.
        entry = _ApprovalEntry({"command": "rm -rf /"})
        _gateway_queues[channel_key] = [entry]

        # User replied /approve inside a thread under the agent's post.
        thread_source = _make_mattermost_source(thread_id="root_post")
        result = await runner._handle_approve_command(_make_event("/approve", thread_source))

        assert "approved" in result.lower()
        assert entry.event.is_set()
        assert entry.result == "once"

    @pytest.mark.asyncio
    async def test_approve_in_thread_with_thread_pending_still_works(self):
        """When the entry IS registered against the thread key, the normal
        non-fallback path still resolves it."""
        from tools.approval import _ApprovalEntry, _gateway_queues

        runner = _make_runner()
        thread_source = _make_mattermost_source(thread_id="root_post")
        thread_key = runner._session_key_for_source(thread_source)

        entry = _ApprovalEntry({"command": "ls"})
        _gateway_queues[thread_key] = [entry]

        result = await runner._handle_approve_command(_make_event("/approve", thread_source))
        assert "approved" in result.lower()
        assert entry.event.is_set()

    @pytest.mark.asyncio
    async def test_approve_in_thread_no_pending_anywhere(self):
        """When nothing is pending under either key, return the no-pending
        message (not approval_expired)."""
        runner = _make_runner()
        thread_source = _make_mattermost_source(thread_id="root_post")

        result = await runner._handle_approve_command(_make_event("/approve", thread_source))
        assert "No pending command" in result

    @pytest.mark.asyncio
    async def test_approve_in_thread_stale_old_style_under_fallback(self):
        """Stale old-style approval under the channel key (no blocking entry)
        should report expired and be cleaned up via the fallback key."""
        runner = _make_runner()
        channel_source = _make_mattermost_source(thread_id=None, message_id=None)
        channel_key = runner._session_key_for_source(channel_source)
        runner._pending_approvals[channel_key] = {"command": "ls"}

        thread_source = _make_mattermost_source(thread_id="root_post")
        result = await runner._handle_approve_command(_make_event("/approve", thread_source))

        assert "expired" in result.lower() or "no longer waiting" in result.lower()
        assert channel_key not in runner._pending_approvals


# ---------------------------------------------------------------------------
# /deny in a thread — falls back to parent-channel session key
# ---------------------------------------------------------------------------


class TestDenyThreadFallback:

    def setup_method(self):
        _clear_approval_state()

    @pytest.mark.asyncio
    async def test_deny_in_thread_resolves_channel_pending(self):
        from tools.approval import _ApprovalEntry, _gateway_queues

        runner = _make_runner()
        channel_source = _make_mattermost_source(thread_id=None, message_id=None)
        channel_key = runner._session_key_for_source(channel_source)

        entry = _ApprovalEntry({"command": "rm -rf /"})
        _gateway_queues[channel_key] = [entry]

        thread_source = _make_mattermost_source(thread_id="root_post")
        result = await runner._handle_deny_command(_make_event("/deny", thread_source))

        assert "denied" in result.lower()
        assert entry.event.is_set()
        assert entry.result == "deny"

    @pytest.mark.asyncio
    async def test_deny_in_thread_stale_old_style_under_fallback(self):
        runner = _make_runner()
        channel_source = _make_mattermost_source(thread_id=None, message_id=None)
        channel_key = runner._session_key_for_source(channel_source)
        runner._pending_approvals[channel_key] = {"command": "ls"}

        thread_source = _make_mattermost_source(thread_id="root_post")
        result = await runner._handle_deny_command(_make_event("/deny", thread_source))

        assert "stale" in result.lower() or "no longer" in result.lower()
        assert channel_key not in runner._pending_approvals

    @pytest.mark.asyncio
    async def test_deny_in_thread_no_pending_anywhere(self):
        runner = _make_runner()
        thread_source = _make_mattermost_source(thread_id="root_post")
        result = await runner._handle_deny_command(_make_event("/deny", thread_source))
        assert "No pending command" in result


# ---------------------------------------------------------------------------
# Mattermost adapter — build_source stamps message_id with the post id
# ---------------------------------------------------------------------------


def _make_adapter():
    from plugins.platforms.mattermost.adapter import MattermostAdapter
    config = PlatformConfig(
        enabled=True,
        token="test-token",
        extra={"url": "https://mm.example.com"},
    )
    return MattermostAdapter(config)


class TestMattermostMessageIdInSource:
    """Verify build_source(message_id=post_id) lands on SessionSource.

    The gateway uses ``source.message_id`` as a thread-anchor fallback when
    the channel @mention has not yet spawned a thread.  Without this field
    populated, tool-progress bubbles flatten back into the channel.
    """

    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._bot_user_id = "bot_user_id"
        self.adapter._bot_username = "hermes-bot"
        self.adapter.handle_message = AsyncMock()

    @pytest.mark.asyncio
    async def test_channel_mention_sets_message_id(self):
        """A non-thread channel @mention should populate source.message_id."""
        post_data = {
            "id": "post_mention_abc",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id Please help",
        }
        ws_event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }
        await self.adapter._handle_ws_event(ws_event)
        assert self.adapter.handle_message.called
        msg_event = self.adapter.handle_message.call_args[0][0]
        # message_id flows through to source so the gateway can use it as
        # a thread anchor even when source.thread_id is None.
        assert msg_event.source.message_id == "post_mention_abc"

    @pytest.mark.asyncio
    async def test_thread_reply_sets_message_id(self):
        """A reply inside an existing thread should also populate it."""
        post_data = {
            "id": "post_reply_xyz",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id follow-up",
            "root_id": "root_post_123",
        }
        ws_event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }
        await self.adapter._handle_ws_event(ws_event)
        msg_event = self.adapter.handle_message.call_args[0][0]
        assert msg_event.source.message_id == "post_reply_xyz"
        assert msg_event.source.thread_id == "root_post_123"


# ---------------------------------------------------------------------------
# Mattermost adapter — metadata["thread_id"] routes send() into the thread
# ---------------------------------------------------------------------------


class TestMattermostSendThreadMetadata:
    """The gateway's progress/status bubbles arrive via the send_message tool
    with ``metadata={"thread_id": ...}`` and ``reply_to=None`` (no anchor on
    the synthetic send).  Verify the adapter honors that metadata so the
    progress bubble lands in the same thread as the user's prompt."""

    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._session = MagicMock()

    @pytest.mark.asyncio
    async def test_metadata_thread_id_becomes_root_id_when_no_reply_to(self):
        self.adapter._reply_mode = "thread"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post_new"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        self.adapter._session.post = MagicMock(return_value=mock_resp)

        result = await self.adapter.send(
            "chan_1",
            "Working on it...",
            reply_to=None,
            metadata={"thread_id": "root_post_xyz"},
        )

        assert result.success is True
        payload = self.adapter._session.post.call_args[1]["json"]
        assert payload["root_id"] == "root_post_xyz"

    @pytest.mark.asyncio
    async def test_reply_to_wins_over_metadata_thread_id(self):
        """When both reply_to and metadata thread_id are provided, the
        explicit reply_to (resolved to its root) takes precedence."""
        self.adapter._reply_mode = "thread"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post_new"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_get = AsyncMock()
        mock_get.status = 200
        mock_get.json = AsyncMock(return_value={"id": "anchor_post", "root_id": ""})
        mock_get.text = AsyncMock(return_value="")
        mock_get.__aenter__ = AsyncMock(return_value=mock_get)
        mock_get.__aexit__ = AsyncMock(return_value=False)

        self.adapter._session.post = MagicMock(return_value=mock_resp)
        self.adapter._session.get = MagicMock(return_value=mock_get)

        result = await self.adapter.send(
            "chan_1",
            "anchored reply",
            reply_to="anchor_post",
            metadata={"thread_id": "other_thread"},
        )

        assert result.success is True
        payload = self.adapter._session.post.call_args[1]["json"]
        # reply_to-derived root wins.
        assert payload["root_id"] == "anchor_post"

    @pytest.mark.asyncio
    async def test_metadata_thread_id_ignored_when_reply_mode_off(self):
        self.adapter._reply_mode = "off"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post_new"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        self.adapter._session.post = MagicMock(return_value=mock_resp)

        result = await self.adapter.send(
            "chan_1",
            "no thread please",
            reply_to=None,
            metadata={"thread_id": "root_post_xyz"},
        )

        assert result.success is True
        payload = self.adapter._session.post.call_args[1]["json"]
        assert "root_id" not in payload
