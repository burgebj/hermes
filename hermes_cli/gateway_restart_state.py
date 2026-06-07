"""Gateway restart state management — intent, locks, status, and JSONL logging.

Provides the durable state layer for the Windows transactional restart
coordinator.  All paths are profile-scoped under ``{HERMES_HOME}/run/``.

Design invariants:
- Intent files use atomic write (tmpfile + rename).
- Profile locks use OS-level file locking with TTL.
- Status files are JSON, overwritten on each state transition.
- JSONL log is append-only, one record per state change.
"""

from __future__ import annotations

import json
import os
import secrets
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

_IS_WINDOWS = sys.platform == "win32"
_SCHEMA_VERSION = 1
_INTENT_MAX_BYTES = 4096
_DEFAULT_TTL_S = 300  # 5 minutes
_LOCK_TTL_S = 120     # 2 minutes
_COALESCE_WINDOW_S = 5  # collapse restarts within this window


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _get_run_dir() -> Path:
    """Return ``{HERMES_HOME}/run/``, creating it if needed."""
    from hermes_cli.config import get_hermes_home
    run_dir = Path(get_hermes_home()) / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def _get_logs_dir() -> Path:
    from hermes_cli.config import get_hermes_home
    logs_dir = Path(get_hermes_home()) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def intent_path(profile: str = "default") -> Path:
    return _get_run_dir() / f"gateway-restart-{profile}-intent.json"


def lock_path(profile: str = "default") -> Path:
    return _get_run_dir() / f"gateway-restart-{profile}.lock"


def status_path(profile: str = "default") -> Path:
    return _get_run_dir() / f"gateway-restart-{profile}-status.json"


def jsonl_log_path() -> Path:
    return _get_logs_dir() / "gateway-restart.jsonl"


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

def create_intent(
    *,
    profile: str = "default",
    hermes_home: str | None = None,
    target_pid: int = 0,
    task_name: str = "",
    origin: str = "external-cli",
    ttl_s: int = _DEFAULT_TTL_S,
) -> dict[str, Any]:
    """Create and atomically write a restart intent.  Returns the intent dict."""
    now = datetime.now(timezone.utc)
    intent = {
        "schema_version": _SCHEMA_VERSION,
        "request_id": str(uuid.uuid4()),
        "nonce": secrets.token_urlsafe(32),
        "profile": profile,
        "hermes_home": hermes_home or str(Path.home() / ".hermes"),
        "target_pid": target_pid,
        "task_name": task_name,
        "origin": origin,
        "created_at": now.isoformat(),
        "expires_at": now.timestamp() + ttl_s,
        "state": "scheduled",
    }
    _atomic_write_json(intent_path(profile), intent)
    return intent


def read_intent(profile: str = "default") -> Optional[dict[str, Any]]:
    """Read and validate the intent file.  Returns None if missing/expired/malformed."""
    path = intent_path(profile)
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8").strip()
        if len(raw.encode("utf-8")) > _INTENT_MAX_BYTES:
            return None
        data = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    # Schema check
    if data.get("schema_version") != _SCHEMA_VERSION:
        return None
    # TTL check
    expires = data.get("expires_at", 0)
    if isinstance(expires, (int, float)) and time.time() > expires:
        cleanup_intent(profile)
        return None
    # Required fields
    for key in ("request_id", "nonce", "profile", "hermes_home", "target_pid"):
        if key not in data:
            return None
    return data


def validate_intent_nonce(intent: dict[str, Any], nonce: str) -> bool:
    """Constant-time nonce comparison."""
    expected = intent.get("nonce", "")
    if not expected or not nonce:
        return False
    return secrets.compare_digest(expected, nonce)


def update_intent_state(profile: str, state: str) -> None:
    """Update just the state field of an existing intent."""
    path = intent_path(profile)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["state"] = state
        _atomic_write_json(path, data)
    except (OSError, json.JSONDecodeError):
        pass


def cleanup_intent(profile: str = "default") -> None:
    """Remove the intent file."""
    try:
        intent_path(profile).unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Profile lock (atomic creation + TTL + coalesce)
# ---------------------------------------------------------------------------

