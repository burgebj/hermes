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
    """Worker entry point.

    P0-8: Top-level exception handling ensures that ANY unhandled error
    results in a ``failed`` status and resource cleanup, so the coordinator
    never sees a stuck intermediate state.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Gateway restart worker")
    parser.add_argument("--intent-file", required=True,
                        help="Path to JSON intent file")
    args = parser.parse_args()

    # Read and delete the intent file (nonce-safe: removed from disk)
    intent_path = Path(args.intent_file)
    try:
        raw = intent_path.read_text(encoding="utf-8")
    except OSError as e:
        _log_error("intent_file_read", f"Failed to read intent file: {e}",
                   path=str(intent_path))
        sys.exit(1)
    finally:
        try:
            intent_path.unlink(missing_ok=True)
        except OSError:
            pass

    try:
        intent = json.loads(raw)
    except json.JSONDecodeError as e:
        _log_error("invalid_intent", f"Failed to parse intent JSON: {e}",
                   raw_length=len(raw))
        sys.exit(1)

    if not isinstance(intent, dict):
        _log_error("invalid_intent", "Intent is not a dict",
                   intent_type=type(intent).__name__)
        sys.exit(1)

    profile = intent.get("profile", "default")
    request_id = intent.get("request_id", "")
    old_pid = intent.get("target_pid", 0)
    origin = intent.get("origin", "worker")

    nonce = intent.get("nonce", "")

    try:
        _run_restart_transaction(intent)
    except Exception as exc:
        # P0-8: Write failed status on ANY unhandled exception
        from hermes_cli.gateway_restart_state import (
            append_restart_log,
            write_status,
        )
        write_status(profile, "failed", request_id=request_id, error=str(exc))
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error=f"unhandled: {exc}",
        )
        sys.exit(1)
    finally:
        # P0-8: Cleanup in finally — but only OUR resources.
        # P0-4: Pass request_id + nonce so stale workers don't delete
        # a newer transaction's intent.
        from hermes_cli.gateway_restart_state import (
            RestartLock,
            cleanup_intent,
        )
        try:
            lock = RestartLock(profile)
            lock.release()  # release() verifies owner_token — safe
        except Exception:
            pass
        try:
            cleanup_intent(profile, request_id=request_id, nonce=nonce)
        except Exception:
            pass


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
        _pid_exists,
    )

    profile = intent.get("profile", "default")
    request_id = intent.get("request_id", "")
    old_pid = intent.get("target_pid", 0)
    origin = intent.get("origin", "worker")
    hermes_home = intent.get("hermes_home", "")
    task_name = intent.get("task_name", "")
    nonce = intent.get("nonce", "")

    # Validate intent TTL
    expires = intent.get("expires_at", 0)
    if isinstance(expires, (int, float)) and time.time() > expires:
        _log_error("expired_intent", f"Intent expired at {expires}", profile=profile, request_id=request_id)
        write_status(profile, "failed", request_id=request_id, error="Intent expired")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error="Intent expired",
        )
        cleanup_intent(profile, request_id=request_id, nonce=nonce)
        sys.exit(1)

    # P0-5: Full intent validation before ANY destructive action
    disk_intent = read_intent(profile)
    if not disk_intent:
        _fail_closed(profile, request_id, old_pid, origin, "missing_intent",
                     "Intent file missing or unreadable", nonce=nonce)
    if disk_intent["request_id"] != request_id:
        _fail_closed(profile, request_id, old_pid, origin, "request_id_mismatch",
                     f"Expected {request_id}, got {disk_intent['request_id']}", nonce=nonce)
    if not validate_intent_nonce(disk_intent, intent.get("nonce", "")):
        _fail_closed(profile, request_id, old_pid, origin, "nonce_mismatch",
                     "Nonce validation failed", nonce=nonce)
    if disk_intent["profile"] != profile:
        _fail_closed(profile, request_id, old_pid, origin, "profile_mismatch",
                     f"Expected profile {profile}, got {disk_intent['profile']}", nonce=nonce)
    if disk_intent["target_pid"] != old_pid:
        _fail_closed(profile, request_id, old_pid, origin, "target_pid_mismatch",
                     f"Expected PID {old_pid}, got {disk_intent['target_pid']}", nonce=nonce)
    if disk_intent.get("schema_version") != 1:
        _fail_closed(profile, request_id, old_pid, origin, "schema_version_unsupported",
                     f"Unsupported schema_version: {disk_intent.get('schema_version')}", nonce=nonce)
    # TTL already checked above (expires_at), but re-check on disk intent
    disk_expires = disk_intent.get("expires_at", 0)
    if isinstance(disk_expires, (int, float)) and time.time() > disk_expires:
        _fail_closed(profile, request_id, old_pid, origin, "expired_intent",
                     f"Disk intent expired at {disk_expires}", nonce=nonce)
    # Mark intent as consumed to prevent replay
    update_intent_state(profile, "consumed")

    # P0-4: Claim lease from coordinator
    lock = RestartLock(profile)
    if not lock.claim_lease(request_id):
        _log_error("lease_claim_failed", "Worker could not claim lease", profile=profile, request_id=request_id)
        write_status(profile, "failed", request_id=request_id, error="Worker could not claim lease")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error="lease claim failed",
        )
        cleanup_intent(profile, request_id=request_id, nonce=nonce)
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

        # P0-6: Old PID MUST be dead before starting a new gateway.
        # Two gateways running simultaneously causes port conflicts,
        # duplicate message processing, and state corruption.
        if old_pid > 0 and _pid_exists(old_pid):
            raise RuntimeError(
                f"Old gateway PID {old_pid} is still alive after drain/stop/terminate/force-kill. "
                "Cannot safely start a new gateway."
            )

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
        cleanup_intent(profile, request_id=request_id, nonce=nonce)


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
        _pid_exists,
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
    """Wait for the port to be released — with closed-loop verification.

    P0-7: Full closed-loop protocol:
    1. Wait for port release (timeout).
    2. If still occupied → query listening PIDs.
    3. If PID query fails or returns empty → fail closed.
    4. If listener is unrelated process → fail closed (no kill).
    5. If listener is Hermes Gateway → terminate it.
    6. MUST re-verify port is now free (second socket check).
    7. If still occupied after kill → fail closed.
    """
    from hermes_cli.gateway_restart_state import append_restart_log

    # Step 1: Wait for natural release
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

    # Step 2: Port still occupied — query who owns it
    pids = _get_pids_on_port(port)

    if not pids:
        # P0-7: PID query returned empty but port is still occupied.
        # Cannot identify owner → fail closed.
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", port=port,
            error=f"Port {port} still occupied but no PIDs returned from query",
        )
        raise RuntimeError(
            f"Port {port} is still in use but no listening PIDs could be identified. "
            "Cannot safely proceed."
        )

    # Step 3: Identify each listener
    for pid in pids:
        if pid == os.getpid():
            continue  # Never kill ourselves
        if _is_ancestor(pid):
            continue  # Never kill ancestors

        # P1-5: Only terminate if PID matches the old gateway PID we are
        # restarting.  Any other process — even another Hermes instance —
        # must NOT be killed.  Fail closed instead.
        if pid == old_pid:
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="waiting_port_release",
                port=port, listener_pid=pid,
                reason="cleaning_old_gateway_listener",
            )
            try:
                from gateway.status import terminate_pid
                terminate_pid(pid, force=True)
            except Exception:
                pass
        else:
            # PID != old_pid — could be another Hermes instance or an
            # unrelated process.  Either way, do NOT kill.
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="failed",
                port=port, listener_pid=pid,
                error=f"Port {port} occupied by PID {pid} (not old gateway {old_pid})",
            )
            raise RuntimeError(
                f"Port {port} is occupied by PID {pid} (not the old gateway {old_pid}). "
                "Cannot safely restart.  Will NOT kill."
            )

    # Step 4: Re-verify port release after killing Hermes listeners
    verify_deadline = time.monotonic() + 10.0
    while time.monotonic() < verify_deadline:
        if not _is_port_in_use(port):
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                origin=origin, state="waiting_port_release",
                port=port, reason="port_released_after_cleanup",
            )
            return
        time.sleep(0.5)

    # Step 5: Port STILL occupied after kill — fail closed
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="failed", port=port,
        error=f"Port {port} still occupied after terminating Hermes listeners",
    )
    raise RuntimeError(
        f"Port {port} is still occupied after terminating Hermes Gateway listeners. "
        "Cannot safely start a new gateway."
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
    if new_pid <= 0:
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            new_pid=0, origin=origin, state="starting_direct_fallback",
            launcher="direct_spawn", error="direct spawn failed (no PID)",
        )
        raise RuntimeError("Direct spawn failed: no PID returned")

    # P0-5: MUST obtain launch evidence — a Popen PID alone is not enough
    verified_pid = _wait_for_launch_evidence(old_pid, timeout=15.0)
    if verified_pid <= 0:
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            new_pid=new_pid, origin=origin, state="starting_direct_fallback",
            launcher="direct_spawn", error="no launch evidence after direct spawn",
        )
        raise RuntimeError(
            f"Direct-spawned gateway (PID {new_pid}) did not produce launch evidence"
        )
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
        _pid_exists,
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

    # P1-2: Stability window — verify new PID stays alive for a few seconds
    # A process that starts and immediately exits is not a valid restart.
    stable_seconds = 3.0
    stable_deadline = time.monotonic() + stable_seconds
    while time.monotonic() < stable_deadline:
        if not _pid_exists(new_pid):
            write_status(profile, "failed", request_id=request_id,
                         error=f"New PID {new_pid} died within {stable_seconds}s stability window")
            append_restart_log(
                request_id=request_id, profile=profile, old_pid=old_pid,
                new_pid=new_pid, origin=origin, state="failed",
                launcher=launcher, error="New PID unstable (died within stability window)",
            )
            return
        time.sleep(0.5)

    # P1-2: Verify no dual gateway (old PID should be dead)
    if old_pid > 0 and _pid_exists(old_pid):
        write_status(profile, "failed", request_id=request_id,
                     error=f"Dual gateway detected: old PID {old_pid} still alive alongside new PID {new_pid}")
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            new_pid=new_pid, origin=origin, state="failed",
            launcher=launcher, error="dual gateway detected",
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


def _pid_wait(pid: int, timeout: float = 10.0) -> bool:
    """Wait for PID to exit.  Returns True if it exited within timeout."""
    from hermes_cli.gateway_restart_state import _pid_exists

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
                # POSIX fallback: read ppid from /proc (Linux only)
                try:
                    with open(f"/proc/{ppid}/stat", "r") as f:
                        parts = f.read().split(")")
                        if len(parts) >= 2:
                            fields = parts[1].split()
                            ppid = int(fields[1]) if len(fields) > 1 else 0
                        else:
                            break
                except (OSError, ValueError, IndexError):
                    break
    except Exception:
        pass
    return False


def _fail_closed(
    profile: str,
    request_id: str,
    old_pid: int,
    origin: str,
    error_code: str,
    detail: str,
    nonce: str = "",
) -> None:
    """Fail closed: write status, log, cleanup, and exit.

    Called when any validation fails.  Guarantees no destructive action
    (stop, kill, start) has been taken before this point.
    """
    from hermes_cli.gateway_restart_state import (
        append_restart_log,
        cleanup_intent,
        write_status,
    )
    write_status(profile, "failed", request_id=request_id,
                 error=f"{error_code}: {detail}")
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="failed", error=f"{error_code}: {detail}",
    )
    cleanup_intent(profile, request_id=request_id, nonce=nonce)
    sys.exit(1)


def _log_error(code: str, detail: str, **extra: Any) -> None:
    """Log an error to JSONL."""
    from hermes_cli.gateway_restart_state import append_restart_log
    # Filter extra to only include fields append_restart_log accepts
    _KNOWN = {"request_id", "profile", "old_pid", "new_pid", "origin",
              "launcher", "reason", "error", "listener_pid", "port"}
    filtered = {k: v for k, v in extra.items() if k in _KNOWN}
    append_restart_log(state="failed", error=f"{code}: {detail}", **filtered)


if __name__ == "__main__":
    main()
