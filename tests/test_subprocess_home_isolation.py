"""Tests for subprocess HOME handling.

Subprocesses should inherit the user's real HOME. Hermes profile state stays
isolated via HERMES_HOME, but common CLIs such as git, ssh, gh, npm, and az need
``~`` to resolve to the same directory the user's normal shell sees.

See: https://github.com/NousResearch/hermes-agent/issues/36144
"""

import os
import sys
from types import ModuleType, SimpleNamespace
import threading
from pathlib import Path

import hermes_constants
import pytest


# ---------------------------------------------------------------------------
# get_subprocess_home()
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_container_cache(monkeypatch):
    monkeypatch.setattr(hermes_constants, "_container_detected", False)


class TestGetSubprocessHome:
    """Unit tests for hermes_constants.get_subprocess_home()."""

    def test_returns_none_when_hermes_home_unset(self, monkeypatch):
        monkeypatch.delenv("HERMES_HOME", raising=False)
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() is None

    def test_returns_none_when_home_dir_missing(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        # No home/ subdirectory created
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() is None

    def test_returns_none_when_profile_home_exists_but_home_is_real(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        profile_home = hermes_home / "home"
        profile_home.mkdir()
        real_home = tmp_path / "real-home"
        real_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        monkeypatch.setenv("HOME", str(real_home))
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() is None

    def test_profile_home_env_is_corrected_to_account_home(self, tmp_path, monkeypatch):
        """If the parent HOME already points at profile home, repair it."""
        profile_dir = tmp_path / ".hermes" / "profiles" / "coder"
        profile_dir.mkdir(parents=True)
        profile_home = profile_dir / "home"
        profile_home.mkdir()
        real_home = tmp_path / "real-home"
        real_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(profile_dir))
        monkeypatch.setenv("HOME", str(profile_home))
        monkeypatch.delenv("USERPROFILE", raising=False)
        monkeypatch.delenv("HOMEDRIVE", raising=False)
        monkeypatch.delenv("HOMEPATH", raising=False)
        fake_pwd = ModuleType("pwd")
        fake_pwd.getpwuid = lambda _uid: SimpleNamespace(pw_dir=str(real_home))
        monkeypatch.setitem(sys.modules, "pwd", fake_pwd)
        monkeypatch.setattr(hermes_constants.os, "getuid", lambda: 1000, raising=False)
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() == str(real_home)

    def test_profile_home_env_is_corrected_to_userprofile_when_pwd_unavailable(self, tmp_path, monkeypatch):
        profile_dir = tmp_path / ".hermes" / "profiles" / "coder"
        profile_home = profile_dir / "home"
        profile_home.mkdir(parents=True)
        real_home = tmp_path / "real-home"
        real_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(profile_dir))
        monkeypatch.setenv("HOME", str(profile_home))
        monkeypatch.setenv("USERPROFILE", str(real_home))
        monkeypatch.delenv("HOMEDRIVE", raising=False)
        monkeypatch.delenv("HOMEPATH", raising=False)
        monkeypatch.setitem(sys.modules, "pwd", None)
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() == str(real_home)

    def test_profile_home_env_is_corrected_to_home_drive_path_when_pwd_unavailable(self, tmp_path, monkeypatch):
        profile_dir = tmp_path / ".hermes" / "profiles" / "coder"
        profile_home = profile_dir / "home"
        profile_home.mkdir(parents=True)
        monkeypatch.setenv("HERMES_HOME", str(profile_dir))
        monkeypatch.setenv("HOME", str(profile_home))
        monkeypatch.delenv("USERPROFILE", raising=False)
        monkeypatch.setenv("HOMEDRIVE", "C:")
        monkeypatch.setenv("HOMEPATH", "\\Users\\real-home")
        monkeypatch.setitem(sys.modules, "pwd", None)
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() == "C:\\Users\\real-home"

    def test_explicit_real_home_override_wins(self, tmp_path, monkeypatch):
        profile_dir = tmp_path / ".hermes" / "profiles" / "coder"
        profile_home = profile_dir / "home"
        profile_home.mkdir(parents=True)
        real_home = tmp_path / "real-home"
        real_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(profile_dir))
        monkeypatch.setenv("HOME", str(profile_home))
        monkeypatch.setenv("HERMES_REAL_HOME", str(real_home))
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() == str(real_home)

    def test_container_keeps_persistent_profile_home(self, tmp_path, monkeypatch):
        docker_home = tmp_path / "opt" / "data"
        profile_home = docker_home / "home"
        profile_home.mkdir(parents=True)
        monkeypatch.setenv("HERMES_HOME", str(docker_home))
        monkeypatch.setenv("HOME", str(docker_home))
        monkeypatch.setattr(hermes_constants, "_container_detected", True)
        from hermes_constants import get_subprocess_home
        assert get_subprocess_home() == str(profile_home)

    def test_two_profiles_do_not_override_home(self, tmp_path, monkeypatch):
        base = tmp_path / ".hermes" / "profiles"
        real_home = tmp_path / "real-home"
        real_home.mkdir()
        monkeypatch.setenv("HOME", str(real_home))
        for name in ("alpha", "beta"):
            p = base / name
            p.mkdir(parents=True)
            (p / "home").mkdir()

        from hermes_constants import get_subprocess_home

        monkeypatch.setenv("HERMES_HOME", str(base / "alpha"))
        home_a = get_subprocess_home()

        monkeypatch.setenv("HERMES_HOME", str(base / "beta"))
        home_b = get_subprocess_home()

        assert home_a is None
        assert home_b is None

    def test_context_override_is_thread_local(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        profile = tmp_path / "profile"
        root.mkdir()
        profile.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(root))

        from hermes_constants import (
            get_hermes_home,
            reset_hermes_home_override,
            set_hermes_home_override,
        )

        ready = threading.Event()
        release = threading.Event()
        seen: list[str] = []

        def read_from_other_thread():
            ready.set()
            release.wait(timeout=5)
            seen.append(str(get_hermes_home()))

        thread = threading.Thread(target=read_from_other_thread)
        thread.start()
        assert ready.wait(timeout=5)

        token = set_hermes_home_override(profile)
        try:
            assert get_hermes_home() == profile
            release.set()
            thread.join(timeout=5)
        finally:
            reset_hermes_home_override(token)
            release.set()

        assert seen == [str(root)]
        assert get_hermes_home() == root


