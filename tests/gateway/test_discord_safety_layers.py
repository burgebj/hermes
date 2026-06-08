"""Tests for Discord bot message filtering — multi-layer safety (#32791).

Layer 1: free_response_channels must respect DISCORD_ALLOW_BOTS=mentions.
Layer 2: Anti-loop circuit breaker after N bot replies in a channel.
Layer 3: In-band operator HALT signal suspends auto-reply globally.

These are production-path tests: they create a real DiscordAdapter, configure
env vars, and call _handle_message, verifying whether the message is accepted
or blocked via adapter.handle_message (AsyncMock).
"""

import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
import sys

import pytest


def _ensure_discord_mock():
    if "discord" in sys.modules and hasattr(sys.modules["discord"], "__file__"):
        return

    discord_mod = MagicMock()
    discord_mod.Intents.default.return_value = MagicMock()
    discord_mod.Client = MagicMock
    discord_mod.File = MagicMock
    discord_mod.DMChannel = type("DMChannel", (), {})
    discord_mod.Thread = type("Thread", (), {})
    discord_mod.ForumChannel = type("ForumChannel", (), {})
    discord_mod.MessageType = SimpleNamespace(
        default=0, reply=19,
    )
    discord_mod.ui = SimpleNamespace(
        View=object,
        button=lambda *a, **k: (lambda fn: fn),
        Button=object,
    )
    discord_mod.ButtonStyle = SimpleNamespace(
        success=1, primary=2, secondary=2, danger=3,
        green=1, grey=2, blurple=2, red=3,
    )
    discord_mod.Color = SimpleNamespace(
        orange=lambda: 1, green=lambda: 2, blue=lambda: 3,
        red=lambda: 4, purple=lambda: 5,
    )
    discord_mod.Interaction = object
    discord_mod.Embed = MagicMock
    discord_mod.app_commands = SimpleNamespace(
        describe=lambda **kwargs: (lambda fn: fn),
        choices=lambda **kwargs: (lambda fn: fn),
        Choice=lambda **kwargs: SimpleNamespace(**kwargs),
    )

    ext_mod = MagicMock()
    commands_mod = MagicMock()
    commands_mod.Bot = MagicMock
    ext_mod.commands = commands_mod

    sys.modules.setdefault("discord", discord_mod)
    sys.modules.setdefault("discord.ext", ext_mod)
    sys.modules.setdefault("discord.ext.commands", commands_mod)


_ensure_discord_mock()

import plugins.platforms.discord.adapter as discord_platform  # noqa: E402
from plugins.platforms.discord.adapter import DiscordAdapter  # noqa: E402


# ── Test helpers ────────────────────────────────────────────────────────────


class FakeTextChannel:
    def __init__(self, channel_id: int = 1, name: str = "general",
                 guild_name: str = "Hermes Server"):
        self.id = channel_id
        self.name = name
        self.guild = SimpleNamespace(name=guild_name)
        self.topic = None

    def history(self, *, limit, before, after=None, oldest_first=None):
        async def _iter():
            return
            yield
        return _iter()


class FakeDMChannel:
    def __init__(self, channel_id: int = 1, name: str = "dm"):
        self.id = channel_id
        self.name = name


def _make_user(user_id: int, *, bot: bool = False,
               display_name: str = "User", name: str = "User"):
    user = SimpleNamespace(
        id=user_id, display_name=display_name, name=name, bot=bot,
    )
    return user


def _make_message(*, channel, content: str, author=None, mentions=None):
    author = author or _make_user(42)
    return SimpleNamespace(
        id=123,
        content=content,
        mentions=list(mentions or []),
        attachments=[],
        reference=None,
        created_at=None,
        channel=channel,
        author=author,
        type=discord_platform.discord.MessageType.default,
    )


@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setattr(discord_platform.discord, "DMChannel",
                        FakeDMChannel, raising=False)
    monkeypatch.setattr(discord_platform.discord, "Thread",
                        FakeTextChannel, raising=False)

    for _var in (
        "DISCORD_REQUIRE_MENTION",
        "DISCORD_THREAD_REQUIRE_MENTION",
        "DISCORD_FREE_RESPONSE_CHANNELS",
        "DISCORD_AUTO_THREAD",
        "DISCORD_NO_THREAD_CHANNELS",
        "DISCORD_ALLOWED_CHANNELS",
        "DISCORD_IGNORED_CHANNELS",
        "DISCORD_ALLOW_BOTS",
        "DISCORD_OPERATOR_IDS",
        "DISCORD_HALT_PATTERN",
        "DISCORD_HALT_COOLDOWN_S",
        "DISCORD_CIRCUIT_BREAKER_WINDOW_S",
        "DISCORD_CIRCUIT_BREAKER_THRESHOLD",
        "DISCORD_CIRCUIT_BREAKER_COOLDOWN_S",
        "DISCORD_TEXT_BATCH_DELAY_SECONDS",
    ):
        monkeypatch.delenv(_var, raising=False)

    from gateway.config import PlatformConfig
    config = PlatformConfig(enabled=True, token="fake-token")
    adapter = DiscordAdapter(config)
    adapter._client = SimpleNamespace(user=SimpleNamespace(id=999))
    adapter._text_batch_delay_seconds = 0
    adapter.handle_message = AsyncMock()
    return adapter


