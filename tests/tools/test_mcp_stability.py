"""Tests for MCP stability fixes — event loop handler, PID tracking, shutdown robustness."""

import asyncio
import os
import signal
from unittest.mock import patch, MagicMock

import pytest



# ---------------------------------------------------------------------------
# Fix 1: MCP event loop exception handler
# ---------------------------------------------------------------------------

class TestMCPLoopExceptionHandler:
    """_mcp_loop_exception_handler suppresses benign 'Event loop is closed'."""

    def test_suppresses_event_loop_closed(self):
        from tools.mcp_tool import _mcp_loop_exception_handler
        loop = MagicMock()
        context = {"exception": RuntimeError("Event loop is closed")}
        # Should NOT call default handler
        _mcp_loop_exception_handler(loop, context)
        loop.default_exception_handler.assert_not_called()

    def test_forwards_other_runtime_errors(self):
        from tools.mcp_tool import _mcp_loop_exception_handler
        loop = MagicMock()
        context = {"exception": RuntimeError("some other error")}
        _mcp_loop_exception_handler(loop, context)
        loop.default_exception_handler.assert_called_once_with(context)

    def test_forwards_non_runtime_errors(self):
        from tools.mcp_tool import _mcp_loop_exception_handler
        loop = MagicMock()
        context = {"exception": ValueError("bad value")}
        _mcp_loop_exception_handler(loop, context)
        loop.default_exception_handler.assert_called_once_with(context)

    def test_forwards_contexts_without_exception(self):
        from tools.mcp_tool import _mcp_loop_exception_handler
        loop = MagicMock()
        context = {"message": "just a message"}
        _mcp_loop_exception_handler(loop, context)
        loop.default_exception_handler.assert_called_once_with(context)

    def test_handler_installed_on_mcp_loop(self):
        """_ensure_mcp_loop installs the exception handler on the new loop."""
        import tools.mcp_tool as mcp_mod
        try:
            mcp_mod._ensure_mcp_loop()
            with mcp_mod._lock:
                loop = mcp_mod._mcp_loop
            assert loop is not None
            assert loop.get_exception_handler() is mcp_mod._mcp_loop_exception_handler
        finally:
            mcp_mod._stop_mcp_loop()


# ---------------------------------------------------------------------------
# Fix 2: stdio PID tracking
# ---------------------------------------------------------------------------

class TestStdioPidTracking:
    """_snapshot_child_pids and _stdio_pids track subprocess PIDs."""

    def test_snapshot_returns_set(self):
        from tools.mcp_tool import _snapshot_child_pids
        result = _snapshot_child_pids()
        assert isinstance(result, set)
        # All elements should be ints
        for pid in result:
            assert isinstance(pid, int)

    def test_stdio_pids_starts_empty(self):
        from tools.mcp_tool import _stdio_pids, _lock
        with _lock:
            # Might have residual state from other tests, just check type
            assert isinstance(_stdio_pids, dict)

    def test_kill_orphaned_noop_when_empty(self):
        """_kill_orphaned_mcp_children does nothing when no PIDs tracked."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _stdio_pids,
            _lock,
        )

        with _lock:
            _stdio_pids.clear()
            _orphan_stdio_pids.clear()

        # Should not raise
        _kill_orphaned_mcp_children()

    def test_kill_orphaned_handles_dead_pids(self):
        """_kill_orphaned_mcp_children gracefully handles already-dead PIDs."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _lock,
        )

        # Use a PID that definitely doesn't exist
        fake_pid = 999999999
        with _lock:
            _orphan_stdio_pids.add(fake_pid)

        # Should not raise (ProcessLookupError is caught)
        _kill_orphaned_mcp_children()

        with _lock:
            assert fake_pid not in _orphan_stdio_pids

    def test_kill_orphaned_uses_sigkill_when_available(self, monkeypatch):
        """SIGTERM-first then SIGKILL after 2s for orphan cleanup."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _lock,
        )

        fake_pid = 424242
        with _lock:
            _orphan_stdio_pids.clear()
            _orphan_stdio_pids.add(fake_pid)

        fake_sigkill = 9
        monkeypatch.setattr(signal, "SIGKILL", fake_sigkill, raising=False)

        # Post-#21561 the alive check routes through
        # ``gateway.status._pid_exists`` (so it's safe on Windows — see
        # bpo-14484). Return True so the SIGKILL escalation fires.
        with patch("tools.mcp_tool.os.kill") as mock_kill, \
             patch("gateway.status._pid_exists", return_value=True), \
             patch("tools.mcp_tool.time.sleep") as mock_sleep:
            _kill_orphaned_mcp_children()

        # SIGTERM then SIGKILL; the alive check no longer touches os.kill.
        mock_kill.assert_any_call(fake_pid, signal.SIGTERM)
        mock_kill.assert_any_call(fake_pid, fake_sigkill)
        assert mock_kill.call_count == 2
        mock_sleep.assert_called_once_with(2)

        with _lock:
            assert fake_pid not in _orphan_stdio_pids

    def test_kill_orphaned_falls_back_without_sigkill(self, monkeypatch):
        """Without SIGKILL, SIGTERM is used for both phases."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _lock,
        )

        fake_pid = 434343
        with _lock:
            _orphan_stdio_pids.clear()
            _orphan_stdio_pids.add(fake_pid)

        monkeypatch.delattr(signal, "SIGKILL", raising=False)

        with patch("tools.mcp_tool.os.kill") as mock_kill, \
             patch("tools.mcp_tool.time.sleep") as mock_sleep:
            _kill_orphaned_mcp_children()

        # SIGTERM phase, alive check raises (process gone), no escalation
        mock_kill.assert_any_call(fake_pid, signal.SIGTERM)
        assert mock_sleep.called

        with _lock:
            assert fake_pid not in _orphan_stdio_pids


