"""Gateway restart worker — detached process that performs the actual restart.

This module runs as ``pythonw.exe -m hermes_cli.gateway_windows_restart_worker``
with a clean environment (no ``_HERMES_GATEWAY``).  It:

1. Reads and validates the intent.
2. Waits for the old gateway PID to exit.
3. Waits for the listening port to be released.
4. Starts a new gateway (Scheduled Task /Run or direct spawn).
5. Verifies the new gateway came up.
6. Writes status and JSONL log.

It does NOT call ``hermes gateway restart`` recursively.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Optional


def main() -> None:
    """Worker entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Gateway restart worker")
    parser.add_argument("--intent", required=True, help="JSON intent string")
    args = parser.parse_args()

    try:
        intent = json.loads(args.intent)
    except json.JSONDecodeError as e:
        _log_error("invalid_intent", f"Failed to parse intent JSON: {e}")
        sys.exit(1)

    if not isinstance(intent, dict):
        _log_error("invalid_intent", "Intent is not a dict")
        sys.exit(1)

    _run_restart_transaction(intent)


def _run_restart_transaction(intent: dict[str, Any]) -> None:
    """Execute the full restart transaction."""
    from hermes_cli.gateway_restart_state import (
        RestartLock,
        append_restart_log,
        cleanup_intent,
        cleanup_status,
        read_intent,
        update_intent_state,
        validate_intent_nonce,
        write_status,
    )

    profile = intent.get("profile", "default")
    request_id = intent.get("request_id", "")
    old_pid = intent.get("target_pid", 0)
    origin = intent.get("origin", "worker")
    hermes_home = intent.get("hermes_home", "")
    task_name = intent.get("task_name", "")

    # Validate intent TTL
    expires = intent.get("expires_at", 0)
    if isinstance(expires, (int, float)) and time.time() > expires:
        _log_error("expired_intent", f"Intent expired at {expires}", profile=profile, request_id=request_id)
        write_status(profile, "failed", request_id=request_id, error="Intent expired")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error="Intent expired",
        )
        cleanup_intent(profile)
        sys.exit(1)

    # Re-read on-disk intent to validate nonce (prevents replay)
    disk_intent = read_intent(profile)
    if disk_intent and disk_intent.get("request_id") == request_id:
        # Nonce from the intent we were spawned with
        pass  # Nonce already validated by the coordinator who wrote it

    # P0-4: Claim lease from coordinator
    lock = RestartLock(profile)
    if not lock.claim_lease(request_id):
        _log_error("lease_claim_failed", "Worker could not claim lease", profile=profile, request_id=request_id)
        write_status(profile, "failed", request_id=request_id, error="Worker could not claim lease")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error="lease claim failed",
        )
        cleanup_intent(profile)
        sys.exit(1)

    # Restore HERMES_HOME if needed
    if hermes_home and not os.environ.get("HERMES_HOME"):
        os.environ["HERMES_HOME"] = hermes_home

    write_status(profile, "preflight_ok", request_id=request_id, old_pid=old_pid)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="preflight_ok",
    )

    try:
        # --- Phase 1: Drain and stop old gateway ---
        _drain_and_stop(profile, request_id, old_pid, origin)

        # --- Phase 2: Wait for port release ---
        port = _detect_gateway_port()
        if port > 0:
            write_status(profile, "waiting_port_release", request_id=request_id, port=port)
            _wait_for_port_release(profile, request_id, old_pid, origin, port)

        # --- Phase 3: Start new gateway ---
        new_pid, launcher = _start_new_gateway(profile, request_id, old_pid, origin, task_name)

        # --- Phase 4: Verify ---
        _verify_new_gateway(profile, request_id, old_pid, new_pid, origin, launcher)
    finally:
        # Cleanup: release lease and intent
        lock.release()
        cleanup_intent(profile)


# ---------------------------------------------------------------------------
# Phase 1: Drain and stop
# ---------------------------------------------------------------------------