# ── Layer 1: free_response_channels must respect DISCORD_ALLOW_BOTS ─────────


@pytest.mark.asyncio
async def test_free_response_gated_by_allow_bots_mentions(adapter, monkeypatch):
    """Bot message in free-response channel blocked when
    DISCORD_ALLOW_BOTS=mentions and no @mention (#32791 L1)."""
    monkeypatch.setenv("DISCORD_FREE_RESPONSE_CHANNELS", "789")
    monkeypatch.setenv("DISCORD_ALLOW_BOTS", "mentions")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "true")

    bot_author = _make_user(888, bot=True, display_name="OtherBot")
    message = _make_message(
        channel=FakeTextChannel(channel_id=789),
        content="hello from another bot",
        author=bot_author,
    )

    await adapter._handle_message(message)

    # Should be blocked: free_response_channels must not bypass
    # DISCORD_ALLOW_BOTS=mentions for bot messages without @mention.
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_free_response_allows_bots_with_allow_bots_all(adapter, monkeypatch):
    """With DISCORD_ALLOW_BOTS=all, bot messages in free-response
    channels ARE accepted (operator intentionally allows bot-to-bot)."""
    monkeypatch.setenv("DISCORD_FREE_RESPONSE_CHANNELS", "789")
    monkeypatch.setenv("DISCORD_ALLOW_BOTS", "all")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "true")

    bot_author = _make_user(888, bot=True, display_name="OtherBot")
    message = _make_message(
        channel=FakeTextChannel(channel_id=789),
        content="hello from another bot",
        author=bot_author,
    )

    await adapter._handle_message(message)

    # Should be accepted: ALLOW_BOTS=all explicitly permits bot messages.
    adapter.handle_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_free_response_allows_bots_when_mentioned(adapter, monkeypatch):
    """Bot message WITH @mention in free-response channel is accepted
    even with ALLOW_BOTS=mentions (Layer 1 doesn't block @mentions)."""
    monkeypatch.setenv("DISCORD_FREE_RESPONSE_CHANNELS", "789")
    monkeypatch.setenv("DISCORD_ALLOW_BOTS", "mentions")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "true")

    our_user = SimpleNamespace(id=999)
    bot_author = _make_user(888, bot=True, display_name="OtherBot")
    message = _make_message(
        channel=FakeTextChannel(channel_id=789),
        content="hello @hermes",
        author=bot_author,
        mentions=[our_user],
    )

    await adapter._handle_message(message)

    # Should be accepted: the bot @mentioned us.
    adapter.handle_message.assert_awaited_once()


# ── Layer 2: Anti-loop circuit breaker ──────────────────────────────────────


