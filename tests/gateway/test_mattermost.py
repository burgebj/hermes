"""Tests for Mattermost platform adapter."""
import json
import os
import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from gateway.config import Platform, PlatformConfig


# ---------------------------------------------------------------------------
# Platform & Config
# ---------------------------------------------------------------------------

class TestMattermostConfigLoading:
    def test_apply_env_overrides_mattermost(self, monkeypatch):
        monkeypatch.setenv("MATTERMOST_TOKEN", "mm-tok-abc123")
        monkeypatch.setenv("MATTERMOST_URL", "https://mm.example.com")

        from gateway.config import GatewayConfig, _apply_env_overrides
        config = GatewayConfig()
        _apply_env_overrides(config)

        assert Platform.MATTERMOST in config.platforms
        mc = config.platforms[Platform.MATTERMOST]
        assert mc.enabled is True
        assert mc.token == "mm-tok-abc123"
        assert mc.extra.get("url") == "https://mm.example.com"

    def test_mattermost_not_loaded_without_token(self, monkeypatch):
        monkeypatch.delenv("MATTERMOST_TOKEN", raising=False)
        monkeypatch.delenv("MATTERMOST_URL", raising=False)

        from gateway.config import GatewayConfig, _apply_env_overrides
        config = GatewayConfig()
        _apply_env_overrides(config)

        assert Platform.MATTERMOST not in config.platforms

    def test_mattermost_home_channel(self, monkeypatch):
        monkeypatch.setenv("MATTERMOST_TOKEN", "mm-tok-abc123")
        monkeypatch.setenv("MATTERMOST_URL", "https://mm.example.com")
        monkeypatch.setenv("MATTERMOST_HOME_CHANNEL", "ch_abc123")
        monkeypatch.setenv("MATTERMOST_HOME_CHANNEL_NAME", "General")

        from gateway.config import GatewayConfig, _apply_env_overrides
        config = GatewayConfig()
        _apply_env_overrides(config)

        home = config.get_home_channel(Platform.MATTERMOST)
        assert home is not None
        assert home.chat_id == "ch_abc123"
        assert home.name == "General"

    def test_mattermost_url_warning_without_url(self, monkeypatch):
        """MATTERMOST_TOKEN set but MATTERMOST_URL missing should still load."""
        monkeypatch.setenv("MATTERMOST_TOKEN", "mm-tok-abc123")
        monkeypatch.delenv("MATTERMOST_URL", raising=False)

        from gateway.config import GatewayConfig, _apply_env_overrides
        config = GatewayConfig()
        _apply_env_overrides(config)

        assert Platform.MATTERMOST in config.platforms
        assert config.platforms[Platform.MATTERMOST].extra.get("url") == ""


# ---------------------------------------------------------------------------
# Adapter format / truncate
# ---------------------------------------------------------------------------

def _make_adapter():
    """Create a MattermostAdapter with mocked config."""
    from plugins.platforms.mattermost.adapter import MattermostAdapter
    config = PlatformConfig(
        enabled=True,
        token="test-token",
        extra={"url": "https://mm.example.com", "allowed_channels": []},
    )
    adapter = MattermostAdapter(config)
    return adapter


class TestMattermostFormatMessage:
    def setup_method(self):
        self.adapter = _make_adapter()

    def test_image_markdown_to_url(self):
        """![alt](url) should be converted to just the URL."""
        result = self.adapter.format_message("![cat](https://img.example.com/cat.png)")
        assert result == "https://img.example.com/cat.png"

    def test_image_markdown_strips_alt_text(self):
        result = self.adapter.format_message("Here: ![my image](https://x.com/a.jpg) done")
        assert "![" not in result
        assert "https://x.com/a.jpg" in result

    def test_regular_markdown_preserved(self):
        """Regular markdown (bold, italic, code) should be kept as-is."""
        content = "**bold** and *italic* and `code`"
        assert self.adapter.format_message(content) == content

    def test_regular_links_preserved(self):
        """Non-image links should be preserved."""
        content = "[click](https://example.com)"
        assert self.adapter.format_message(content) == content

    def test_plain_text_unchanged(self):
        content = "Hello, world!"
        assert self.adapter.format_message(content) == content

    def test_multiple_images(self):
        content = "![a](http://a.com/1.png) text ![b](http://b.com/2.png)"
        result = self.adapter.format_message(content)
        assert "![" not in result
        assert "http://a.com/1.png" in result
        assert "http://b.com/2.png" in result


