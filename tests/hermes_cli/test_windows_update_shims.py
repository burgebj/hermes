import os
import subprocess
from pathlib import Path

import pytest

from hermes_cli import main as hm


def test_scan_windows_hermes_entrypoint_pids_matches_same_scripts_dir(
    tmp_path, monkeypatch
):
    scripts_dir = tmp_path / "venv" / "Scripts"
    scripts_dir.mkdir(parents=True)
    hermes_exe = scripts_dir / "hermes.exe"
    gateway_exe = scripts_dir / "hermes-gateway.exe"
    other_exe = tmp_path / "other" / "Scripts" / "hermes.exe"
    other_exe.parent.mkdir(parents=True)

    monkeypatch.setattr(hm, "_is_windows", lambda: True)

    stdout = "\n\n".join(
        [
            f"CommandLine={hermes_exe} update\nExecutablePath={hermes_exe}\nProcessId=123",
            f"CommandLine={gateway_exe}\nExecutablePath={gateway_exe}\nProcessId=456",
            f"CommandLine={other_exe}\nExecutablePath={other_exe}\nProcessId=789",
            (
                f"CommandLine={hermes_exe} update\n"
                f"ExecutablePath={hermes_exe}\nProcessId={os.getpid()}"
            ),
            "CommandLine=python something\nExecutablePath=C:\\Python\\python.exe\nProcessId=222",
        ]
    )

    def fake_run(cmd, **kwargs):
        assert cmd[:3] == ["wmic", "process", "get"]
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(hm.subprocess, "run", fake_run)

    assert hm._scan_windows_hermes_entrypoint_pids(scripts_dir) == [123, 456]


def test_stop_windows_hermes_entrypoint_processes_uses_taskkill_tree(
    tmp_path, monkeypatch
):
    scripts_dir = tmp_path / "venv" / "Scripts"
    calls = []

    monkeypatch.setattr(hm, "_is_windows", lambda: True)
    monkeypatch.setattr(hm, "_scan_windows_hermes_entrypoint_pids", lambda _d: [123])

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(hm.subprocess, "run", fake_run)

    assert hm._stop_windows_hermes_entrypoint_processes(scripts_dir) is True
    assert calls == [["taskkill", "/PID", "123", "/T", "/F"]]


def test_prepare_windows_entrypoint_shims_kills_blockers_and_retries(
    tmp_path, monkeypatch
):
    scripts_dir = tmp_path / "venv" / "Scripts"
    scripts_dir.mkdir(parents=True)
    shim = scripts_dir / "hermes.exe"
    quarantined = scripts_dir / "hermes.exe.old.1"
    attempts = []

    def fake_quarantine(_scripts_dir):
        attempts.append("quarantine")
        if len(attempts) == 1:
            return [], [shim]
        return [(shim, quarantined)], []

    stopped = []
    monkeypatch.setattr(hm, "_quarantine_running_hermes_exe", fake_quarantine)
    monkeypatch.setattr(
        hm,
        "_stop_windows_hermes_entrypoint_processes",
        lambda _scripts_dir: stopped.append(True) or True,
    )

    assert hm._prepare_windows_entrypoint_shims_for_install(scripts_dir) == [
        (shim, quarantined)
    ]
    assert attempts == ["quarantine", "quarantine"]
    assert stopped == [True]


def test_prepare_windows_entrypoint_shims_fails_before_uv_when_still_locked(
    tmp_path, monkeypatch
):
    scripts_dir = tmp_path / "venv" / "Scripts"
    scripts_dir.mkdir(parents=True)
    shim = scripts_dir / "hermes.exe"

    monkeypatch.setattr(
        hm, "_quarantine_running_hermes_exe", lambda _scripts_dir: ([], [shim])
    )
    monkeypatch.setattr(
        hm, "_stop_windows_hermes_entrypoint_processes", lambda _scripts_dir: True
    )

    with pytest.raises(RuntimeError, match="locked Windows entry-point shim"):
        hm._prepare_windows_entrypoint_shims_for_install(scripts_dir)
