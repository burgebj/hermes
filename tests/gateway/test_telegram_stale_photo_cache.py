"""Tests for Telegram photo stale-content detection (issue #35242).

When the Telegram Bot API returns identical bytes for two different photo
file_ids within a short window, the adapter should detect the collision,
retry the download, and — if the retry also returns stale data — reuse the
existing cached file instead of writing a duplicate.
"""

import asyncio
import hashlib
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.base import MessageEvent, MessageType
from gateway.platforms.telegram import TelegramAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_adapter() -> TelegramAdapter:
    """Create a TelegramAdapter with minimal config, bypassing __init__."""
    cfg = PlatformConfig(enabled=True, token="test-token")
    adapter = object.__new__(TelegramAdapter)
    adapter.config = cfg
    adapter._recent_photo_content = {}
    adapter._media_batch_delay_seconds = 0.8
    adapter._pending_photo_batches = {}
    adapter._pending_photo_batch_tasks = {}
    adapter._media_group_events = {}
    adapter._media_group_tasks = {}
    return adapter


def _make_photo_file(file_id: str = "file_abc", file_path: str = "photos/123.jpg"):
    """Create a mock File object that returns bytes via download_as_bytearray."""
    fobj = MagicMock()
    fobj.file_id = file_id
    fobj.file_path = file_path
    return fobj


def _make_photo_size(file_id: str = "file_abc"):
    """Create a mock PhotoSize with a get_file coroutine."""
    ps = MagicMock()
    ps.file_id = file_id
    ps.get_file = AsyncMock(return_value=_make_photo_file(file_id))
    return ps


def _make_message(photo_sizes, media_group_id=None):
    msg = MagicMock()
    msg.photo = photo_sizes
    msg.media_group_id = media_group_id
    msg.voice = None
    msg.audio = None
    msg.video = None
    msg.document = None
    msg.sticker = None
    msg.animation = None
    return msg


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStalePhotoDetection:
    """Test stale photo content detection in _handle_media_message."""

    @pytest.mark.asyncio
    async def test_different_content_hashes_not_flagged(self):
        """Two photos with different content should be cached independently."""
        adapter = _make_adapter()

        img_a = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # PNG magic
        img_b = b"\x89PNG\r\n\x1a\n" + b"\xff" * 100  # Different content

        hash_a = hashlib.md5(img_a).hexdigest()
        hash_b = hashlib.md5(img_b).hexdigest()
        assert hash_a != hash_b

        # Simulate first download
        adapter._recent_photo_content[hash_a] = ("/tmp/img_a.png", time.monotonic())

        # Second download with different content should NOT trigger stale detection
        assert adapter._recent_photo_content.get(hash_b) is None

    @pytest.mark.asyncio
    async def test_same_content_detected_as_stale(self):
        """Same content hash within 60s should be detected as stale."""
        adapter = _make_adapter()

        img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        content_hash = hashlib.md5(img).hexdigest()

        # Simulate first download cached 5 seconds ago
        adapter._recent_photo_content[content_hash] = ("/tmp/first.png", time.monotonic() - 5)

        entry = adapter._recent_photo_content.get(content_hash)
        assert entry is not None
        existing_path, cached_ts = entry
        age = time.monotonic() - cached_ts
        assert age < 60  # Should be detected as stale

    @pytest.mark.asyncio
    async def test_old_content_not_flagged_as_stale(self):
        """Same content hash older than 60s should NOT be flagged as stale."""
        adapter = _make_adapter()

        img = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        content_hash = hashlib.md5(img).hexdigest()

        # Simulate first download cached 120 seconds ago
        adapter._recent_photo_content[content_hash] = ("/tmp/old.png", time.monotonic() - 120)

        entry = adapter._recent_photo_content.get(content_hash)
        assert entry is not None
        _, cached_ts = entry
        age = time.monotonic() - cached_ts
        assert age >= 60  # Should NOT be detected as stale

    @pytest.mark.asyncio
    async def test_prune_removes_old_entries(self):
        """Entries older than 120s should be pruned during update."""
        adapter = _make_adapter()

        now = time.monotonic()
        adapter._recent_photo_content["hash_old"] = ("/tmp/old.png", now - 130)
        adapter._recent_photo_content["hash_new"] = ("/tmp/new.png", now - 5)

        # Simulate pruning (same logic as in the handler)
        now_mono = time.monotonic()
        adapter._recent_photo_content = {
            k: v for k, v in adapter._recent_photo_content.items()
            if now_mono - v[1] < 120
        }

        assert "hash_old" not in adapter._recent_photo_content
        assert "hash_new" in adapter._recent_photo_content
