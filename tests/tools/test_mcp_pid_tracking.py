"""Tests for MCP stdio PID tracking — grandchild process discovery via _discover_descendants().

Verifies the fix for #26042: shell-wrapper MCP servers spawn grandchildren
that escape direct-child PID snapshots, leading to zombie accumulation.
"""
import os
import signal
from unittest.mock import patch, MagicMock, mock_open

import pytest

from tools.mcp_tool import _discover_descendants, _kill_orphaned_mcp_children


# ---------------------------------------------------------------------------
# _discover_descendants() — recursive BFS through /proc with psutil fallback
# ---------------------------------------------------------------------------

class TestDiscoverDescendants:
    """Verify _discover_descendants discovers grandchildren, not just direct children."""

    def _reset_state(self):
        from tools.mcp_tool import _stdio_pids, _orphan_stdio_pids, _stdio_pgids, _lock
        with _lock:
            _stdio_pids.clear()
            _orphan_stdio_pids.clear()
            _stdio_pgids.clear()

    def test_discover_grandchildren_via_proc(self):
        """Simulate /proc/{pid}/task/{pid}/children with a process tree:

        Hermes (PID 1) -> bash (PID 10) -> node (PID 20)

        Old code only saw PID 10 (direct child).
        New _discover_descendants() should find PID 20 (grandchild) by recursing.
        """
        proc_children = {
            1: "10",
            10: "20",
            20: "",
        }

        def mock_open_children(path, *args, **kwargs):
            # Extract PID from path like /proc/1/task/1/children
            parts = path.split("/")
            pid = int(parts[2])
            return mock_open(read_data=proc_children.get(pid, ""))()

        with patch("builtins.open", side_effect=mock_open_children):
            result = _discover_descendants(1)

        # Must include both direct child (10) AND grandchild (20)
        assert 10 in result, "Direct child PID should be discovered"
        assert 20 in result, "Grandchild PID should be discovered via recursive walk"
        assert 1 not in result, "Root PID should not be in the result"

    def test_handles_proc_read_errors_gracefully(self):
        """Individual /proc reads that fail should not prevent other children."""
        def selective_open(path, *args, **kwargs):
            if "/42/" in path:
                return mock_open(read_data="100 101")()
            elif "/100/" in path:
                return mock_open(read_data="200")()
            elif "/101/" in path:
                raise OSError("process gone")
            raise FileNotFoundError(path)

        with patch("builtins.open", side_effect=selective_open):
            result = _discover_descendants(42)

        # Should still find 100, 101, and 200, skipping 101's children gracefully
        assert 100 in result
        assert 101 in result
        assert 200 in result
        assert 42 not in result

    def test_psutil_fallback_uses_recursive(self):
        """Verify the psutil fallback path uses children(recursive=True)."""
        import inspect
        source = inspect.getsource(_discover_descendants)
        assert "children(recursive=True)" in source, (
            "psutil fallback must use recursive=True to discover grandchildren"
        )

    def test_returns_empty_set_when_no_children(self):
        """A PID with no children returns an empty set."""
        def mock_open_children(path, *args, **kwargs):
            return mock_open(read_data="")()

        with patch("builtins.open", side_effect=mock_open_children):
            result = _discover_descendants(1)

        assert result == set()

    def test_returns_empty_set_gracefully(self):
        """When /proc is entirely unavailable, returns an empty set without raising."""
        with patch("builtins.open", side_effect=FileNotFoundError("no /proc")):
            result = _discover_descendants(1)

        assert result == set()


# ---------------------------------------------------------------------------
# _kill_orphaned_mcp_children() — descendant reaping via _discover_descendants
# ---------------------------------------------------------------------------

class TestKillOrphanedMcpChildren:
    """Verify _kill_orphaned_mcp_children also terminates descendants of tracked PIDs."""

    def _reset_state(self):
        from tools.mcp_tool import _stdio_pids, _orphan_stdio_pids, _stdio_pgids, _lock
        with _lock:
            _stdio_pids.clear()
            _orphan_stdio_pids.clear()
            _stdio_pgids.clear()

    def test_kills_descendants_of_orphans(self):
        """When killing an orphan PID, also discover and kill its descendants via _discover_descendants()."""
        import tools.mcp_tool as mcp_mod

        self._reset_state()
        with mcp_mod._lock:
            mcp_mod._orphan_stdio_pids.add(100)

        killed_pids = []

        def mock_kill(pid, sig):
            killed_pids.append(pid)

        # _discover_descendants(100) returns {200, 300} — two descendants
        with patch("tools.mcp_tool._discover_descendants", return_value={200, 300}), \
             patch("tools.mcp_tool.os.kill", side_effect=mock_kill), \
             patch("time.sleep"), \
             patch("gateway.status._pid_exists", return_value=False):
            _kill_orphaned_mcp_children()

        # Should have sent SIGTERM to both 100 and its descendants 200, 300
        assert 100 in killed_pids, "Orphan PID should be killed"
        assert 200 in killed_pids, "Descendant PID 200 should also be killed"
        assert 300 in killed_pids, "Descendant PID 300 should also be killed"

        self._reset_state()

    def test_no_proc_still_kills_tracked_pids(self):
        """Even when _discover_descendants returns empty, tracked orphan PIDs are still killed."""
        import tools.mcp_tool as mcp_mod

        self._reset_state()
        with mcp_mod._lock:
            mcp_mod._orphan_stdio_pids.add(300)

        killed_pids = []

        def mock_kill(pid, sig):
            killed_pids.append(pid)

        with patch("tools.mcp_tool._discover_descendants", return_value=set()), \
             patch("tools.mcp_tool.os.kill", side_effect=mock_kill), \
             patch("time.sleep"), \
             patch("gateway.status._pid_exists", return_value=False):
            _kill_orphaned_mcp_children()

        assert 300 in killed_pids

        self._reset_state()
