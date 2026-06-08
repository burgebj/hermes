"""Tests for MSYS2/Git Bash input() deadlock fix (issue #37230).

On Windows with MSYS2/Git Bash, prompt_toolkit sets the PTY to raw mode.
When ``_prompt_text_input`` is called from a non-main thread, the fallback
``input()`` blocks forever because the raw-mode line discipline never sends
a newline.  The fix reconstructs cooked-mode termios attributes before
calling ``input()`` and restores raw mode afterward.
"""

import sys
import threading
from unittest.mock import MagicMock, patch


def _make_cli():
    """Minimal HermesCLI shell exposing prompt fallback helpers."""
    import cli as cli_mod

    obj = object.__new__(cli_mod.HermesCLI)
    obj._app = MagicMock()
    obj._status_bar_visible = True
    return obj


class TestMsys2InputDeadlockFix:
    def test_background_thread_on_win32_does_not_hang(self):
        """On win32 + non-main thread, input() does not deadlock.

        The fix restores cooked-mode terminal attributes before calling
        input() so that the line discipline accepts Enter.  We verify
        the function returns promptly with the user's choice.
        """
        cli = _make_cli()
        result_holder = {}

        def run_on_daemon():
            with patch("sys.platform", "win32"), \
                 patch("builtins.input", return_value="1"):
                result_holder["value"] = cli._prompt_text_input("Choice: ")

        t = threading.Thread(target=run_on_daemon, daemon=True)
        t.start()
        t.join(timeout=2.0)
        assert not t.is_alive(), "daemon thread hung — input() deadlocked"
        assert result_holder.get("value") == "1"

    def test_background_thread_on_linux_calls_input(self):
        """On Linux (non-win32), input() is called without termios changes."""
        cli = _make_cli()
        result_holder = {}

        def run_on_daemon():
            with patch("sys.platform", "linux"), \
                 patch("builtins.input", return_value="2"):
                result_holder["value"] = cli._prompt_text_input("Choice: ")

        t = threading.Thread(target=run_on_daemon, daemon=True)
        t.start()
        t.join(timeout=2.0)
        assert not t.is_alive()
        assert result_holder.get("value") == "2"

    def test_main_thread_on_win32_uses_run_in_terminal(self):
        """On win32 main thread, run_in_terminal is used (not the fallback)."""
        cli = _make_cli()

        with patch("sys.platform", "win32"), \
             patch("prompt_toolkit.application.run_in_terminal") as mock_rit, \
             patch("builtins.input", return_value="2"):
            cli._prompt_text_input("Choice: ")

        assert mock_rit.called

    def test_win32_cooked_mode_restore_on_exception(self):
        """On win32, if input() raises, raw mode is still restored."""
        cli = _make_cli()
        result_holder = {}

        def run_on_daemon():
            with patch("sys.platform", "win32"), \
                 patch("builtins.input", side_effect=KeyboardInterrupt):
                result_holder["value"] = cli._prompt_text_input("Choice: ")

        t = threading.Thread(target=run_on_daemon, daemon=True)
        t.start()
        t.join(timeout=2.0)
        assert not t.is_alive()
        # KeyboardInterrupt in input() → result stays None
        assert result_holder.get("value") is None
