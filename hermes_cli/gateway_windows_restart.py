"""Windows Gateway Transactional Restart Coordinator.

Orchestrates safe, verifiable gateway restarts from three entry points:
1. Chat platform /restart command
2. Agent terminal ``hermes gateway restart``
3. External PowerShell ``hermes gateway restart``

The coordinator writes an intent, spawns a detached worker, and lets the
current gateway drain and exit.  The worker waits for the old gateway to
die, verifies the port is free, starts a new gateway, and confirms it came
up — all without inheriting ``_HERMES_GATEWAY=1``.

This module does NOT call ``hermes gateway restart`` recursively.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Optional

if sys.platform != "win32":
    # This module is Windows-specific.  Import is safe on other platforms
    # (functions raise RuntimeError if called).
    pass


def _assert_windows() -> None:
    if sys.platform != "win32":
        raise RuntimeError("gateway_windows_restart is Windows-only")


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------

def preflight_check(
    *,
    profile: str = "default",
    hermes_home: str | None = None,
    target_pid: int = 0,
) -> tuple[bool, str]:
    """Run preflight checks before stopping the old gateway.

    Returns (ok, detail).  If ok is False, the old gateway must NOT be stopped.
    """
    _assert_windows()
    errors: list[str] = []

    # 1. Python / pythonw available
    python_exe = sys.executable
    if not python_exe or not Path(python_exe).exists():
        errors.append(f"Python executable not found: {python_exe}")
    try:
        from hermes_cli.gateway_windows import _derive_venv_pythonw
        pythonw = _derive_venv_pythonw(python_exe)
        if not pythonw or not Path(pythonw).exists():
            errors.append("pythonw.exe not found — detached restart will fail")
    except Exception as e:
        errors.append(f"pythonw resolution failed: {e}")

    # 2. Worker module importable
    try:
        import hermes_cli.gateway_windows_restart_worker  # noqa: F401
    except ImportError as e:
        errors.append(f"Worker module not importable: {e}")

    # 3. HERMES_HOME readable
    from hermes_cli.config import get_hermes_home
    home = hermes_home or str(Path(get_hermes_home()).resolve())
    if not Path(home).is_dir():
        errors.append(f"HERMES_HOME not readable: {home}")

    # 4. Profile config exists
    profile_dir = Path(home) / "profiles" / profile if profile != "default" else Path(home)
    if not profile_dir.is_dir():
        errors.append(f"Profile directory not found: {profile_dir}")

    # 5. Task name resolvable
    try:
        from hermes_cli.gateway_windows import get_task_name
        task_name = get_task_name()
        if not task_name:
            errors.append("Task name resolved to empty")
    except Exception as e:
        errors.append(f"Task name resolution failed: {e}")

    # 6. Status directory writable
    try:
        from hermes_cli.gateway_restart_state import _get_run_dir
        run_dir = _get_run_dir()
        test_file = run_dir / ".preflight-test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except (OSError, Exception) as e:
        errors.append(f"Run directory not writable: {e}")

    # 7. Logs directory writable
    try:
        from hermes_cli.gateway_restart_state import _get_logs_dir
        logs_dir = _get_logs_dir()
        test_file = logs_dir / ".preflight-test"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
    except (OSError, Exception) as e:
        errors.append(f"Logs directory not writable: {e}")

    if errors:
        return False, "; ".join(errors)
    return True, "preflight_ok"


# ---------------------------------------------------------------------------
# Schedule restart handoff
# ---------------------------------------------------------------------------

def schedule_restart_handoff(
    *,
    origin: str = "external-cli",
    profile: str = "default",
    wait: bool = True,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    """Schedule a transactional restart.

    Returns a result dict with keys:
    - request_id: str
    - scheduled: bool
    - detail: str
    - completed: bool (only if wait=True)
    - old_pid: int
    - new_pid: int (only if completed)
    - launcher: str (only if completed)
    """
    _assert_windows()
    from hermes_cli.gateway_restart_state import (
        RestartLock,
        append_restart_log,
        cleanup_intent,
        cleanup_status,
        create_intent,
        read_intent,
        write_status,
    )
    from gateway.status import get_running_pid

    # Resolve current gateway PID
    old_pid = get_running_pid() or 0

    # Get task name
    try:
        from hermes_cli.gateway_windows import get_task_name
        task_name = get_task_name()
    except Exception:
        task_name = ""

    # Preflight
    ok, detail = preflight_check(profile=profile, target_pid=old_pid)
    if not ok:
        append_restart_log(
            request_id="", profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error=f"preflight: {detail}",
        )
        return {
            "request_id": "",
            "scheduled": False,
            "detail": f"Preflight failed: {detail}",
        }

    # Create intent
    intent = create_intent(
        profile=profile,
        target_pid=old_pid,
        task_name=task_name,
        origin=origin,
    )
    request_id = intent["request_id"]

    # Acquire lock (coalesce if same request within window)
    lock = RestartLock(profile)
    if not lock.try_acquire(request_id):
        # Check if existing intent is from the same origin within coalesce window
        existing = read_intent(profile)
        if existing:
            cleanup_intent(profile)
            lock.release()
            # Retry once
            intent = create_intent(
                profile=profile,
                target_pid=old_pid,
                task_name=task_name,
                origin=origin,
            )
            request_id = intent["request_id"]
            if not lock.try_acquire(request_id):
                append_restart_log(
                    request_id=request_id, profile=profile, old_pid=old_pid,
                    origin=origin, state="failed", error="lock contention",
                )
                cleanup_intent(profile)
                return {
                    "request_id": request_id,
                    "scheduled": False,
                    "detail": "Another restart is already in progress",
                }
        else:
            cleanup_intent(profile)
            return {
                "request_id": request_id,
                "scheduled": False,
                "detail": "Another restart is already in progress",
            }

    write_status(profile, "scheduled", request_id=request_id, old_pid=old_pid)
    append_restart_log(
        request_id=request_id, profile=profile, old_pid=old_pid,
        origin=origin, state="scheduled",
    )

    # Spawn detached worker
    try:
        worker_pid = _spawn_worker(intent, profile)
    except Exception as e:
        lock.release()
        cleanup_intent(profile)
        cleanup_status(profile)
        append_restart_log(
            request_id=request_id, profile=profile, old_pid=old_pid,
            origin=origin, state="failed", error=f"worker spawn: {e}",
        )
        return {
            "request_id": request_id,
            "scheduled": False,
            "detail": f"Failed to spawn worker: {e}",
        }

    result: dict[str, Any] = {
        "request_id": request_id,
        "scheduled": True,
        "detail": f"Restart scheduled (worker PID: {worker_pid})",
        "old_pid": old_pid,
    }

    # If external CLI with wait, poll for completion
    if wait:
        completed = _wait_for_completion(profile, timeout_s, lock)
        result["completed"] = completed
        final_status = _read_final_status(profile)
        if final_status:
            result["new_pid"] = final_status.get("new_pid", 0)
            result["launcher"] = final_status.get("launcher", "")
            if final_status.get("state") == "failed":
                result["detail"] = f"Restart failed: {final_status.get('error', 'unknown')}"
            else:
                result["detail"] = "Restart completed successfully"
        else:
            result["detail"] = "Restart timed out waiting for completion"
    else:
        # Don't wait — release lock so worker can acquire it
        lock.release()

    return result


def _wait_for_completion(
    profile: str,
    timeout_s: float,
    lock: RestartLock,
) -> bool:
    """Poll status file until completion or timeout."""
    from hermes_cli.gateway_restart_state import read_status

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        status = read_status(profile)
        if status and status.get("state") in ("completed", "failed"):
            lock.release()
            return status["state"] == "completed"
        time.sleep(1.0)
    lock.release()
    return False


def _read_final_status(profile: str) -> Optional[dict[str, Any]]:
    from hermes_cli.gateway_restart_state import read_status
    return read_status(profile)


# ---------------------------------------------------------------------------
# Worker spawning
# ---------------------------------------------------------------------------

def _spawn_worker(intent: dict[str, Any], profile: str) -> int:
    """Spawn the restart worker as a fully detached process.

    Returns the worker PID.

    The worker does NOT inherit _HERMES_GATEWAY=1.
    """
    import subprocess
    from hermes_cli._subprocess_compat import windows_detach_popen_kwargs
    from hermes_cli.gateway_windows import _build_gateway_argv, _derive_venv_pythonw

    python_exe = sys.executable
    pythonw = _derive_venv_pythonw(python_exe) or python_exe

    # Build worker command
    worker_module = "hermes_cli.gateway_windows_restart_worker"
    argv = [pythonw, "-m", worker_module, "--intent", json.dumps(intent)]

    # Clean environment: remove _HERMES_GATEWAY
    env = os.environ.copy()
    env.pop("_HERMES_GATEWAY", None)
    env["HERMES_GATEWAY_RESTART_WORKER"] = "1"

    # Working directory
    from hermes_cli.config import get_hermes_home
    cwd = str(Path(get_hermes_home()).resolve())

    # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
    # + CREATE_BREAKAWAY_FROM_JOB
    flags = 0x00000008 | 0x00000200 | 0x08000000 | 0x01000000

    try:
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            creationflags=flags,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        # Retry without CREATE_BREAKAWAY_FROM_JOB
        flags_no_breakaway = flags & ~0x01000000
        proc = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            creationflags=flags_no_breakaway,
            close_fds=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return proc.pid
