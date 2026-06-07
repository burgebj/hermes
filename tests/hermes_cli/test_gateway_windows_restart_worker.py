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
            "hermes_cli.gateway_windows_restart_worker._pid_exists",
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

        with pytest.raises(RuntimeError, match="unrelated process"):
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
                old_pid=1234,
                origin="test",
                port=8080,
                timeout=0.5,
            )

    def test_port_still_occupied_after_kill(self, worker_env, monkeypatch):
        """Port occupied → hermes PID → kill → port STILL occupied → RuntimeError."""
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

            with pytest.raises(RuntimeError, match="still occupied"):
                _wait_for_port_release(
                    profile="default",
                    request_id="req-1",
                    old_pid=1234,
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

    def test_unhandled_exception_writes_failed(self, worker_env, monkeypatch):
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
            "hermes_cli.gateway_windows_restart_worker._pid_exists",
            lambda pid: False,
        )

        # Call main() with the intent
        monkeypatch.setattr(sys, "argv", [
            "worker", "--intent", json.dumps(intent),
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
            "hermes_cli.gateway_windows_restart_worker._pid_exists",
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
            "hermes_cli.gateway_windows_restart_worker._pid_exists",
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

    def test_unhandled_exception_writes_failed_status_field(self, worker_env, monkeypatch):
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
            "hermes_cli.gateway_windows_restart_worker._pid_exists",
            lambda pid: False,
        )

        monkeypatch.setattr(sys, "argv", [
            "worker", "--intent", json.dumps(intent),
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
            "hermes_cli.gateway_windows_restart_worker._pid_exists",
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
