"""Regression tests for Windows creationflags in LocalEnvironment._run_bash.

PR #29059 removed a duplicate explicit ``creationflags=`` kwarg that was
passed alongside ``**_popen_kwargs`` (issue #29651 / #28920).  These tests
ensure ``subprocess.Popen`` receives ``creationflags`` exactly once.

See: https://github.com/NousResearch/hermes-agent/issues/29651
See: https://github.com/NousResearch/hermes-agent/pull/29059
"""

import inspect
import re
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hermes_cli._subprocess_compat import windows_hide_flags
from tools.environments.local import LocalEnvironment


def _make_fake_popen(captured: dict):
    """Return a fake Popen that records kwargs (including creationflags)."""

    def fake_popen(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["kwargs"] = dict(kwargs)
        proc = MagicMock()
        proc.poll.return_value = 0
        proc.returncode = 0
        proc.stdout = MagicMock(
            __iter__=lambda s: iter([]),
            __next__=lambda s: (_ for _ in ()).throw(StopIteration),
        )
        proc.stdin = MagicMock()
        proc.pid = 12345
        return proc

    return fake_popen


class TestLocalPopenCreationflags:
    """LocalEnvironment must not pass creationflags twice to subprocess.Popen."""

    def test_run_bash_passes_creationflags_once_on_windows(self, monkeypatch, tmp_path):
        """Simulated Windows: Popen kwargs contain a single creationflags entry."""
        monkeypatch.setattr("tools.environments.local._IS_WINDOWS", True)
        captured = {}

        env = LocalEnvironment(cwd=str(tmp_path), timeout=10)
        with patch("tools.environments.local._find_bash", return_value="/bin/bash"), \
             patch("subprocess.Popen", side_effect=_make_fake_popen(captured)):
            env._run_bash("echo hello")

        kwargs = captured["kwargs"]
        assert "creationflags" in kwargs
        assert kwargs["creationflags"] == windows_hide_flags()
        # Duplicate explicit + spread would raise at call time; ensure one source.
        assert list(kwargs).count("creationflags") == 1

    @pytest.mark.skipif(sys.platform == "win32", reason="POSIX os.setsid branch")
    def test_run_bash_omits_creationflags_on_posix(self, monkeypatch, tmp_path):
        """Non-Windows: no creationflags kwarg (POSIX uses preexec_fn instead)."""
        monkeypatch.setattr("tools.environments.local._IS_WINDOWS", False)
        captured = {}

        env = LocalEnvironment(cwd=str(tmp_path), timeout=10)
        with patch("tools.environments.local._find_bash", return_value="/bin/bash"), \
             patch("subprocess.Popen", side_effect=_make_fake_popen(captured)):
            env._run_bash("echo hello")

        assert "creationflags" not in captured["kwargs"]

    def test_duplicate_explicit_and_spread_creationflags_raises(self):
        """Document the failure mode PR #29059 fixed (explicit + **_popen_kwargs)."""
        import subprocess

        extra = {"creationflags": windows_hide_flags()}
        with pytest.raises(
            TypeError,
            match="multiple values for keyword argument 'creationflags'",
        ):
            subprocess.Popen(
                ["echo"],
                creationflags=0x08000000,
                **extra,
            )


class TestLocalRunBashSourceGuard:
    """Static guard: _run_bash must not combine explicit creationflags= with **_popen_kwargs."""

    def test_run_bash_no_duplicate_creationflags_in_source(self):
        root = Path(__file__).resolve().parents[2]
        source = inspect.getsource(
            __import__("tools.environments.local", fromlist=["LocalEnvironment"]).LocalEnvironment._run_bash
        )
        # Explicit kwarg before spread caused #29651.
        assert re.search(
            r"creationflags\s*=",
            source,
        ) is None, (
            "_run_bash must not pass creationflags= explicitly; use **_popen_kwargs only"
        )
        assert "**_popen_kwargs" in source