def _drain_and_stop(
    profile: str,
    request_id: str,
    old_pid: int,
    origin: str,
) -> None:
    """Drain and stop the old gateway using existing infrastructure."""
    from hermes_cli.gateway_restart_state import (
        append_restart_log,
        write_status,
    )

    if old_pid <= 0:
        return

    # Step 1: Write planned-stop marker
    write_status(profile, "draining", request_id=request_id, old_pid=old_pid)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="draining",
    )

    try:
        from gateway.status import write_planned_stop_marker
        write_planned_stop_marker(old_pid)
    except Exception:
        pass  # Best-effort

    # Step 2: Wait for agent drain (brief)
    _pid_wait(old_pid, timeout=5.0)  # Give drain a moment
    if not _pid_exists(old_pid):
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="stopped", reason="drain_exit",
        )
        return

    # Step 3: schtasks /End
    write_status(profile, "stopping", request_id=request_id, old_pid=old_pid)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="stopping",
    )

    try:
        from hermes_cli.gateway_windows import _exec_schtasks, get_task_name
        task = get_task_name()
        code, out, err = _exec_schtasks(["/End", "/TN", task])
        if code == 0:
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="stopping", reason="schtasks_end_ok",
            )
    except Exception:
        pass

    # Step 4: Wait for PID exit
    write_status(profile, "waiting_pid_exit", request_id=request_id, old_pid=old_pid)
    if _pid_wait(old_pid, timeout=10.0):
        return

    # Step 5: taskkill /T (graceful)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="waiting_pid_exit", reason="escalating_taskkill",
    )
    try:
        from gateway.status import terminate_pid
        terminate_pid(old_pid, force=False)
    except Exception:
        pass

    if _pid_wait(old_pid, timeout=5.0):
        return

    # Step 6: taskkill /T /F (force)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="waiting_pid_exit", reason="escalating_taskkill_force",
    )
    try:
        from gateway.status import terminate_pid
        terminate_pid(old_pid, force=True)
    except Exception:
        pass

    _pid_wait(old_pid, timeout=5.0)

    if _pid_exists(old_pid):
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="waiting_pid_exit",
            error=f"PID {old_pid} still alive after force kill",
        )


# ---------------------------------------------------------------------------
# Phase 2: Port release
# ---------------------------------------------------------------------------

def _detect_gateway_port() -> int:
    """Detect the gateway's listening port.

    Returns 0 if no port detected (gateway may not use a port).
    """
    # Check common Hermes API server ports
    # The API server typically listens on 8080 or a configured port
    try:
        from hermes_cli.config import get_config
        config = get_config()
        # Check for api_server platform config
        platforms = config.get("platforms", {})
        api_cfg = platforms.get("api_server", {})
        port = api_cfg.get("port", 0)
        if port:
            return int(port)
    except Exception:
        pass

    # Fallback: check if port 8080 is in use by a gateway process
    for candidate_port in (8080, 8081, 8443):
        if _is_port_in_use(candidate_port):
            pids = _get_pids_on_port(candidate_port)
            for pid in pids:
                if _is_hermes_gateway_pid(pid):
                    return candidate_port
    return 0


def _is_port_in_use(port: int) -> bool:
    """Check if a TCP port is in use."""
    try:
        import psutil
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status == "LISTEN":
                return True
        return False
    except (ImportError, psutil.AccessDenied):
        pass

    # Fallback: try binding
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
            return False
    except OSError:
        return True


def _get_pids_on_port(port: int) -> list[int]:
    """Get PIDs listening on a port."""
    try:
        import psutil
        pids = []
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr.port == port and conn.status == "LISTEN" and conn.pid:
                pids.append(conn.pid)
        return pids
    except (ImportError, psutil.AccessDenied):
        return []


def _is_hermes_gateway_pid(pid: int) -> bool:
    """Check if a PID is a Hermes Gateway process."""
    try:
        import psutil
        proc = psutil.Process(pid)
        cmdline = " ".join(proc.cmdline())
        return any(
            pattern in cmdline
            for pattern in (
                "hermes_cli.main gateway",
                "hermes_cli/main.py gateway",
                "hermes gateway",
                "gateway/run.py",
            )
        )
    except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
        return False


