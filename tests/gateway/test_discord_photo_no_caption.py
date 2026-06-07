"""Tests for Discord photo handling without caption text.

Ensures that when a user sends a photo without a caption, the placeholder
text "(The user sent a message with no text content)" is NOT set — the
empty text is preserved so the gateway vision-enrichment pipeline can
prepend the image description cleanly.
"""

import os
import sys
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import PlatformConfig
from gateway.platforms.base import MessageType


# ---------------------------------------------------------------------------
# Discord mock setup
# ---------------------------------------------------------------------------
def _ensure_discord_mock():
    """Install a mock discord module when discord.py isn't available."""
    if "discord" in sys.modules and hasattr(sys.modules["discord"], "__file__"):
        return

    discord_mod = MagicMock()
    discord_mod.Intents.default.return_value = MagicMock()
    discord_mod.Client = MagicMock
    discord_mod.File = MagicMock
    discord_mod.DMChannel = type("DMChannel", (), {})
    discord_mod.Thread = type("Thread", (), {})
    discord_mod.ForumChannel = type("ForumChannel", (), {})

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


class FakeDMChannel:
    def __init__(self, channel_id: int = 1):
        self.id = channel_id
        self.name = "dm"


class FakeThread:
    def __init__(self, channel_id: int = 10):
        self.id = channel_id
        self.name = "thread"
        self.parent = None
        self.parent_id = None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _redirect_cache(tmp_path, monkeypatch):
    """Point image cache to tmp_path so tests never write to ~/.hermes."""
    monkeypatch.setattr(
        "gateway.platforms.base.IMAGE_CACHE_DIR", tmp_path / "img_cache"
    )
    monkeypatch.setattr(
        "gateway.platforms.base.DOCUMENT_CACHE_DIR", tmp_path / "doc_cache"
    )


@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setattr(discord_platform.discord, "DMChannel", FakeDMChannel, raising=False)

    config = PlatformConfig(enabled=True, token="fake-token")
    a = DiscordAdapter(config)
    a._client = SimpleNamespace(user=SimpleNamespace(id=999))
    a.handle_message = AsyncMock()
    return a


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_attachment(
    *,
    filename: str = "photo.png",
    content_type: str = "image/png",
    url: str = "https://cdn.discordapp.com/attachments/fake/photo.png",
) -> SimpleNamespace:
    return SimpleNamespace(
        filename=filename,
        content_type=content_type,
        url=url,
        # No read() — triggers URL fallback in _cache_discord_image,
        # which we mock below.
    )


def make_message(attachments: list, content: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        id=123,
        content=content,
        attachments=attachments,
        mentions=[],
        reference=None,
        created_at=datetime.now(timezone.utc),
        channel=FakeDMChannel(),
        author=SimpleNamespace(id=42, display_name="Tester", name="Tester"),
        guild=SimpleNamespace(id=1, name="TestServer"),
        message_snapshots=None,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestPhotoNoCaption:

    @pytest.mark.asyncio
    async def test_photo_without_caption_skips_placeholder(self, adapter):
        """A photo with no caption should NOT get the placeholder text."""
        fake_cached_path = "/tmp/fake_cached_photo.png"

        with patch(
            "plugins.platforms.discord.adapter.cache_image_from_url",
            return_value=fake_cached_path,
        ):
            msg = make_message(
                [make_attachment(filename="photo.png", content_type="image/png")],
                content="",
            )
            await adapter._handle_message(msg)

        event = adapter.handle_message.call_args[0][0]

        # Should be typed as PHOTO
        assert event.message_type == MessageType.PHOTO

        # Should have the cached image path
        assert len(event.media_urls) == 1
        assert event.media_urls[0] == fake_cached_path

        # The placeholder should NOT be present
        assert "(The user sent a message with no text content)" not in (event.text or "")

        # Text should be empty (or very short) — no placeholder injected
        assert not event.text or not event.text.strip()

    @pytest.mark.asyncio
    async def test_photo_with_caption_preserves_text(self, adapter):
        """A photo with a caption should keep the caption as event.text."""
        fake_cached_path = "/tmp/fake_cached_photo_2.png"
        caption = "look at this cat!"

        with patch(
            "plugins.platforms.discord.adapter.cache_image_from_url",
            return_value=fake_cached_path,
        ):
            msg = make_message(
                [make_attachment(filename="photo.png", content_type="image/png")],
                content="look at this cat!",
            )
            await adapter._handle_message(msg)

        event = adapter.handle_message.call_args[0][0]

        assert event.message_type == MessageType.PHOTO
        assert len(event.media_urls) == 1
        assert "look at this cat!" in (event.text or "")

    @pytest.mark.asyncio
    async def test_bare_mention_without_media_sets_placeholder(self, adapter):
        """A bare @mention with no text and no media should still get the placeholder."""
        adapter._text_batch_delay_seconds = 0
        msg = make_message([], content="")
        await adapter._handle_message(msg)

        event = adapter.handle_message.call_args[0][0]

        assert "(The user sent a message with no text content)" in (event.text or "")