@pytest.mark.asyncio
async def test_circuit_breaker_trips_after_threshold(adapter, monkeypatch):
    """After N bot replies in a channel within the window, further
    messages are blocked until the cooldown expires (#32791 L2)."""
    monkeypatch.setenv("DISCORD_FREE_RESPONSE_CHANNELS", "789")
    monkeypatch.setenv("DISCORD_ALLOW_BOTS", "all")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "true")
    monkeypatch.setenv("DISCORD_CIRCUIT_BREAKER_THRESHOLD", "3")
    monkeypatch.setenv("DISCORD_CIRCUIT_BREAKER_WINDOW_S", "3600")
    monkeypatch.setenv("DISCORD_CIRCUIT_BREAKER_COOLDOWN_S", "999999")

    bot = _make_user(888, bot=True, display_name="OtherBot")
    channel = FakeTextChannel(channel_id=789)

    # First N-1 messages should pass
    for i in range(2):
        adapter.handle_message.reset_mock()
        msg = _make_message(
            channel=channel,
            content=f"reply {i}",
            author=bot,
        )
        await adapter._handle_message(msg)
        adapter.handle_message.assert_awaited_once()

    # Third message should trip the breaker and be blocked
    adapter.handle_message.reset_mock()
    msg = _make_message(
        channel=channel,
        content="reply 3 — trip!",
        author=bot,
    )
    await adapter._handle_message(msg)
    adapter.handle_message.assert_not_awaited()

    # Verify breaker state
    channel_key = str(channel.id)
    assert channel_key in adapter._circuit_breaker_until
    assert adapter._circuit_breaker_until[channel_key] > time.monotonic()

    # Subsequent messages also blocked
    adapter.handle_message.reset_mock()
    msg = _make_message(
        channel=channel,
        content="should still be blocked",
        author=bot,
    )
    await adapter._handle_message(msg)
    adapter.handle_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_circuit_breaker_timestamps_rotate(adapter, monkeypatch):
    """Old timestamps outside the window are expired; only recent
    ones count toward the threshold."""
    monkeypatch.setenv("DISCORD_FREE_RESPONSE_CHANNELS", "789")
    monkeypatch.setenv("DISCORD_ALLOW_BOTS", "all")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "true")
    # Short window: timestamps older than 1s don't count
    monkeypatch.setenv("DISCORD_CIRCUIT_BREAKER_WINDOW_S", "0.1")
    monkeypatch.setenv("DISCORD_CIRCUIT_BREAKER_THRESHOLD", "3")

    bot = _make_user(888, bot=True, display_name="OtherBot")
    channel = FakeTextChannel(channel_id=789)

    # Add two old timestamps (now - 5s) directly to bypass window
    adapter._bot_reply_timestamps["789"] = [
        time.monotonic() - 5.0,
        time.monotonic() - 5.0,
    ]

    # This message should NOT trip because old timestamps are expired
    adapter.handle_message.reset_mock()
    msg = _make_message(
        channel=channel,
        content="only 1 recent",
        author=bot,
    )
    await adapter._handle_message(msg)
    adapter.handle_message.assert_awaited_once()
    # Only the new timestamp remains
    timestamps = adapter._bot_reply_timestamps.get("789", [])
    assert len(timestamps) == 1


# ── Layer 3: In-band operator HALT signal ───────────────────────────────────


@pytest.mark.asyncio
async def test_operator_halt_suspends_all_channels(adapter, monkeypatch):
    """When a known operator posts STOP/HALT/KILL/FREEZE, all auto-reply
    is suspended globally (#32791 L3)."""
    monkeypatch.setenv("DISCORD_OPERATOR_IDS", "42")
    monkeypatch.setenv("DISCORD_HALT_COOLDOWN_S", "999999")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "false")

    operator = _make_user(42, bot=False, display_name="Operator")
    channel = FakeTextChannel(channel_id=789)

    # Operator posts HALT
    halt_msg = _make_message(
        channel=channel,
        content="HALT — you are in a loop",
        author=operator,
    )
    await adapter._handle_message(halt_msg)
    adapter.handle_message.assert_not_awaited()

    # Any subsequent message in any channel is blocked
    adapter.handle_message.reset_mock()
    other_channel = FakeTextChannel(channel_id=999)
    other_user = _make_user(55, display_name="Regular User")
    normal_msg = _make_message(
        channel=other_channel,
        content="hello?",
        author=other_user,
    )
    await adapter._handle_message(normal_msg)
    adapter.handle_message.assert_not_awaited()

    # Verify global halt state
    assert adapter._global_halt_until is not None
    assert adapter._global_halt_until > time.monotonic()


@pytest.mark.asyncio
async def test_operator_halt_requires_operator_id(adapter, monkeypatch):
    """HALT from a non-operator user is NOT honored (#32791 L3)."""
    monkeypatch.setenv("DISCORD_OPERATOR_IDS", "42")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "false")

    non_operator = _make_user(99, bot=False, display_name="Random User")
    channel = FakeTextChannel(channel_id=789)

    # Non-operator posts "STOP"
    msg = _make_message(
        channel=channel,
        content="STOP",
        author=non_operator,
    )
    await adapter._handle_message(msg)
    # Should be accepted normally — not an operator
    adapter.handle_message.assert_awaited_once()

    # Global halt should NOT be set
    assert adapter._global_halt_until is None


@pytest.mark.asyncio
async def test_operator_halt_not_triggered_by_non_halt_message(adapter, monkeypatch):
    """Operator messages that don't match the HALT pattern are processed normally."""
    monkeypatch.setenv("DISCORD_OPERATOR_IDS", "42")
    monkeypatch.setenv("DISCORD_REQUIRE_MENTION", "false")

    operator = _make_user(42, bot=False, display_name="Operator")
    channel = FakeTextChannel(channel_id=789)

    msg = _make_message(
        channel=channel,
        content="hello everyone",
        author=operator,
    )
    await adapter._handle_message(msg)
    adapter.handle_message.assert_awaited_once()

    # Global halt should NOT be set
    assert adapter._global_halt_until is None