# ---------------------------------------------------------------------------
# _make_run_env() injection
# ---------------------------------------------------------------------------

class TestMakeRunEnvHomeInjection:
    """Verify _make_run_env() preserves real HOME in subprocess envs."""

    def test_preserves_home_when_profile_home_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hermes_constants, "_container_detected", False)
        hermes_home = tmp_path / "hermes"
        hermes_home.mkdir()
        (hermes_home / "home").mkdir()
        real_home = tmp_path / "real-home"
        real_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        monkeypatch.setenv("HOME", str(real_home))
        monkeypatch.setenv("PATH", "/usr/bin:/bin")

        from tools.environments.local import _make_run_env
        result = _make_run_env({})

        assert result["HOME"] == str(real_home)

    def test_no_injection_when_home_dir_missing(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / "hermes"
        hermes_home.mkdir()
        # No home/ subdirectory
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))
        monkeypatch.setenv("HOME", "/root")
        monkeypatch.setenv("PATH", "/usr/bin:/bin")

        from tools.environments.local import _make_run_env
        result = _make_run_env({})

        assert result["HOME"] == "/root"

    def test_no_injection_when_hermes_home_unset(self, monkeypatch):
        monkeypatch.delenv("HERMES_HOME", raising=False)
        monkeypatch.setenv("HOME", "/home/user")
        monkeypatch.setenv("PATH", "/usr/bin:/bin")

        from tools.environments.local import _make_run_env
        result = _make_run_env({})

        assert result["HOME"] == "/home/user"

    def test_context_override_bridges_to_subprocess_env(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hermes_constants, "_container_detected", False)
        root = tmp_path / "root"
        profile = tmp_path / "profile"
        root.mkdir()
        profile.mkdir()
        (profile / "home").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(root))
        monkeypatch.setenv("HOME", "/root")
        monkeypatch.setenv("PATH", "/usr/bin:/bin")

        from hermes_constants import reset_hermes_home_override, set_hermes_home_override
        from tools.environments.local import _make_run_env

        token = set_hermes_home_override(profile)
        try:
            result = _make_run_env({})
        finally:
            reset_hermes_home_override(token)

        assert result["HERMES_HOME"] == str(profile)
        assert result["HOME"] == "/root"


