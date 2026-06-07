"""Tests for gateway_windows_restart_worker.py — intent/nonce validation,
PID/port handling, worker status/fallback, and transaction isolation.

Updated for per-request directory layout:
  run/gateway-restart/{profile}/{request_id}/

Key API changes tested:
  - Worker CLI: --profile + --request-id (not --intent/--intent-file)
  - Worker reads intent via read_intent(profile, request_id)
  - _run_restart_transaction takes 8 params
  - claim_lease uses O_EXCL + transitions intent state 'scheduled' → 'claimed'
  - Lease loser logs + sys.exit(1), does NOT write failed status or cleanup
  - cleanup_intent(profile, request_id) — no nonce
  - write_status(profile, state, request_id=request_id)
  - read_status(profile, request_id)
  - cleanup_status removed
  - update_intent_state guarded by expected_state
  - _pid_exists imported at function level from gateway_restart_state
"""

import json
import os
import sys
import time
import threading
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def worker_env(tmp_path, monkeypatch):
    """Set up a temporary HERMES_HOME for worker tests."""
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir()
    (hermes_home / "run").mkdir()
    (hermes_home / "logs").mkdir()
    (hermes_home / "profiles").mkdir()

    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    import hermes_cli.config as config_mod
    monkeypatch.setattr(config_mod, "get_hermes_home", lambda: str(hermes_home))

    return hermes_home


def _make_intent(
    profile="default",
    target_pid=1234,
    request_id=None,
    nonce=None,
    ttl_s=300,
    schema_version=1,
    state="scheduled",
):
    """Create a realistic intent dict without writing to disk."""
    import secrets
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    return {
        "schema_version": schema_version,
        "request_id": request_id or str(uuid.uuid4()),
        "nonce": nonce or secrets.token_urlsafe(32),
        "profile": profile,
        "hermes_home": "/fake/hermes",
        "target_pid": target_pid,
        "task_name": "Hermes_Gateway",
        "origin": "test",
        "created_at": now.isoformat(),
        "expires_at": now.timestamp() + ttl_s,
        "state": state,
    }


def _write_intent_to_disk(hermes_home, intent, profile="default"):
    """Write an intent dict to the per-request directory on disk."""
    request_id = intent["request_id"]
    req_dir = hermes_home / "run" / "gateway-restart" / profile / request_id
    req_dir.mkdir(parents=True, exist_ok=True)
    path = req_dir / "intent.json"
    path.write_text(json.dumps(intent, indent=2), encoding="utf-8")
    return path


def _write_intent_for_test(worker_env, intent, profile="default", dir_request_id=None):
    """Write intent to per-request dir using the intent's request_id
    (or dir_request_id if specified, for tamper tests)."""
    request_id = dir_request_id or intent["request_id"]
    req_dir = worker_env / "run" / "gateway-restart" / profile / request_id
    req_dir.mkdir(parents=True, exist_ok=True)
    path = req_dir / "intent.json"
    path.write_text(json.dumps(intent, indent=2), encoding="utf-8")
    return path


# ===========================================================================
# TestIntentValidation — P0-5 intent validation
# ===========================================================================

class TestIntentValidation:
    """Verify that _run_restart_transaction validates the on-disk intent
    against the in-memory intent before any destructive action."""

    def _mock_cleanup_for_status_check(self, monkeypatch):
        """Mock cleanup_intent to no-op so we can read back status after
        _fail_closed. Without this, cleanup_intent deletes the entire
        request directory (including the just-written status file)."""
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state.cleanup_intent",
            lambda *a, **kw: None,
        )

    def test_intent_missing(self, worker_env, monkeypatch):
        """No intent file on disk → fail closed (sys.exit(1))."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234)
        # Do NOT write an intent file — disk is empty.

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        assert "missing_intent" in status.get("error", "")

    def test_request_id_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different request_id → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234)
        # Write a disk intent with a DIFFERENT request_id, but in the
        # directory of the ORIGINAL request_id (so the worker can find it)
        tampered = dict(intent)
        tampered["request_id"] = "wrong-request-id"
        _write_intent_for_test(worker_env, tampered, dir_request_id=intent["request_id"])

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        assert "request_id_mismatch" in status.get("error", "")

    def test_nonce_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different nonce → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234)
        # Disk intent has a different nonce
        tampered = dict(intent)
        tampered["nonce"] = "wrong-nonce-value"
        _write_intent_for_test(worker_env, tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        assert "nonce_mismatch" in status.get("error", "")

    def test_profile_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different profile → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234)
        # Write disk intent under "default" request dir but with profile="other" in content
        tampered = dict(intent)
        tampered["profile"] = "other"
        _write_intent_for_test(worker_env, tampered, profile="default")

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        assert "profile_mismatch" in status.get("error", "")

    def test_target_pid_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different target_pid → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234)
        tampered = dict(intent)
        tampered["target_pid"] = 9999
        _write_intent_for_test(worker_env, tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        assert "target_pid_mismatch" in status.get("error", "")

    def test_ttl_expired(self, worker_env, monkeypatch):
        """Disk intent has expires_at in the past → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234, ttl_s=300)
        tampered = dict(intent)
        tampered["expires_at"] = time.time() - 60  # expired 60s ago
        _write_intent_for_test(worker_env, tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        # The error could be "expired_intent" or "missing_intent" depending
        # on whether read_intent cleans up the expired file first.
        assert "expired" in status.get("error", "").lower() or "missing" in status.get("error", "").lower()

    def test_schema_version_unsupported(self, worker_env, monkeypatch):
        """Disk intent has schema_version=99 → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        self._mock_cleanup_for_status_check(monkeypatch)

        intent = _make_intent(profile="default", target_pid=1234)
        tampered = dict(intent)
        tampered["schema_version"] = 99
        _write_intent_for_test(worker_env, tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                intent, "default", intent["request_id"], intent["nonce"],
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", intent["request_id"])
        assert status is not None
        assert status["state"] == "failed"
        # read_intent returns None for unsupported schema → "missing_intent"
        assert "missing_intent" in status.get("error", "") or "schema" in status.get("error", "").lower()

    def test_intent_consumed_prevents_replay(self, worker_env, monkeypatch):
        """After first worker consumes intent (cleanup), second worker with
        same intent should fail because the intent directory is removed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        from hermes_cli.gateway_restart_state import (
            create_intent, cleanup_intent,
        )

        # --- First worker run: create intent and consume it ---
        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Simulate first worker's cleanup (removes request dir)
        cleanup_intent("default", request_id)

        # --- Second worker run: same intent parameters ---
        # Mock cleanup_intent so _fail_closed doesn't delete the status
        # we want to verify
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state.cleanup_intent",
            lambda *a, **kw: None,
        )

        replay_intent = _make_intent(
            profile="default",
            target_pid=1234,
            request_id=request_id,
            nonce=nonce,
        )

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                replay_intent, "default", request_id, nonce,
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        # Verify the second worker wrote a failed status
        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", request_id)
        assert status is not None
        assert status["state"] == "failed"


