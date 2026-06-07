"""Tests for the terminal / execute_code write-safe-root guard (#36645).

The ``terminal`` and ``execute_code`` tools bypass ``HERMES_WRITE_SAFE_ROOT``
(which only the native Write/Edit tools honor). These cover the best-effort
static scan that surfaces out-of-safe-root writes to the model.
"""

import os
from pathlib import Path

import pytest

from agent.file_safety import (
    build_unsafe_write_warning,
    find_unsafe_code_writes,
    find_unsafe_shell_writes,
    get_terminal_write_guard_mode,
)


@pytest.fixture
def safe_root(tmp_path: Path, monkeypatch) -> str:
    """A configured safe root plus a sibling 'outside' dir, both real dirs."""
    root = tmp_path / "session_workdir"
    root.mkdir()
    (tmp_path / "outside").mkdir()
    monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(root))
    return os.path.realpath(str(root))


class TestGuardMode:
    def test_default_is_warn(self, monkeypatch):
        monkeypatch.delenv("HERMES_TERMINAL_WRITE_GUARD", raising=False)
        assert get_terminal_write_guard_mode() == "warn"

    def test_explicit_modes(self, monkeypatch):
        for mode in ("off", "warn", "block"):
            monkeypatch.setenv("HERMES_TERMINAL_WRITE_GUARD", mode)
            assert get_terminal_write_guard_mode() == mode

    def test_unknown_falls_back_to_warn(self, monkeypatch):
        monkeypatch.setenv("HERMES_TERMINAL_WRITE_GUARD", "banana")
        assert get_terminal_write_guard_mode() == "warn"


