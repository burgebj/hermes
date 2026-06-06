"""Tests for `hermes memory status` CLI command.

Covers:
- Status output clarity when no provider is configured (built-in only)
- Status output clarity when an external provider is configured
- The status message should NOT confuse "built-in memory subsystem"
  with the "built-in storage backend" (issue #18404)
"""

import pytest
from unittest.mock import patch
from io import StringIO


def _run_cmd_status(capfd, mem_config=None):
    """Run cmd_status with a mocked config and return captured stdout."""
    from hermes_cli.memory_setup import cmd_status

    config = {"memory": mem_config or {}}

    with patch("hermes_cli.config.load_config", return_value=config):
        with patch("hermes_cli.memory_setup._get_available_providers", return_value=[]):
            cmd_status(args=None)

    captured = capfd.readouterr()
    return captured.out


class TestMemoryStatusClarity:
    """Status output should not mislead users about built-in store state."""

    def test_no_provider_shows_subsystem_label(self, capfd):
        """When no external provider is set, status should use 'Memory subsystem'
        (or equivalent) rather than ambiguous 'Built-in' that could be confused
        with the built-in storage backend."""
        out = _run_cmd_status(capfd)
        # The old misleading text
        assert "Built-in:  always active" not in out, (
            "Status should not show 'Built-in: always active' which confuses "
            "the memory framework with the built-in storage backend"
        )
        # Should display the corrected label (not the old ambiguous "Built-in")
        # Tighter: checks the exact label+status combination, not just any "active" substring
        # (old output "Built-in:  always active" also contains "active")
        assert "Memory subsystem:  active" in out
        assert "Built-in" not in out

    def test_with_provider_does_not_imply_builtin_store_running(self, capfd):
        """When an external provider is configured, the status should not
        imply the built-in store is running alongside it."""
        out = _run_cmd_status(capfd, mem_config={"provider": "mnemosyne"})
        assert "Built-in:  always active" not in out, (
            "With an external provider configured, 'Built-in: always active' "
            "implies the built-in store is also collecting duplicates"
        )
        assert "mnemosyne" in out
