"""Tests for gateway_windows_restart.py — coordinator logic."""

import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


@pytest.fixture
def coordinator_env(tmp_path, monkeypatch):
    """Set up environment for coordinator tests."""
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir()
    (hermes_home / "run").mkdir()
    (hermes_home / "logs").mkdir()
    (hermes_home / "profiles").mkdir()

    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setenv("_HERMES_GATEWAY", "1")

    import hermes_cli.config as config_mod
    monkeypatch.setattr(config_mod, "get_hermes_home", lambda: str(hermes_home))

    return hermes_home


class TestPreflight:
    def test_preflight_passes_with_valid_env(self, coordinator_env, monkeypatch):
        """Preflight should pass when all dependencies are available."""
        monkeypatch.setattr(sys, "platform", "win32")

        mock_gw = MagicMock()
        mock_gw.get_task_name.return_value = "Hermes_Gateway"
        mock_gw.is_task_registered.return_value = True
        mock_gw._derive_venv_pythonw.return_value = sys.executable  # pretend pythonw exists

        # Mock _get_restart_base to use tmp_path
        mock_restart_state = MagicMock()
        restart_base = coordinator_env / "run" / "gateway-restart"
        restart_base.mkdir(parents=True, exist_ok=True)
        mock_restart_state._get_restart_base.return_value = restart_base
        logs_dir = coordinator_env / "logs"
        mock_restart_state._get_logs_dir.return_value = logs_dir

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
            "hermes_cli.gateway_windows_restart_worker": MagicMock(),
            "hermes_cli.gateway_restart_state": mock_restart_state,
        }):
            from hermes_cli.gateway_windows_restart import preflight_check
            ok, detail = preflight_check(profile="default", target_pid=1234)
            assert ok is True

    def test_preflight_fails_without_pythonw(self, coordinator_env, monkeypatch):
        """Preflight should fail when pythonw.exe is not found."""
        monkeypatch.setattr(sys, "platform", "win32")

        # Mock _derive_venv_pythonw to return None (no pythonw)
        mock_gw = MagicMock()
        mock_gw._derive_venv_pythonw.return_value = None
        mock_gw.get_task_name.return_value = "Hermes_Gateway"

        # Mock _get_restart_base to use tmp_path
        mock_restart_state = MagicMock()
        restart_base = coordinator_env / "run" / "gateway-restart"
        restart_base.mkdir(parents=True, exist_ok=True)
        mock_restart_state._get_restart_base.return_value = restart_base
        logs_dir = coordinator_env / "logs"
        mock_restart_state._get_logs_dir.return_value = logs_dir

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
            "hermes_cli.gateway_windows_restart_worker": MagicMock(),
            "hermes_cli.gateway_restart_state": mock_restart_state,
        }):
            from hermes_cli.gateway_windows_restart import preflight_check as pc
            ok, detail = pc(profile="default", target_pid=1234)
            assert ok is False
            assert "pythonw" in detail.lower()


