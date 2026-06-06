import types

import pytest

from tui_gateway import slash_worker


def test_orphan_watchdog_is_disabled_without_psutil(monkeypatch):
    started = []

    class _Thread:
        def __init__(self, *args, **kwargs):
            started.append((args, kwargs))

        def start(self):
            raise AssertionError("watchdog thread should not start without psutil")

    monkeypatch.setattr(slash_worker, "psutil", None)
    monkeypatch.setattr(slash_worker.threading, "Thread", _Thread)

    slash_worker._start_orphan_watchdog()

    assert started == []


def test_orphan_watchdog_exits_when_parent_fingerprint_changes(monkeypatch):
    targets = []
    process_create_times = iter([100.0, 101.0])

    class _Thread:
        def __init__(self, target, daemon, name):
            targets.append((target, daemon, name))

        def start(self):
            return None

    def _process(_pid):
        return types.SimpleNamespace(create_time=lambda: next(process_create_times))

    monkeypatch.setattr(slash_worker.os, "getppid", lambda: 1234)
    monkeypatch.setattr(
        slash_worker,
        "psutil",
        types.SimpleNamespace(
            Process=_process,
            pid_exists=lambda _pid: True,
            NoSuchProcess=RuntimeError,
            AccessDenied=PermissionError,
        ),
    )
    monkeypatch.setattr(slash_worker.threading, "Thread", _Thread)
    monkeypatch.setattr(slash_worker.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        slash_worker.os,
        "_exit",
        lambda code: (_ for _ in ()).throw(SystemExit(code)),
    )

    slash_worker._start_orphan_watchdog()

    assert len(targets) == 1
    target, daemon, name = targets[0]
    assert daemon is True
    assert name == "OrphanWatchdog"

    with pytest.raises(SystemExit) as exc:
        target()
    assert exc.value.code == 0
