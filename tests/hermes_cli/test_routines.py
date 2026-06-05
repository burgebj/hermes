import json
from types import SimpleNamespace

from hermes_cli import routines


def test_routines_report_redacts_prompt_and_secretish_names(monkeypatch, tmp_path):
    home = tmp_path / "hermes"
    cron = home / "cron"
    cron.mkdir(parents=True)
    (cron / "jobs.json").write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "abc123",
                        "name": "TOKEN_ROTATION should hide",
                        "prompt": "do not print this prompt with sk-live-secret",
                        "schedule": {"display": "every 10m"},
                        "enabled": True,
                        "last_status": "ok",
                        "last_run_at": "2026-01-01T00:00:00+00:00",
                        "next_run_at": "2099-01-01T00:00:00+00:00",
                        "deliver": "telegram:-100123456",
                        "script": "safe_watchdog.py",
                        "no_agent": True,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(routines, "get_hermes_home", lambda: home)
    report = routines.build_routines_report(include_disabled=False, include_launchd=False, limit=5)
    assert "abc123" in report
    assert "safe_watchdog.py" in report
    assert "[redacted]" in report
    assert "sk-live-secret" not in report
    assert "do not print this prompt" not in report


def test_cmd_routines_prints(monkeypatch, capsys, tmp_path):
    home = tmp_path / "hermes"
    (home / "cron").mkdir(parents=True)
    (home / "cron" / "jobs.json").write_text('{"jobs": []}', encoding="utf-8")
    monkeypatch.setattr(routines, "get_hermes_home", lambda: home)
    routines.cmd_routines(SimpleNamespace(all=False, limit=3, no_launchd=True))
    out = capsys.readouterr().out
    assert "Routine status" in out
    assert "no cron jobs" in out
