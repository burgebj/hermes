"""Tests for cron.scheduler.heartbeat_loop (gateway-liveness heartbeat).

Covers:
  - heartbeat stays fresh while a long job holds the .tick.lock flock
    (the liveness signal is decoupled from tick execution)
  - alive_check() False -> file is never created/bumped (a hung event loop
    must NOT keep the heartbeat alive, or real outages would be masked)
  - stop_event.set() -> loop exits promptly
  - bump is a path-based touch + os.utime; file is auto-created
  - an explicit heartbeat_path wins over the process-global Hermes home
    (race-safe when a tick job transiently mutates the global)
"""

from __future__ import annotations

import fcntl
import threading
import time
from pathlib import Path

import cron.scheduler as sched


def _run_loop(home: Path, alive, interval=0.05, heartbeat_path=None):
    """Start heartbeat_loop bound to `home` in a thread; return (stop, thread)."""
    sched._hermes_home = home  # monkeypatch hook honored by _get_hermes_home()
    stop = threading.Event()
    kwargs = {"interval": interval}
    if heartbeat_path is not None:
        kwargs["heartbeat_path"] = heartbeat_path
    t = threading.Thread(
        target=sched.heartbeat_loop,
        args=(stop, alive),
        kwargs=kwargs,
        daemon=True,
        name="test-heartbeat",
    )
    t.start()
    return stop, t


def test_bumps_while_tick_lock_held(tmp_path):
    """Heartbeat stays fresh even while a long job holds the tick flock."""
    home = tmp_path
    hb = home / "cron" / ".gateway.heartbeat"
    (home / "cron").mkdir(parents=True, exist_ok=True)
    # Simulate a long sequential job: hold an exclusive flock on .tick.lock
    # in THIS thread for the whole test.
    lock_fd = open(home / "cron" / ".tick.lock", "w")
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    stop, t = _run_loop(home, lambda: True)
    try:
        time.sleep(0.4)  # several 0.05s cycles
        assert hb.exists(), "heartbeat file should be created"
        m1 = hb.stat().st_mtime
        time.sleep(0.4)
        m2 = hb.stat().st_mtime
        assert m2 >= m1, "heartbeat mtime should advance while job blocks"
        assert time.time() - m2 < 2.0, "heartbeat must be fresh despite tick lock held"
    finally:
        stop.set()
        t.join(timeout=2)
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()


def test_no_bump_when_not_alive(tmp_path):
    """alive_check() False => file must never be created/bumped."""
    home = tmp_path
    hb = home / "cron" / ".gateway.heartbeat"
    stop, t = _run_loop(home, lambda: False)
    try:
        time.sleep(0.4)
        assert not hb.exists(), (
            "heartbeat must NOT be bumped when alive_check is False"
        )
    finally:
        stop.set()
        t.join(timeout=2)


def test_stops_promptly_on_stop_event(tmp_path):
    stop, t = _run_loop(tmp_path, lambda: True, interval=5.0)
    time.sleep(0.2)
    stop.set()
    t.join(timeout=2)
    assert not t.is_alive(), "heartbeat_loop should exit promptly on stop_event"


def test_path_based_autocreate(tmp_path):
    home = tmp_path
    hb = home / "cron" / ".gateway.heartbeat"
    assert not hb.exists()
    stop, t = _run_loop(home, lambda: True)
    try:
        time.sleep(0.3)
        assert hb.exists(), "heartbeat file auto-created via touch(exist_ok)"
    finally:
        stop.set()
        t.join(timeout=2)


def test_explicit_path_honored_over_global(tmp_path):
    """Explicit heartbeat_path wins over the (mutable) global Hermes home.

    Simulates the cross-thread race: the global _hermes_home points at a WRONG
    profile, but the gateway passed an explicit path resolved on the main
    thread. The bump must land at the explicit path, never the global one.
    """
    good = tmp_path / "good"
    wrong = tmp_path / "wrong"
    good.mkdir()
    wrong.mkdir()
    good_hb = good / "cron" / ".gateway.heartbeat"
    wrong_hb = wrong / "cron" / ".gateway.heartbeat"
    stop, t = _run_loop(wrong, lambda: True, heartbeat_path=good_hb)
    try:
        time.sleep(0.3)
        assert good_hb.exists(), "bump must land at the explicit path"
        assert not wrong_hb.exists(), "bump must NOT use the mutated global home"
    finally:
        stop.set()
        t.join(timeout=2)