class TestNoOpWithoutSafeRoot:
    def test_shell_scan_inert_without_safe_root(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HERMES_WRITE_SAFE_ROOT", raising=False)
        outside = tmp_path / "anywhere" / "x.txt"
        assert find_unsafe_shell_writes(f"echo hi > {outside}") == []

    def test_code_scan_inert_without_safe_root(self, monkeypatch):
        monkeypatch.delenv("HERMES_WRITE_SAFE_ROOT", raising=False)
        assert find_unsafe_code_writes("open('/etc/x','w')") == []


class TestShellWriteScan:
    def test_redirect_outside_is_flagged(self, safe_root, tmp_path):
        outside = tmp_path / "outside" / "evil.conf"
        hits = find_unsafe_shell_writes(f"echo hi > {outside}", str(tmp_path))
        assert os.path.realpath(str(outside)) in hits

    def test_append_redirect_outside_is_flagged(self, safe_root, tmp_path):
        outside = tmp_path / "outside" / "log.txt"
        hits = find_unsafe_shell_writes(f"echo x >> {outside}", str(tmp_path))
        assert os.path.realpath(str(outside)) in hits

    def test_write_inside_safe_root_is_clean(self, safe_root):
        inside = os.path.join(safe_root, "ok.txt")
        assert find_unsafe_shell_writes(f"echo hi > {inside}", safe_root) == []

    def test_relative_write_inside_safe_root_is_clean(self, safe_root):
        # Relative path resolved against the safe root (cwd) stays inside.
        assert find_unsafe_shell_writes("echo hi > out.txt", safe_root) == []

    def test_cp_destination_outside_is_flagged(self, safe_root, tmp_path):
        dest = tmp_path / "outside" / "copy.txt"
        hits = find_unsafe_shell_writes(f"cp a.txt {dest}", str(tmp_path))
        assert os.path.realpath(str(dest)) in hits

    def test_touch_multiple_targets(self, safe_root, tmp_path):
        outside = tmp_path / "outside"
        cmd = f"touch {outside}/a.log {outside}/b.log"
        hits = find_unsafe_shell_writes(cmd, str(tmp_path))
        assert os.path.realpath(str(outside / "a.log")) in hits
        assert os.path.realpath(str(outside / "b.log")) in hits

    def test_dd_of_target(self, safe_root, tmp_path):
        dest = tmp_path / "outside" / "img.bin"
        hits = find_unsafe_shell_writes(
            f"dd if=/dev/zero of={dest} bs=1 count=1", str(tmp_path)
        )
        assert os.path.realpath(str(dest)) in hits

    def test_temp_dir_writes_excluded_when_safe_root_outside_temp(self, monkeypatch):
        # When the safe root is a normal project dir, scratch writes to the
        # system temp dir are noise and get excluded from the signal.
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", "/opt/hermes_ws_nonexistent")
        assert find_unsafe_shell_writes(
            "echo hi > /tmp/scratch_xyz.txt", "/opt/hermes_ws_nonexistent"
        ) == []

    def test_temp_sibling_flagged_when_safe_root_inside_temp(self, safe_root):
        # Broker layout: safe root lives under /tmp. A write to a sibling
        # /tmp path is a real leak (#36645) and must NOT be temp-excluded.
        # ``safe_root`` fixture lives under the pytest temp dir.
        sibling = os.path.join(os.path.dirname(safe_root), "other", "leak.txt")
        hits = find_unsafe_shell_writes(f"echo hi > {sibling}", os.path.dirname(safe_root))
        assert os.path.realpath(sibling) in hits

    def test_cd_then_python_open_relative_repro(self, safe_root, tmp_path):
        # The exact #36645 repro: cd outside the safe root, then a relative
        # write inside a python3 -c payload resolves against the cd'd dir.
        outside = tmp_path / "outside"
        cmd = (
            f"cd {outside} && python3 -c \"open('boss_login_qr.png','wb')"
            f".write(b'x')\""
        )
        hits = find_unsafe_shell_writes(cmd, str(tmp_path))
        assert os.path.realpath(str(outside / "boss_login_qr.png")) in hits

    def test_cd_inside_safe_root_relative_write_clean(self, safe_root):
        cmd = f"cd {safe_root} && python3 -c \"open('out.png','wb').write(b'x')\""
        assert find_unsafe_shell_writes(cmd, os.path.dirname(safe_root)) == []

    def test_read_only_command_is_clean(self, safe_root, tmp_path):
        # Reads / listings outside the safe root are fine — only writes flagged.
        assert find_unsafe_shell_writes("cat /etc/hosts && ls /var", str(tmp_path)) == []


class TestCodeWriteScan:
    def test_open_write_mode_outside_flagged(self, safe_root, tmp_path):
        target = tmp_path / "outside" / "out.bin"
        hits = find_unsafe_code_writes(f"open('{target}','wb').write(b'x')", str(tmp_path))
        assert os.path.realpath(str(target)) in hits

    def test_open_read_mode_not_flagged(self, safe_root, tmp_path):
        target = tmp_path / "outside" / "in.txt"
        assert find_unsafe_code_writes(f"open('{target}','r').read()", str(tmp_path)) == []

    def test_write_text_helper_flagged(self, safe_root, tmp_path):
        target = tmp_path / "outside" / "note.txt"
        code = f"from pathlib import Path; Path('{target}').write_text('y')"
        hits = find_unsafe_code_writes(code, str(tmp_path))
        assert os.path.realpath(str(target)) in hits

    def test_write_inside_safe_root_clean(self, safe_root):
        inside = os.path.join(safe_root, "out.bin")
        assert find_unsafe_code_writes(f"open('{inside}','wb')", safe_root) == []


class _FakeEnv:
    def __init__(self, cwd: str):
        self.cwd = cwd
        self.env = {}
        self.executed = []

    def execute(self, command, **kwargs):
        self.executed.append((command, kwargs))
        return {"output": "", "returncode": 0}


class TestTerminalToolWiring:
    """End-to-end wiring of the guard into terminal_tool (#36645)."""

    def _setup(self, monkeypatch, safe_root_dir, mode):
        import json as _json

        import tools.terminal_tool as tt

        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe_root_dir))
        monkeypatch.setenv("HERMES_TERMINAL_WRITE_GUARD", mode)
        monkeypatch.setattr(
            tt, "_get_env_config",
            lambda: {"env_type": "local", "cwd": str(safe_root_dir), "timeout": 30},
        )
        monkeypatch.setattr(tt, "_resolve_container_task_id", lambda task_id: "t")
        fake = _FakeEnv(str(safe_root_dir))
        tt._active_environments["t"] = fake
        tt._last_activity["t"] = 0
        return tt, fake, _json

    def test_block_mode_refuses_out_of_root_write(self, monkeypatch, tmp_path):
        safe = tmp_path / "ws"
        safe.mkdir()
        (tmp_path / "outside").mkdir()
        tt, fake, _json = self._setup(monkeypatch, safe, "block")
        outside = tmp_path / "outside" / "leak.txt"

        out = _json.loads(tt.terminal_tool(command=f"echo hi > {outside}"))

        assert out["status"] == "blocked"
        assert "BLOCKED" in out["error"]
        # Blocked before execution — the command never ran.
        assert fake.executed == []

    def test_warn_mode_runs_and_attaches_warning(self, monkeypatch, tmp_path):
        safe = tmp_path / "ws"
        safe.mkdir()
        (tmp_path / "outside").mkdir()
        tt, fake, _json = self._setup(monkeypatch, safe, "warn")
        outside = tmp_path / "outside" / "leak.txt"

        out = _json.loads(tt.terminal_tool(command=f"echo hi > {outside}"))

        assert out["exit_code"] == 0
        assert "safe_root_warning" in out
        assert "WARNING" in out["safe_root_warning"]
        # Warn mode still executes the command.
        assert len(fake.executed) == 1

    def test_warn_mode_clean_command_no_warning(self, monkeypatch, tmp_path):
        safe = tmp_path / "ws"
        safe.mkdir()
        tt, fake, _json = self._setup(monkeypatch, safe, "warn")
        inside = safe / "ok.txt"

        out = _json.loads(tt.terminal_tool(command=f"echo hi > {inside}"))

        assert "safe_root_warning" not in out

    def test_off_mode_disables_guard(self, monkeypatch, tmp_path):
        safe = tmp_path / "ws"
        safe.mkdir()
        (tmp_path / "outside").mkdir()
        tt, fake, _json = self._setup(monkeypatch, safe, "off")
        outside = tmp_path / "outside" / "leak.txt"

        out = _json.loads(tt.terminal_tool(command=f"echo hi > {outside}"))

        assert out.get("status") != "blocked"
        assert "safe_root_warning" not in out


class TestWarningBuilder:
    def test_warn_message_lists_targets(self, safe_root):
        msg = build_unsafe_write_warning(["/a/b.txt", "/c/d.txt"], blocked=False)
        assert "WARNING" in msg
        assert "/a/b.txt" in msg
        assert "not a security boundary" in msg

    def test_block_message(self, safe_root):
        msg = build_unsafe_write_warning(["/a/b.txt"], blocked=True)
        assert "BLOCKED" in msg
        assert "refused" in msg

    def test_truncates_long_lists(self, safe_root):
        targets = [f"/x/f{i}.txt" for i in range(25)]
        msg = build_unsafe_write_warning(targets, blocked=False)
        assert "and 15 more" in msg
