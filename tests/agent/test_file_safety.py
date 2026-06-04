"""Tests for agent/file_safety.py read guards — env file blocking.

Run with:  python -m pytest tests/agent/test_file_safety.py -v
"""

import os
from unittest.mock import patch

import pytest

from agent.file_safety import (
    _BLOCKED_PROJECT_ENV_BASENAMES,
    get_read_block_error,
    get_safe_write_root,
    is_write_denied,
)


# ---------------------------------------------------------------------------
# Project-local .env file blocking (issue #20734)
# ---------------------------------------------------------------------------


class TestEnvFileReadBlocking:
    """Secret-bearing .env files must be blocked by get_read_block_error."""

    @pytest.mark.parametrize("basename", [
        ".env",
        ".env.local",
        ".env.development",
        ".env.production",
        ".env.test",
        ".env.staging",
        ".envrc",
    ])
    def test_blocked_env_basenames(self, basename):
        """All secret-bearing .env basenames are blocked regardless of directory."""
        path = f"/tmp/project/{basename}"
        error = get_read_block_error(path)
        assert error is not None, f"{basename} should be blocked"
        assert "Access denied" in error
        assert "secret-bearing" in error.lower() or "environment file" in error.lower()

    def test_blocked_env_in_subdirectory(self):
        """Nested .env files are also blocked."""
        error = get_read_block_error("/home/user/app/services/api/.env.production")
        assert error is not None

    def test_blocked_env_absolute_path(self):
        """Absolute paths to .env files are blocked."""
        error = get_read_block_error("/opt/myapp/.env")
        assert error is not None

    def test_allowed_env_example(self):
        """"The .env.example file is explicitly allowed — it's documentation, not a secret."""
        error = get_read_block_error("/tmp/project/.env.example")
        assert error is None

    def test_allowed_env_sample(self):
        """Other .env variants like .env.sample are allowed."""
        error = get_read_block_error("/tmp/project/.env.sample")
        assert error is None

    def test_allowed_non_env_files(self):
        """Regular files are not affected by the env guard."""
        for path in ["/tmp/project/config.yaml", "/tmp/project/main.py",
                     "/tmp/project/README.md", "/tmp/project/.gitignore"]:
            error = get_read_block_error(path)
            assert error is None, f"{path} should be allowed"

    def test_allowed_hermes_env(self):
        """Hermes' own .env inside HERMES_HOME is NOT blocked by this rule
        (it's handled by other mechanisms). Only project-local .env is blocked."""
        # Note: hermes internal .env is in ~/.hermes/.env which is NOT a project-local
        # path, but the basename check applies to ANY .env. This is intentional —
        # even ~/.hermes/.env should not be readable via read_file.
        error = get_read_block_error(os.path.expanduser("~/.hermes/.env"))
        assert error is not None

    def test_blocked_set_is_lowercase(self):
        """All entries in the blocked set are lowercase for case-insensitive matching."""
        for name in _BLOCKED_PROJECT_ENV_BASENAMES:
            assert name == name.lower(), f"{name} should be lowercase"


# ---------------------------------------------------------------------------
# Existing cache-file blocking (regression — must still work)
# ---------------------------------------------------------------------------


class TestCacheFileReadBlocking:
    """Internal Hermes cache files must remain blocked."""

    def test_hub_index_cache_blocked(self, tmp_path):
        """Hub index-cache reads are blocked."""
        hermes_home = tmp_path / ".hermes"
        cache = hermes_home / "skills" / ".hub" / "index-cache" / "data.json"
        cache.parent.mkdir(parents=True)
        cache.write_text("{}")

        with patch("agent.file_safety._hermes_home_path", return_value=hermes_home):
            error = get_read_block_error(str(cache))
            assert error is not None
            assert "internal Hermes cache" in error

    def test_hub_directory_blocked(self, tmp_path):
        """Hub directory reads are blocked."""
        hermes_home = tmp_path / ".hermes"
        hub = hermes_home / "skills" / ".hub" / "metadata.json"
        hub.parent.mkdir(parents=True)
        hub.write_text("{}")

        with patch("agent.file_safety._hermes_home_path", return_value=hermes_home):
            error = get_read_block_error(str(hub))
            assert error is not None


# ---------------------------------------------------------------------------
# Combined: env guard + cache guard don't interfere
# ---------------------------------------------------------------------------


class TestCombinedGuards:
    """Both guards should work independently without interference."""

    def test_env_guard_works_regardless_of_hermes_home(self, tmp_path):
        """The env basename guard does not depend on HERMES_HOME resolution."""
        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()

        with patch("agent.file_safety._hermes_home_path", return_value=hermes_home):
            # Regular project .env should still be blocked
            error = get_read_block_error("/workspace/.env")
            assert error is not None

            # .env.example should still be allowed
            error = get_read_block_error("/workspace/.env.example")
            assert error is None

    def test_cache_guard_still_works_with_env_guard(self, tmp_path):
        """Cache file blocking still works when env guard is active."""
        hermes_home = tmp_path / ".hermes"
        cache = hermes_home / "skills" / ".hub" / "index-cache" / "x"
        cache.parent.mkdir(parents=True)
        cache.write_text("")

        with patch("agent.file_safety._hermes_home_path", return_value=hermes_home):
            error = get_read_block_error(str(cache))
            assert error is not None
            assert "internal Hermes cache" in error


# ---------------------------------------------------------------------------
# HERMES_WRITE_SAFE_ROOT write guard (is_write_denied + get_safe_write_root)
# ---------------------------------------------------------------------------


class TestWriteSafeRoot:
    """is_write_denied() respects HERMES_WRITE_SAFE_ROOT when set."""

    def test_is_write_denied_inside_safe_root(self, tmp_path, monkeypatch):
        """A path inside the safe root is not denied by the safe-root check."""
        safe_root = tmp_path / "session"
        safe_root.mkdir()
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root))
        target = str(safe_root / "output.txt")
        # Must not be blocked by safe-root (may still be blocked by the static
        # denylist for sensitive names, but a generic .txt inside a temp dir is not).
        assert not is_write_denied(target)

    def test_is_write_denied_outside_safe_root(self, tmp_path, monkeypatch):
        """A path outside the safe root is denied."""
        safe_root = tmp_path / "session"
        safe_root.mkdir()
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root))
        # /tmp/other is a sibling, not inside safe_root
        outside = str(tmp_path / "other" / "output.txt")
        assert is_write_denied(outside)

    def test_is_write_denied_safe_root_unset(self, monkeypatch):
        """When HERMES_WRITE_SAFE_ROOT is unset, the safe-root check is skipped."""
        monkeypatch.delenv("HERMES_WRITE_SAFE_ROOT", raising=False)
        # /tmp/anywhere is not on the static denylist, so should be allowed.
        assert not is_write_denied("/tmp/anywhere_test_file.txt")
