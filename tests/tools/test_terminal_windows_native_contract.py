"""Native Windows terminal execution contract tests.

These tests focus on the failure modes that make Hermes unusable on native
Windows: flashing console windows, empty output, stale Git Bash cwd values,
background process cwd/path drift, and PTY fallback when winpty is absent.
They mock Windows-specific branches where possible so the contract remains
checkable on any CI host.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tools.environments import local as local_mod
from tools.environments.local import LocalEnvironment
from tools.process_registry import ProcessRegistry


class _FakePopen:
    pid = 4321

    def __init__(self):
        self.stdin = None


def test_foreground_windows_popen_uses_native_cwd_and_no_window(monkeypatch, tmp_path):
    """Foreground local commands must use native cwd and CREATE_NO_WINDOW."""
    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    monkeypatch.setattr(local_mod, "_find_bash", lambda: r"C:\Program Files\Git\bin\bash.exe")

    native_cwd = str(tmp_path)
    captured = {}

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return _FakePopen()

    monkeypatch.setattr(local_mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(local_mod.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    with patch.object(LocalEnvironment, "init_session", autospec=True, return_value=None):
        env = LocalEnvironment(cwd="/c/Users/ignored", timeout=10)
    env.cwd = "/c/Users/ignored"

    with patch.object(local_mod, "_resolve_safe_cwd", return_value=native_cwd):
        proc = env._run_bash("echo hi")

    assert proc.pid == 4321
    assert captured["kwargs"]["cwd"] == native_cwd
    assert captured["kwargs"]["creationflags"] == 0x08000000
    assert captured["kwargs"]["preexec_fn"] is None
    assert captured["kwargs"]["stdout"] == subprocess.PIPE
    assert captured["kwargs"]["stderr"] == subprocess.STDOUT
    assert captured["kwargs"]["encoding"] == "utf-8"


def test_windows_find_bash_ignores_wsl_launcher(monkeypatch, tmp_path):
    """Native Windows terminal must not pick the WSL bash.exe shim."""
    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.delenv("HERMES_GIT_BASH_PATH", raising=False)
    monkeypatch.setattr(local_mod.shutil, "which", lambda name: r"C:\Windows\System32\bash.exe")
    monkeypatch.setattr(local_mod.os.path, "isfile", lambda path: False)

    with pytest.raises(RuntimeError, match="WSL bash launcher is not supported"):
        local_mod._find_bash()


def test_windows_find_bash_rejects_bad_explicit_env_path(monkeypatch):
    """A bad HERMES_GIT_BASH_PATH should fail with setup guidance, not be ignored."""
    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    monkeypatch.setenv("HERMES_GIT_BASH_PATH", r"C:\missing\bash.exe")
    monkeypatch.setattr(local_mod.os.path, "isfile", lambda path: False)

    with pytest.raises(RuntimeError) as exc_info:
        local_mod._find_bash()

    message = str(exc_info.value)
    assert "HERMES_GIT_BASH_PATH points at a missing file" in message
    assert "scripts\\install.ps1" in message
    assert "Git for Windows" in message


def test_windows_find_bash_rejects_explicit_wsl_launcher(monkeypatch):
    """HERMES_GIT_BASH_PATH must not opt back into WSL bash."""
    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    monkeypatch.setenv("SystemRoot", r"C:\Windows")
    monkeypatch.setenv("HERMES_GIT_BASH_PATH", r"C:\Windows\System32\bash.exe")
    monkeypatch.setattr(local_mod.os.path, "isfile", lambda path: True)

    with pytest.raises(RuntimeError) as exc_info:
        local_mod._find_bash()

    message = str(exc_info.value)
    assert "HERMES_GIT_BASH_PATH points at the WSL bash launcher" in message
    assert "WSL bash launcher is not supported" in message


def test_windows_find_bash_prefers_portable_git(monkeypatch):
    """Portable Git installed by Hermes wins over PATH, including WSL bash."""
    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    monkeypatch.setenv("LOCALAPPDATA", r"C:\Users\Alice\AppData\Local")
    monkeypatch.delenv("HERMES_GIT_BASH_PATH", raising=False)
    monkeypatch.setattr(local_mod.shutil, "which", lambda name: r"C:\Windows\System32\bash.exe")

    portable = r"C:\Users\Alice\AppData\Local\hermes\git\bin\bash.exe"

    def fake_isfile(path):
        return path == portable

    monkeypatch.setattr(local_mod.os.path, "isfile", fake_isfile)

    assert local_mod._find_bash() == portable


def test_foreground_execute_round_trip_output_and_cwd_when_bash_available(monkeypatch, tmp_path):
    """Real smoke test: local terminal returns output and persists cwd."""
    try:
        local_mod._find_bash()
    except RuntimeError:
        pytest.skip("Git Bash/bash is not available on this host")

    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    env = LocalEnvironment(cwd=str(first), timeout=15)
    second_for_bash = str(second).replace("\\", "/")
    result = env.execute(f"cd {shlex.quote(second_for_bash)} && printf 'hermes-output-ok'")

    assert result["returncode"] == 0
    assert "hermes-output-ok" in result["output"]
    assert Path(env.cwd).resolve() == second.resolve()


def test_windows_temp_dir_falls_back_when_hermes_cache_is_not_writable(monkeypatch, tmp_path):
    """Terminal startup must survive a locked/unwritable HERMES_HOME cache."""
    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    fallback_root = tmp_path / "system-temp"
    fallback_root.mkdir()

    class FakeHermesHomePath:
        def __truediv__(self, part):
            return FakeHermesHomePath()

        def mkdir(self, *args, **kwargs):
            raise PermissionError("Access is denied")

        def __str__(self):
            return r"C:\Users\Josh\.hermes\cache\terminal"

    class FakeTempPath:
        def __init__(self, value):
            self.value = Path(value)

        def __truediv__(self, part):
            return FakeTempPath(self.value / part)

        def mkdir(self, *args, **kwargs):
            self.value.mkdir(*args, **kwargs)

        def __str__(self):
            return str(self.value)

    def fake_path(value):
        if str(value) == str(fallback_root):
            return FakeTempPath(value)
        return Path(value)

    monkeypatch.setattr("hermes_constants.get_hermes_home", lambda: FakeHermesHomePath())
    monkeypatch.setattr(local_mod.tempfile, "gettempdir", lambda: str(fallback_root))
    monkeypatch.setattr(local_mod, "Path", fake_path)

    with patch.object(LocalEnvironment, "init_session", autospec=True, return_value=None):
        env = LocalEnvironment(cwd=str(tmp_path), timeout=10)

    tmp_dir = env.get_temp_dir()
    assert tmp_dir == str(fallback_root / "hermes_terminal").replace("\\", "/")
    assert (fallback_root / "hermes_terminal").is_dir()


def test_background_windows_spawn_normalizes_cwd_and_hides_window(monkeypatch, tmp_path):
    """Background local commands should not inherit MSYS cwd or flash windows."""
    import tools.process_registry as pr_mod

    monkeypatch.setattr(pr_mod.platform_info, "is_windows", True)
    monkeypatch.setattr(pr_mod, "_find_shell", lambda: r"C:\Program Files\Git\bin\bash.exe")
    monkeypatch.setattr(pr_mod.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    native_cwd = str(tmp_path)
    captured = {}

    class FakeProcess:
        pid = 9876
        stdout = None

        def poll(self):
            return None

    def fake_popen(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return FakeProcess()

    monkeypatch.setattr(pr_mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(pr_mod, "_resolve_safe_cwd", lambda cwd: native_cwd)
    monkeypatch.setattr(pr_mod.threading.Thread, "start", lambda self: None)
    monkeypatch.setattr(ProcessRegistry, "_write_checkpoint", lambda self: None)

    registry = ProcessRegistry()
    session = registry.spawn_local("printf hi", cwd="/c/Users/ignored")

    assert session.cwd == native_cwd
    assert captured["kwargs"]["cwd"] == native_cwd
    assert captured["kwargs"]["creationflags"] == 0x08000000
    assert captured["kwargs"]["preexec_fn"] is None
    assert captured["kwargs"]["stdout"] == subprocess.PIPE
    assert captured["kwargs"]["stderr"] == subprocess.STDOUT


def test_process_registry_uses_reentrant_lock_for_checkpoint_write():
    """spawn_local writes checkpoints while holding the registry lock."""
    import threading

    registry = ProcessRegistry()
    assert isinstance(registry._lock, type(threading.RLock()))


def test_process_registry_checkpoint_write_timeout_does_not_block_spawn(monkeypatch):
    """A wedged Windows checkpoint write must not block background spawn forever."""
    import time
    import utils

    monkeypatch.setattr(local_mod, "_IS_WINDOWS", True)
    import tools.process_registry as pr_mod

    monkeypatch.setattr(pr_mod, "_IS_WINDOWS", True)
    monkeypatch.setattr(pr_mod, "_find_shell", lambda: r"C:\Program Files\Git\bin\bash.exe")
    monkeypatch.setattr(pr_mod, "_resolve_safe_cwd", lambda cwd: cwd or os.getcwd())
    monkeypatch.setattr(pr_mod.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)

    class FakeProcess:
        pid = 1010
        stdout = None
        returncode = 0

        def poll(self):
            return self.returncode

    monkeypatch.setattr(pr_mod.subprocess, "Popen", lambda *args, **kwargs: FakeProcess())

    def stuck_atomic_write(*args, **kwargs):
        time.sleep(5)

    monkeypatch.setattr(utils, "atomic_json_write", stuck_atomic_write)

    registry = ProcessRegistry()
    started = time.monotonic()
    session = registry.spawn_local("printf hi", cwd=os.getcwd())
    elapsed = time.monotonic() - started

    assert session.pid == 1010
    assert elapsed < 3.0
    assert registry._checkpoint_write_disabled is True


def test_real_background_spawn_wait_output_when_shell_available(monkeypatch, tmp_path):
    """Real background local spawn must return, capture output, and exit."""
    import tools.process_registry as pr_mod

    try:
        local_mod._find_bash()
    except RuntimeError:
        pytest.skip("Git Bash/bash is not available on this host")

    monkeypatch.setattr(pr_mod, "CHECKPOINT_PATH", tmp_path / "processes.json")

    registry = ProcessRegistry()
    session = registry.spawn_local(
        command="printf bg-ok; pwd -P",
        cwd=str(tmp_path),
        use_pty=False,
    )
    result = registry.wait(session.id, timeout=10)

    assert result["status"] == "exited"
    assert result["exit_code"] == 0
    assert "bg-ok" in result["output"]


def test_background_windows_pty_missing_falls_back_to_pipe(monkeypatch, tmp_path):
    """PTY=True on Windows must gracefully fall back if winpty is unavailable."""
    import tools.process_registry as pr_mod

    monkeypatch.setattr(pr_mod.platform_info, "is_windows", True)
    monkeypatch.setitem(sys.modules, "winpty", None)
    monkeypatch.setattr(pr_mod, "_find_shell", lambda: r"C:\Program Files\Git\bin\bash.exe")
    monkeypatch.setattr(pr_mod.subprocess, "CREATE_NO_WINDOW", 0x08000000, raising=False)
    monkeypatch.setattr(pr_mod, "_resolve_safe_cwd", lambda cwd: str(tmp_path))

    class FakeProcess:
        pid = 2468
        stdout = None

        def poll(self):
            return None

    monkeypatch.setattr(pr_mod.subprocess, "Popen", lambda *a, **kw: FakeProcess())
    monkeypatch.setattr(pr_mod.threading.Thread, "start", lambda self: None)
    monkeypatch.setattr(ProcessRegistry, "_write_checkpoint", lambda self: None)

    registry = ProcessRegistry()
    session = registry.spawn_local("python -i", cwd=str(tmp_path), use_pty=True)

    assert session.pid == 2468
    assert session.process is not None
    assert session._pty is None


def test_terminal_tool_background_uses_registry_cwd_and_pty_fallback_contract(monkeypatch, tmp_path):
    """terminal(background=True) passes workdir and pty intent to the registry."""
    import tools.terminal_tool as terminal_tool_module
    from tools import process_registry as process_registry_module

    config = {
        "env_type": "local",
        "docker_image": "",
        "singularity_image": "",
        "modal_image": "",
        "daytona_image": "",
        "cwd": str(tmp_path),
        "timeout": 30,
    }
    dummy_env = SimpleNamespace(env={})
    captured = {}

    def fake_spawn_local(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(id="proc_contract", pid=1357, notify_on_complete=False)

    monkeypatch.setattr(terminal_tool_module, "_get_env_config", lambda: config)
    monkeypatch.setattr(terminal_tool_module, "_start_cleanup_thread", lambda: None)
    monkeypatch.setattr(
        terminal_tool_module,
        "_check_all_guards",
        lambda *_args, **_kwargs: {"approved": True},
    )
    monkeypatch.setattr(process_registry_module.process_registry, "spawn_local", fake_spawn_local)
    monkeypatch.setitem(terminal_tool_module._active_environments, "default", dummy_env)
    monkeypatch.setitem(terminal_tool_module._last_activity, "default", 0.0)

    try:
        terminal_tool_module.terminal_tool(
            command="python -i",
            background=True,
            workdir=str(tmp_path),
            pty=True,
        )
    finally:
        terminal_tool_module._active_environments.pop("default", None)
        terminal_tool_module._last_activity.pop("default", None)

    assert captured["cwd"] == str(tmp_path)
    assert captured["use_pty"] is True