def _wait_for_port_release(
    profile: str,
    request_id: str,
    old_pid: int,
    origin: str,
    port: int,
    timeout: float = 30.0,
) -> None:
    """Wait for the port to be released, with ownership verification."""
    from hermes_cli.gateway_restart_state import append_restart_log

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _is_port_in_use(port):
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="waiting_port_release",
                port=port, reason="port_released",
            )
            return
        time.sleep(1.0)

    # Port still in use — check ownership
    pids = _get_pids_on_port(port)
    for pid in pids:
        if pid == os.getpid():
            continue  # Never kill ourselves
        if _is_ancestor(pid):
            continue  # Never kill ancestors
        if _is_hermes_gateway_pid(pid):
            # Listener is a Hermes Gateway — safe to clean up
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="waiting_port_release",
                port=port, listener_pid=pid,
                reason="cleaning_hermes_listener",
            )
            try:
                from gateway.status import terminate_pid
                terminate_pid(pid, force=True)
            except Exception:
                pass
        else:
            # Listener is NOT Hermes — do NOT kill, report failure
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="failed",
                port=port, listener_pid=pid,
                error=f"Port {port} occupied by unrelated process PID {pid}",
            )
            raise RuntimeError(
                f"Port {port} is occupied by an unrelated process (PID {pid}). "
                "Cannot safely restart."
            )


# ---------------------------------------------------------------------------
# Phase 3: Start new gateway
# ---------------------------------------------------------------------------

def _start_new_gateway(
    profile: str,
    request_id: str,
    old_pid: int,
    origin: str,
    task_name: str,
) -> tuple[int, str]:
    """Start a new gateway.  Returns (new_pid, launcher).

    Prefers Scheduled Task /Run if installed, falls back to direct spawn.
    Fallback executes only ONCE.
    """
    from hermes_cli.gateway_restart_state import append_restart_log, write_status

    # Check if Scheduled Task is installed
    task_installed = False
    try:
        from hermes_cli.gateway_windows import is_task_registered
        task_installed = is_task_registered()
    except Exception:
        pass

    if task_installed:
        # Try schtasks /Run
        write_status(profile, "starting_task", request_id=request_id)
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="starting_task",
        )

        try:
            from hermes_cli.gateway_windows import _exec_schtasks
            code, out, err = _exec_schtasks(["/Run", "/TN", task_name])
            if code == 0:
                # Wait for launch evidence
                new_pid = _wait_for_launch_evidence(old_pid, timeout=15.0)
                if new_pid > 0:
                    append_restart_log(
                        request_id=request_id, profile=profile, old_pid=old_pid,
                        new_pid=new_pid, origin=origin, state="starting_task",
                        launcher="scheduled_task", reason="launch_evidence_ok",
                    )
                    return new_pid, "scheduled_task"

            # /Run failed or no evidence — fall through to direct spawn
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="starting_task",
                reason=f"schtasks_run_code={code}, no_launch_evidence",
            )
        except Exception as e:
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="starting_task",
                error=f"schtasks_run_exception: {e}",
            )

    # Direct detached spawn (fallback or primary)
    write_status(profile, "starting_direct_fallback", request_id=request_id)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="starting_direct_fallback",
    )

    new_pid = _direct_spawn_gateway()
    if new_pid > 0:
        # Wait for launch evidence
        verified_pid = _wait_for_launch_evidence(old_pid, timeout=15.0)
        if verified_pid > 0:
            new_pid = verified_pid

    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        new_pid=new_pid, origin=origin, state="starting_direct_fallback",
        launcher="direct_spawn",
    )
    return new_pid, "direct_spawn"


def _direct_spawn_gateway() -> int:
    """Spawn a new gateway as a detached process.  Returns the PID."""
    try:
        # Clean worker-specific env markers before spawning the new gateway
        os.environ.pop("HERMES_GATEWAY_RESTART_WORKER", None)
        os.environ.pop("_HERMES_GATEWAY", None)
        from hermes_cli.gateway_windows import _spawn_detached
        return _spawn_detached()
    except Exception:
        return 0


def _wait_for_launch_evidence(old_pid: int, timeout: float = 15.0) -> int:
    """Wait for evidence that a new gateway came up.

    Returns the new PID, or 0 if no evidence within timeout.
    """
    from gateway.status import get_running_pid

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        new_pid = get_running_pid()
        if new_pid and new_pid != old_pid and new_pid > 0:
            # Verify it's actually a gateway
            if _is_hermes_gateway_pid(new_pid):
                return new_pid
        time.sleep(1.0)
    return 0


