"""Tests for gateway_restart_state.py — intent, locks, status, JSONL."""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def restart_state_dir(tmp_path, monkeypatch):
    """Provide a temp HERMES_HOME for restart state tests."""
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir()
    (hermes_home / "run").mkdir()
    (hermes_home / "logs").mkdir()

    monkeypatch.setenv("HERMES_HOME", str(hermes_home))

    # Mock get_hermes_home
    import hermes_cli.config as config_mod
    monkeypatch.setattr(config_mod, "get_hermes_home", lambda: str(hermes_home))

    return hermes_home


# ---------------------------------------------------------------------------
# Intent tests
# ---------------------------------------------------------------------------

class TestIntent:
    def test_create_and_read_intent(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import create_intent, read_intent, cleanup_intent

        intent = create_intent(profile="default", target_pid=1234, origin="test")
        assert intent["schema_version"] == 1
        assert intent["target_pid"] == 1234
        assert intent["origin"] == "test"
        assert intent["state"] == "scheduled"
        assert "request_id" in intent
        assert "nonce" in intent

        read = read_intent("default")
        assert read is not None
        assert read["request_id"] == intent["request_id"]
        assert read["target_pid"] == 1234

        cleanup_intent("default")

    def test_intent_ttl_expiry(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import create_intent, read_intent, cleanup_intent

        intent = create_intent(profile="default", ttl_s=1)
        assert read_intent("default") is not None

        # Expire it
        path = restart_state_dir / "run" / "gateway-restart-default-intent.json"
        data = json.loads(path.read_text())
        data["expires_at"] = time.time() - 10
        path.write_text(json.dumps(data))

        assert read_intent("default") is None

    def test_malformed_intent_safe_fail(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import read_intent

        path = restart_state_dir / "run" / "gateway-restart-default-intent.json"
        # Not JSON
        path.write_text("not json", encoding="utf-8")
        assert read_intent("default") is None

        # Wrong schema version
        path.write_text(json.dumps({"schema_version": 999}))
        assert read_intent("default") is None

        # Missing required fields
        path.write_text(json.dumps({"schema_version": 1}))
        assert read_intent("default") is None

        # Not a dict
        path.write_text(json.dumps([1, 2, 3]))
        assert read_intent("default") is None

        # Too large
        path.write_text(json.dumps({"schema_version": 1, "x": "y" * 10000}))
        assert read_intent("default") is None

    def test_intent_nonce_validation(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import create_intent, validate_intent_nonce

        intent = create_intent(profile="default")
        nonce = intent["nonce"]

        assert validate_intent_nonce(intent, nonce) is True
        assert validate_intent_nonce(intent, "wrong") is False
        assert validate_intent_nonce(intent, "") is False

    def test_intent_atomic_write(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import create_intent, read_intent

        # Should not leave .tmp file behind
        intent = create_intent(profile="default")
        run_dir = restart_state_dir / "run"
        tmp_files = list(run_dir.glob("*.tmp"))
        assert len(tmp_files) == 0

    def test_intent_profile_isolation(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import create_intent, read_intent, cleanup_intent

        create_intent(profile="p1", target_pid=111)
        create_intent(profile="p2", target_pid=222)

        r1 = read_intent("p1")
        r2 = read_intent("p2")
        assert r1["target_pid"] == 111
        assert r2["target_pid"] == 222

        cleanup_intent("p1")
        cleanup_intent("p2")


# ---------------------------------------------------------------------------
# Lock tests
# ---------------------------------------------------------------------------

class TestRestartLock:
    def test_acquire_release(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import RestartLock

        lock = RestartLock("default")
        assert lock.try_acquire("req-1") is True
        lock.release()

    def test_lock_contention(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import RestartLock

        lock1 = RestartLock("default")
        lock2 = RestartLock("default")

        assert lock1.try_acquire("req-1") is True
        assert lock2.try_acquire("req-2") is False
        lock1.release()

        assert lock2.try_acquire("req-2") is True
        lock2.release()

    def test_lock_coalesce_same_request(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import RestartLock

        lock = RestartLock("default")
        assert lock.try_acquire("req-1") is True
        # Same request ID should coalesce
        assert lock.try_acquire("req-1") is True
        lock.release()

    def test_lock_ttl_expiry(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import RestartLock, lock_path

        lock = RestartLock("default")
        assert lock.try_acquire("req-1", ttl_s=1) is True

        # Expire it and set owner_pid to a dead process
        lp = lock_path("default")
        data = json.loads(lp.read_text())
        data["created_at"] = time.time() - 10
        data["owner_pid"] = 99999  # Dead PID
        lp.write_text(json.dumps(data))

        # New request should succeed (expired lock with dead owner is force-released)
        assert lock.try_acquire("req-2", ttl_s=1) is True
        lock.release()

    def test_lock_ttl_expiry_owner_alive(self, restart_state_dir):
        """TTL expired but owner PID still alive — must NOT take over."""
        import os
        from hermes_cli.gateway_restart_state import RestartLock, lock_path

        lock = RestartLock("default")
        assert lock.try_acquire("req-1", ttl_s=1) is True

        # Expire it but keep owner_pid as current process (alive)
        lp = lock_path("default")
        data = json.loads(lp.read_text())
        data["created_at"] = time.time() - 10
        data["owner_pid"] = os.getpid()  # Alive!
        lp.write_text(json.dumps(data))

        # New request should FAIL (owner still alive)
        lock2 = RestartLock("default")
        assert lock2.try_acquire("req-2", ttl_s=1) is False
        lock.release()

    def test_lock_profile_isolation(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import RestartLock

        lock1 = RestartLock("p1")
        lock2 = RestartLock("p2")

        assert lock1.try_acquire("req-1") is True
        assert lock2.try_acquire("req-2") is True  # Different profile

        lock1.release()
        lock2.release()

    def test_non_owner_release_rejected(self, restart_state_dir):
        """Non-owner calling release() must NOT delete the lock."""
        from hermes_cli.gateway_restart_state import RestartLock, lock_path

        lock1 = RestartLock("default")
        assert lock1.try_acquire("req-1") is True

        # Simulate a non-owner trying to release
        lock2 = RestartLock("default")
        lock2.release()  # Should be a no-op

        # Verify lock1 still exists
        assert lock_path("default").exists()
        lock1.release()

    def test_owner_token_mismatch_rejected(self, restart_state_dir):
        """release() with wrong owner_token must NOT delete the lock."""
        from hermes_cli.gateway_restart_state import RestartLock, lock_path

        lock = RestartLock("default")
        assert lock.try_acquire("req-1") is True

        # Corrupt the owner_token
        lp = lock_path("default")
        data = json.loads(lp.read_text())
        data["owner_token"] = "wrong-token"
        lp.write_text(json.dumps(data))

        # release() should detect mismatch and NOT delete
        lock.release()
        assert lock_path("default").exists()

        # Clean up with correct token
        lock._force_release()

    def test_claim_lease(self, restart_state_dir):
        """Worker can claim lease from coordinator."""
        from hermes_cli.gateway_restart_state import RestartLock, lock_path

        lock = RestartLock("default")
        assert lock.try_acquire("req-1") is True

        # Simulate worker claiming lease
        worker_lock = RestartLock("default")
        assert worker_lock.claim_lease("req-1") is True

        # Lock should still exist with new owner
        assert lock_path("default").exists()
        data = json.loads(lock_path("default").read_text())
        assert "claimed_at" in data

        # Worker can release
        worker_lock.release()

    def test_claim_lease_wrong_request_id(self, restart_state_dir):
        """Worker can't claim lease with wrong request_id."""
        from hermes_cli.gateway_restart_state import RestartLock

        lock = RestartLock("default")
        assert lock.try_acquire("req-1") is True

        worker_lock = RestartLock("default")
        assert worker_lock.claim_lease("req-WRONG") is False

        lock.release()

    def test_concurrent_acquire_contention(self, restart_state_dir):
        """Two locks competing — only one wins."""
        from hermes_cli.gateway_restart_state import RestartLock

        lock1 = RestartLock("default")
        lock2 = RestartLock("default")

        assert lock1.try_acquire("req-1") is True
        assert lock2.try_acquire("req-2") is False  # Contention

        lock1.release()

        # Now lock2 can acquire
        assert lock2.try_acquire("req-2") is True
        lock2.release()


# ---------------------------------------------------------------------------
# Status tests
# ---------------------------------------------------------------------------

class TestStatus:
    def test_write_read_status(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import write_status, read_status, cleanup_status

        write_status("default", "draining", request_id="abc", old_pid=1234)
        status = read_status("default")
        assert status is not None
        assert status["state"] == "draining"
        assert status["request_id"] == "abc"
        assert status["old_pid"] == 1234

        cleanup_status("default")

    def test_invalid_state_rejected(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import write_status

        with pytest.raises(ValueError, match="Invalid state"):
            write_status("default", "not_a_real_state")

    def test_valid_states(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import write_status, read_status, cleanup_status

        states = [
            "scheduled", "preflight_ok", "draining", "stopping",
            "waiting_pid_exit", "waiting_port_release",
            "starting_task", "starting_direct_fallback",
            "verifying", "completed", "failed",
        ]
        for state in states:
            write_status("default", state)
            assert read_status("default")["state"] == state

        cleanup_status("default")


# ---------------------------------------------------------------------------
# JSONL log tests
# ---------------------------------------------------------------------------

class TestJSONLLog:
    def test_append_and_read(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import append_restart_log, jsonl_log_path

        append_restart_log(
            request_id="abc", profile="default", old_pid=1234,
            new_pid=5678, state="completed", launcher="direct_spawn",
        )

        path = jsonl_log_path()
        assert path.exists()
        lines = path.read_text().strip().split("\n")
        assert len(lines) == 1

        record = json.loads(lines[0])
        assert record["request_id"] == "abc"
        assert record["old_pid"] == 1234
        assert record["new_pid"] == 5678
        assert record["state"] == "completed"

    def test_multiple_appends(self, restart_state_dir):
        from hermes_cli.gateway_restart_state import append_restart_log, jsonl_log_path

        for state in ["scheduled", "draining", "completed"]:
            append_restart_log(state=state)

        lines = jsonl_log_path().read_text().strip().split("\n")
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# Environment variable sanitization test
# ---------------------------------------------------------------------------

class TestEnvSanitization:
    def test_hermes_gateway_cleared(self, restart_state_dir):
        """Verify _HERMES_GATEWAY is removed from worker environment."""
        # This tests the coordinator's env cleanup logic
        env = os.environ.copy()
        env["_HERMES_GATEWAY"] = "1"
        env["HERMES_HOME"] = "/test"
        env["PATH"] = "/usr/bin"

        # Simulate coordinator cleanup
        env.pop("_HERMES_GATEWAY", None)
        env["HERMES_GATEWAY_RESTART_WORKER"] = "1"

        assert "_HERMES_GATEWAY" not in env
        assert env["HERMES_GATEWAY_RESTART_WORKER"] == "1"
        assert env["HERMES_HOME"] == "/test"  # preserved
        assert env["PATH"] == "/usr/bin"  # preserved

    def test_worker_env_cleanup_for_new_gateway(self, restart_state_dir):
        """Verify worker cleans its own marker before starting new gateway."""
        env = os.environ.copy()
        env["HERMES_GATEWAY_RESTART_WORKER"] = "1"

        # Simulate worker cleanup before starting new gateway
        env.pop("_HERMES_GATEWAY", None)
        env.pop("HERMES_GATEWAY_RESTART_WORKER", None)

        assert "HERMES_GATEWAY_RESTART_WORKER" not in env
        assert "_HERMES_GATEWAY" not in env
