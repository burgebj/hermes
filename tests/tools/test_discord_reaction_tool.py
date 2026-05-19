"""Tests for the discord_add_reaction + discord_remove_reaction outbound tools.

Covers:
1.  add_reaction happy path — message.add_reaction called with correct emoji
2.  add_reaction missing channel_id → tool_error
3.  add_reaction missing message_id → tool_error
4.  add_reaction missing emoji → tool_error
5.  add_reaction adapter not initialized → tool_error
6.  add_reaction channel not found (cache miss + fetch raises) → tool_error
7.  add_reaction message not found (channel.fetch_message raises NotFound) → tool_error
8.  add_reaction Forbidden (no ADD_REACTIONS perm) → tool_error mentioning permission
9.  remove_reaction happy path — message.remove_reaction called with correct emoji and bot user
10. remove_reaction Forbidden → tool_error
11. remove_reaction missing inputs validation parity
12. add_reaction non-numeric channel_id → tool_error
"""

from __future__ import annotations

import json
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# Discord mock is set up in tests/tools/conftest.py before this module imports.
# Import after mock is in place
from tools.discord_reaction_tool import (  # noqa: E402
    _handler_add_async,
    _handler_remove_async,
)


# ---------------------------------------------------------------------------
# Fake adapter / channel / message
# ---------------------------------------------------------------------------

def _make_message(message_id: str = "555000555") -> MagicMock:
    """Fake discord.Message with awaitable add_reaction / remove_reaction."""
    message = MagicMock()
    message.id = int(message_id)
    message.channel = SimpleNamespace(id=111222333)
    message.add_reaction = AsyncMock(return_value=None)
    message.remove_reaction = AsyncMock(return_value=None)
    return message


def _make_channel(message: Any = None, fetch_message_raises: Exception | None = None) -> MagicMock:
    """Fake discord.TextChannel with .fetch_message returning the given message."""
    channel = MagicMock()
    fake_message = message or _make_message()
    if fetch_message_raises is not None:
        channel.fetch_message = AsyncMock(side_effect=fetch_message_raises)
    else:
        channel.fetch_message = AsyncMock(return_value=fake_message)
    return channel


def _make_adapter(
    channel: Any = None,
    fetch_channel_raises: bool = False,
    bot_user: Any | None = None,
) -> MagicMock:
    """Build a minimal fake DiscordAdapter exposing ._client."""
    adapter = MagicMock()
    fake_channel = channel or _make_channel()
    client = MagicMock()
    client.get_channel.return_value = fake_channel
    if fetch_channel_raises:
        client.fetch_channel = AsyncMock(side_effect=Exception("channel not found"))
    else:
        client.fetch_channel = AsyncMock(return_value=fake_channel)
    client.user = bot_user if bot_user is not None else SimpleNamespace(id=987654321, name="bluenode-bot")
    adapter._client = client
    return adapter


def _patch_adapter(adapter: Any):
    return patch("tools.discord_reaction_tool._get_discord_adapter", return_value=adapter)


# ===========================================================================
# add_reaction tests
# ===========================================================================

@pytest.mark.asyncio
async def test_add_reaction_happy_path() -> None:
    message = _make_message(message_id="111000111")
    channel = _make_channel(message=message)
    adapter = _make_adapter(channel=channel)

    with _patch_adapter(adapter):
        result_str = await _handler_add_async({
            "channel_id": "123456789",
            "message_id": "111000111",
            "emoji": "✅",
        })

    result = json.loads(result_str)
    assert "error" not in result
    assert result["message_id"] == "111000111"
    assert result["channel_id"] == "111222333"
    assert result["emoji"] == "✅"
    message.add_reaction.assert_called_once_with("✅")


@pytest.mark.asyncio
async def test_add_reaction_missing_channel_id() -> None:
    result = json.loads(await _handler_add_async({
        "message_id": "1",
        "emoji": "✅",
    }))
    assert "error" in result
    assert "channel_id" in result["error"]


@pytest.mark.asyncio
async def test_add_reaction_missing_message_id() -> None:
    result = json.loads(await _handler_add_async({
        "channel_id": "1",
        "emoji": "✅",
    }))
    assert "error" in result
    assert "message_id" in result["error"]


@pytest.mark.asyncio
async def test_add_reaction_missing_emoji() -> None:
    result = json.loads(await _handler_add_async({
        "channel_id": "1",
        "message_id": "2",
    }))
    assert "error" in result
    assert "emoji" in result["error"]


