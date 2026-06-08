"""
Tests for the Slack adapter's explicit NO_REPLY sentinel handling.

Mirrors the precedent in ``gateway/platforms/feishu_comment.py``: when the
agent returns exactly ``NO_REPLY`` (after trimming surrounding whitespace),
the Slack adapter must treat the turn as intentional silence and skip the
final ``chat_postMessage`` call instead of posting the literal sentinel.
"""

import importlib.util
import sys
import time
from unittest.mock import AsyncMock, MagicMock

import pytest


def _is_missing(name: str) -> bool:
    """``find_spec`` raises ``ModuleNotFoundError`` when a parent package
    is absent, or ``ValueError`` when a previous test injected a MagicMock
    for the parent (no ``__spec__``).  Both cases mean we have no real
    package — treat them as 'missing' rather than letting the test
    collection fail.  Direct ``sys.modules`` presence also counts as
    'present' since the original test installed mocks there.
    """
    if name in sys.modules:
        return False
    try:
        return importlib.util.find_spec(name) is None
    except (ModuleNotFoundError, ValueError):
        return True


def _missing_modules() -> list[str]:
    """Return the slack/aiohttp imports that this test file would need to
    stub in.  We only install stubs for modules that are genuinely absent —
    shadowing a real installed package would leak into the rest of the test
    run.
    """
    candidates = [
        "slack_bolt",
        "slack_bolt.async_app",
        "slack_bolt.adapter",
        "slack_bolt.adapter.socket_mode",
        "slack_bolt.adapter.socket_mode.async_handler",
        "slack_sdk",
        "slack_sdk.web",
        "slack_sdk.web.async_client",
        "aiohttp",
    ]
    return [name for name in candidates if _is_missing(name)]


@pytest.fixture(autouse=True)
def _slack_module_stubs(monkeypatch):
    """Insert mock slack/aiohttp modules only when absent, and remove them
    after the test so other tests are not affected.

    The earlier implementation used ``sys.modules.setdefault`` at import
    time, which could shadow real packages that simply hadn't been imported
    yet (notably ``aiohttp``) and leaked into other tests in the same run.
    """
    slack_bolt = MagicMock()
    slack_bolt.async_app.AsyncApp = MagicMock
    slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler = MagicMock

    slack_sdk = MagicMock()
    slack_sdk.web.async_client.AsyncWebClient = MagicMock

    submodules = {
        "slack_bolt": slack_bolt,
        "slack_bolt.async_app": slack_bolt.async_app,
        "slack_bolt.adapter": slack_bolt.adapter,
        "slack_bolt.adapter.socket_mode": slack_bolt.adapter.socket_mode,
        "slack_bolt.adapter.socket_mode.async_handler": (
            slack_bolt.adapter.socket_mode.async_handler
        ),
        "slack_sdk": slack_sdk,
        "slack_sdk.web": slack_sdk.web,
        "slack_sdk.web.async_client": slack_sdk.web.async_client,
        "aiohttp": MagicMock(),
    }
    for name in _missing_modules():
        monkeypatch.setitem(sys.modules, name, submodules[name])

    yield


@pytest.fixture()
def adapter():
    import gateway.platforms.slack as _slack_mod
    from gateway.config import PlatformConfig
    from gateway.platforms.slack import SlackAdapter

    _slack_mod.SLACK_AVAILABLE = True
    config = PlatformConfig(enabled=True, token="xoxb-fake-token")
    a = SlackAdapter(config)
    a._app = MagicMock()
    a._app.client = AsyncMock()
    a._app.client.chat_postMessage = AsyncMock(return_value={"ts": "111.222"})
    a._bot_user_id = "U_BOT"
    a._running = True
    return a


def test_sentinel_is_no_reply():
    from gateway.platforms.slack import _NO_REPLY_SENTINEL

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


@pytest.mark.asyncio
async def test_send_no_reply_consumes_slash_context_and_clears_typing(adapter):
    """NO_REPLY after a slash command must consume the stashed response_url
    and clear any typing indicator, so a later unrelated send() to the same
    channel doesn't inherit the stale ephemeral context.
    """
    delete_calls: list[dict] = []

    async def fake_delete(ctx):
        delete_calls.append(ctx)

    stop_calls: list[str] = []

    async def fake_stop_typing(chat_id, metadata=None):
        stop_calls.append(chat_id)

    adapter._delete_slash_ephemeral = fake_delete
    adapter.stop_typing = fake_stop_typing
    # Seed a slash context for (channel, user); use the precise key form
    # that ``_pop_slash_context`` looks up against.
    from gateway.platforms.slack import _slash_user_id

    _slash_user_id.set("U_USER")
    adapter._slash_command_contexts[("C123", "U_USER")] = {
        "response_url": "https://hooks.slack.com/commands/T/1/abc",
        "ts": time.monotonic(),
    }

    result = await adapter.send("C123", "NO_REPLY")

    assert result.success is True
    assert result.raw_response == {"suppressed": "NO_REPLY"}
    adapter._app.client.chat_postMessage.assert_not_called()
    # The stashed slash context was consumed (not left for later sends).
    assert ("C123", "U_USER") not in adapter._slash_command_contexts
    # The ephemeral ack was deleted via response_url.
    assert len(delete_calls) == 1
    assert delete_calls[0]["response_url"].endswith("/abc")
    # The typing indicator was cleared.
    assert stop_calls == ["C123"]
