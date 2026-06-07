from types import SimpleNamespace

from agent.platform import process as process_mod
from agent.platform.process import ProcessManager


class _Proc:
    pid = 1234

    def __init__(self, *, wait_raises=False):
        self.killed = 0
        self.wait_raises = wait_raises

    def kill(self):
        self.killed += 1

    def wait(self, timeout=None):
        if self.wait_raises:
            raise process_mod.subprocess.TimeoutExpired(["test"], timeout)
        return 0


def test_kill_process_group_windows_uses_taskkill_tree(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", True)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(process_mod.subprocess, "run", fake_run)

    ProcessManager.kill_process_group(_Proc())

    assert calls == [
        (
            ["taskkill", "/T", "/PID", "1234"],
            {"capture_output": True, "timeout": 10},
        )
    ]


def test_kill_process_group_windows_escalates_with_force(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", True)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(process_mod.subprocess, "run", fake_run)

    ProcessManager.kill_process_group(_Proc(wait_raises=True), escalate=True)

    assert calls == [
        ["taskkill", "/T", "/PID", "1234"],
        ["taskkill", "/F", "/T", "/PID", "1234"],
    ]


def test_kill_process_tree_windows_delegates_to_taskkill(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", True)
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(process_mod.subprocess, "run", fake_run)

    ProcessManager.kill_process_tree(_Proc(), escalate=True)

    assert calls == [
        ["taskkill", "/T", "/PID", "1234"],
    ]


def test_kill_process_tree_falls_back_when_psutil_unavailable(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", False)
    monkeypatch.setattr(process_mod, "psutil", None)
    calls = []
    monkeypatch.setattr(process_mod.os, "getpgid", lambda pid: pid, raising=False)
    monkeypatch.setattr(process_mod.os, "killpg", lambda pgid, sig: calls.append((pgid, sig)), raising=False)

    ProcessManager.kill_process_tree(_Proc())

    assert calls == [(1234, process_mod.signal.SIGTERM)]


def test_kill_pid_posix_force_uses_sigterm_fallback_when_sigkill_missing(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", False)
    monkeypatch.delattr(process_mod.signal, "SIGKILL", raising=False)
    calls = []
    monkeypatch.setattr(process_mod.os, "kill", lambda pid, sig: calls.append((pid, sig)))

    ProcessManager.kill_pid(55, force=True)

    assert calls == [(55, process_mod.signal.SIGTERM)]


def test_is_process_alive_uses_psutil_pid_exists(monkeypatch):
    calls = []
    monkeypatch.setattr(
        process_mod,
        "psutil",
        SimpleNamespace(pid_exists=lambda pid: calls.append(pid) or True),
    )

    assert ProcessManager.is_process_alive(77) is True
    assert calls == [77]


def test_is_process_alive_windows_falls_back_when_psutil_unavailable(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", True)
    monkeypatch.setattr(process_mod, "psutil", None)

    def fake_run(cmd, **kwargs):
        assert cmd == ["tasklist", "/FI", "PID eq 77"]
        return SimpleNamespace(returncode=0, stdout="Image Name                     PID\npython.exe                      77\n")

    monkeypatch.setattr(process_mod.subprocess, "run", fake_run)

    assert ProcessManager.is_process_alive(77) is True


def test_setup_new_process_group_returns_none_when_setsid_missing(monkeypatch):
    monkeypatch.setattr(process_mod.platform_info, "is_windows", False)
    monkeypatch.delattr(process_mod.os, "setsid", raising=False)

    assert ProcessManager.setup_new_process_group() is None