class TestMattermostTruncateMessage:
    def setup_method(self):
        self.adapter = _make_adapter()

    def test_short_message_single_chunk(self):
        msg = "Hello, world!"
        chunks = self.adapter.truncate_message(msg, 4000)
        assert len(chunks) == 1
        assert chunks[0] == msg

    def test_long_message_splits(self):
        msg = "a " * 2500  # 5000 chars
        chunks = self.adapter.truncate_message(msg, 4000)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert len(chunk) <= 4000

    def test_custom_max_length(self):
        msg = "Hello " * 20
        chunks = self.adapter.truncate_message(msg, max_length=50)
        assert all(len(c) <= 50 for c in chunks)

    def test_exactly_at_limit(self):
        msg = "x" * 4000
        chunks = self.adapter.truncate_message(msg, 4000)
        assert len(chunks) == 1


# ---------------------------------------------------------------------------
# Send
# ---------------------------------------------------------------------------

class TestMattermostSend:
    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._session = MagicMock()

    @pytest.mark.asyncio
    async def test_send_calls_api_post(self):
        """send() should POST to /api/v4/posts with channel_id and message."""
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post123"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        self.adapter._session.post = MagicMock(return_value=mock_resp)

        result = await self.adapter.send("channel_1", "Hello!")

        assert result.success is True
        assert result.message_id == "post123"

        # Verify post was called with correct URL
        call_args = self.adapter._session.post.call_args
        assert "/api/v4/posts" in call_args[0][0]
        # Verify payload
        payload = call_args[1]["json"]
        assert payload["channel_id"] == "channel_1"
        assert payload["message"] == "Hello!"

    @pytest.mark.asyncio
    async def test_send_empty_content_succeeds(self):
        """Empty content should return success without calling the API."""
        result = await self.adapter.send("channel_1", "")
        assert result.success is True

    @pytest.mark.asyncio
    async def test_send_with_thread_reply(self):
        """When reply_mode is 'thread', reply_to should become root_id."""
        self.adapter._reply_mode = "thread"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post456"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        # send() now calls _resolve_root_id → _api_get("posts/<id>") first
        # to make sure root_id points to a thread root, so we need to mock
        # the GET too.  Return an empty dict (no root_id) so the resolver
        # falls back to the original reply_to as the root.
        mock_get_resp = AsyncMock()
        mock_get_resp.status = 200
        mock_get_resp.json = AsyncMock(return_value={"id": "root_post", "root_id": ""})
        mock_get_resp.text = AsyncMock(return_value="")
        mock_get_resp.__aenter__ = AsyncMock(return_value=mock_get_resp)
        mock_get_resp.__aexit__ = AsyncMock(return_value=False)

        self.adapter._session.post = MagicMock(return_value=mock_resp)
        self.adapter._session.get = MagicMock(return_value=mock_get_resp)

        result = await self.adapter.send("channel_1", "Reply!", reply_to="root_post")

        assert result.success is True
        payload = self.adapter._session.post.call_args[1]["json"]
        assert payload["root_id"] == "root_post"

    @pytest.mark.asyncio
    async def test_send_with_metadata_thread_id(self):
        """When reply_mode is 'thread', metadata.thread_id should become root_id."""
        self.adapter._reply_mode = "thread"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post456"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_get_resp = AsyncMock()
        mock_get_resp.status = 200
        mock_get_resp.json = AsyncMock(return_value={"id": "root_from_metadata", "root_id": ""})
        mock_get_resp.text = AsyncMock(return_value="")
        mock_get_resp.__aenter__ = AsyncMock(return_value=mock_get_resp)
        mock_get_resp.__aexit__ = AsyncMock(return_value=False)

        self.adapter._session.post = MagicMock(return_value=mock_resp)
        self.adapter._session.get = MagicMock(return_value=mock_get_resp)

        result = await self.adapter.send(
            "channel_1", "Reply!", metadata={"thread_id": "root_from_metadata"}
        )

        assert result.success is True
        payload = self.adapter._session.post.call_args[1]["json"]
        assert payload["root_id"] == "root_from_metadata"

    @pytest.mark.asyncio
    async def test_send_exec_approval_posts_interactive_buttons_in_thread(self):
        """Approval prompts should use Mattermost buttons and stay in thread."""
        self.adapter._reply_mode = "thread"
        self.adapter._actions_public_url = "http://192.168.1.50:9120"
        self.adapter._api_get = AsyncMock(return_value={"id": "root_post", "root_id": ""})
        self.adapter._api_post = AsyncMock(return_value={"id": "approval_post"})

        result = await self.adapter.send_exec_approval(
            chat_id="channel_1",
            command="docker restart immich",
            session_key="session-123",
            description="dangerous command",
            metadata={"thread_id": "root_post"},
        )

        assert result.success is True
        payload = self.adapter._api_post.call_args[0][1]
        assert payload["channel_id"] == "channel_1"
        assert payload["root_id"] == "root_post"
        actions = payload["props"]["attachments"][0]["actions"]
        assert [a["name"] for a in actions] == [
            "Allow Once", "Allow Session", "Always Allow", "Deny"
        ]
        assert actions[0]["integration"]["url"] == "http://192.168.1.50:9120/mattermost/actions"
        approval_id = actions[0]["integration"]["context"]["approval_id"]
        assert self.adapter._approval_state[approval_id]["session_key"] == "session-123"

    @pytest.mark.asyncio
    async def test_action_request_resolves_stored_approval(self, monkeypatch):
        """Mattermost button callbacks should resolve the stored gateway approval."""
        monkeypatch.setenv("MATTERMOST_ALLOWED_USERS", "user_123")
        self.adapter._approval_state["approval-1"] = {
            "session_key": "session-123",
            "message_id": "approval_post",
            "chat_id": "channel_1",
            "thread_id": "root_post",
            "message": "approval message",
            "nonce": "nonce-123",
        }
        self.adapter._api_put = AsyncMock(return_value={})
        calls = []

        def fake_resolve(session_key, choice):
            calls.append((session_key, choice))
            return 1

        monkeypatch.setattr("tools.approval.resolve_gateway_approval", fake_resolve)

        class FakeRequest:
            async def json(self):
                return {
                    "user_id": "user_123",
                    "user_name": "alice",
                    "context": {
                        "approval_id": "approval-1",
                        "nonce": "nonce-123",
                        "action": "approve_session",
                    },
                }

        response = await self.adapter._handle_action_request(FakeRequest())

        assert response.status == 200
        assert calls == [("session-123", "session")]
        assert "approval-1" not in self.adapter._approval_state
        self.adapter._api_put.assert_called_once()

    @pytest.mark.asyncio
    async def test_action_request_rejects_invalid_nonce_without_consuming_state(self, monkeypatch):
        """Button callbacks must include the per-approval nonce."""
        monkeypatch.setenv("MATTERMOST_ALLOWED_USERS", "user_123")
        self.adapter._approval_state["approval-1"] = {
            "session_key": "session-123",
            "message_id": "approval_post",
            "chat_id": "channel_1",
            "thread_id": "root_post",
            "message": "approval message",
            "nonce": "nonce-123",
        }

        class FakeRequest:
            async def json(self):
                return {
                    "user_id": "user_123",
                    "context": {
                        "approval_id": "approval-1",
                        "nonce": "wrong",
                        "action": "approve_session",
                    },
                }

        response = await self.adapter._handle_action_request(FakeRequest())

        assert response.status == 200
        assert "approval-1" in self.adapter._approval_state

    @pytest.mark.asyncio
    async def test_action_request_does_not_consume_state_when_no_pending_approval(self, monkeypatch):
        """A stale tools.approval store should not burn the Mattermost button state."""
        monkeypatch.setenv("MATTERMOST_ALLOWED_USERS", "user_123")
        self.adapter._approval_state["approval-1"] = {
            "session_key": "session-123",
            "message_id": "approval_post",
            "chat_id": "channel_1",
            "thread_id": "root_post",
            "message": "approval message",
            "nonce": "nonce-123",
        }

        def fake_resolve(session_key, choice):
            return 0

        monkeypatch.setattr("tools.approval.resolve_gateway_approval", fake_resolve)

        class FakeRequest:
            async def json(self):
                return {
                    "user_id": "user_123",
                    "context": {
                        "approval_id": "approval-1",
                        "nonce": "nonce-123",
                        "action": "approve_session",
                    },
                }

        response = await self.adapter._handle_action_request(FakeRequest())

        assert response.status == 200
        assert "approval-1" in self.adapter._approval_state

    def test_bridge_server_starts_for_slash_endpoint_without_public_action_url(self):
        """Profile-local slash endpoints may bind loopback without a public action URL."""
        self.adapter._actions_public_url = ""
        self.adapter._actions_host = "127.0.0.1"
        self.adapter._slash_enabled = True

        assert self.adapter._actions_url() == ""
        assert self.adapter._should_start_bridge_server() is True

    @pytest.mark.asyncio
    async def test_slash_request_creates_command_event_without_trigger_id_as_message_id(self):
        """Native Mattermost slash commands should become command events safely."""
        self.adapter._slash_enabled = True
        self.adapter._slash_tokens = {"tok123"}
        self.adapter.handle_message = AsyncMock()

        class FakeRequest:
            async def post(self):
                return {
                    "token": "tok123",
                    "command": "/approve",
                    "text": "session",
                    "channel_id": "channel_1",
                    "user_id": "user_123",
                    "user_name": "alice",
                    "trigger_id": "ephemeral-trigger-not-a-post",
                }

        response = await self.adapter._handle_slash_request(FakeRequest())

        assert response.status == 200
        self.adapter.handle_message.assert_awaited_once()
        event = self.adapter.handle_message.call_args[0][0]
        assert event.text == "/approve session"
        assert event.message_type.name == "COMMAND"
        assert event.message_id is None
        assert event.source.message_id is None
        assert event.source.thread_id is None
        assert event.raw_message["trigger_id"] == "ephemeral-trigger-not-a-post"

    @pytest.mark.asyncio
    async def test_slash_request_rejects_unknown_token(self):
        self.adapter._slash_enabled = True
        self.adapter._slash_tokens = {"tok123"}
        self.adapter.handle_message = AsyncMock()

        class FakeRequest:
            async def post(self):
                return {
                    "token": "wrong",
                    "command": "/status",
                    "channel_id": "channel_1",
                }

        response = await self.adapter._handle_slash_request(FakeRequest())

        assert response.status == 403
        self.adapter.handle_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_slash_request_forwards_configured_channel(self, monkeypatch):
        """Router profile should forward selected channels to profile-local slash endpoints."""
        self.adapter._slash_enabled = True
        self.adapter._slash_tokens = {"tok123"}
        self.adapter._slash_forward_channels = {
            "channel_1": "http://127.0.0.1:9121/mattermost/slash"
        }
        self.adapter.handle_message = AsyncMock()
        posted = []

        class FakeForwardResponse:
            status = 200
            headers = {"Content-Type": "application/json"}
            async def read(self):
                return b'{"response_type":"ephemeral","text":"forwarded"}'
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False

        class FakeSession:
            def __init__(self, *args, **kwargs):
                pass
            async def __aenter__(self):
                return self
            async def __aexit__(self, *args):
                return False
            def post(self, url, data=None):
                posted.append((url, data))
                return FakeForwardResponse()

        monkeypatch.setattr("aiohttp.ClientSession", FakeSession)

        class FakeRequest:
            async def post(self):
                return {
                    "token": "tok123",
                    "command": "/profile",
                    "channel_id": "channel_1",
                    "user_id": "user_123",
                }

        response = await self.adapter._handle_slash_request(FakeRequest())

        assert response.status == 200
        assert posted == [("http://127.0.0.1:9121/mattermost/slash", {
            "token": "tok123",
            "command": "/profile",
            "channel_id": "channel_1",
            "user_id": "user_123",
        })]
        self.adapter.handle_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_slash_request_rejects_invalid_forward_target(self):
        self.adapter._slash_enabled = True
        self.adapter._slash_tokens = {"tok123"}
        self.adapter._slash_forward_channels = {"channel_1": "file:///tmp/bridge"}
        self.adapter.handle_message = AsyncMock()

        class FakeRequest:
            async def post(self):
                return {
                    "token": "tok123",
                    "command": "/profile",
                    "channel_id": "channel_1",
                    "user_id": "user_123",
                }

        response = await self.adapter._handle_slash_request(FakeRequest())

        assert response.status == 502
        self.adapter.handle_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_without_thread_no_root_id(self):
        """When reply_mode is 'off', reply_to should NOT set root_id."""
        self.adapter._reply_mode = "off"

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value={"id": "post789"})
        mock_resp.text = AsyncMock(return_value="")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        self.adapter._session.post = MagicMock(return_value=mock_resp)

        result = await self.adapter.send("channel_1", "Reply!", reply_to="root_post")

        assert result.success is True
        payload = self.adapter._session.post.call_args[1]["json"]
        assert "root_id" not in payload

    @pytest.mark.asyncio
    async def test_send_api_failure(self):
        """When API returns error, send should return failure."""
        mock_resp = AsyncMock()
        mock_resp.status = 500
        mock_resp.json = AsyncMock(return_value={})
        mock_resp.text = AsyncMock(return_value="Internal Server Error")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        self.adapter._session.post = MagicMock(return_value=mock_resp)

        result = await self.adapter.send("channel_1", "Hello!")

        assert result.success is False