class RestartLock:
    """Profile-scoped restart lock with TTL and coalesce support.

    Usage::

        lock = RestartLock(profile)
        if lock.try_acquire(request_id):
            # we won the race
            ...
            lock.release()
    """

    def __init__(self, profile: str = "default"):
        self._path = lock_path(profile)
        self._handle = None

    def try_acquire(self, request_id: str, ttl_s: int = _LOCK_TTL_S) -> bool:
        """Try to acquire the lock.  Returns True on success.

        If the lock file exists but is expired (TTL), it is force-released first.
        If the lock file exists and the request_id matches (within coalesce
        window), returns True (coalesce).
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Check existing lock
        existing = self._read_lock()
        if existing:
            age = time.time() - existing.get("acquired_at", 0)
            if age > ttl_s:
                # Expired — force release
                self._force_release()
            elif existing.get("request_id") == request_id:
                # Coalesce — same request
                return True
            else:
                # Active lock by another request
                return False

        # Atomic create
        lock_data = {
            "request_id": request_id,
            "pid": os.getpid(),
            "acquired_at": time.time(),
        }
        tmp = self._path.with_suffix(".tmp")
        try:
            fd = os.open(str(tmp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(lock_data, f)
                f.flush()
                os.fsync(f.fileno())
            tmp.replace(self._path)
        except FileExistsError:
            # Race lost
            return False
        except OSError:
            return False

        # Verify we still hold it (no race between create and replace)
        verify = self._read_lock()
        if verify and verify.get("request_id") == request_id:
            return self._acquire_os_lock()
        return False

    def release(self) -> None:
        """Release the lock."""
        self._release_os_lock()
        try:
            self._path.unlink(missing_ok=True)
        except OSError:
            pass

    def _read_lock(self) -> Optional[dict[str, Any]]:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def _force_release(self) -> None:
        self._release_os_lock()
        try:
            self._path.unlink(missing_ok=True)
        except OSError:
            pass

    def _acquire_os_lock(self) -> bool:
        """Best-effort OS file lock on the lock file."""
        try:
            self._handle = open(str(self._path), "r+", encoding="utf-8")
            if _IS_WINDOWS:
                self._handle.seek(0, os.SEEK_END)
                if self._handle.tell() == 0:
                    self._handle.write("\n")
                    self._handle.flush()
                self._handle.seek(1024 * 1024)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except (BlockingIOError, OSError):
            if self._handle:
                self._handle.close()
                self._handle = None
            return True  # Lock file created, OS lock is best-effort

    def _release_os_lock(self) -> None:
        if self._handle is None:
            return
        try:
            if _IS_WINDOWS:
                self._handle.seek(1024 * 1024)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            self._handle.close()
        except OSError:
            pass
        self._handle = None


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

_VALID_STATES = frozenset({
    "scheduled",
    "preflight_ok",
    "draining",
    "stopping",
    "waiting_pid_exit",
    "waiting_port_release",
    "starting_task",
    "starting_direct_fallback",
    "verifying",
    "completed",
    "failed",
})


def write_status(profile: str, state: str, **extra: Any) -> None:
    """Write the status file.  Only overwrites, does not append."""
    if state not in _VALID_STATES:
        raise ValueError(f"Invalid state: {state!r}")
    payload = {
        "state": state,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    _atomic_write_json(status_path(profile), payload)


def read_status(profile: str = "default") -> Optional[dict[str, Any]]:
    path = status_path(profile)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def cleanup_status(profile: str = "default") -> None:
    try:
        status_path(profile).unlink(missing_ok=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# JSONL log
# ---------------------------------------------------------------------------

def append_restart_log(
    *,
    request_id: str = "",
    profile: str = "default",
    old_pid: int = 0,
    new_pid: int = 0,
    origin: str = "",
    state: str = "",
    launcher: str = "",
    reason: str = "",
    error: str = "",
    listener_pid: int = 0,
    port: int = 0,
) -> None:
    """Append one record to the JSONL restart log."""
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "profile": profile,
        "old_pid": old_pid,
        "new_pid": new_pid,
        "origin": origin,
        "state": state,
        "launcher": launcher,
        "reason": reason,
        "error": error,
        "listener_pid": listener_pid,
        "port": port,
    }
    path = jsonl_log_path()
    try:
        with open(str(path), "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            f.flush()
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically (tmpfile + rename)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise
