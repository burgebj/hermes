"""Tests for cron _run_job_script Windows-specific fixes (issue #38633).

Bug 1: pythonw.exe loses stdout when spawning child pythonw.exe — the scheduler
should substitute python.exe (console subsystem) from the same dir on Windows.

Bug 2: subprocess.run(text=True) without explicit encoding uses locale encoding
(GBK on Chinese Windows), crashing the reader thread on non-ASCII output. The
scheduler must pass encoding="utf-8", errors="replace".
"""

import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from cron import scheduler as cron_scheduler


@pytest.fixture
def script_path(tmp_path, monkeypatch):
    """Create a script inside an isolated HERMES_HOME/scripts/ directory."""
    home = tmp_path / ".hermes"
    (home / "scripts").mkdir(parents=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    p = home / "scripts" / "job.py"
    p.write_text("print('hi')\n", encoding="utf-8")
    return p


def test_run_job_script_passes_utf8_encoding_and_replace(script_path):
    """Bug 2: subprocess.run must be called with encoding='utf-8', errors='replace'."""
    completed = mock.MagicMock(returncode=0, stdout="ok", stderr="")
    with mock.patch.object(cron_scheduler.subprocess, "run", return_value=completed) as run_mock:
        cron_scheduler._run_job_script(str(script_path))

    assert run_mock.call_count == 1, "subprocess.run should be invoked once"
    kwargs = run_mock.call_args.kwargs
    assert kwargs.get("encoding") == "utf-8", f"expected utf-8 encoding, got {kwargs.get('encoding')!r}"
    assert kwargs.get("errors") == "replace", f"expected errors='replace', got {kwargs.get('errors')!r}"
    assert kwargs.get("text") is True
    assert kwargs.get("capture_output") is True


def test_run_job_script_substitutes_python_exe_for_pythonw_on_windows(script_path, tmp_path):
    """Bug 1: on Windows, pythonw.exe must be swapped for sibling python.exe."""
    fake_dir = tmp_path / "py"
    fake_dir.mkdir()
    pythonw = fake_dir / "pythonw.exe"
    pythonw.write_text("")
    python = fake_dir / "python.exe"
    python.write_text("")

    completed = mock.MagicMock(returncode=0, stdout="", stderr="")
    with mock.patch.object(cron_scheduler.sys, "platform", "win32"), \
         mock.patch.object(cron_scheduler.sys, "executable", str(pythonw)), \
         mock.patch.object(cron_scheduler.subprocess, "run", return_value=completed) as run_mock:
        cron_scheduler._run_job_script(str(script_path))

    argv = run_mock.call_args.args[0]
    assert argv[0] == str(python), f"expected python.exe, got argv={argv!r}"


def test_run_job_script_keeps_pythonw_when_no_sibling_python(script_path, tmp_path):
    """Bug 1 fallback: if no python.exe exists next to pythonw.exe, keep pythonw."""
    fake_dir = tmp_path / "py"
    fake_dir.mkdir()
    pythonw = fake_dir / "pythonw.exe"
    pythonw.write_text("")
    # no python.exe sibling

    completed = mock.MagicMock(returncode=0, stdout="", stderr="")
    with mock.patch.object(cron_scheduler.sys, "platform", "win32"), \
         mock.patch.object(cron_scheduler.sys, "executable", str(pythonw)), \
         mock.patch.object(cron_scheduler.subprocess, "run", return_value=completed) as run_mock:
        cron_scheduler._run_job_script(str(script_path))

    argv = run_mock.call_args.args[0]
    assert argv[0] == str(pythonw)


def test_run_job_script_does_not_substitute_on_non_windows(script_path, tmp_path):
    """Bug 1: pythonw substitution must be Windows-only."""
    fake_dir = tmp_path / "py"
    fake_dir.mkdir()
    pythonw = fake_dir / "pythonw.exe"
    pythonw.write_text("")
    python = fake_dir / "python.exe"
    python.write_text("")

    completed = mock.MagicMock(returncode=0, stdout="", stderr="")
    with mock.patch.object(cron_scheduler.sys, "platform", "linux"), \
         mock.patch.object(cron_scheduler.sys, "executable", str(pythonw)), \
         mock.patch.object(cron_scheduler.subprocess, "run", return_value=completed) as run_mock:
        cron_scheduler._run_job_script(str(script_path))

    argv = run_mock.call_args.args[0]
    assert argv[0] == str(pythonw), "must not rewrite on non-Windows"