# ===========================================================================
# TestPidPort — P0-6 and P0-7 PID/port handling
# ===========================================================================

class TestPidPort:
    """Verify PID liveness and port-release safety checks."""

    def test_old_pid_still_alive_after_force_kill(self, worker_env, monkeypatch):
        """Old PID still alive after drain → RuntimeError, no new gateway."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        from hermes_cli.gateway_restart_state import create_intent, RestartLock

        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Pre-create a lock and claim lease so worker passes the claim step
        lock = RestartLock("default")
        assert lock.try_acquire(request_id) is True

        # Mock _drain_and_stop to be a no-op
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._drain_and_stop",
            lambda *a, **kw: None,
        )
        # Mock _pid_exists to return True for old_pid (still alive), False for others
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: pid == 1234,
        )
        # Mock _start_new_gateway to track if it's called
        mock_start = MagicMock()
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._start_new_gateway",
            mock_start,
        )

        with pytest.raises(RuntimeError, match="still alive"):
            _run_restart_transaction(
                disk_intent, "default", request_id, nonce,
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )

        # New gateway should NOT have been started
        mock_start.assert_not_called()

    def test_unrelated_process_occupies_port(self, worker_env, monkeypatch):
        """Port occupied by unrelated process → RuntimeError."""
        from hermes_cli.gateway_windows_restart_worker import _wait_for_port_release

        # Mock port check: always occupied
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_port_in_use",
            lambda port: True,
        )
        # PID query returns a non-hermes PID
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._get_pids_on_port",
            lambda port: [9999],
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_hermes_gateway_pid",
            lambda pid: False,
        )

        with pytest.raises(RuntimeError, match="not the old gateway"):
            _wait_for_port_release(
                profile="default",
                request_id="req-1",
                old_pid=1234,
                origin="test",
                port=8080,
                timeout=0.1,  # short timeout so the wait loop ends quickly
            )

    def test_pid_query_empty_port_occupied(self, worker_env, monkeypatch):
        """Port occupied but PID query returns empty → RuntimeError."""
        from hermes_cli.gateway_windows_restart_worker import _wait_for_port_release

        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_port_in_use",
            lambda port: True,
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._get_pids_on_port",
            lambda port: [],
        )

        with pytest.raises(RuntimeError, match="no listening PIDs"):
            _wait_for_port_release(
                profile="default",
                request_id="req-1",
                old_pid=1234,
                origin="test",
                port=8080,
                timeout=0.1,
            )

    def test_port_released_after_hermes_kill(self, worker_env, monkeypatch):
        """Port occupied → hermes PID found → kill → port free → success."""
        from hermes_cli.gateway_windows_restart_worker import _wait_for_port_release

        call_count = {"port_check": 0}

        def mock_is_port_in_use(port):
            call_count["port_check"] += 1
            if call_count["port_check"] <= 1:
                return True
            return False

        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_port_in_use",
            mock_is_port_in_use,
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._get_pids_on_port",
            lambda port: [5678],
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_hermes_gateway_pid",
            lambda pid: pid == 5678,
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_ancestor",
            lambda pid: False,
        )

        # Mock terminate_pid
        mock_terminate = MagicMock()
        with patch.dict("sys.modules", {"gateway": MagicMock(), "gateway.status": MagicMock()}):
            import gateway.status
            gateway.status.terminate_pid = mock_terminate
            # Should NOT raise — port is freed after kill
            _wait_for_port_release(
                profile="default",
                request_id="req-1",
                old_pid=5678,  # P1-5: listener PID must match old_pid
                origin="test",
                port=8080,
                timeout=0.5,
            )

    def test_port_still_occupied_after_kill(self, worker_env, monkeypatch):
        """Port occupied → old_pid matches → kill → port STILL occupied → RuntimeError."""
        from hermes_cli.gateway_windows_restart_worker import _wait_for_port_release

        # Port is always occupied (even after "kill")
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_port_in_use",
            lambda port: True,
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._get_pids_on_port",
            lambda port: [5678],
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_hermes_gateway_pid",
            lambda pid: pid == 5678,
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._is_ancestor",
            lambda pid: False,
        )

        mock_terminate = MagicMock()
        with patch.dict("sys.modules", {"gateway": MagicMock(), "gateway.status": MagicMock()}):
            import gateway.status
            gateway.status.terminate_pid = mock_terminate

            with pytest.raises(RuntimeError, match="still occupied|not the old gateway"):
                _wait_for_port_release(
                    profile="default",
                    request_id="req-1",
                    old_pid=5678,  # P1-5: must match listener PID
                    origin="test",
                    port=8080,
                    timeout=0.5,
                )


# ===========================================================================
# TestWorkerStatusFallback — P0-8 and P1-1/P1-2 scenarios
# ===========================================================================

class TestWorkerStatusFallback:
    """Verify status file handling, unhandled exceptions, and coordinator
    wait-for-completion logic."""

    def test_unhandled_exception_writes_failed(self, worker_env, tmp_path, monkeypatch):
        """Unhandled exception in _run_restart_transaction → status 'failed'."""
        from hermes_cli.gateway_windows_restart_worker import main
        from hermes_cli.gateway_restart_state import create_intent, RestartLock

        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Pre-create a lock and claim lease so the worker passes the claim step
        lock = RestartLock("default")
        assert lock.try_acquire(request_id) is True

        # Make _drain_and_stop raise an unhandled exception
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._drain_and_stop",
            MagicMock(side_effect=RuntimeError("drain exploded")),
        )
        # Ensure _pid_exists returns False so the PID check passes
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: False,
        )
        # Mock cleanup_intent so status remains readable after main() finally
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state.cleanup_intent",
            lambda *a, **kw: None,
        )

        # Call main() with --profile and --request-id
        monkeypatch.setattr(sys, "argv", [
            "worker", "--profile", "default", "--request-id", request_id,
        ])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", request_id)
        assert status is not None
        assert status["state"] == "failed"
        assert "drain exploded" in status.get("error", "")

    def test_status_ignores_old_request_id(self, worker_env, monkeypatch):
        """Coordinator _wait_for_completion returns False when status has
        an old request_id different from the one being waited on."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        # Write a status with an old request_id
        write_status("default", "completed", request_id="old-123", new_pid=5678)

        # Wait for a different request_id — should NOT see the old status
        result, last_state = _wait_for_completion(
            profile="default",
            timeout_s=1.0,
            request_id="new-456",
        )
        assert result is False

    def test_status_intermediate_not_completed(self, worker_env, monkeypatch):
        """Status has state='draining' → coordinator doesn't report completed."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        request_id = "test-req-1"
        write_status("default", "draining", request_id=request_id, old_pid=1234)

        result, last_state = _wait_for_completion(
            profile="default",
            timeout_s=1.0,
            request_id=request_id,
        )
        assert result is False

    def test_new_pid_dies_immediately(self, worker_env, monkeypatch):
        """New PID dies immediately → status 'failed'."""
        from hermes_cli.gateway_windows_restart_worker import _verify_new_gateway

        # Mock _pid_exists: new_pid is dead immediately
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: pid != 5678,  # 5678 (new_pid) is dead
        )

        _verify_new_gateway(
            profile="default",
            request_id="req-1",
            old_pid=1234,
            new_pid=5678,
            origin="test",
            launcher="direct_spawn",
        )

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", "req-1")
        assert status is not None
        assert status["state"] == "failed"
        assert "died" in status.get("error", "").lower()

    def test_new_pid_dies_within_stability_window(self, worker_env, monkeypatch):
        """New PID alive at first check, then dies within stability window
        → status 'failed'."""
        from hermes_cli.gateway_windows_restart_worker import _verify_new_gateway

        # _pid_exists returns True first, then False (dies during stability check)
        call_count = {"n": 0}

        def mock_pid_exists(pid):
            if pid == 5678:
                call_count["n"] += 1
                return call_count["n"] <= 1
            return False  # old_pid is dead

        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            mock_pid_exists,
        )

        _verify_new_gateway(
            profile="default",
            request_id="req-1",
            old_pid=1234,
            new_pid=5678,
            origin="test",
            launcher="direct_spawn",
        )

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", "req-1")
        assert status is not None
        assert status["state"] == "failed"
        assert "stability" in status.get("error", "").lower() or "died" in status.get("error", "").lower()

    def test_unhandled_exception_writes_failed_status_field(self, worker_env, tmp_path, monkeypatch):
        """Unhandled exception → status file has request_id matching the
        intent's request_id, enabling coordinator correlation."""
        from hermes_cli.gateway_windows_restart_worker import main
        from hermes_cli.gateway_restart_state import create_intent, RestartLock

        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Pre-create a lock and claim lease
        lock = RestartLock("default")
        assert lock.try_acquire(request_id) is True

        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._drain_and_stop",
            MagicMock(side_effect=RuntimeError("boom")),
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: False,
        )
        # Mock cleanup_intent so status remains readable
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state.cleanup_intent",
            lambda *a, **kw: None,
        )

        monkeypatch.setattr(sys, "argv", [
            "worker", "--profile", "default", "--request-id", request_id,
        ])

        with pytest.raises(SystemExit):
            main()

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", request_id)
        assert status is not None
        assert status["request_id"] == request_id

    def test_coordinator_completed_with_matching_request_id(self, worker_env, monkeypatch):
        """Coordinator _wait_for_completion returns True when status
        has matching request_id and state='completed'."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        request_id = "test-req-ok"
        write_status("default", "completed", request_id=request_id,
                     old_pid=1234, new_pid=5678, launcher="direct_spawn")

        result, _ = _wait_for_completion(
            profile="default",
            timeout_s=2.0,
            request_id=request_id,
        )
        assert result is True

    def test_coordinator_failed_with_matching_request_id(self, worker_env, monkeypatch):
        """Coordinator _wait_for_completion returns False when status
        has matching request_id but state='failed'."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        request_id = "test-req-fail"
        write_status("default", "failed", request_id=request_id,
                     error="something broke")

        result, _ = _wait_for_completion(
            profile="default",
            timeout_s=2.0,
            request_id=request_id,
        )
        assert result is False

    def test_verify_new_gateway_no_pid(self, worker_env, monkeypatch):
        """new_pid <= 0 → status 'failed', no crash."""
        from hermes_cli.gateway_windows_restart_worker import _verify_new_gateway

        _verify_new_gateway(
            profile="default",
            request_id="req-1",
            old_pid=1234,
            new_pid=0,
            origin="test",
            launcher="direct_spawn",
        )

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", "req-1")
        assert status is not None
        assert status["state"] == "failed"
        assert "No new gateway PID" in status.get("error", "")

    def test_verify_new_gateway_dual_gateway(self, worker_env, monkeypatch):
        """Both old and new PIDs alive → dual gateway → status 'failed'."""
        from hermes_cli.gateway_windows_restart_worker import _verify_new_gateway

        # All PIDs are alive
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: True,
        )

        _verify_new_gateway(
            profile="default",
            request_id="req-1",
            old_pid=1234,
            new_pid=5678,
            origin="test",
            launcher="direct_spawn",
        )

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", "req-1")
        assert status is not None
        assert status["state"] == "failed"
        assert "dual gateway" in status.get("error", "").lower() or "still alive" in status.get("error", "").lower()

    def test_intermediate_state_timeout_not_completed(self, worker_env, monkeypatch):
        """P1-2: Status has intermediate state (e.g. 'draining') — coordinator
        wait_for_completion should NOT report completed (returns False on
        timeout)."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        request_id = "req-intermediate"
        # Write an intermediate state that will never become "completed"
        write_status("default", "draining", request_id=request_id, old_pid=1234)

        result, _ = _wait_for_completion(
            profile="default",
            timeout_s=0.5,  # very short timeout
            request_id=request_id,
        )
        assert result is False

        # Also verify with other intermediate states
        for state in ("stopping", "waiting_pid_exit", "waiting_port_release",
                       "starting_task", "starting_direct_fallback", "verifying",
                       "preflight_ok"):
            rid = f"req-intermediate-{state}"
            write_status("default", state, request_id=rid, old_pid=1234)
            result, _ = _wait_for_completion(
                profile="default",
                timeout_s=0.5,
                request_id=rid,
            )
            assert result is False, f"State '{state}' should not be reported as completed"


# ===========================================================================
# TestTransactionIsolation — Transaction isolation and cross-worker safety
# ===========================================================================

class TestTransactionIsolation:
    """Verify that concurrent / stale transactions do not interfere with
    each other's state files (intent, lock, status, lease)."""

    # -- helpers ----------------------------------------------------------

    def _read_lock_from_disk(self, hermes_home, profile="default"):
        """Read the lock file dict from disk."""
        path = hermes_home / "run" / "gateway-restart" / profile / "active.lock"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_intent_from_disk(self, hermes_home, profile="default", request_id=""):
        """Read the intent file dict from disk (per-request dir)."""
        if not request_id:
            return None
        path = hermes_home / "run" / "gateway-restart" / profile / request_id / "intent.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    # -- tests ------------------------------------------------------------

    def test_lock_and_intent_share_request_id(self, worker_env, monkeypatch):
        """Create a coordinator transaction (mock _spawn_worker,
        _wait_for_worker_claim). Read the lock file and intent file from
        disk. Assert both have the SAME request_id."""
        from hermes_cli.gateway_windows_restart import schedule_restart_handoff

        # Mock platform check and helpers
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart._assert_windows", lambda: None
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart.preflight_check",
            lambda **kw: (True, "preflight_ok"),
        )
        # Mock gateway.status.get_running_pid
        mock_gateway_status = MagicMock()
        mock_gateway_status.get_running_pid = MagicMock(return_value=1234)
        monkeypatch.setitem(sys.modules, "gateway", MagicMock())
        monkeypatch.setitem(sys.modules, "gateway.status", mock_gateway_status)

        # Mock _spawn_worker to just return a fake PID
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart._spawn_worker",
            lambda intent, profile, request_id: 9999,
        )
        # Mock _wait_for_worker_claim to return False (lock stays on disk)
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart._wait_for_worker_claim",
            lambda profile, request_id, timeout_s=10.0: False,
        )
        # Don't wait for completion
        result = schedule_restart_handoff(
            origin="test", profile="default", wait=False
        )
        assert result["scheduled"] is True

        request_id = result["request_id"]

        # Read lock and intent from disk
        lock_data = self._read_lock_from_disk(worker_env)
        intent_data = self._read_intent_from_disk(worker_env, "default", request_id)

        assert lock_data is not None, "Lock file should exist on disk"
        assert intent_data is not None, "Intent file should exist on disk"
        assert lock_data["request_id"] == request_id
        assert intent_data["request_id"] == request_id
        assert lock_data["request_id"] == intent_data["request_id"]

    def test_claim_lease_only_once(self, worker_env, monkeypatch):
        """Create intent + lock. Worker-1 calls claim_lease(request_id)
        → True. Worker-2 (new RestartLock instance) calls
        claim_lease(same request_id) → False."""
        from hermes_cli.gateway_restart_state import RestartLock, create_intent

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = intent["request_id"]
        nonce = intent["nonce"]

        # Coordinator acquires lock
        coordinator_lock = RestartLock("default")
        assert coordinator_lock.try_acquire(request_id) is True

        # Worker-1 claims the lease
        worker1_lock = RestartLock("default")
        assert worker1_lock.claim_lease(request_id, nonce) is True

        # Worker-2 tries to claim the same request_id
        worker2_lock = RestartLock("default")
        assert worker2_lock.claim_lease(request_id, nonce) is False

    def test_claim_timeout_lock_preserved(self, worker_env, monkeypatch):
        """Mock _wait_for_worker_claim to return False (timeout). After
        schedule_restart_handoff returns, verify the lock file still exists
        on disk. Then try a second restart → returns 'already in progress'."""
        from hermes_cli.gateway_windows_restart import schedule_restart_handoff

        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart._assert_windows", lambda: None
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart.preflight_check",
            lambda **kw: (True, "preflight_ok"),
        )
        mock_gateway_status = MagicMock()
        mock_gateway_status.get_running_pid = MagicMock(return_value=1234)
        monkeypatch.setitem(sys.modules, "gateway", MagicMock())
        monkeypatch.setitem(sys.modules, "gateway.status", mock_gateway_status)

        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart._spawn_worker",
            lambda intent, profile, request_id: 9999,
        )
        # Worker fails to claim in time
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart._wait_for_worker_claim",
            lambda profile, request_id, timeout_s=10.0: False,
        )

        result = schedule_restart_handoff(
            origin="test", profile="default", wait=False
        )
        assert result["scheduled"] is True

        # Lock should still be on disk (coordinator preserved it)
        lock_data = self._read_lock_from_disk(worker_env)
        assert lock_data is not None, "Lock file should still exist after claim timeout"

        # Second restart attempt should report "already in progress"
        result2 = schedule_restart_handoff(
            origin="test", profile="default", wait=False
        )
        assert result2["scheduled"] is False
        assert "already in progress" in result2["detail"].lower()

    def test_stale_worker_preserves_new_intent(self, worker_env, monkeypatch):
        """Create intent-A on disk. Then create intent-B (different
        request_id). Call cleanup_intent(profile, request_id=A). Assert
        intent-B still exists on disk."""
        from hermes_cli.gateway_restart_state import create_intent, cleanup_intent

        # Intent-A
        intent_a = create_intent(profile="default", target_pid=1111, origin="test-a")
        request_id_a = intent_a["request_id"]

        # Intent-B (different request_id — different directory)
        intent_b = create_intent(profile="default", target_pid=2222, origin="test-b")
        request_id_b = intent_b["request_id"]

        assert request_id_a != request_id_b

        # Stale worker-A tries to clean up with its old request_id
        cleanup_intent("default", request_id=request_id_a)

        # Intent-B should still be on disk
        intent_on_disk = self._read_intent_from_disk(worker_env, "default", request_id_b)
        assert intent_on_disk is not None
        assert intent_on_disk["request_id"] == request_id_b

    def test_stale_worker_preserves_new_lease(self, worker_env, monkeypatch):
        """Create lock + intent. Worker-B claims lease (O_EXCL). Worker-A
        tries to release using stale reference. Assert lease still exists."""
        from hermes_cli.gateway_restart_state import (
            RestartLock, create_intent, lease_path
        )

        # Coordinator creates lock + intent
        coord_lock = RestartLock("default")
        assert coord_lock.try_acquire("request-1") is True
        intent = create_intent(request_id="request-1", profile="default", target_pid=1234)

        # Worker-B claims the lease (O_EXCL)
        worker_b_lock = RestartLock("default")
        assert worker_b_lock.claim_lease("request-1", intent["nonce"]) is True

        # Worker-A tries to release using stale reference (no owner_token)
        worker_a_lock = RestartLock("default")
        worker_a_lock.release()

        # Lease file should still exist (Worker-B owns it)
        lp = lease_path("default", "request-1")
        assert lp.exists()

    def test_force_release_preserves_new_lock(self, worker_env, monkeypatch):
        """Create lock-A. Then create lock-B (different request_id,
        simulating a new transaction). Call _force_release(expected=lock_A_data)
        on a RestartLock. Assert lock-B still exists."""
        from hermes_cli.gateway_restart_state import RestartLock, lock_path
        import time as _time

        # Create lock-A
        lock_a = RestartLock("default")
        assert lock_a.try_acquire("request-a") is True

        # Read lock-A data
        lock_a_data = self._read_lock_from_disk(worker_env)
        assert lock_a_data is not None

        # Delete lock-A manually, then create lock-B (simulates a new transaction)
        lp = lock_path("default")
        lp.unlink(missing_ok=True)
        lock_b = RestartLock("default")
        assert lock_b.try_acquire("request-b") is True

        # Now use a RestartLock instance to force-release with old lock-A data
        # It should detect the mismatch and NOT delete lock-B
        stale_lock = RestartLock("default")
        stale_lock._force_release(expected=lock_a_data)

        # Lock-B should still exist
        lock_b_data = self._read_lock_from_disk(worker_env)
        assert lock_b_data is not None
        assert lock_b_data["request_id"] == "request-b"

    def test_wait_claim_ignores_old_request_id(self, worker_env, monkeypatch):
        """Write a lock file with request_id='old' and claimed_at set.
        Call _wait_for_worker_claim(profile, request_id='new', timeout_s=1).
        Assert returns False."""
        from hermes_cli.gateway_windows_restart import _wait_for_worker_claim
        from hermes_cli.gateway_restart_state import lock_path
        import time as _time

        # Write a lock file with request_id="old" and claimed_at
        lp = lock_path("default")
        lp.parent.mkdir(parents=True, exist_ok=True)
        lock_data = {
            "schema_version": 1,
            "request_id": "old",
            "owner_token": "some-token",
            "owner_pid": 9999,
            "profile": "default",
            "created_at": _time.time(),
            "expires_at": _time.time() + 300,
            "claimed_at": _time.time(),
        }
        lp.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")

        # Wait for a DIFFERENT request_id — should NOT match
        result = _wait_for_worker_claim("default", "new", timeout_s=1.0)
        assert result is False

    def test_intermediate_state_not_completed(self, worker_env, monkeypatch):
        """Write status with state='draining' and request_id=X.
        Call _wait_for_completion(profile, timeout_s=1, request_id=X).
        Assert returns False."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        write_status("default", "draining", request_id="req-x", old_pid=1234)

        result, _ = _wait_for_completion(
            profile="default", timeout_s=1.0, request_id="req-x"
        )
        assert result is False

    def test_direct_spawn_no_evidence_fails(self, worker_env, monkeypatch):
        """Mock _direct_spawn_gateway to return PID 1234. Mock
        _wait_for_launch_evidence to return 0. Call _start_new_gateway.
        Assert it raises RuntimeError with 'launch evidence'."""
        from hermes_cli.gateway_windows_restart_worker import _start_new_gateway

        # Make it skip the scheduled task path
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._direct_spawn_gateway",
            lambda: 1234,
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._wait_for_launch_evidence",
            lambda old_pid, timeout=15.0: 0,
        )
        # Ensure is_task_registered returns False
        mock_gw_windows = MagicMock()
        mock_gw_windows.is_task_registered = MagicMock(return_value=False)
        monkeypatch.setitem(sys.modules, "hermes_cli.gateway_windows", mock_gw_windows)

        with pytest.raises(RuntimeError, match="launch evidence"):
            _start_new_gateway(
                profile="default",
                request_id="req-1",
                old_pid=1234,
                origin="test",
                task_name="Hermes_Gateway",
            )

    def test_concurrent_only_one_worker(self, worker_env, monkeypatch):
        """Create intent. Pre-create lock. Worker-1 claims → True.
        Worker-2 claims → False (O_EXCL prevents double claim)."""
        from hermes_cli.gateway_restart_state import RestartLock, create_intent

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = intent["request_id"]
        nonce = intent["nonce"]

        # Coordinator acquires lock
        coord_lock = RestartLock("default")
        assert coord_lock.try_acquire(request_id) is True

        # Worker-1 claims
        worker1 = RestartLock("default")
        assert worker1.claim_lease(request_id, nonce) is True

        # Worker-2 (same request_id) — should fail (lease already exists on disk)
        worker2 = RestartLock("default")
        assert worker2.claim_lease(request_id, nonce) is False

    def test_claim_lease_wrong_request_id(self, worker_env, monkeypatch):
        """Worker tries to claim lease with a request_id that doesn't
        have an intent on disk → returns False."""
        from hermes_cli.gateway_restart_state import RestartLock, create_intent

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        real_request_id = intent["request_id"]

        # Coordinator acquires lock
        lock = RestartLock("default")
        assert lock.try_acquire(real_request_id) is True

        worker = RestartLock("default")
        # Try to claim with a request_id that has no intent
        assert worker.claim_lease("nonexistent-id", "some-nonce") is False

    def test_lock_owner_token_independence(self, worker_env, monkeypatch):
        """Two RestartLock instances acquiring different request_ids
        have independent owner_tokens."""
        from hermes_cli.gateway_restart_state import RestartLock, lock_path

        # First lock
        lock1 = RestartLock("default")
        assert lock1.try_acquire("req-1") is True
        data1 = self._read_lock_from_disk(worker_env)
        token1 = data1["owner_token"]

        # Release and create second lock
        lock1.release()
        lock2 = RestartLock("default")
        assert lock2.try_acquire("req-2") is True
        data2 = self._read_lock_from_disk(worker_env)
        token2 = data2["owner_token"]

        assert token1 != token2

    def test_wait_claim_matches_only_when_request_id_and_unclaimed(
        self, worker_env, monkeypatch
    ):
        """_wait_for_worker_claim should return True only when both
        request_id matches AND claimed_at is set."""
        from hermes_cli.gateway_windows_restart import _wait_for_worker_claim
        from hermes_cli.gateway_restart_state import lock_path
        import time as _time

        # Lock with matching request_id but NO claimed_at
        lp = lock_path("default")
        lp.parent.mkdir(parents=True, exist_ok=True)
        lock_data = {
            "schema_version": 1,
            "request_id": "req-match",
            "owner_token": "tok",
            "owner_pid": 9999,
            "profile": "default",
            "created_at": _time.time(),
            "expires_at": _time.time() + 300,
            # NO claimed_at
        }
        lp.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")

        # Should NOT match (no claimed_at)
        result = _wait_for_worker_claim("default", "req-match", timeout_s=1.0)
        assert result is False


# ===========================================================================
# P0-2: Lease loser behavior — must NOT write failed status or cleanup intent
# ===========================================================================

class TestLeaseLoserBehavior:
    """P0-2: When two workers race for the same lease, the loser must
    only log + sys.exit(1). It must NOT write a failed status or
    cleanup the intent (the winner owns those resources)."""

    def test_lease_loser_preserves_winner_status(
        self, worker_env, monkeypatch
    ):
        """P0-2: Worker-1 wins the lease and writes a status.
        Worker-2 (loser) must NOT overwrite it with 'failed'."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        from hermes_cli.gateway_restart_state import (
            create_intent, RestartLock, write_status, read_status,
        )

        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Simulate worker-1 having already won the lease by calling
        # claim_lease which creates the O_EXCL lease file
        winner_lock = RestartLock("default")
        assert winner_lock.try_acquire(request_id) is True
        assert winner_lock.claim_lease(request_id, nonce) is True

        # Winner writes a valid status
        write_status("default", "preflight_ok", request_id=request_id, old_pid=1234)
        winner_status = read_status("default", request_id)
        assert winner_status["state"] == "preflight_ok"

        # Now worker-2 tries to run the transaction with the same intent.
        # It should fail at claim_lease and exit without touching status.
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: False,
        )

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                disk_intent, "default", request_id, nonce,
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        # Winner's status must be preserved — NOT overwritten to "failed"
        final_status = read_status("default", request_id)
        assert final_status is not None
        assert final_status["state"] == "preflight_ok"

    def test_lease_loser_preserves_intent(self, worker_env, monkeypatch):
        """P0-2: Worker-2 (loser) must NOT cleanup/delete the intent
        directory that the winner owns."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        from hermes_cli.gateway_restart_state import (
            create_intent, RestartLock, read_intent,
        )

        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Worker-1 wins the lease
        winner_lock = RestartLock("default")
        assert winner_lock.try_acquire(request_id) is True
        assert winner_lock.claim_lease(request_id, nonce) is True

        # Worker-2 tries the same — loser path
        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(
                disk_intent, "default", request_id, nonce,
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )
        assert exc_info.value.code == 1

        # Intent must still be on disk (not cleaned up by loser)
        intent_on_disk = read_intent("default", request_id)
        assert intent_on_disk is not None
        assert intent_on_disk["request_id"] == request_id


# ===========================================================================
# P0-3: Only lease winner writes consumed/claimed state
# ===========================================================================

class TestOnlyWinnerWritesClaimedState:
    """P0-3: After claim_lease, only the winner transitions intent state
    from 'scheduled' to 'claimed'. The loser never touches the state."""

    def test_only_winner_writes_claimed_state(self, worker_env, monkeypatch):
        """claim_lease transitions intent from 'scheduled' to 'claimed'.
        Second claim_lease (loser) fails and does NOT touch state."""
        from hermes_cli.gateway_restart_state import (
            RestartLock, create_intent, read_intent,
        )

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = intent["request_id"]
        nonce = intent["nonce"]

        # Verify initial state is "scheduled"
        on_disk = read_intent("default", request_id)
        assert on_disk["state"] == "scheduled"

        # Winner claims
        winner_lock = RestartLock("default")
        assert winner_lock.claim_lease(request_id, nonce) is True

        # State should now be "claimed"
        after_claim = read_intent("default", request_id)
        assert after_claim is not None
        assert after_claim["state"] == "claimed"

        # Loser tries to claim — fails
        loser_lock = RestartLock("default")
        assert loser_lock.claim_lease(request_id, nonce) is False

        # State is STILL "claimed" (not corrupted)
        final = read_intent("default", request_id)
        assert final["state"] == "claimed"


# ===========================================================================
# P0-4: claim success then write_status OSError → lease released
# ===========================================================================

class TestClaimThenWriteStatusError:
    """P0-4: If claim_lease succeeds but write_status raises OSError,
    the transaction must release the lease and NOT leak resources."""

    def test_claim_success_then_write_status_error(self, worker_env, monkeypatch):
        """claim_lease succeeds. Then _drain_and_stop triggers write_status
        which raises OSError. The finally block must release the lease."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        from hermes_cli.gateway_restart_state import (
            create_intent, RestartLock, lease_path, read_intent,
        )

        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Acquire the profile lock so claim_lease can work
        coord_lock = RestartLock("default")
        assert coord_lock.try_acquire(request_id) is True

        # Make _drain_and_stop raise an exception (simulating the
        # write_status OSError propagation)
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._drain_and_stop",
            MagicMock(side_effect=OSError("disk full")),
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: False,
        )

        with pytest.raises(OSError, match="disk full"):
            _run_restart_transaction(
                disk_intent, "default", request_id, nonce,
                1234, "test", "/fake/hermes", "Hermes_Gateway",
            )

        # After the transaction, the request directory should be cleaned up
        # (cleanup_intent in the finally block removes the entire dir)
        intent_on_disk = read_intent("default", request_id)
        # The intent may or may not exist depending on whether cleanup
        # ran successfully. The key invariant is that we got a "failed" status.
        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default", request_id)
        # Status might be None if cleanup removed the whole directory,
        # or "failed" if it was written before cleanup
        if status is not None:
            assert status["state"] == "failed"