class TestScheduleRestartHandoff:
    def test_returns_request_id(self, coordinator_env, monkeypatch):
        """schedule_restart_handoff should return a request_id."""
        monkeypatch.setattr(sys, "platform", "win32")

        mock_lock = MagicMock()
        mock_lock.try_acquire.return_value = True

        mock_restart_state = MagicMock()
        mock_restart_state.RestartLock.return_value = mock_lock
        mock_restart_state.create_intent.return_value = {
            "request_id": "test-rid", "profile": "default",
        }
        mock_restart_state.write_status.return_value = None
        mock_restart_state.cleanup_intent.return_value = None
        mock_restart_state.append_restart_log.return_value = None

        mock_gw = MagicMock()
        mock_gw.get_task_name.return_value = "Hermes_Gateway"

        mock_gateway_status = MagicMock()
        mock_gateway_status.get_running_pid.return_value = 1234

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
            "hermes_cli.gateway_restart_state": mock_restart_state,
            "gateway": MagicMock(),
            "gateway.status": mock_gateway_status,
        }):
            import hermes_cli.gateway_windows_restart as mod

            # Override module-level functions directly on the module object
            mod.preflight_check = lambda **kw: (True, "ok")
            mod._spawn_worker = lambda intent, profile, request_id: 5678
            mod._wait_for_worker_claim = lambda profile, request_id, timeout_s=10.0: True
            mod._wait_for_completion = lambda profile, timeout_s, request_id="": (True, "completed")
            mod._read_final_status = lambda profile, request_id: {
                "state": "completed", "new_pid": 5678, "launcher": "direct_spawn",
            }

            result = mod.schedule_restart_handoff(origin="test", wait=True)
            assert "request_id" in result
            assert result["scheduled"] is True

    def test_intermediate_states_do_not_report_success(self, coordinator_env, monkeypatch):
        """P1-2: intermediate states like 'draining' should not be treated as success."""
        monkeypatch.setattr(sys, "platform", "win32")

        mock_lock = MagicMock()
        mock_lock.try_acquire.return_value = True

        mock_restart_state = MagicMock()
        mock_restart_state.RestartLock.return_value = mock_lock
        mock_restart_state.create_intent.return_value = {
            "request_id": "test-rid", "profile": "default",
        }
        mock_restart_state.write_status.return_value = None
        mock_restart_state.cleanup_intent.return_value = None
        mock_restart_state.append_restart_log.return_value = None

        mock_gw = MagicMock()
        mock_gw.get_task_name.return_value = "Hermes_Gateway"

        mock_gateway_status = MagicMock()
        mock_gateway_status.get_running_pid.return_value = 1234

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
            "hermes_cli.gateway_restart_state": mock_restart_state,
            "gateway": MagicMock(),
            "gateway.status": mock_gateway_status,
        }):
            import hermes_cli.gateway_windows_restart as mod

            mod.preflight_check = lambda **kw: (True, "ok")
            mod._spawn_worker = lambda intent, profile, request_id: 5678
            mod._wait_for_worker_claim = lambda profile, request_id, timeout_s=10.0: True
            # _wait_for_completion returns False with intermediate state
            mod._wait_for_completion = lambda profile, timeout_s, request_id="": (False, "draining")
            # _read_final_status returns an intermediate state
            mod._read_final_status = lambda profile, request_id: {"state": "draining"}

            result = mod.schedule_restart_handoff(origin="test", wait=True)
            assert result["scheduled"] is True
            assert result["completed"] is False
            # Intermediate state should not produce a success message
            assert "successfully" not in result["detail"].lower()


class TestWorkerSpawn:
    def test_worker_env_cleans_hermes_gateway(self, coordinator_env, monkeypatch):
        """Worker spawn should remove _HERMES_GATEWAY from env."""
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("_HERMES_GATEWAY", "1")

        captured_env = {}
        captured_argv = []

        def fake_popen(argv, **kwargs):
            captured_env.update(kwargs.get("env", {}))
            captured_argv.extend(argv)
            proc = MagicMock()
            proc.pid = 9999
            return proc

        import subprocess
        monkeypatch.setattr(subprocess, "Popen", fake_popen)

        mock_gw = MagicMock()
        mock_gw._derive_venv_pythonw.return_value = "pythonw.exe"

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
        }):
            from hermes_cli.gateway_windows_restart import _spawn_worker
            intent = {"request_id": "test-rid", "profile": "default"}
            pid = _spawn_worker(intent, "default", "test-rid")

            assert "_HERMES_GATEWAY" not in captured_env
            assert captured_env.get("HERMES_GATEWAY_RESTART_WORKER") == "1"
            assert pid == 9999
            # Worker is now invoked with --profile and --request-id
            assert "--profile" in captured_argv
            assert "default" in captured_argv
            assert "--request-id" in captured_argv
            assert "test-rid" in captured_argv