# ---------------------------------------------------------------------------
# WebSocket event parsing
# ---------------------------------------------------------------------------

class TestMattermostWebSocketParsing:
    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._bot_user_id = "bot_user_id"
        self.adapter._bot_username = "hermes-bot"
        # Mock handle_message to capture the MessageEvent without processing
        self.adapter.handle_message = AsyncMock()

    @pytest.mark.asyncio
    async def test_parse_posted_event(self):
        """'posted' events should extract message from double-encoded post JSON."""
        post_data = {
            "id": "post_abc",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id Hello from Matrix!",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),  # double-encoded JSON string
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert self.adapter.handle_message.called
        msg_event = self.adapter.handle_message.call_args[0][0]
        # @mention is stripped from the message text
        assert msg_event.text == "Hello from Matrix!"
        assert msg_event.message_id == "post_abc"

    @pytest.mark.asyncio
    async def test_ignore_own_messages(self):
        """Messages from the bot's own user_id should be ignored."""
        post_data = {
            "id": "post_self",
            "user_id": "bot_user_id",  # same as bot
            "channel_id": "chan_456",
            "message": "Bot echo",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert not self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_ignore_non_posted_events(self):
        """Non-'posted' events should be ignored."""
        event = {
            "event": "typing",
            "data": {"user_id": "user_123"},
        }

        await self.adapter._handle_ws_event(event)
        assert not self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_ignore_system_posts(self):
        """Posts with a 'type' field (system messages) should be ignored."""
        post_data = {
            "id": "sys_post",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "user joined",
            "type": "system_join_channel",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert not self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_channel_type_mapping(self):
        """channel_type 'D' should map to 'dm'."""
        post_data = {
            "id": "post_dm",
            "user_id": "user_123",
            "channel_id": "chan_dm",
            "message": "DM message",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "D",
                "sender_name": "@bob",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert self.adapter.handle_message.called
        msg_event = self.adapter.handle_message.call_args[0][0]
        assert msg_event.source.chat_type == "dm"
        assert msg_event.source.thread_id is None

    @pytest.mark.asyncio
    async def test_root_channel_post_uses_own_id_as_thread_id(self):
        """Root channel posts should become their own Mattermost thread root."""
        post_data = {
            "id": "root_post_abc",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id Start a session",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert self.adapter.handle_message.called
        msg_event = self.adapter.handle_message.call_args[0][0]
        assert msg_event.source.thread_id == "root_post_abc"

    @pytest.mark.asyncio
    async def test_thread_id_from_root_id(self):
        """Post with root_id should have thread_id set."""
        post_data = {
            "id": "post_reply",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id Thread reply",
            "root_id": "root_post_123",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert self.adapter.handle_message.called
        msg_event = self.adapter.handle_message.call_args[0][0]
        assert msg_event.source.thread_id == "root_post_123"

    @pytest.mark.asyncio
    async def test_invalid_post_json_ignored(self):
        """Invalid JSON in data.post should be silently ignored."""
        event = {
            "event": "posted",
            "data": {
                "post": "not-valid-json{{{",
                "channel_type": "O",
            },
        }

        await self.adapter._handle_ws_event(event)
        assert not self.adapter.handle_message.called


# ---------------------------------------------------------------------------
# Mention behavior (require_mention + free_response_channels)
# ---------------------------------------------------------------------------

class TestMattermostMentionBehavior:
    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._bot_user_id = "bot_user_id"
        self.adapter._bot_username = "hermes-bot"
        self.adapter.handle_message = AsyncMock()

    def _make_event(self, message, channel_type="O", channel_id="chan_456"):
        post_data = {
            "id": "post_mention",
            "user_id": "user_123",
            "channel_id": channel_id,
            "message": message,
        }
        return {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": channel_type,
                "sender_name": "@alice",
            },
        }

    @pytest.mark.asyncio
    async def test_require_mention_true_skips_without_mention(self):
        """Default: messages without @mention in channels are skipped."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MATTERMOST_REQUIRE_MENTION", None)
            os.environ.pop("MATTERMOST_FREE_RESPONSE_CHANNELS", None)
            await self.adapter._handle_ws_event(self._make_event("hello"))
            assert not self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_require_mention_false_responds_to_all(self):
        """MATTERMOST_REQUIRE_MENTION=false: respond to all channel messages."""
        with patch.dict(os.environ, {"MATTERMOST_REQUIRE_MENTION": "false"}):
            await self.adapter._handle_ws_event(self._make_event("hello"))
            assert self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_free_response_channel_responds_without_mention(self):
        """Messages in free-response channels don't need @mention."""
        with patch.dict(os.environ, {"MATTERMOST_FREE_RESPONSE_CHANNELS": "chan_456,chan_789"}):
            os.environ.pop("MATTERMOST_REQUIRE_MENTION", None)
            await self.adapter._handle_ws_event(self._make_event("hello", channel_id="chan_456"))
            assert self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_non_free_channel_still_requires_mention(self):
        """Channels NOT in free-response list still require @mention."""
        with patch.dict(os.environ, {"MATTERMOST_FREE_RESPONSE_CHANNELS": "chan_789"}):
            os.environ.pop("MATTERMOST_REQUIRE_MENTION", None)
            await self.adapter._handle_ws_event(self._make_event("hello", channel_id="chan_456"))
            assert not self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_dm_always_responds(self):
        """DMs (channel_type=D) always respond regardless of mention settings."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MATTERMOST_REQUIRE_MENTION", None)
            await self.adapter._handle_ws_event(self._make_event("hello", channel_type="D"))
            assert self.adapter.handle_message.called

    @pytest.mark.asyncio
    async def test_mention_stripped_from_text(self):
        """@mention is stripped from message text."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MATTERMOST_REQUIRE_MENTION", None)
            await self.adapter._handle_ws_event(
                self._make_event("@hermes-bot what is 2+2")
            )
            assert self.adapter.handle_message.called
            msg = self.adapter.handle_message.call_args[0][0]
            assert "@hermes-bot" not in msg.text
            assert "2+2" in msg.text


# ---------------------------------------------------------------------------
# File upload (send_image)
# ---------------------------------------------------------------------------

class TestMattermostFileUpload:
    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._session = MagicMock()

    @pytest.mark.asyncio
    @patch("tools.url_safety.is_safe_url", return_value=True)
    async def test_send_image_downloads_and_uploads(self, _mock_safe):
        """send_image should download the URL, upload via /api/v4/files, then post."""
        # Mock the download (GET)
        mock_dl_resp = AsyncMock()
        mock_dl_resp.status = 200
        mock_dl_resp.read = AsyncMock(return_value=b"\x89PNG\x00fake-image-data")
        mock_dl_resp.content_type = "image/png"
        mock_dl_resp.__aenter__ = AsyncMock(return_value=mock_dl_resp)
        mock_dl_resp.__aexit__ = AsyncMock(return_value=False)

        # Mock the upload (POST to /files)
        mock_upload_resp = AsyncMock()
        mock_upload_resp.status = 200
        mock_upload_resp.json = AsyncMock(return_value={
            "file_infos": [{"id": "file_abc123"}]
        })
        mock_upload_resp.text = AsyncMock(return_value="")
        mock_upload_resp.__aenter__ = AsyncMock(return_value=mock_upload_resp)
        mock_upload_resp.__aexit__ = AsyncMock(return_value=False)

        # Mock the post (POST to /posts)
        mock_post_resp = AsyncMock()
        mock_post_resp.status = 200
        mock_post_resp.json = AsyncMock(return_value={"id": "post_with_file"})
        mock_post_resp.text = AsyncMock(return_value="")
        mock_post_resp.__aenter__ = AsyncMock(return_value=mock_post_resp)
        mock_post_resp.__aexit__ = AsyncMock(return_value=False)

        # Route calls: first GET (download), then POST (upload), then POST (create post)
        self.adapter._session.get = MagicMock(return_value=mock_dl_resp)
        post_call_count = 0
        original_post_returns = [mock_upload_resp, mock_post_resp]

        def post_side_effect(*args, **kwargs):
            nonlocal post_call_count
            resp = original_post_returns[min(post_call_count, len(original_post_returns) - 1)]
            post_call_count += 1
            return resp

        self.adapter._session.post = MagicMock(side_effect=post_side_effect)

        result = await self.adapter.send_image(
            "channel_1", "https://img.example.com/cat.png", caption="A cat"
        )

        assert result.success is True
        assert result.message_id == "post_with_file"


# ---------------------------------------------------------------------------
# Dedup cache
# ---------------------------------------------------------------------------

class TestMattermostDedup:
    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._bot_user_id = "bot_user_id"
        # Mock handle_message to capture calls without processing
        self.adapter.handle_message = AsyncMock()

    @pytest.mark.asyncio
    async def test_duplicate_post_ignored(self):
        """The same post_id within the TTL window should be ignored."""
        post_data = {
            "id": "post_dup",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id Hello!",
        }
        event = {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }

        # First time: should process
        await self.adapter._handle_ws_event(event)
        assert self.adapter.handle_message.call_count == 1

        # Second time (same post_id): should be deduped
        await self.adapter._handle_ws_event(event)
        assert self.adapter.handle_message.call_count == 1  # still 1

    @pytest.mark.asyncio
    async def test_different_post_ids_both_processed(self):
        """Different post IDs should both be processed."""
        for i, pid in enumerate(["post_a", "post_b"]):
            post_data = {
                "id": pid,
                "user_id": "user_123",
                "channel_id": "chan_456",
                "message": f"@bot_user_id Message {i}",
            }
            event = {
                "event": "posted",
                "data": {
                    "post": json.dumps(post_data),
                    "channel_type": "O",
                    "sender_name": "@alice",
                },
            }
            await self.adapter._handle_ws_event(event)

        assert self.adapter.handle_message.call_count == 2

    def test_prune_seen_clears_expired(self):
        """Dedup cache should remove entries older than TTL on overflow."""
        now = time.time()
        dedup = self.adapter._dedup
        # Fill with enough expired entries to trigger pruning
        for i in range(dedup._max_size + 10):
            dedup._seen[f"old_{i}"] = now - 600  # 10 min ago (older than default TTL)

        # Add a fresh one
        dedup._seen["fresh"] = now

        # Trigger pruning by calling is_duplicate with a new entry (over max_size)
        dedup.is_duplicate("trigger_prune")

        # Old entries should be pruned, fresh one kept
        assert "fresh" in dedup._seen
        assert len(dedup._seen) < dedup._max_size + 10

    def test_seen_cache_tracks_post_ids(self):
        """Posts are tracked in the dedup cache."""
        self.adapter._dedup._seen["test_post"] = time.time()
        assert "test_post" in self.adapter._dedup._seen


# ---------------------------------------------------------------------------
# Requirements check
# ---------------------------------------------------------------------------

class TestMattermostRequirements:
    def test_check_requirements_with_token_and_url(self, monkeypatch):
        monkeypatch.setenv("MATTERMOST_TOKEN", "test-token")
        monkeypatch.setenv("MATTERMOST_URL", "https://mm.example.com")
        from plugins.platforms.mattermost.adapter import check_mattermost_requirements
        assert check_mattermost_requirements() is True

    def test_check_requirements_without_token(self, monkeypatch):
        monkeypatch.delenv("MATTERMOST_TOKEN", raising=False)
        monkeypatch.delenv("MATTERMOST_URL", raising=False)
        from plugins.platforms.mattermost.adapter import check_mattermost_requirements
        assert check_mattermost_requirements() is False

    def test_check_requirements_without_url(self, monkeypatch):
        monkeypatch.setenv("MATTERMOST_TOKEN", "test-token")
        monkeypatch.delenv("MATTERMOST_URL", raising=False)
        from plugins.platforms.mattermost.adapter import check_mattermost_requirements
        assert check_mattermost_requirements() is False


# ---------------------------------------------------------------------------
# Media type propagation (MIME types, not bare strings)
# ---------------------------------------------------------------------------

class TestMattermostMediaTypes:
    """Verify that media_types contains actual MIME types (e.g. 'image/png')
    rather than bare category strings ('image'), so downstream
    ``mtype.startswith("image/")`` checks in run.py work correctly."""

    def setup_method(self):
        self.adapter = _make_adapter()
        self.adapter._bot_user_id = "bot_user_id"
        self.adapter.handle_message = AsyncMock()

    def _make_event(self, file_ids):
        post_data = {
            "id": "post_media",
            "user_id": "user_123",
            "channel_id": "chan_456",
            "message": "@bot_user_id file attached",
            "file_ids": file_ids,
        }
        return {
            "event": "posted",
            "data": {
                "post": json.dumps(post_data),
                "channel_type": "O",
                "sender_name": "@alice",
            },
        }

    @pytest.mark.asyncio
    async def test_image_media_type_is_full_mime(self):
        """An image attachment should produce 'image/png', not 'image'."""
        file_info = {"name": "photo.png", "mime_type": "image/png"}
        self.adapter._api_get = AsyncMock(return_value=file_info)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"\x89PNG fake")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        self.adapter._session = MagicMock()
        self.adapter._session.get = MagicMock(return_value=mock_resp)

        with patch("gateway.platforms.base.cache_image_from_bytes", return_value="/tmp/photo.png"):
            await self.adapter._handle_ws_event(self._make_event(["file1"]))

        msg = self.adapter.handle_message.call_args[0][0]
        assert msg.media_types == ["image/png"]
        assert msg.media_types[0].startswith("image/")

    @pytest.mark.asyncio
    async def test_audio_media_type_is_full_mime(self):
        """An audio attachment should produce 'audio/ogg', not 'audio'."""
        file_info = {"name": "voice.ogg", "mime_type": "audio/ogg"}
        self.adapter._api_get = AsyncMock(return_value=file_info)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"OGG fake")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        self.adapter._session = MagicMock()
        self.adapter._session.get = MagicMock(return_value=mock_resp)

        with patch("gateway.platforms.base.cache_audio_from_bytes", return_value="/tmp/voice.ogg"), \
             patch("gateway.platforms.base.cache_image_from_bytes"), \
             patch("gateway.platforms.base.cache_document_from_bytes"):
            await self.adapter._handle_ws_event(self._make_event(["file2"]))

        msg = self.adapter.handle_message.call_args[0][0]
        assert msg.media_types == ["audio/ogg"]
        assert msg.media_types[0].startswith("audio/")

    @pytest.mark.asyncio
    async def test_video_media_type_is_full_mime_and_video_message(self):
        """A video attachment should stay video, not degrade to a document."""
        file_info = {"name": "clip.mp4", "mime_type": "video/mp4"}
        self.adapter._api_get = AsyncMock(return_value=file_info)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"MP4 fake")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        self.adapter._session = MagicMock()
        self.adapter._session.get = MagicMock(return_value=mock_resp)

        with patch("gateway.platforms.base.cache_video_from_bytes", return_value="/tmp/clip.mp4"), \
             patch("gateway.platforms.base.cache_document_from_bytes"), \
             patch("gateway.platforms.base.cache_image_from_bytes"):
            await self.adapter._handle_ws_event(self._make_event(["file4"]))

        msg = self.adapter.handle_message.call_args[0][0]
        from gateway.platforms.base import MessageType
        assert msg.message_type == MessageType.VIDEO
        assert msg.media_types == ["video/mp4"]
        assert msg.media_types[0].startswith("video/")

    @pytest.mark.asyncio
    async def test_document_media_type_is_full_mime(self):
        """A document attachment should produce 'application/pdf', not 'document'."""
        file_info = {"name": "report.pdf", "mime_type": "application/pdf"}
        self.adapter._api_get = AsyncMock(return_value=file_info)

        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.read = AsyncMock(return_value=b"PDF fake")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        self.adapter._session = MagicMock()
        self.adapter._session.get = MagicMock(return_value=mock_resp)

        with patch("gateway.platforms.base.cache_document_from_bytes", return_value="/tmp/report.pdf"), \
             patch("gateway.platforms.base.cache_image_from_bytes"):
            await self.adapter._handle_ws_event(self._make_event(["file3"]))

        msg = self.adapter.handle_message.call_args[0][0]
        assert msg.media_types == ["application/pdf"]
        assert not msg.media_types[0].startswith("image/")
        assert not msg.media_types[0].startswith("audio/")