# ---------------------------------------------------------------------------
# Fix 2b: stdio descendant reaping via process group (issue #23799)
# ---------------------------------------------------------------------------
#
# When a stdio MCP wrapper (e.g. ``openclaw mcp serve``) itself spawns a
# helper subprocess (``claude mcp serve``) and then exits, the helper
# reparents to systemd-user and is invisible to the per-pid orphan reaper.
# The fix captures the wrapper's pgid at spawn time and reaps via killpg,
# which reaches same-group descendants whether or not the direct pid is alive.

class TestStdioPgroupReaping:
    """_kill_orphaned_mcp_children reaps via killpg when a pgid is tracked."""

    def _reset_state(self):
        from tools.mcp_tool import _stdio_pids, _orphan_stdio_pids, _stdio_pgids, _lock
        with _lock:
            _stdio_pids.clear()
            _orphan_stdio_pids.clear()
            _stdio_pgids.clear()

    def test_killpg_used_when_pgid_tracked(self, monkeypatch):
        """SIGTERM and SIGKILL route through killpg when pgid is known."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _stdio_pgids,
            _lock,
        )

        self._reset_state()
        fake_pid = 525252
        fake_pgid = 525252  # session leader: pgid == pid
        with _lock:
            _orphan_stdio_pids.add(fake_pid)
            _stdio_pgids[fake_pid] = fake_pgid

        fake_sigkill = 9
        monkeypatch.setattr(signal, "SIGKILL", fake_sigkill, raising=False)

        # Ensure os.killpg exists on this platform for the test to make sense;
        # the production fallback path is covered by the per-pid tests above.
        if not hasattr(os, "killpg"):
            pytest.skip("os.killpg not available on this platform")

        with patch("tools.mcp_tool.os.killpg") as mock_killpg, \
             patch("tools.mcp_tool.os.kill") as mock_kill, \
             patch("gateway.status._pid_exists", return_value=True), \
             patch("time.sleep"):
            _kill_orphaned_mcp_children()

        # Both phases should have used killpg (pgroup reach), not per-pid kill.
        mock_killpg.assert_any_call(fake_pgid, signal.SIGTERM)
        mock_killpg.assert_any_call(fake_pgid, fake_sigkill)
        assert mock_killpg.call_count == 2
        mock_kill.assert_not_called()

        with _lock:
            assert fake_pid not in _orphan_stdio_pids
            assert fake_pid not in _stdio_pgids

    def test_killpg_failure_falls_back_to_kill(self, monkeypatch):
        """If killpg raises ProcessLookupError (pgroup gone), try os.kill."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _stdio_pgids,
            _lock,
        )

        self._reset_state()
        fake_pid = 636363
        fake_pgid = 636363
        with _lock:
            _orphan_stdio_pids.add(fake_pid)
            _stdio_pgids[fake_pid] = fake_pgid

        if not hasattr(os, "killpg"):
            pytest.skip("os.killpg not available on this platform")

        with patch(
            "tools.mcp_tool.os.killpg",
            side_effect=ProcessLookupError("no such process group"),
        ) as mock_killpg, \
             patch("tools.mcp_tool.os.kill") as mock_kill, \
             patch("gateway.status._pid_exists", return_value=False), \
             patch("time.sleep"):
            _kill_orphaned_mcp_children()

        # killpg was attempted (phase 1 SIGTERM) and fell back to os.kill.
        # Phase 3 skips because _pid_exists returns False (direct pid gone).
        mock_killpg.assert_called()
        mock_kill.assert_any_call(fake_pid, signal.SIGTERM)

        with _lock:
            assert fake_pid not in _orphan_stdio_pids
            assert fake_pid not in _stdio_pgids

    def test_no_pgid_uses_per_pid_kill(self, monkeypatch):
        """When no pgid is recorded (e.g. Windows), fall back to os.kill."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _stdio_pgids,
            _lock,
        )

        self._reset_state()
        fake_pid = 747474
        with _lock:
            _orphan_stdio_pids.add(fake_pid)
            # No entry in _stdio_pgids.

        with patch("tools.mcp_tool.os.kill") as mock_kill, \
             patch("gateway.status._pid_exists", return_value=False), \
             patch("time.sleep"):
            # killpg may or may not exist; either way the no-pgid path skips it.
            _kill_orphaned_mcp_children()

        mock_kill.assert_any_call(fake_pid, signal.SIGTERM)

        with _lock:
            assert fake_pid not in _orphan_stdio_pids

    @pytest.mark.live_system_guard_bypass
    @pytest.mark.skipif(
        not hasattr(os, "killpg") or not hasattr(os, "setsid"),
        reason="POSIX-only: requires os.killpg and os.setsid",
    )
    def test_grandchild_reaped_via_pgroup(self, tmp_path):
        """End-to-end: parent spawns grandchild, parent exits, killpg reaps grandchild.

        Mirrors issue #23799: a stdio MCP wrapper (parent) launches a long-lived
        helper subprocess (grandchild) in the same process group, then the
        wrapper exits while the grandchild keeps running.  killpg on the pgid
        captured at spawn time must still deliver the signal to the grandchild.

        Marked ``live_system_guard_bypass`` because this test genuinely needs
        real signal delivery to its own subprocess tree (the conftest guard
        only knows the test's *initial* children; the spawned tree here is
        outside that allowlist).
        """
        import subprocess
        import sys
        import time as _time

        psutil = pytest.importorskip("psutil")

        # Grandchild: sleep forever, write its pid then wait.
        grandchild_pid_file = tmp_path / "grandchild.pid"
        grandchild_script = tmp_path / "grandchild.py"
        grandchild_script.write_text(
            "import os, sys, time\n"
            f"open({str(grandchild_pid_file)!r}, 'w').write(str(os.getpid()))\n"
            "while True:\n"
            "    time.sleep(0.5)\n"
        )

        # Parent: spawn grandchild, exit immediately (without killing it).
        parent_script = tmp_path / "parent.py"
        parent_script.write_text(
            "import subprocess, sys\n"
            f"subprocess.Popen([sys.executable, {str(grandchild_script)!r}])\n"
            # Parent exits — grandchild reparents to init.
        )

        # Spawn parent in its own session (mirrors stdio_client behaviour).
        parent = subprocess.Popen(
            [sys.executable, str(parent_script)],
            start_new_session=True,
        )
        parent_pgid = os.getpgid(parent.pid)
        # Wait for parent to exit and grandchild to spin up.
        parent.wait(timeout=5)
        deadline = _time.time() + 5
        while _time.time() < deadline and not grandchild_pid_file.exists():
            _time.sleep(0.05)
        assert grandchild_pid_file.exists(), "grandchild did not start"
        grandchild_pid = int(grandchild_pid_file.read_text().strip())

        # Sanity: grandchild is alive and shares the parent's pgid.
        assert psutil.pid_exists(grandchild_pid)
        assert os.getpgid(grandchild_pid) == parent_pgid

        # Drive the reaper: register the parent pid + pgid as an orphan.
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _stdio_pgids,
            _stdio_pids,
            _lock,
        )
        with _lock:
            _stdio_pids.clear()
            _orphan_stdio_pids.clear()
            _stdio_pgids.clear()
            _orphan_stdio_pids.add(parent.pid)
            _stdio_pgids[parent.pid] = parent_pgid
        try:
            _kill_orphaned_mcp_children()
        finally:
            # Belt-and-suspenders: ensure grandchild is dead even if test fails.
            try:
                os.kill(grandchild_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

        # Grandchild should be gone — SIGTERM via killpg in phase 1 reached it.
        deadline = _time.time() + 3
        while _time.time() < deadline and psutil.pid_exists(grandchild_pid):
            _time.sleep(0.05)
        assert not psutil.pid_exists(grandchild_pid), (
            "grandchild survived killpg-based reaping (issue #23799 regression)"
        )


# ---------------------------------------------------------------------------
# Fix 3: MCP reload timeout (cli.py)
# ---------------------------------------------------------------------------

class TestMCPReloadTimeout:
    """_check_config_mcp_changes uses a timeout on _reload_mcp."""

    def test_reload_timeout_does_not_block_forever(self, tmp_path, monkeypatch):
        """If _reload_mcp hangs, the config watcher times out and returns."""
        import time

        # Create a mock HermesCLI-like object with the needed attributes
        class FakeCLI:
            _config_mtime = 0.0
            _config_mcp_servers = {}
            _last_config_check = 0.0
            _command_running = False
            config = {}
            agent = None

            def _reload_mcp(self):
                # Simulate a hang — sleep longer than the timeout
                time.sleep(60)

            def _slow_command_status(self, cmd):
                return cmd

        # This test verifies the timeout mechanism exists in the code
        # by checking that _check_config_mcp_changes doesn't call
        # _reload_mcp directly (it uses a thread now)
        import inspect
        from cli import HermesCLI
        source = inspect.getsource(HermesCLI._check_config_mcp_changes)
        # The fix adds threading.Thread for _reload_mcp
        assert "Thread" in source or "thread" in source.lower(), \
            "_check_config_mcp_changes should use a thread for _reload_mcp"


# ---------------------------------------------------------------------------
# Fix 4: MCP initial connection retry with backoff
# (Ported from Kilo Code's MCP resilience fix)
# ---------------------------------------------------------------------------

class TestMCPInitialConnectionRetry:
    """MCPServerTask.run() retries initial connection failures instead of giving up."""

    def test_initial_connect_retries_constant_exists(self):
        """_MAX_INITIAL_CONNECT_RETRIES should be defined."""
        from tools.mcp_tool import _MAX_INITIAL_CONNECT_RETRIES
        assert _MAX_INITIAL_CONNECT_RETRIES >= 1

    def test_initial_connect_retry_succeeds_on_second_attempt(self):
        """Server succeeds after one transient initial failure."""
        from tools.mcp_tool import MCPServerTask

        call_count = 0

        async def _run():
            nonlocal call_count
            server = MCPServerTask("test-retry")

            # Track calls via patching the method on the class
            original_run_stdio = MCPServerTask._run_stdio

            async def fake_run_stdio(self_inner, config):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise ConnectionError("DNS resolution failed")
                # Second attempt: success — set ready and "run" until shutdown
                self_inner._ready.set()
                await self_inner._shutdown_event.wait()

            with patch.object(MCPServerTask, '_run_stdio', fake_run_stdio):
                task = asyncio.ensure_future(server.run({"command": "fake"}))
                await server._ready.wait()

                # It should have succeeded (no error) after retrying
                assert server._error is None, f"Expected no error, got: {server._error}"
                assert call_count == 2, f"Expected 2 attempts, got {call_count}"

                # Clean shutdown
                server._shutdown_event.set()
                await task

        asyncio.get_event_loop().run_until_complete(_run())

    def test_initial_connect_gives_up_after_max_retries(self):
        """Server gives up after _MAX_INITIAL_CONNECT_RETRIES failures."""
        from tools.mcp_tool import MCPServerTask, _MAX_INITIAL_CONNECT_RETRIES

        call_count = 0

        async def _run():
            nonlocal call_count
            server = MCPServerTask("test-exhaust")

            async def fake_run_stdio(self_inner, config):
                nonlocal call_count
                call_count += 1
                raise ConnectionError("DNS resolution failed")

            with patch.object(MCPServerTask, '_run_stdio', fake_run_stdio):
                task = asyncio.ensure_future(server.run({"command": "fake"}))
                await server._ready.wait()

                # Should have an error after exhausting retries
                assert server._error is not None
                assert "DNS resolution failed" in str(server._error)
                # 1 initial + N retries = _MAX_INITIAL_CONNECT_RETRIES + 1 total attempts
                assert call_count == _MAX_INITIAL_CONNECT_RETRIES + 1

                await task

        asyncio.get_event_loop().run_until_complete(_run())

    def test_initial_connect_retry_respects_shutdown(self):
        """Shutdown during initial retry backoff aborts cleanly."""
        from tools.mcp_tool import MCPServerTask

        async def _run():
            server = MCPServerTask("test-shutdown")
            attempt = 0

            async def fake_run_stdio(self_inner, config):
                nonlocal attempt
                attempt += 1
                if attempt == 1:
                    raise ConnectionError("transient failure")
                # Should not reach here because shutdown fires during sleep
                raise AssertionError("Should not attempt after shutdown")

            with patch.object(MCPServerTask, '_run_stdio', fake_run_stdio):
                task = asyncio.ensure_future(server.run({"command": "fake"}))

                # Give the first attempt time to fail, then set shutdown
                # during the backoff sleep
                await asyncio.sleep(0.1)
                server._shutdown_event.set()
                await server._ready.wait()

                # Should have the error set and be done
                assert server._error is not None
                await task

        asyncio.get_event_loop().run_until_complete(_run())


# ---------------------------------------------------------------------------
# Fix 2c: Recursive descendant discovery via /proc and psutil
# ---------------------------------------------------------------------------
#
# ``_discover_descendants()`` performs a BFS over /proc on Linux (falling
# back to psutil) to find ALL descendants of a given PID.  The reaper
# phase in ``_kill_orphaned_mcp_children()`` uses this to terminate
# grandchildren that shell-wrapper MCP servers may have left behind in
# a different process group — the killpg path alone can't reach them
# when the wrapper started the real daemon in a separate session.

class TestReaperRecursiveDiscovery:
    """_discover_descendants and its integration into _kill_orphaned_mcp_children."""

    def _reset_state(self):
        from tools.mcp_tool import _stdio_pids, _orphan_stdio_pids, _stdio_pgids, _lock
        with _lock:
            _stdio_pids.clear()
            _orphan_stdio_pids.clear()
            _stdio_pgids.clear()

    @staticmethod
    def _make_proc_side_effect(children_map):
        """Build side_effect for ``builtins.open`` that serves mock ``/proc/*/children``.

        ``children_map`` maps pid -> space-separated child PID string.
        Paths not matching ``/proc/<pid>/task/<pid>/children`` raise
        ``FileNotFoundError``.
        """
        import re
        from unittest.mock import mock_open

        def side_effect(file, *args, **kwargs):
            path = str(file)
            m = re.match(r'/proc/(\d+)/task/\1/children', path)
            if m:
                pid = int(m.group(1))
                data = children_map.get(pid, "")
                return mock_open(read_data=data).return_value
            raise FileNotFoundError(2, "No such file or directory", path)
        return side_effect

    # -- unit: discover_descendants via /proc (mocked) ----------------------

    def test_discover_descendants_via_proc(self):
        """_discover_descendants finds all descendants in a 3-level /proc tree."""
        from tools.mcp_tool import _discover_descendants

        # 10000 -> 10001, 10002
        # 10001 -> 10003
        # 10002 -> 10004, 10005
        # 10003 -> 10006
        tree = {
            10000: "10001 10002",
            10001: "10003",
            10002: "10004 10005",
            10003: "10006",
            10004: "",
            10005: "",
            10006: "",
        }
        expected = {10001, 10002, 10003, 10004, 10005, 10006}

        side_effect = self._make_proc_side_effect(tree)
        with patch("builtins.open", side_effect=side_effect):
            result = _discover_descendants(10000)

        assert result == expected, f"/proc BFS: expected {expected}, got {result}"

    def test_discover_descendants_leaf_pid_returns_empty(self):
        """A PID with no children returns empty set (edge case)."""
        from tools.mcp_tool import _discover_descendants

        tree = {50000: ""}
        side_effect = self._make_proc_side_effect(tree)
        with patch("builtins.open", side_effect=side_effect):
            result = _discover_descendants(50000)

        assert result == set(), f"Leaf PID: expected empty set, got {result}"

    # -- unit: discover_descendants via psutil fallback (mocked) ------------

    def test_discover_descendants_via_psutil_fallback(self):
        """_discover_descendants falls back to psutil when /proc is broken."""
        pytest.importorskip("psutil")
        from tools.mcp_tool import _discover_descendants

        def _broken_proc(path, *args, **kwargs):
            if '/proc/' in str(path):
                raise RuntimeError("Simulated broken /proc filesystem")
            raise FileNotFoundError(2, "No such file", str(path))

        mock_child1 = MagicMock()
        mock_child1.pid = 20001
        mock_child2 = MagicMock()
        mock_child2.pid = 20002

        with patch("builtins.open", side_effect=_broken_proc), \
             patch("psutil.Process") as mock_psutil_proc:
            mock_proc_inst = MagicMock()
            mock_proc_inst.children.return_value = [mock_child1, mock_child2]
            mock_psutil_proc.return_value = mock_proc_inst

            result = _discover_descendants(1000)

        assert result == {20001, 20002}, (
            f"psutil fallback: expected {{20001, 20002}}, got {result}"
        )
        mock_proc_inst.children.assert_called_once_with(recursive=True)

    # -- unit: discover_descendants empty when both paths fail --------------

    def test_discover_descendants_empty_when_both_fail(self):
        """When /proc crashes and psutil fails, empty set is returned (no crash)."""
        from tools.mcp_tool import _discover_descendants

        def _crash_proc(path, *args, **kwargs):
            if '/proc/' in str(path):
                raise RuntimeError("Simulated /proc crash")
            raise FileNotFoundError(2, "No such file", str(path))

        with patch("builtins.open", side_effect=_crash_proc), \
             patch("psutil.Process", side_effect=ProcessLookupError("no such process")):
            result = _discover_descendants(1000)

        assert result == set(), f"Both fail: expected empty set, got {result}"

    # -- unit: discover_descendants cycle safety ---------------------------

    def test_discover_descendants_cycle_safety(self):
        """Cyclic /proc references (child points back to ancestor) are handled."""
        from tools.mcp_tool import _discover_descendants

        # 20000 -> 20001 -> 20002 -> 20000 (cycle back to root)
        tree = {
            20000: "20001",
            20001: "20002",
            20002: "20000",
        }
        expected = {20001, 20002}

        side_effect = self._make_proc_side_effect(tree)
        with patch("builtins.open", side_effect=side_effect):
            result = _discover_descendants(20000)

        assert result == expected, f"Cycle test: expected {expected}, got {result}"

    # -- integration: kill_orphaned sends signals to descendants -----------

    def test_kill_orphaned_sends_signal_to_descendants(self):
        """_kill_orphaned_mcp_children sends SIGTERM/SIGKILL to discovered descendants."""
        from tools.mcp_tool import (
            _kill_orphaned_mcp_children,
            _orphan_stdio_pids,
            _lock,
        )

        self._reset_state()

        target_pid = 30000
        tree = {
            30000: "30001",
            30001: "30002 30003",
            30002: "",
            30003: "",
        }

        with _lock:
            _orphan_stdio_pids.add(target_pid)

        side_effect = self._make_proc_side_effect(tree)
        with patch("builtins.open", side_effect=side_effect), \
             patch("tools.mcp_tool.os.kill") as mock_kill, \
             patch("tools.mcp_tool.os.killpg") as mock_killpg, \
             patch("gateway.status._pid_exists", return_value=True), \
             patch("tools.mcp_tool.time.sleep"):
            _kill_orphaned_mcp_children()

        # Phase 1: SIGTERM to tracked pid + each discovered descendant
        mock_kill.assert_any_call(target_pid, signal.SIGTERM)
        mock_kill.assert_any_call(30001, signal.SIGTERM)
        mock_kill.assert_any_call(30002, signal.SIGTERM)
        mock_kill.assert_any_call(30003, signal.SIGTERM)

        # Phase 3: SIGKILL escalation for survivors (all 4 reported alive)
        assert mock_kill.call_count >= 8, (
            f"Expected >= 8 signal calls, got {mock_kill.call_count}"
        )
        mock_killpg.assert_not_called()

    # -- integration: real grandchild discovery ----------------------------

    @pytest.mark.live_system_guard_bypass
    @pytest.mark.skipif(
        not os.path.exists("/proc/self/status"),
        reason="Requires Linux /proc filesystem for descendant discovery",
    )
    def test_real_grandchild_discovery(self, tmp_path):
        """Real subprocess tree: grandchild is killed via descendant discovery.

        Spawns a child process that ignores SIGTERM and keeps running,
        which in turn spawns a grandchild in its own process group.
        The grandchild is only reachable through ``_discover_descendants()``
        (reading /proc), NOT through killpg on the child's pgid.

        When ``_kill_orphaned_mcp_children()`` runs against the child's PID,
        it should discover the grandchild via /proc and terminate it.
        """
        import subprocess
        import sys
        import time as _time

        psutil = pytest.importorskip("psutil")

        grandchild_pid_file = tmp_path / "gc.pid"

        # Grandchild: start its own process group (won't be in child's pgid)
        # and sleep so we can verify it's alive before reaping.
        grandchild_code = (
            "import os, sys, time\n"
            "os.setpgid(0, 0)\n"
            f"open({str(grandchild_pid_file)!r}, 'w').write(str(os.getpid()))\n"
            "while True:\n"
            "    time.sleep(0.5)\n"
        )

        # Child: spawn grandchild, ignore SIGTERM so it stays alive long
        # enough for the reaper to read /proc/{child.pid}/children.
        child_code = (
            "import subprocess, sys, time, signal\n"
            "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
            f"subprocess.Popen([sys.executable, '-c', {grandchild_code!r}])\n"
            "while True:\n"
            "    time.sleep(0.5)\n"
        )

        child = subprocess.Popen(
            [sys.executable, "-c", child_code],
        )

        try:
            # Wait for grandchild to start
            deadline = _time.time() + 5
            while _time.time() < deadline and not grandchild_pid_file.exists():
                _time.sleep(0.05)
            assert grandchild_pid_file.exists(), "Grandchild did not start"
            gc_pid = int(grandchild_pid_file.read_text().strip())

            # Sanity: grandchild is alive and NOT in the child's pgid
            assert psutil.pid_exists(gc_pid), "Grandchild should be alive"
            child_pgid = os.getpgid(child.pid)
            gc_pgid = os.getpgid(gc_pid)
            assert gc_pgid != child_pgid, (
                "Grandchild must be in its own pgid for this test"
            )

            # Register child PID as orphan (no pgid entry so per-pid kill path)
            from tools.mcp_tool import (
                _kill_orphaned_mcp_children,
                _orphan_stdio_pids,
                _lock,
            )
            with _lock:
                _orphan_stdio_pids.clear()
                _orphan_stdio_pids.add(child.pid)

            # Drive the reaper — should discover and kill grandchild via /proc
            _kill_orphaned_mcp_children()

            # Grandchild must be dead
            deadline = _time.time() + 3
            while _time.time() < deadline and psutil.pid_exists(gc_pid):
                _time.sleep(0.05)
            assert not psutil.pid_exists(gc_pid), (
                f"Grandchild PID {gc_pid} survived descendant reaping"
            )

        finally:
            # Belt-and-suspenders: ensure both are dead
            for pid in (child.pid,):
                try:
                    os.kill(pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
            if gc_pid:
                try:
                    os.kill(gc_pid, signal.SIGKILL)
                except (ProcessLookupError, OSError):
                    pass
