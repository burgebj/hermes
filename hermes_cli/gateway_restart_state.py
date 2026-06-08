"""Gateway restart state management — intent, locks, status, and JSONL logging.

Provides the durable state layer for the Windows transactional restart
coordinator.  Each restart transaction gets its own request-scoped directory
under ``{HERMES_HOME}/run/gateway-restart/{profile}/{request_id}/``.

Design invariants:
- Profile-level ``active.lock`` prevents concurrent coordinators.
- Per-request directories eliminate TOCTOU on intent/status cleanup.
- Lease files use ``O_EXCL`` for atomic one-time-only worker claim.
- Intent state transitions require request_id + nonce verification.
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

_SCHEMA_VERSION = 1
_INTENT_MAX_BYTES = 4096
_DEFAULT_TTL_S = 300  # 5 minutes
_LOCK_TTL_S = 120     # 2 minutes


# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------
# run/gateway-restart/
#   {profile}/
#     active.lock                    ← profile-level lock (prevents concurrent coordinators)
#     {request_id}/
#       intent.json                  ← restart intent (signed with nonce)
#       status.json                  ← current state
#       lease.lock                   ← O_EXCL worker lease (atomic claim)
# ---------------------------------------------------------------------------

def _get_restart_base() -> Path:
    """Return ``{HERMES_HOME}/run/gateway-restart/``, creating if needed."""
    from hermes_cli.config import get_hermes_home
    base = Path(get_hermes_home()) / "run" / "gateway-restart"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _get_profile_dir(profile: str = "default") -> Path:
    """Return ``{HERMES_HOME}/run/gateway-restart/{profile}/``."""
    d = _get_restart_base() / profile
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_request_dir(profile: str, request_id: str) -> Path:
    """Return ``{HERMES_HOME}/run/gateway-restart/{profile}/{request_id}/``."""
    d = _get_profile_dir(profile) / request_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_logs_dir() -> Path:
    from hermes_cli.config import get_hermes_home
    logs_dir = Path(get_hermes_home()) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


def intent_path(profile: str = "default", request_id: str = "") -> Path:
    """Path to intent file.  If request_id given, uses per-request dir."""
    if request_id:
        return _get_request_dir(profile, request_id) / "intent.json"
    return _get_profile_dir(profile) / "active-intent.json"


def lock_path(profile: str = "default") -> Path:
    """Path to profile-level active lock."""
    return _get_profile_dir(profile) / "active.lock"


def lease_path(profile: str, request_id: str) -> Path:
    """Path to request-scoped lease file (O_EXCL atomic claim)."""
    return _get_request_dir(profile, request_id) / "lease.lock"


def status_path(profile: str = "default", request_id: str = "") -> Path:
    """Path to status file.  If request_id given, uses per-request dir."""
    if request_id:
        return _get_request_dir(profile, request_id) / "status.json"
    return _get_profile_dir(profile) / "active-status.json"


def request_dir_path(profile: str, request_id: str) -> Path:
    """Public accessor for the request directory."""
    return _get_request_dir(profile, request_id)


def jsonl_log_path() -> Path:
    return _get_logs_dir() / "gateway-restart.jsonl"


# ---------------------------------------------------------------------------
# Intent
# ---------------------------------------------------------------------------

def create_intent(
    *,
    request_id: str | None = None,
    profile: str = "default",
    hermes_home: str | None = None,
    target_pid: int = 0,
    task_name: str = "",
    origin: str = "external-cli",
    ttl_s: int = _DEFAULT_TTL_S,
) -> dict[str, Any]:
    """Create and atomically write a restart intent.  Returns the intent dict.

    Intent is written to the per-request directory.
    """
    from hermes_cli.config import get_hermes_home
    rid = request_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    intent = {
        "schema_version": _SCHEMA_VERSION,
        "request_id": rid,
        "nonce": secrets.token_urlsafe(32),
        "profile": profile,
        "hermes_home": hermes_home or str(Path(get_hermes_home()).resolve()),
        "target_pid": target_pid,
        "task_name": task_name,
        "origin": origin,
        "created_at": now.isoformat(),
        "expires_at": now.timestamp() + ttl_s,
        "state": "scheduled",
    }
    _atomic_write_json(intent_path(profile, rid), intent)
    return intent


def read_intent(profile: str = "default", request_id: str = "") -> Optional[dict[str, Any]]:
    """Read and validate the intent file.  Returns None if missing/expired/malformed."""
    path = intent_path(profile, request_id)
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
    if data.get("schema_version") != _SCHEMA_VERSION:
        return None
    expires = data.get("expires_at", 0)
    if isinstance(expires, (int, float)) and time.time() > expires:
        return None
    for key in ("request_id", "nonce", "profile", "hermes_home", "target_pid"):
        if key not in data:
            return None
    return data


def read_intent_by_profile(profile: str = "default") -> Optional[dict[str, Any]]:
    """Read intent from the profile-level fallback path (backward compat)."""
    return read_intent(profile, request_id="")


def validate_intent_nonce(intent: dict[str, Any], nonce: str) -> bool:
    """Constant-time nonce comparison."""
    expected = intent.get("nonce", "")
    if not expected or not nonce:
        return False
    return secrets.compare_digest(expected, nonce)


def update_intent_state(profile: str, request_id: str, state: str,
                        expected_state: str = "") -> bool:
    """Update intent state with optional expected_state guard.

    P0-3: Only updates if current state matches expected_state (when provided).
    Returns True on success.
    """
    path = intent_path(profile, request_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        if expected_state and data.get("state") != expected_state:
            return False
        data["state"] = state
        _atomic_write_json(path, data)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def release_lease(profile: str, request_id: str,
                  owner_token: str = "", worker_pid: int = 0) -> bool:
    """Release only the request-scoped lease file, verifying ownership.

    P0-3: Only the lease owner (matching owner_token and worker_pid)
    can release the lease.  Returns True if lease was released.
    """
    if not request_id:
        return False
    lp = lease_path(profile, request_id)
    if not lp.exists():
        return False
    try:
        data = json.loads(lp.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        if owner_token and data.get("owner_token") != owner_token:
            return False
        if worker_pid and data.get("worker_pid") != worker_pid:
            return False
        lp.unlink(missing_ok=True)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def sanitize_intent(profile: str, request_id: str,
                    expected_nonce: str = "", owner_token: str = "") -> bool:
    """Clear sensitive fields from intent, verifying ownership.

    P0-3: Only clears nonce if expected_nonce matches (or is empty).
    Returns True on success.
    """
    if not request_id:
        return False
    ip = intent_path(profile, request_id)
    try:
        data = json.loads(ip.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        if expected_nonce and not secrets.compare_digest(
                data.get("nonce", ""), expected_nonce):
            return False
        data["nonce"] = ""
        _atomic_write_json(ip, data)
        return True
    except (OSError, json.JSONDecodeError):
        return False


def gc_expired_request_dirs(profile: str = "default",
                            max_age_s: int = 3600,
                            active_request_id: str = "") -> int:
    """Garbage-collect expired request directories.

    P1-3: Skips directories that are still running or have active leases.
    Never deletes the active_request_id directory.
    """
    profile_dir = _get_profile_dir(profile)
    now = time.time()
    removed = 0
    _TERMINAL_STATES = frozenset({"completed", "failed"})
    try:
        for d in profile_dir.iterdir():
            if not d.is_dir():
                continue
            # Never delete the active request
            if d.name == active_request_id:
                continue
            # Skip if lease still exists (worker still running)
            if (d / "lease.lock").exists():
                continue
            sp = d / "status.json"
            if not sp.exists():
                # No status = stale/orphaned, check age by directory mtime
                try:
                    age = now - d.stat().st_mtime
                    if age > max_age_s:
                        import shutil
                        shutil.rmtree(d, ignore_errors=True)
                        removed += 1
                except OSError:
                    continue
                continue
            try:
                data = json.loads(sp.read_text(encoding="utf-8"))
                state = data.get("state", "")
                # Only GC terminal states
                if state not in _TERMINAL_STATES:
                    continue
                ts_str = data.get("updated_at", "")
                if ts_str:
                    from datetime import datetime as _dt
                    ts = _dt.fromisoformat(ts_str).timestamp()
                    if now - ts > max_age_s:
                        import shutil
                        shutil.rmtree(d, ignore_errors=True)
                        removed += 1
            except (OSError, json.JSONDecodeError, ValueError):
                continue
    except OSError:
        pass
    return removed


def cleanup_intent(profile: str = "default", request_id: str = "") -> None:
    """Remove the entire request directory (intent + status + lease).

    DEPRECATED for Worker use — Workers should use release_lease() +
    sanitize_intent() to preserve terminal status for the Coordinator.

    Only use this for:
    - Coordinator crash recovery (invalid request cleanup)
    - _fail_closed() on validation failures
    """
    if not request_id:
        return
    try:
        d = _get_request_dir(profile, request_id)
        if d.exists():
            import shutil
            shutil.rmtree(d, ignore_errors=True)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Profile lock (prevents concurrent coordinators)
# ---------------------------------------------------------------------------

class RestartLock:
    """Profile-scoped restart lock with ownership, TTL, and stale recovery.

    Lock is created with ``O_EXCL`` on the final path.  Stores owner_token,
    owner_pid, worker_pid, and claim_deadline for stale recovery.

    P1-1: If the lock records a worker_pid and claim_deadline, and both
    conditions are met (deadline expired + worker PID dead), the lock
    can be safely reclaimed even if the coordinator PID is still alive.

    P1-4: No coalesce — same request_id does NOT reuse an existing lock.
    """

    _LOCK_SCHEMA_VERSION = 1

    def __init__(self, profile: str = "default"):
        self._path = lock_path(profile)
        self._owner_token: str = ""
        self._owner_request_id: str = ""

    @property
    def owner_token(self) -> str:
        """Expose owner_token for handoff verification."""
        return self._owner_token

    def try_acquire(self, request_id: str, ttl_s: int = _LOCK_TTL_S,
                    worker_pid: int = 0) -> bool:
        """Try to acquire the lock.  Returns True on success.

        No coalesce — each request_id gets a fresh lock.
        Stale recovery considers worker_pid + claim_deadline (P1-1).
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)

        existing = self._read_lock()
        if existing:
            age = time.time() - existing.get("created_at", 0)

            # P1-1: Check claim_deadline-based recovery
            phase = existing.get("phase", "")
            claim_deadline = existing.get("claim_deadline", 0)
            existing_worker_pid = existing.get("worker_pid", 0)

            if phase == "awaiting_claim" and claim_deadline > 0 and time.time() > claim_deadline:
                # Claim deadline expired — check if worker is dead
                if existing_worker_pid > 0 and not _pid_exists(existing_worker_pid):
                    # Worker dead and never claimed — safe to reclaim
                    self._force_release(expected=existing)
                elif existing_worker_pid <= 0:
                    # No worker PID recorded — safe to reclaim
                    self._force_release(expected=existing)
                else:
                    # Worker still alive — wait
                    return False
            elif age > ttl_s:
                # Standard TTL expiry — verify owner is dead
                owner_pid = existing.get("owner_pid", 0)
                if owner_pid > 0 and _pid_exists(owner_pid):
                    return False
                self._force_release(expected=existing)
            else:
                # Active lock by another request
                return False

        # Generate owner token for this acquisition
        self._owner_token = secrets.token_urlsafe(32)
        self._owner_request_id = request_id

        lock_data = {
            "schema_version": self._LOCK_SCHEMA_VERSION,
            "request_id": request_id,
            "owner_token": self._owner_token,
            "owner_pid": os.getpid(),
            "worker_pid": worker_pid,
            "claim_deadline": time.time() + 30 if worker_pid else 0,
            "phase": "awaiting_claim" if worker_pid else "acquired",
            "profile": self._profile(),
            "created_at": time.time(),
            "expires_at": time.time() + ttl_s,
        }
        try:
            fd = os.open(str(self._path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(lock_data, f)
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError:
            return False
        except OSError:
            return False

        return True

    def release(self) -> None:
        """Release the lock ONLY if we are the owner."""
        existing = self._read_lock()
        if not existing:
            return
        if (existing.get("owner_token") != self._owner_token
                or existing.get("request_id") != self._owner_request_id):
            return
        try:
            self._path.unlink(missing_ok=True)
        except OSError:
            pass

    def mark_phase(self, phase: str) -> None:
        """Update the lock's phase field (must be owner)."""
        existing = self._read_lock()
        if not existing:
            return
        if existing.get("owner_token") != self._owner_token:
            return
        existing["phase"] = phase
        try:
            _atomic_write_json(self._path, existing)
        except OSError:
            pass

    def mark_worker_spawned(self, worker_pid: int,
                            claim_deadline: float) -> bool:
        """Record that a worker has been spawned.

        P0-3: Atomically updates phase, worker_pid, and claim_deadline.
        This enables claim-timeout stale recovery even if the coordinator
        process is still alive (the coordinator PID check in TTL recovery
        would block because the coordinator is alive, but the worker may
        have silently died).

        Returns True on success.
        """
        existing = self._read_lock()
        if not existing:
            return False
        if existing.get("owner_token") != self._owner_token:
            return False
        existing["phase"] = "awaiting_claim"
        existing["worker_pid"] = worker_pid
        existing["claim_deadline"] = claim_deadline
        try:
            _atomic_write_json(self._path, existing)
            return True
        except OSError:
            return False

    def handoff_active_lock(
        self,
        request_id: str,
        coordinator_owner_token: str,
        worker_pid: int,
        lease_owner_token: str,
    ) -> bool:
        """Transfer active.lock ownership from Coordinator to Worker.

        P0-1 + P0-2: After the Worker claims the lease, the Coordinator
        hands off the active.lock so the Worker can release it when done.
        This prevents the Coordinator from releasing the lock while the
        Worker is still running drain/stop/start/verify.

        Validates:
        - active.lock.request_id matches
        - Coordinator's owner_token matches
        - Lease file exists with matching worker_pid and lease_owner_token

        On success, active.lock.owner_token = lease_owner_token,
        active.lock.owner_pid = worker_pid, phase = "running".

        Returns True on success.
        """
        existing = self._read_lock()
        if not existing:
            return False
        if existing.get("request_id") != request_id:
            return False
        if existing.get("owner_token") != coordinator_owner_token:
            return False

        # Verify lease exists with matching owner_token and worker_pid
        lp = lease_path(self._profile(), request_id)
        if not lp.exists():
            return False
        try:
            lease_data = json.loads(lp.read_text(encoding="utf-8"))
            if not isinstance(lease_data, dict):
                return False
            if lease_data.get("owner_token") != lease_owner_token:
                return False
            if lease_data.get("worker_pid") != worker_pid:
                return False
        except (OSError, json.JSONDecodeError):
            return False

        # Transfer ownership
        existing["owner_token"] = lease_owner_token
        existing["owner_pid"] = worker_pid
        existing["phase"] = "running"
        try:
            _atomic_write_json(self._path, existing)
            # Update our in-memory token so release() works
            self._owner_token = lease_owner_token
            return True
        except OSError:
            return False

    def claim_lease(self, request_id: str, nonce: str,
                    expected_state: str = "scheduled") -> bool:
        """Atomically claim the lease for a request using O_EXCL.

        P0-1: Uses independent lease file with O_EXCL — truly one-time-only.
        P0-3: After successful claim, transitions intent state from
        expected_state to "claimed" with request_id + nonce verification.

        Returns True on success (caller is the lease winner).
        """
        lp = lease_path(self._profile(), request_id)

        # Verify intent exists and is in expected state
        ip = intent_path(self._profile(), request_id)
        try:
            intent_data = json.loads(ip.read_text(encoding="utf-8"))
            if not isinstance(intent_data, dict):
                return False
            if intent_data.get("request_id") != request_id:
                return False
            if not validate_intent_nonce(intent_data, nonce):
                return False
            if expected_state and intent_data.get("state") != expected_state:
                return False
        except (OSError, json.JSONDecodeError):
            return False

        # Atomic lease claim via O_EXCL
        lease_data = {
            "request_id": request_id,
            "owner_token": secrets.token_urlsafe(32),
            "worker_pid": os.getpid(),
            "claimed_at": time.time(),
        }
        try:
            fd = os.open(str(lp), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(lease_data, f)
                f.flush()
                os.fsync(f.fileno())
        except FileExistsError:
            return False  # Another worker already claimed
        except OSError:
            return False

        # P0-3: Update intent state to "claimed" (only winner does this)
        # P1-2: If intent state update fails, rollback the lease
        self._owner_token = lease_data["owner_token"]
        self._owner_request_id = request_id
        if not update_intent_state(self._profile(), request_id, "claimed",
                                   expected_state=expected_state):
            # Rollback: delete the lease we just created
            try:
                lp.unlink(missing_ok=True)
            except OSError:
                pass
            self._owner_token = ""
            self._owner_request_id = ""
            return False
        return True

    def release_lease(self, profile: str, request_id: str) -> None:
        """Release the request-scoped lease file."""
        try:
            lp = lease_path(profile, request_id)
            lp.unlink(missing_ok=True)
        except OSError:
            pass

    def _profile(self) -> str:
        """Extract profile name from lock path."""
        return self._path.parent.name

    def _read_lock(self) -> Optional[dict[str, Any]]:
        if not self._path.exists():
            return None
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else None
        except (OSError, json.JSONDecodeError):
            return None

    def _force_release(self, expected: dict[str, Any] | None = None) -> None:
        """Force-release an expired lock whose owner is confirmed dead.

        Re-reads and compares before deleting (TOCTOU protection).
        """
        if expected:
            current = self._read_lock()
            if not current:
                return
            if (current.get("request_id") != expected.get("request_id")
                    or current.get("created_at") != expected.get("created_at")
                    or current.get("owner_token") != expected.get("owner_token")):
                return
        try:
            self._path.unlink(missing_ok=True)
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

_VALID_STATES = frozenset({
    "scheduled",
    "claimed",
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


def write_status(profile: str, state: str, request_id: str = "",
                 **extra: Any) -> None:
    """Write the status file to the per-request directory."""
    if state not in _VALID_STATES:
        raise ValueError(f"Invalid state: {state!r}")
    payload = {
        "state": state,
        "request_id": request_id,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        **extra,
    }
    _atomic_write_json(status_path(profile, request_id), payload)


def read_status(profile: str = "default", request_id: str = "") -> Optional[dict[str, Any]]:
    path = status_path(profile, request_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def read_latest_status(profile: str = "default") -> Optional[dict[str, Any]]:
    """Read the most recent status for this profile.

    Scans per-request directories for the latest status.json.
    """
    profile_dir = _get_profile_dir(profile)
    best = None
    best_time = ""
    try:
        for d in profile_dir.iterdir():
            if not d.is_dir():
                continue
            sp = d / "status.json"
            if not sp.exists():
                continue
            try:
                data = json.loads(sp.read_text(encoding="utf-8"))
                ts = data.get("updated_at", "")
                if ts > best_time:
                    best_time = ts
                    best = data
            except (OSError, json.JSONDecodeError):
                continue
    except OSError:
        pass
    return best


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
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except OSError:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def _pid_exists(pid: int) -> bool:
    """Cross-platform PID existence check (best-effort)."""
    if pid <= 0:
        return False
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