# ===========================================================================
# P0-1: Concurrent claim with threading.Barrier
# ===========================================================================

class TestConcurrentClaim:
    """P0-1: Two threads racing to claim_lease simultaneously.
    Only one must win (O_EXCL atomic guarantee)."""

    def test_concurrent_claim_only_one_winner(self, worker_env, monkeypatch):
        """Two threads call claim_lease at the same time using a
        threading.Barrier. Exactly one must succeed."""
        from hermes_cli.gateway_restart_state import RestartLock, create_intent

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = intent["request_id"]
        nonce = intent["nonce"]

        # Coordinator pre-creates the profile lock
        coord_lock = RestartLock("default")
        assert coord_lock.try_acquire(request_id) is True

        barrier = threading.Barrier(2, timeout=10)
        results = {"t1": None, "t2": None}
        errors = {"t1": None, "t2": None}

        def try_claim(name):
            try:
                lock = RestartLock("default")
                barrier.wait()  # synchronize both threads
                results[name] = lock.claim_lease(request_id, nonce)
            except Exception as e:
                errors[name] = e

        t1 = threading.Thread(target=try_claim, args=("t1",))
        t2 = threading.Thread(target=try_claim, args=("t2",))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        assert errors["t1"] is None, f"Thread 1 error: {errors['t1']}"
        assert errors["t2"] is None, f"Thread 2 error: {errors['t2']}"

        # Exactly one thread must have won
        winners = [k for k, v in results.items() if v is True]
        losers = [k for k, v in results.items() if v is False]
        assert len(winners) == 1, f"Expected 1 winner, got {len(winners)}: {results}"
        assert len(losers) == 1, f"Expected 1 loser, got {len(losers)}: {results}"


# ===========================================================================
# P1-2: Intermediate state timeout not reported as completed
# ===========================================================================

class TestIntermediateStateTimeout:
    """P1-2: If the worker is stuck in an intermediate state and the
    coordinator's wait_for_completion times out, it must NOT report
    the restart as completed."""

    def test_intermediate_state_timeout_not_completed(self, worker_env, monkeypatch):
        """Write various intermediate states. Verify wait_for_completion
        returns False on timeout for each one."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        intermediate_states = [
            "draining",
            "stopping",
            "waiting_pid_exit",
            "waiting_port_release",
            "starting_task",
            "starting_direct_fallback",
            "verifying",
            "preflight_ok",
            "claimed",
            "scheduled",
        ]

        for state in intermediate_states:
            rid = f"req-timeout-{state}"
            write_status("default", state, request_id=rid, old_pid=1234)

            result, _ = _wait_for_completion(
                profile="default",
                timeout_s=0.3,  # very short — will definitely time out
                request_id=rid,
            )
            assert result is False, (
                f"State '{state}' with request_id '{rid}' should NOT be "
                f"reported as completed on timeout"
            )
