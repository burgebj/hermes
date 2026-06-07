"""Tests for gateway_windows_restart_worker.py — intent/nonce validation,
PID/port handling, and worker status/fallback scenarios."""

import json
import os
import sys
import time
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
):
    """Create a realistic intent dict without writing to disk."""
    import uuid
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
        "state": "scheduled",
    }


def _write_intent_to_disk(hermes_home, intent, profile="default"):
    """Manually write an intent dict to the expected disk path."""
    run_dir = hermes_home / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"gateway-restart-{profile}-intent.json"
    path.write_text(json.dumps(intent, indent=2), encoding="utf-8")
    return path


# ===========================================================================
# TestIntentValidation — P0-5 intent validation
# ===========================================================================

class TestIntentValidation:
    """Verify that _run_restart_transaction validates the on-disk intent
    against the in-memory intent before any destructive action."""

    def test_intent_missing(self, worker_env, monkeypatch):
        """No intent file on disk → fail closed (sys.exit(1))."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234)
        # Do NOT write an intent file — disk is empty.

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "missing_intent" in status.get("error", "")

    def test_request_id_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different request_id → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234)
        # Write a disk intent with a DIFFERENT request_id
        tampered = dict(intent)
        tampered["request_id"] = "wrong-request-id"
        _write_intent_to_disk(hermes_home=worker_env, intent=tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "request_id_mismatch" in status.get("error", "")

    def test_nonce_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different nonce → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234)
        # Disk intent has a different nonce
        tampered = dict(intent)
        tampered["nonce"] = "wrong-nonce-value"
        _write_intent_to_disk(hermes_home=worker_env, intent=tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "nonce_mismatch" in status.get("error", "")

    def test_profile_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different profile → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234)
        # Write disk intent under "default" but with profile="other"
        tampered = dict(intent)
        tampered["profile"] = "other"
        _write_intent_to_disk(hermes_home=worker_env, intent=tampered, profile="default")

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "profile_mismatch" in status.get("error", "")

    def test_target_pid_mismatch(self, worker_env, monkeypatch):
        """Disk intent has different target_pid → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234)
        tampered = dict(intent)
        tampered["target_pid"] = 9999
        _write_intent_to_disk(hermes_home=worker_env, intent=tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "target_pid_mismatch" in status.get("error", "")

    def test_ttl_expired(self, worker_env, monkeypatch):
        """Disk intent has expires_at in the past → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234, ttl_s=300)
        tampered = dict(intent)
        tampered["expires_at"] = time.time() - 60  # expired 60s ago
        _write_intent_to_disk(hermes_home=worker_env, intent=tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        # The error could be "expired_intent" or "missing_intent" depending
        # on whether read_intent cleans up the expired file first.
        assert "expired" in status.get("error", "").lower() or "missing" in status.get("error", "").lower()

    def test_schema_version_unsupported(self, worker_env, monkeypatch):
        """Disk intent has schema_version=99 → fail closed."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction

        intent = _make_intent(profile="default", target_pid=1234)
        tampered = dict(intent)
        tampered["schema_version"] = 99
        _write_intent_to_disk(hermes_home=worker_env, intent=tampered)

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(intent)
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        # read_intent returns None for unsupported schema → "missing_intent"
        assert "missing_intent" in status.get("error", "") or "schema" in status.get("error", "").lower()

    def test_intent_consumed_prevents_replay(self, worker_env, monkeypatch):
        """After first worker consumes intent, second worker with same
        intent should fail because the intent file is cleaned up."""
        from hermes_cli.gateway_windows_restart_worker import _run_restart_transaction
        from hermes_cli.gateway_restart_state import (
            create_intent, update_intent_state, cleanup_intent, RestartLock,
        )

        # --- First worker run: set up and partially execute ---
        disk_intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = disk_intent["request_id"]
        nonce = disk_intent["nonce"]

        # Simulate first worker marking intent as consumed
        update_intent_state("default", "consumed")

        # Now simulate what happens after a successful first run:
        # the intent file is cleaned up (deleted), as _run_restart_transaction
        # does in its finally block.
        cleanup_intent("default")

        # --- Second worker run: same intent parameters ---
        replay_intent = _make_intent(
            profile="default",
            target_pid=1234,
            request_id=request_id,
            nonce=nonce,
        )

        with pytest.raises(SystemExit) as exc_info:
            _run_restart_transaction(replay_intent)
        assert exc_info.value.code == 1

        # Verify the second worker wrote a failed status
        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
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

        intent = _make_intent(profile="default", target_pid=1234)
        # Write matching intent to disk
        disk_intent = create_intent(
            profile="default", target_pid=1234, origin="test",
        )
        # Align the in-memory intent with the disk intent
        intent["request_id"] = disk_intent["request_id"]
        intent["nonce"] = disk_intent["nonce"]

        # Pre-create a lock that the worker can claim
        lock = RestartLock("default")
        lock.try_acquire(disk_intent["request_id"])

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
            _run_restart_transaction(intent)

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
            # First call (during wait loop): occupied
            # After kill: free
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

        intent = _make_intent(profile="default", target_pid=1234)
        # Write matching disk intent
        disk_intent = create_intent(
            profile="default", target_pid=1234, origin="test",
        )
        intent["request_id"] = disk_intent["request_id"]
        intent["nonce"] = disk_intent["nonce"]

        # Pre-create a lock that the worker can claim
        lock = RestartLock("default")
        lock.try_acquire(disk_intent["request_id"])

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

        # Call main() with the intent via file
        intent_file = tmp_path / "intent.json"
        intent_file.write_text(json.dumps(intent), encoding="utf-8")
        monkeypatch.setattr(sys, "argv", [
            "worker", "--intent-file", str(intent_file),
        ])

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "drain exploded" in status.get("error", "")

    def test_status_ignores_old_request_id(self, worker_env, tmp_path, monkeypatch):
        """Coordinator _wait_for_completion returns False when status has
        an old request_id different from the one being waited on."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        # Write a status with an old request_id
        write_status("default", "completed", request_id="old-123", new_pid=5678)

        # Wait for a different request_id — should NOT see the old status
        result = _wait_for_completion(
            profile="default",
            timeout_s=1.0,  # short timeout
            request_id="new-456",
        )
        assert result is False

    def test_status_intermediate_not_completed(self, worker_env, monkeypatch):
        """Status has state='draining' → coordinator doesn't report completed."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        request_id = "test-req-1"
        write_status("default", "draining", request_id=request_id, old_pid=1234)

        result = _wait_for_completion(
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
        status = read_status("default")
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
                # First call (initial check) → alive
                # Subsequent calls (stability window) → dead
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
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "stability" in status.get("error", "").lower() or "died" in status.get("error", "").lower()

    def test_unhandled_exception_writes_failed_status_field(self, worker_env, tmp_path, monkeypatch):
        """Unhandled exception → status file has request_id matching the
        intent's request_id, enabling coordinator correlation."""
        from hermes_cli.gateway_windows_restart_worker import main
        from hermes_cli.gateway_restart_state import create_intent, RestartLock

        intent = _make_intent(profile="default", target_pid=1234)
        disk_intent = create_intent(
            profile="default", target_pid=1234, origin="test",
        )
        intent["request_id"] = disk_intent["request_id"]
        intent["nonce"] = disk_intent["nonce"]

        # Pre-create a lock that the worker can claim
        lock = RestartLock("default")
        lock.try_acquire(disk_intent["request_id"])

        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker._drain_and_stop",
            MagicMock(side_effect=RuntimeError("boom")),
        )
        monkeypatch.setattr(
            "hermes_cli.gateway_restart_state._pid_exists",
            lambda pid: False,
        )

        intent_file = tmp_path / "intent2.json"
        intent_file.write_text(json.dumps(intent), encoding="utf-8")
        monkeypatch.setattr(sys, "argv", [
            "worker", "--intent-file", str(intent_file),
        ])

        with pytest.raises(SystemExit):
            main()

        from hermes_cli.gateway_restart_state import read_status
        status = read_status("default")
        assert status is not None
        assert status["request_id"] == disk_intent["request_id"]

    def test_coordinator_completed_with_matching_request_id(self, worker_env, monkeypatch):
        """Coordinator _wait_for_completion returns True when status
        has matching request_id and state='completed'."""
        from hermes_cli.gateway_windows_restart import _wait_for_completion
        from hermes_cli.gateway_restart_state import write_status

        request_id = "test-req-ok"
        write_status("default", "completed", request_id=request_id,
                     old_pid=1234, new_pid=5678, launcher="direct_spawn")

        result = _wait_for_completion(
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

        result = _wait_for_completion(
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
        status = read_status("default")
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
        status = read_status("default")
        assert status is not None
        assert status["state"] == "failed"
        assert "dual gateway" in status.get("error", "").lower() or "still alive" in status.get("error", "").lower()


# ===========================================================================
# TestTransactionIsolation — Transaction isolation and cross-worker safety
# ===========================================================================

class TestTransactionIsolation:
    """Verify that concurrent / stale transactions do not interfere with
    each other's state files (intent, lock, status)."""

    # -- helpers ----------------------------------------------------------

    def _read_lock_from_disk(self, hermes_home, profile="default"):
        """Read the lock file dict from disk."""
        path = hermes_home / "run" / f"gateway-restart-{profile}.lock"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_intent_from_disk(self, hermes_home, profile="default"):
        """Read the intent file dict from disk."""
        path = hermes_home / "run" / f"gateway-restart-{profile}-intent.json"
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
            lambda intent, profile: 9999,
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
        intent_data = self._read_intent_from_disk(worker_env)

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

        # Coordinator acquires lock
        coordinator_lock = RestartLock("default")
        assert coordinator_lock.try_acquire(request_id) is True

        # Worker-1 claims the lease
        worker1_lock = RestartLock("default")
        assert worker1_lock.claim_lease(request_id) is True

        # Worker-2 tries to claim the same request_id
        worker2_lock = RestartLock("default")
        assert worker2_lock.claim_lease(request_id) is False

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
            lambda intent, profile: 9999,
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
        """Create intent-A on disk. Then create intent-B (overwrites).
        Call cleanup_intent(profile, request_id=A, nonce=A). Assert
        intent-B still exists on disk."""
        from hermes_cli.gateway_restart_state import create_intent, cleanup_intent

        # Intent-A
        intent_a = create_intent(profile="default", target_pid=1111, origin="test-a")
        request_id_a = intent_a["request_id"]
        nonce_a = intent_a["nonce"]

        # Intent-B overwrites
        intent_b = create_intent(profile="default", target_pid=2222, origin="test-b")
        request_id_b = intent_b["request_id"]
        nonce_b = intent_b["nonce"]

        assert request_id_a != request_id_b

        # Stale worker-A tries to clean up with its old request_id/nonce
        cleanup_intent("default", request_id=request_id_a, nonce=nonce_a)

        # Intent-B should still be on disk
        intent_on_disk = self._read_intent_from_disk(worker_env)
        assert intent_on_disk is not None
        assert intent_on_disk["request_id"] == request_id_b
        assert intent_on_disk["nonce"] == nonce_b

    def test_stale_worker_preserves_new_status(self, worker_env, monkeypatch):
        """Write status with request_id=A. Then write status with
        request_id=B (overwrites). Call cleanup_status(profile, request_id=A).
        Assert status file still exists with request_id=B."""
        from hermes_cli.gateway_restart_state import write_status, cleanup_status, read_status

        write_status("default", "completed", request_id="request-a", new_pid=1111)
        write_status("default", "completed", request_id="request-b", new_pid=2222)

        # Stale worker-A tries to clean up
        cleanup_status("default", request_id="request-a")

        # Status with request-B should still exist
        status = read_status("default")
        assert status is not None
        assert status["request_id"] == "request-b"
        assert status["new_pid"] == 2222

    def test_stale_worker_preserves_new_lease(self, worker_env, monkeypatch):
        """Create lock. Worker-B claims it (new owner_token). Create a new
        RestartLock for Worker-A (with old token). Worker-A calls release().
        Assert lock file still exists on disk."""
        from hermes_cli.gateway_restart_state import RestartLock

        # Coordinator creates lock
        coord_lock = RestartLock("default")
        assert coord_lock.try_acquire("request-1") is True

        # Worker-B claims the lease (changes owner_token)
        worker_b_lock = RestartLock("default")
        assert worker_b_lock.claim_lease("request-1") is True

        # Worker-A tries to release using its stale lock reference
        # Worker-A would have been a separate RestartLock that was NOT the
        # one that claimed.  Simulate by creating a new instance that
        # doesn't have the right token.
        worker_a_lock = RestartLock("default")
        # worker_a_lock has no _owner_token set, so release() should be a no-op
        worker_a_lock.release()

        # Lock file should still exist (Worker-B owns it)
        lock_data = self._read_lock_from_disk(worker_env)
        assert lock_data is not None
        assert lock_data["request_id"] == "request-1"

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

        result = _wait_for_completion(
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
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart_worker.sys",
            sys,
        )
        # We need to mock the import of is_task_registered inside _start_new_gateway
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
        """Create two intents with same request_id. Pre-create lock.
        Worker-1 claims → True. Worker-2 claims → False."""
        from hermes_cli.gateway_restart_state import RestartLock, create_intent

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        request_id = intent["request_id"]

        # Coordinator acquires lock
        coord_lock = RestartLock("default")
        assert coord_lock.try_acquire(request_id) is True

        # Worker-1 claims
        worker1 = RestartLock("default")
        assert worker1.claim_lease(request_id) is True

        # Worker-2 (same request_id) — should fail (already claimed)
        worker2 = RestartLock("default")
        assert worker2.claim_lease(request_id) is False

    def test_finally_only_cleans_own(self, worker_env, monkeypatch):
        """Create intent-A on disk with nonce-A. Create intent-B on disk
        (overwrites) with nonce-B. Call cleanup_intent(profile,
        request_id=A, nonce=A). Read disk → intent-B with nonce-B still
        exists."""
        from hermes_cli.gateway_restart_state import create_intent, cleanup_intent

        # Intent-A
        intent_a = create_intent(profile="default", target_pid=1111, origin="a")
        rid_a, nonce_a = intent_a["request_id"], intent_a["nonce"]

        # Intent-B overwrites
        intent_b = create_intent(profile="default", target_pid=2222, origin="b")
        rid_b, nonce_b = intent_b["request_id"], intent_b["nonce"]

        # Worker-A's finally block cleans up with its own request_id/nonce
        cleanup_intent("default", request_id=rid_a, nonce=nonce_a)

        # Intent-B should still be on disk
        disk = self._read_intent_from_disk(worker_env)
        assert disk is not None
        assert disk["request_id"] == rid_b
        assert disk["nonce"] == nonce_b

    def test_claim_lease_wrong_request_id(self, worker_env, monkeypatch):
        """Worker tries to claim lease with a request_id that doesn't
        match the lock file → returns False."""
        from hermes_cli.gateway_restart_state import RestartLock

        lock = RestartLock("default")
        assert lock.try_acquire("correct-id") is True

        worker = RestartLock("default")
        assert worker.claim_lease("wrong-id") is False

    def test_cleanup_intent_unconditional(self, worker_env, monkeypatch):
        """Call cleanup_intent(profile) with empty request_id and nonce
        (coordinator mode). Intent file should be deleted."""
        from hermes_cli.gateway_restart_state import create_intent, cleanup_intent

        create_intent(profile="default", target_pid=1234, origin="test")

        intent_path = worker_env / "run" / "gateway-restart-default-intent.json"
        assert intent_path.exists()

        # Coordinator-mode cleanup (empty request_id/nonce → unconditional delete)
        cleanup_intent("default", request_id="", nonce="")

        assert not intent_path.exists()

    def test_cleanup_status_unconditional(self, worker_env, monkeypatch):
        """Write status. Call cleanup_status(profile) with empty
        request_id (coordinator mode). Status file should be deleted."""
        from hermes_cli.gateway_restart_state import write_status, cleanup_status

        write_status("default", "completed", request_id="req-1", new_pid=5678)

        status_path = worker_env / "run" / "gateway-restart-default-status.json"
        assert status_path.exists()

        # Coordinator-mode cleanup (empty request_id → unconditional delete)
        cleanup_status("default", request_id="")

        assert not status_path.exists()

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
