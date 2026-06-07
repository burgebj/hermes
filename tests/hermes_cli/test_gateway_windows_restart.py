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

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
            "hermes_cli.gateway_windows_restart_worker": MagicMock(),
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

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
            "hermes_cli.gateway_windows_restart_worker": MagicMock(),
        }):
            from hermes_cli.gateway_windows_restart import preflight_check as pc
            ok, detail = pc(profile="default", target_pid=1234)
            assert ok is False
            assert "pythonw" in detail.lower()


class TestScheduleRestartHandoff:
    def test_returns_request_id(self, coordinator_env, monkeypatch):
        """schedule_restart_handoff should return a request_id."""
        monkeypatch.setattr(sys, "platform", "win32")

        from hermes_cli.gateway_windows_restart import schedule_restart_handoff

        # Mock all dependencies
        monkeypatch.setattr(
            "hermes_cli.gateway_windows_restart.preflight_check",
            lambda **kw: (True, "ok"),
        )
        monkeypatch.setattr(
            "gateway.status.get_running_pid",
            lambda: 1234,
        )

        mock_gw = MagicMock()
        mock_gw.get_task_name.return_value = "Hermes_Gateway"
        mock_gw._spawn_detached.return_value = 5678

        with patch.dict("sys.modules", {
            "hermes_cli.gateway_windows": mock_gw,
        }):
            # Mock _spawn_worker to not actually spawn
            monkeypatch.setattr(
                "hermes_cli.gateway_windows_restart._spawn_worker",
                lambda intent, profile: 5678,
            )
            # Mock _wait_for_worker_claim to return immediately
            monkeypatch.setattr(
                "hermes_cli.gateway_windows_restart._wait_for_worker_claim",
                lambda profile, request_id, timeout_s=10.0: True,
            )
            # Mock _wait_for_completion to return immediately
            monkeypatch.setattr(
                "hermes_cli.gateway_windows_restart._wait_for_completion",
                lambda profile, timeout: True,
            )
            monkeypatch.setattr(
                "hermes_cli.gateway_windows_restart._read_final_status",
                lambda profile: {"state": "completed", "new_pid": 5678, "launcher": "direct_spawn"},
            )

            result = schedule_restart_handoff(origin="test", wait=True)
            assert "request_id" in result
            assert result["scheduled"] is True


class TestWorkerSpawn:
    def test_worker_env_cleans_hermes_gateway(self, coordinator_env, monkeypatch):
        """Worker spawn should remove _HERMES_GATEWAY from env."""
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setenv("_HERMES_GATEWAY", "1")

        captured_env = {}

        def fake_popen(argv, **kwargs):
            captured_env.update(kwargs.get("env", {}))
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
            import json as json_mod
            intent = {"request_id": "test", "profile": "default"}
            pid = _spawn_worker(intent, "default")

            assert "_HERMES_GATEWAY" not in captured_env
            assert captured_env.get("HERMES_GATEWAY_RESTART_WORKER") == "1"
            assert pid == 9999