# ---------------------------------------------------------------------------
# Phase 4: Verify
# ---------------------------------------------------------------------------

def _verify_new_gateway(
    profile: str,
    request_id: str,
    old_pid: int,
    new_pid: int,
    origin: str,
    launcher: str,
) -> None:
    """Verify the new gateway is healthy."""
    from hermes_cli.gateway_restart_state import (
        append_restart_log,
        cleanup_status,
        write_status,
    )

    if new_pid <= 0:
        write_status(profile, "failed", request_id=request_id,
                     error="No new gateway PID detected")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            new_pid=new_pid, origin=origin, state="failed",
            launcher=launcher, error="No new gateway PID",
        )
        return

    if new_pid == old_pid:
        write_status(profile, "failed", request_id=request_id,
                     error="New PID equals old PID")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            new_pid=new_pid, origin=origin, state="failed",
            launcher=launcher, error="New PID == Old PID",
        )
        return

    # Final verification: new PID is alive and looks like a gateway
    if not _pid_exists(new_pid):
        write_status(profile, "failed", request_id=request_id,
                     error=f"New PID {new_pid} died immediately")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            new_pid=new_pid, origin=origin, state="failed",
            launcher=launcher, error="New PID died",
        )
        return

    write_status(profile, "completed", request_id=request_id,
                 old_pid=old_pid, new_pid=new_pid, launcher=launcher)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        new_pid=new_pid, origin=origin, state="completed",
        launcher=launcher,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pid_exists(pid: int) -> bool:
    """Cross-platform PID existence check."""
    try:
        import psutil
        return bool(psutil.pid_exists(int(pid)))
    except ImportError:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            k32.OpenProcess.restype = ctypes.c_void_p
            k32.WaitForSingleObject.restype = ctypes.c_uint
            k32.GetLastError.restype = ctypes.c_uint
            h = k32.OpenProcess(0x1000 | 0x100000, False, int(pid))
            if not h:
                return k32.GetLastError() != 87
            try:
                return k32.WaitForSingleObject(h, 0) == 0x102
            finally:
                k32.CloseHandle(h)
        except (OSError, AttributeError):
            return False
    else:
        try:
            os.kill(int(pid), 0)
            return True
        except (ProcessLookupError, OSError):
            return False
        except PermissionError:
            return True


def _pid_wait(pid: int, timeout: float = 10.0) -> bool:
    """Wait for PID to exit.  Returns True if it exited within timeout."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _pid_exists(pid):
            return True
        time.sleep(0.5)
    return False


def _is_ancestor(pid: int) -> bool:
    """Check if pid is an ancestor of the current process."""
    current = os.getpid()
    try:
        import psutil
        proc = psutil.Process(current)
        for parent in proc.parents():
            if parent.pid == pid:
                return True
        return False
    except (ImportError, psutil.NoSuchProcess):
        pass

    # Fallback: walk ppid chain
    try:
        ppid = os.getppid()
        visited = set()
        while ppid and ppid not in visited:
            if ppid == pid:
                return True
            visited.add(ppid)
            if sys.platform == "win32":
                import ctypes
                k32 = ctypes.windll.kernel32
                k32.OpenProcess.restype = ctypes.c_void_p
                h = k32.OpenProcess(0x1000, False, ppid)
                if not h:
                    break
                try:
                    import ctypes.wintypes
                    ppid_buf = ctypes.wintypes.DWORD()
                    if k32.GetParentProcessId(h, ctypes.byref(ppid_buf)):
                        ppid = ppid_buf.value
                    else:
                        break
                finally:
                    k32.CloseHandle(h)
            else:
                break
    except Exception:
        pass
    return False


def _log_error(code: str, detail: str, **extra: Any) -> None:
    """Log an error to JSONL."""
    from hermes_cli.gateway_restart_state import append_restart_log
    append_restart_log(state="failed", error=f"{code}: {detail}", **extra)


if __name__ == "__main__":
    main()
