"""Regression for #31420: Windows subprocess env must carry PYTHONUTF8=1.

On Windows, when Hermes spawns a Python subprocess WITHOUT explicitly
setting ``PYTHONUTF8=1`` in the child's env, the child uses the system
**legacy code page** for stdio — ``CP936`` on zh-CN, ``CP1252`` on en-US,
``CP932`` on ja-JP, etc. — and any non-ASCII output (Chinese / Japanese /
Korean / emoji / math symbols / …) raises ``UnicodeEncodeError`` or
becomes mojibake.

The fix adds a centralized helper
``hermes_cli._subprocess_compat.apply_windows_utf8_env`` and applies it
to the env-builder chokepoints used by the terminal tool, process
registry, code-execution sandbox, and a couple of direct subprocess
sites (Copilot ACP client, Codex app-server transport).  These tests
cover both the helper's contract and the call-site wiring.
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from hermes_cli._subprocess_compat import apply_windows_utf8_env


# ---------------------------------------------------------------------------
# Helper unit tests — contract guarantees
# ---------------------------------------------------------------------------


class TestApplyWindowsUtf8Env:
    """``apply_windows_utf8_env`` is the single source of truth for the
    Windows-only ``PYTHONUTF8`` / ``PYTHONIOENCODING`` injection.
    """

    def test_sets_both_keys_on_windows(self):
        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", True):
            env: dict[str, str] = {}
            result = apply_windows_utf8_env(env)
            assert result is env, "must mutate-and-return for fluent chaining"
            assert env["PYTHONUTF8"] == "1"
            assert env["PYTHONIOENCODING"] == "utf-8"

    def test_no_op_on_posix(self):
        """On Linux/macOS the helper must not add Windows-specific knobs.

        UTF-8 is the locale default on POSIX so the env vars are
        unnecessary, and adding them would pollute env snapshots in
        tests / dotfiles audits / docker layer caches.
        """
        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", False):
            env: dict[str, str] = {}
            result = apply_windows_utf8_env(env)
            assert result is env
            assert "PYTHONUTF8" not in env
            assert "PYTHONIOENCODING" not in env

    def test_setdefault_honors_explicit_pythonutf8_zero(self):
        """A user that explicitly opted out via ``PYTHONUTF8=0`` (rare but
        legitimate — debugging Windows codepage behavior) must keep that
        intent.  ``setdefault`` is what guarantees this.
        """
        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", True):
            env = {"PYTHONUTF8": "0"}
            apply_windows_utf8_env(env)
            assert env["PYTHONUTF8"] == "0", (
                "must not clobber an explicit user opt-out"
            )
            assert env["PYTHONIOENCODING"] == "utf-8"

    def test_setdefault_honors_explicit_pythonioencoding(self):
        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", True):
            env = {"PYTHONIOENCODING": "latin-1"}
            apply_windows_utf8_env(env)
            assert env["PYTHONIOENCODING"] == "latin-1"
            # PYTHONUTF8 was not set explicitly, so it gets the default.
            assert env["PYTHONUTF8"] == "1"

    def test_idempotent(self):
        """Calling twice must yield the same result as calling once."""
        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", True):
            env: dict[str, str] = {}
            apply_windows_utf8_env(env)
            snapshot = dict(env)
            apply_windows_utf8_env(env)
            assert env == snapshot

    def test_preserves_other_keys(self):
        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", True):
            env = {"PATH": "C:\\Windows", "FOO": "bar"}
            apply_windows_utf8_env(env)
            assert env["PATH"] == "C:\\Windows"
            assert env["FOO"] == "bar"
            assert env["PYTHONUTF8"] == "1"


# ---------------------------------------------------------------------------
# Call-site wiring — the helper has to actually be invoked from the
# env-builders, otherwise the centralization is decorative.
# ---------------------------------------------------------------------------


class TestEnvBuilderWiring:
    """Pin the call-sites so a future refactor can't silently drop the
    UTF-8 injection at any of the chokepoints.
    """

    def test_sanitize_subprocess_env_injects_utf8_on_windows(self):
        """``_sanitize_subprocess_env`` is the env helper used by both the
        process registry (``hermes process``) and the code-execution
        sandbox.  Must inject ``PYTHONUTF8=1`` on Windows.
        """
        from tools.environments import local as local_env_mod

        # Simulate a Windows host with a clean inherited env (the bug
        # repro: nothing has set PYTHONUTF8 yet).
        with patch.object(local_env_mod, "_IS_WINDOWS", True), patch(
            "hermes_cli._subprocess_compat.IS_WINDOWS", True
        ), patch.object(
            local_env_mod, "get_subprocess_home", return_value=None, create=True
        ):
            sanitized = local_env_mod._sanitize_subprocess_env(
                {"PATH": "C:\\Windows"}, None
            )
        assert sanitized.get("PYTHONUTF8") == "1", (
            "_sanitize_subprocess_env must call apply_windows_utf8_env so "
            "the terminal tool / process registry don't crash with "
            "UnicodeEncodeError on CP936/CP1252 locales (#31420)."
        )
        assert sanitized.get("PYTHONIOENCODING") == "utf-8"

    def test_sanitize_subprocess_env_no_op_on_posix(self):
        """The injection must be Windows-only; POSIX shouldn't get the
        env vars planted speculatively (would change subprocess-env
        snapshots that some tests assert on).
        """
        from tools.environments import local as local_env_mod

        with patch.object(local_env_mod, "_IS_WINDOWS", False), patch(
            "hermes_cli._subprocess_compat.IS_WINDOWS", False
        ), patch.object(
            local_env_mod, "get_subprocess_home", return_value=None, create=True
        ):
            sanitized = local_env_mod._sanitize_subprocess_env(
                {"PATH": "/usr/bin"}, None
            )
        assert "PYTHONUTF8" not in sanitized
        assert "PYTHONIOENCODING" not in sanitized

    def test_make_run_env_injects_utf8_on_windows(self):
        """``_make_run_env`` is the env helper used by the synchronous
        terminal tool (the foreground ``terminal`` action).  Same fix
        required.
        """
        from tools.environments import local as local_env_mod

        with patch.object(local_env_mod, "_IS_WINDOWS", True), patch(
            "hermes_cli._subprocess_compat.IS_WINDOWS", True
        ), patch.object(
            local_env_mod, "get_subprocess_home", return_value=None, create=True
        ), patch.dict(os.environ, {"PATH": "C:\\Windows"}, clear=True):
            run_env = local_env_mod._make_run_env({})
        assert run_env.get("PYTHONUTF8") == "1"
        assert run_env.get("PYTHONIOENCODING") == "utf-8"

    def test_make_run_env_no_op_on_posix(self):
        from tools.environments import local as local_env_mod

        with patch.object(local_env_mod, "_IS_WINDOWS", False), patch(
            "hermes_cli._subprocess_compat.IS_WINDOWS", False
        ), patch.object(
            local_env_mod, "get_subprocess_home", return_value=None, create=True
        ), patch.dict(os.environ, {"PATH": "/usr/bin"}, clear=True):
            run_env = local_env_mod._make_run_env({})
        assert "PYTHONUTF8" not in run_env
        assert "PYTHONIOENCODING" not in run_env

    def test_make_run_env_respects_explicit_user_opt_out(self):
        """If the inherited env already says ``PYTHONUTF8=0``,
        ``_make_run_env`` must keep that — the user explicitly opted
        out.
        """
        from tools.environments import local as local_env_mod

        with patch.object(local_env_mod, "_IS_WINDOWS", True), patch(
            "hermes_cli._subprocess_compat.IS_WINDOWS", True
        ), patch.object(
            local_env_mod, "get_subprocess_home", return_value=None, create=True
        ), patch.dict(
            os.environ,
            {"PATH": "C:\\Windows", "PYTHONUTF8": "0"},
            clear=True,
        ):
            run_env = local_env_mod._make_run_env({})
        assert run_env.get("PYTHONUTF8") == "0", (
            "explicit user opt-out via PYTHONUTF8=0 must be preserved"
        )

    def test_copilot_acp_build_subprocess_env_injects_utf8_on_windows(self):
        """The Copilot ACP client builds its own env via
        ``_build_subprocess_env``; pin the wiring even though the spawned
        binary is currently Node — defense in depth keeps the contract
        consistent across helpers and protects future Python-based
        replacements.
        """
        from agent import copilot_acp_client as cac

        with patch("hermes_cli._subprocess_compat.IS_WINDOWS", True), patch.object(
            cac, "_resolve_home_dir", return_value="C:\\Users\\u\\.hermes"
        ), patch.dict(os.environ, {"PATH": "C:\\Windows"}, clear=True):
            env = cac._build_subprocess_env()
        assert env.get("PYTHONUTF8") == "1"
        assert env.get("PYTHONIOENCODING") == "utf-8"

    def test_codex_app_server_spawn_env_invokes_helper(self):
        """``CodexAppServer.__init__`` must call ``apply_windows_utf8_env``
        on its spawn env before launching the codex subprocess.  Codex is
        currently Rust, but it can spawn Python child tools (kanban
        writebacks etc.); planting PYTHONUTF8 in its env keeps those
        grandchildren safe on CP936/CP1252 locales (#31420).

        Source-level check rather than a behavioural one: the constructor
        starts subprocesses and reader threads, which makes mocking
        brittle, but the wiring is a single line we can grep for.
        """
        import inspect

        from agent.transports.codex_app_server import CodexAppServerClient

        src = inspect.getsource(CodexAppServerClient.__init__)
        assert "apply_windows_utf8_env" in src, (
            "CodexAppServerClient.__init__ must call "
            "apply_windows_utf8_env on spawn_env before subprocess.Popen "
            "so non-ASCII output from any Python grandchildren doesn't "
            "crash on CP936/CP1252 Windows locales. See #31420."
        )
        # The call must come BEFORE the Popen invocation, otherwise the
        # env dict reaches the child unmodified.
        helper_idx = src.find("apply_windows_utf8_env")
        popen_idx = src.find("subprocess.Popen")
        assert helper_idx != -1 and popen_idx != -1
        assert helper_idx < popen_idx, (
            "apply_windows_utf8_env must be invoked BEFORE subprocess.Popen, "
            "otherwise the codex child gets the unmodified env."
        )
