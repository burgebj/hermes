"""Tests for the headless TUI fallback in cmd_chat and the oneshot kanban_complete safety net.

Test classes:
1. TestHeadlessFallback  — cmd_chat suppresses TUI when query + no TTY (3 tests)
2. TestOneshotKanban     — run_oneshot auto-completes kanban tasks (3 tests)
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# TestHeadlessFallback — cmd_chat suppresses TUI in headless mode
# ---------------------------------------------------------------------------


class TestHeadlessFallback:
    """Tests that cmd_chat's early headless detector sets use_tui=False
    and unsets HERMES_TUI when a query is provided without a TTY."""

    def _make_args(self, **overrides):
        import argparse
        d = dict(
            tui=False, query=None,
            continue_last=None, resume=None, model=None,
            provider=None, toolsets=None, skills=None,
            verbose=None, quiet=False, image=None,
            worktree=False, checkpoints=False,
            pass_session_id=False, max_turns=None,
            ignore_rules=False, ignore_user_config=False,
            compact=False, yolo=False, accept_hooks=False,
        )
        d.update(overrides)
        return argparse.Namespace(**d)

    def _run_cmd_chat(self, args):
        """Run cmd_chat with all the mocking needed to avoid side effects.
        Catches SystemExit since cmd_chat calls sys.exit() when routing
        to oneshot mode."""
        from hermes_cli.main import cmd_chat
        with patch("cli.main") as mock_cli, \
             patch("hermes_cli.main._resolve_session_by_name_or_id") as mock_resolve, \
             patch("hermes_cli.main._launch_tui") as mock_tui:
            mock_resolve.return_value = None
            with patch("hermes_cli.oneshot.run_oneshot", return_value=0) as mock_oneshot:
                try:
                    cmd_chat(args)
                except SystemExit:
                    pass

    def test_headless_suppresses_tui(self, monkeypatch):
        """When stdin is not a TTY and a query is provided, HERMES_TUI
        should be unset from the environment."""
        monkeypatch.setenv("HERMES_TUI", "1")
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        args = self._make_args(query="work kanban task t_test")
        self._run_cmd_chat(args)
        assert os.environ.get("HERMES_TUI") is None

    def test_headless_does_not_suppress_with_tty(self, monkeypatch):
        """When stdin IS a TTY, HERMES_TUI should remain set."""
        monkeypatch.setenv("HERMES_TUI", "1")
        monkeypatch.setattr("sys.stdin.isatty", lambda: True)
        args = self._make_args(query="hello")
        self._run_cmd_chat(args)
        assert os.environ.get("HERMES_TUI") == "1"

    def test_headless_no_query_preserves_tui(self, monkeypatch):
        """When no query is provided, HERMES_TUI should remain set
        even without a TTY."""
        monkeypatch.setenv("HERMES_TUI", "1")
        monkeypatch.setattr("sys.stdin.isatty", lambda: False)
        args = self._make_args(query=None)
        self._run_cmd_chat(args)
        assert os.environ.get("HERMES_TUI") == "1"


# ---------------------------------------------------------------------------
# TestOneshotKanban — run_oneshot auto-completes kanban tasks
# ---------------------------------------------------------------------------


class TestOneshotKanban:
    """Tests the kanban_complete safety net in run_oneshot."""

    def test_oneshot_completes_kanban_task(self, monkeypatch):
        """When HERMES_KANBAN_TASK is set and agent responds,
        kanban_complete should be called."""
        monkeypatch.setenv("HERMES_KANBAN_TASK", "t_test_task")
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "test-board")

        from hermes_cli import oneshot

        with patch.object(oneshot, "_run_agent", return_value="Here are the results"):
            with patch("hermes_cli.kanban_db.complete_task") as mock_complete, \
                 patch("hermes_cli.kanban_db.connect_closing") as mock_connect:
                mock_connect.return_value.__enter__.return_value = MagicMock()
                mock_complete.return_value = True

                exit_code = oneshot.run_oneshot("test prompt", model="test-model", provider="test")

        assert exit_code == 0
        mock_complete.assert_called_once()
        # Verify the task ID and summary
        args, kwargs = mock_complete.call_args
        call_str = str(args) + str(kwargs)
        assert "t_test_task" in call_str, f"Task ID not found: {args=} {kwargs=}"

    def test_oneshot_skips_kanban_without_task(self, monkeypatch):
        """When HERMES_KANBAN_TASK is NOT set, kanban_complete should NOT be called."""
        monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
        monkeypatch.delenv("HERMES_KANBAN_BOARD", raising=False)

        from hermes_cli import oneshot

        with patch.object(oneshot, "_run_agent", return_value="response"):
            with patch("hermes_cli.kanban_db.complete_task") as mock_complete, \
                 patch("hermes_cli.kanban_db.connect_closing") as mock_connect:
                mock_connect.return_value.__enter__.return_value = MagicMock()
                exit_code = oneshot.run_oneshot("test", model="test", provider="test")

        assert exit_code == 0
        mock_complete.assert_not_called()

    def test_oneshot_handles_kanban_error_gracefully(self, monkeypatch):
        """When kanban_complete raises, run_oneshot should catch it and
        still return success (the agent produced output)."""
        monkeypatch.setenv("HERMES_KANBAN_TASK", "t_test_task")
        monkeypatch.setenv("HERMES_KANBAN_BOARD", "test-board")

        from hermes_cli import oneshot

        with patch.object(oneshot, "_run_agent", return_value="response"):
            with patch("hermes_cli.kanban_db.complete_task") as mock_complete, \
                 patch("hermes_cli.kanban_db.connect_closing") as mock_connect:
                mock_complete.side_effect = RuntimeError("DB locked")

                exit_code = oneshot.run_oneshot("test", model="test", provider="test")

        assert exit_code == 0
        mock_complete.assert_called_once()
