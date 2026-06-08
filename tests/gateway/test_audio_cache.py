"""
Tests for audio cache utilities in gateway/platforms/base.py.

Covers: get_audio_cache_dir, cache_audio_from_bytes, cleanup_audio_cache.
"""

import os
import time
from pathlib import Path

import pytest

from gateway.platforms.base import (
    cache_audio_from_bytes,
    cleanup_audio_cache,
    get_audio_cache_dir,
)

# ---------------------------------------------------------------------------
# Fixture: redirect AUDIO_CACHE_DIR to a temp directory for every test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _redirect_cache(tmp_path, monkeypatch):
    """Point the module-level AUDIO_CACHE_DIR to a fresh tmp_path."""
    monkeypatch.setattr(
        "gateway.platforms.base.AUDIO_CACHE_DIR", tmp_path / "audio_cache"
    )


# ---------------------------------------------------------------------------
# TestGetAudioCacheDir
# ---------------------------------------------------------------------------

class TestGetAudioCacheDir:
    def test_creates_directory(self, tmp_path):
        cache_dir = get_audio_cache_dir()
        assert cache_dir.exists()
        assert cache_dir.is_dir()

    def test_returns_existing_directory(self):
        first = get_audio_cache_dir()
        second = get_audio_cache_dir()
        assert first == second
        assert first.exists()


# ---------------------------------------------------------------------------
# TestCacheAudioFromBytes
# ---------------------------------------------------------------------------

class TestCacheAudioFromBytes:
    def test_basic_caching(self):
        data = b"fake ogg audio bytes"
        path = cache_audio_from_bytes(data, ".ogg")
        assert os.path.exists(path)
        assert Path(path).read_bytes() == data

    def test_default_extension_is_ogg(self):
        path = cache_audio_from_bytes(b"audio")
        assert path.endswith(".ogg")

    def test_mp3_extension(self):
        path = cache_audio_from_bytes(b"audio", ".mp3")
        assert path.endswith(".mp3")

    def test_unique_filenames(self):
        p1 = cache_audio_from_bytes(b"a")
        p2 = cache_audio_from_bytes(b"b")
        assert p1 != p2


# ---------------------------------------------------------------------------
# TestCleanupAudioCache
# ---------------------------------------------------------------------------

class TestCleanupAudioCache:
    def test_removes_old_files(self, tmp_path):
        cache_dir = get_audio_cache_dir()
        old_file = cache_dir / "old.ogg"
        old_file.write_bytes(b"old audio")
        old_mtime = time.time() - 48 * 3600
        os.utime(old_file, (old_mtime, old_mtime))

        removed = cleanup_audio_cache(max_age_hours=24)
        assert removed == 1
        assert not old_file.exists()

    def test_keeps_recent_files(self):
        cache_dir = get_audio_cache_dir()
        recent = cache_dir / "recent.ogg"
        recent.write_bytes(b"fresh audio")

        removed = cleanup_audio_cache(max_age_hours=24)
        assert removed == 0
        assert recent.exists()

    def test_returns_removed_count(self):
        cache_dir = get_audio_cache_dir()
        old_time = time.time() - 48 * 3600
        for i in range(3):
            f = cache_dir / f"old_{i}.ogg"
            f.write_bytes(b"x")
            os.utime(f, (old_time, old_time))

        assert cleanup_audio_cache(max_age_hours=24) == 3

    def test_empty_cache_dir(self):
        assert cleanup_audio_cache(max_age_hours=24) == 0

    def test_skips_subdirectories(self):
        cache_dir = get_audio_cache_dir()
        subdir = cache_dir / "subdir"
        subdir.mkdir()
        old_time = time.time() - 48 * 3600
        os.utime(subdir, (old_time, old_time))

        removed = cleanup_audio_cache(max_age_hours=24)
        assert removed == 0
        assert subdir.exists()