# ---------------------------------------------------------------------------
# _sanitize_subprocess_env() injection
# ---------------------------------------------------------------------------

class TestSanitizeSubprocessEnvHomeInjection:
    """Verify _sanitize_subprocess_env() preserves HOME for background procs."""

    def test_preserves_home_when_profile_home_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hermes_constants, "_container_detected", False)
        hermes_home = tmp_path / "hermes"
        hermes_home.mkdir()
        (hermes_home / "home").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        base_env = {"HOME": "/root", "PATH": "/usr/bin", "USER": "root"}
        from tools.environments.local import _sanitize_subprocess_env
        result = _sanitize_subprocess_env(base_env)

        assert result["HOME"] == "/root"

    def test_no_injection_when_home_dir_missing(self, tmp_path, monkeypatch):
        hermes_home = tmp_path / "hermes"
        hermes_home.mkdir()
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        base_env = {"HOME": "/root", "PATH": "/usr/bin"}
        from tools.environments.local import _sanitize_subprocess_env
        result = _sanitize_subprocess_env(base_env)

        assert result["HOME"] == "/root"

    def test_context_override_bridges_to_background_env(self, tmp_path, monkeypatch):
        monkeypatch.setattr(hermes_constants, "_container_detected", False)
        root = tmp_path / "root"
        profile = tmp_path / "profile"
        root.mkdir()
        profile.mkdir()
        (profile / "home").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(root))

        base_env = {"HOME": "/root", "PATH": "/usr/bin"}
        from hermes_constants import reset_hermes_home_override, set_hermes_home_override
        from tools.environments.local import _sanitize_subprocess_env

        token = set_hermes_home_override(profile)
        try:
            result = _sanitize_subprocess_env(base_env)
        finally:
            reset_hermes_home_override(token)

        assert result["HERMES_HOME"] == str(profile)
        assert result["HOME"] == "/root"


# ---------------------------------------------------------------------------
# Profile bootstrap
# ---------------------------------------------------------------------------

class TestProfileBootstrap:
    """Verify new profiles get a home/ subdirectory."""

    def test_profile_dirs_includes_home(self):
        from hermes_cli.profiles import _PROFILE_DIRS
        assert "home" in _PROFILE_DIRS

    def test_create_profile_bootstraps_home_dir(self, tmp_path, monkeypatch):
        """create_profile() should create home/ inside the profile dir."""
        home = tmp_path / ".hermes"
        home.mkdir()
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        monkeypatch.setenv("HERMES_HOME", str(home))

        from hermes_cli.profiles import create_profile
        profile_dir = create_profile("testbot", no_alias=True)
        assert (profile_dir / "home").is_dir()


# ---------------------------------------------------------------------------
# Python process HOME unchanged
# ---------------------------------------------------------------------------

class TestPythonProcessUnchanged:
    """Confirm the Python process's own HOME is never modified."""

    def test_path_home_unchanged_after_subprocess_home_resolved(
        self, tmp_path, monkeypatch
    ):
        hermes_home = tmp_path / "hermes"
        hermes_home.mkdir()
        (hermes_home / "home").mkdir()
        monkeypatch.setenv("HERMES_HOME", str(hermes_home))

        original_home = os.environ.get("HOME")
        original_path_home = str(Path.home())

        from hermes_constants import get_subprocess_home
        sub_home = get_subprocess_home()

        # Subprocess HOME is no longer redirected away from the real HOME.
        assert sub_home is None
        assert os.environ.get("HOME") == original_home
        assert str(Path.home()) == original_path_home