@pytest.mark.asyncio
async def test_add_reaction_adapter_not_initialized() -> None:
    with _patch_adapter(None):
        result = json.loads(await _handler_add_async({
            "channel_id": "1",
            "message_id": "2",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "adapter" in result["error"].lower() or "not initialized" in result["error"].lower()


@pytest.mark.asyncio
async def test_add_reaction_channel_not_found() -> None:
    adapter = _make_adapter(fetch_channel_raises=True)
    adapter._client.get_channel.return_value = None

    with _patch_adapter(adapter):
        result = json.loads(await _handler_add_async({
            "channel_id": "000000000",
            "message_id": "1",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "not found" in result["error"].lower() or "channel" in result["error"].lower()


@pytest.mark.asyncio
async def test_add_reaction_channel_forbidden() -> None:
    """fetch_channel raising discord.Forbidden surfaces a permission error,
    not the generic 'channel not found' message — addresses architect's
    commit-9 next-pass note #1.
    """
    import discord as _discord_mod
    adapter = _make_adapter(fetch_channel_raises=True)
    adapter._client.get_channel.return_value = None
    adapter._client.fetch_channel = AsyncMock(side_effect=_discord_mod.Forbidden("no view"))

    with _patch_adapter(adapter):
        result = json.loads(await _handler_add_async({
            "channel_id": "1",
            "message_id": "2",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "permission" in result["error"].lower() or "VIEW_CHANNEL" in result["error"]


@pytest.mark.asyncio
async def test_add_reaction_message_not_found() -> None:
    import discord as _discord_mod
    channel = _make_channel(fetch_message_raises=_discord_mod.NotFound("msg gone"))
    adapter = _make_adapter(channel=channel)

    with _patch_adapter(adapter):
        result = json.loads(await _handler_add_async({
            "channel_id": "1",
            "message_id": "999",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "not found" in result["error"].lower() or "999" in result["error"]


@pytest.mark.asyncio
async def test_add_reaction_forbidden() -> None:
    import discord as _discord_mod
    message = _make_message()
    message.add_reaction = AsyncMock(side_effect=_discord_mod.Forbidden("no perm"))
    channel = _make_channel(message=message)
    adapter = _make_adapter(channel=channel)

    with _patch_adapter(adapter):
        result = json.loads(await _handler_add_async({
            "channel_id": "1",
            "message_id": "2",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "permission" in result["error"].lower() or "ADD_REACTIONS" in result["error"]


@pytest.mark.asyncio
async def test_add_reaction_non_numeric_channel_id() -> None:
    adapter = _make_adapter()
    with _patch_adapter(adapter):
        result = json.loads(await _handler_add_async({
            "channel_id": "not-a-number",
            "message_id": "1",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "channel_id" in result["error"] or "snowflake" in result["error"].lower()


# ===========================================================================
# remove_reaction tests
# ===========================================================================

@pytest.mark.asyncio
async def test_remove_reaction_happy_path() -> None:
    message = _make_message(message_id="222000222")
    channel = _make_channel(message=message)
    bot_user = SimpleNamespace(id=987654321, name="bluenode-bot")
    adapter = _make_adapter(channel=channel, bot_user=bot_user)

    with _patch_adapter(adapter):
        result_str = await _handler_remove_async({
            "channel_id": "1",
            "message_id": "222000222",
            "emoji": "✅",
        })

    result = json.loads(result_str)
    assert "error" not in result
    assert result["message_id"] == "222000222"
    assert result["emoji"] == "✅"
    message.remove_reaction.assert_called_once_with("✅", bot_user)


@pytest.mark.asyncio
async def test_remove_reaction_forbidden() -> None:
    import discord as _discord_mod
    message = _make_message()
    message.remove_reaction = AsyncMock(side_effect=_discord_mod.Forbidden("no perm"))
    channel = _make_channel(message=message)
    adapter = _make_adapter(channel=channel)

    with _patch_adapter(adapter):
        result = json.loads(await _handler_remove_async({
            "channel_id": "1",
            "message_id": "2",
            "emoji": "✅",
        }))
    assert "error" in result
    assert "permission" in result["error"].lower() or "MANAGE" in result["error"] or "ADD_REACTIONS" in result["error"]


@pytest.mark.asyncio
async def test_remove_reaction_missing_emoji() -> None:
    result = json.loads(await _handler_remove_async({
        "channel_id": "1",
        "message_id": "2",
    }))
    assert "error" in result
    assert "emoji" in result["error"]
