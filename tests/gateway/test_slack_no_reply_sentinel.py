"""
Tests for the Slack adapter's explicit NO_REPLY sentinel handling.

Mirrors the precedent in ``gateway/platforms/feishu_comment.py``: when the
agent returns exactly ``NO_REPLY`` (after trimming surrounding whitespace),
the Slack adapter must treat the turn as intentional silence and skip the
final ``chat_postMessage`` call instead of posting the literal sentinel.
"""

import sys
from unittest.mock import AsyncMock, MagicMock

import pytest


def _ensure_slack_mock():
    """Install mock slack modules so SlackAdapter can be imported."""
    if "slack_bolt" in sys.modules and hasattr(sys.modules["slack_bolt"], "__file__"):
        return

    slack_bolt = MagicMock()
    slack_bolt.async_app.AsyncApp = MagicMock
    slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler = MagicMock

    slack_sdk = MagicMock()
    slack_sdk.web.async_client.AsyncWebClient = MagicMock

    for name, mod in [
        ("slack_bolt", slack_bolt),
        ("slack_bolt.async_app", slack_bolt.async_app),
        ("slack_bolt.adapter", slack_bolt.adapter),
        ("slack_bolt.adapter.socket_mode", slack_bolt.adapter.socket_mode),
        ("slack_bolt.adapter.socket_mode.async_handler", slack_bolt.adapter.socket_mode.async_handler),
        ("slack_sdk", slack_sdk),
        ("slack_sdk.web", slack_sdk.web),
        ("slack_sdk.web.async_client", slack_sdk.web.async_client),
    ]:
        sys.modules.setdefault(name, mod)

    sys.modules.setdefault("aiohttp", MagicMock())


_ensure_slack_mock()

import gateway.platforms.slack as _slack_mod  # noqa: E402
_slack_mod.SLACK_AVAILABLE = True

from gateway.config import PlatformConfig  # noqa: E402
from gateway.platforms.slack import SlackAdapter, _NO_REPLY_SENTINEL  # noqa: E402


@pytest.fixture()
def adapter():
    config = PlatformConfig(enabled=True, token="xoxb-fake-token")
    a = SlackAdapter(config)
    a._app = MagicMock()
    a._app.client = AsyncMock()
    a._app.client.chat_postMessage = AsyncMock(return_value={"ts": "111.222"})
    a._bot_user_id = "U_BOT"
    a._running = True
    return a


def test_sentinel_is_no_reply():
    assert _NO_REPLY_SENTINEL == "NO_REPLY"


@pytest.mark.asyncio
async def test_send_suppresses_exact_sentinel(adapter):
    result = await adapter.send("C123", "NO_REPLY")

    assert result.success is True
    assert result.message_id is None
    assert result.raw_response == {"suppressed": "NO_REPLY"}
    adapter._app.client.chat_postMessage.assert_not_called()


@pytest.mark.asyncio
async def test_send_suppresses_sentinel_with_whitespace(adapter):
    result = await adapter.send("C123", "  NO_REPLY\n")

    assert result.success is True
    adapter._app.client.chat_postMessage.assert_not_called()


@pytest.mark.asyncio
async def test_send_posts_longer_message_containing_sentinel(adapter):
    result = await adapter.send("C123", "I would not use NO_REPLY here")

    assert result.success is True
    adapter._app.client.chat_postMessage.assert_called_once()
    posted_kwargs = adapter._app.client.chat_postMessage.call_args.kwargs
    assert posted_kwargs["channel"] == "C123"
    assert posted_kwargs["text"] == "I would not use NO_REPLY here"


@pytest.mark.asyncio
async def test_send_posts_empty_string_normally(adapter):
    """Empty string is not the sentinel — fall through to normal send path."""
    result = await adapter.send("C123", "")

    assert result.success is True
    adapter._app.client.chat_postMessage.assert_called_once()


@pytest.mark.asyncio
async def test_send_posts_case_variant_sentinel(adapter):
    """Match is exact and case-sensitive — ``no_reply`` is not suppressed."""
    result = await adapter.send("C123", "no_reply")

    assert result.success is True
    adapter._app.client.chat_postMessage.assert_called_once()
