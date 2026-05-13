from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from importlib import util as importlib_util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "office_watchdog_cron_install.py"


def _run(args: list[str], *, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--skip-liveness", *args],
        cwd=str(ROOT),
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )


def _env_for(home: Path, profile: str = "office-prod") -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    env["HERMES_HOME"] = str(home)
    env["HERMES_PROFILE"] = profile
    return env


def _json(proc: subprocess.CompletedProcess[str]) -> dict:
    assert proc.stdout, proc.stderr
    return json.loads(proc.stdout)


def _load_script_module():
    spec = importlib_util.spec_from_file_location("office_watchdog_cron_install_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib_util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_liveness_summary_requires_live_gateway_runtime(monkeypatch):
    module = _load_script_module()
    future = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    past = (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()
    installed = [{"next_run_at": future, "last_run_at": past}]
    cron_status = {"stdout": "✓ Gateway is running — cron jobs will fire automatically\n  PID: 123"}
    gateway_status = {"stdout": "launchd service details may be stale"}

    monkeypatch.setattr(module, "_runtime_gateway_pids", lambda: [123])
    live = module._liveness_summary(cron_status, gateway_status, installed)

    assert live["ok"] is True
    assert live["gateway_runtime_running"] is True
    assert live["cron_reports_gateway_running"] is True
    assert live["next_run_future"] is True
    assert live["last_run_observed"] is True

    monkeypatch.setattr(module, "_runtime_gateway_pids", lambda: [])
    dormant = module._liveness_summary(cron_status, gateway_status, installed)
    assert dormant["ok"] is False
    assert dormant["gateway_runtime_running"] is False


def test_status_fails_closed_with_profile_context_when_watchdog_missing(tmp_path):
    hermes_home = tmp_path / ".hermes" / "profiles" / "office-prod"
    hermes_home.mkdir(parents=True)

    proc = _run(["status"], env=_env_for(hermes_home))

    payload = _json(proc)
    assert proc.returncode == 2
    assert payload["ok"] is False
    assert payload["state"] == "not_installed"
    assert payload["profile"]["active_profile"] == "office-prod"
    assert payload["hermes_home"] == str(hermes_home)
    assert payload["runner"].endswith("scripts/office_watchdog_cron.py")
    assert payload["runner_exists"] is False
    assert payload["jobs"] == []
    assert payload["scheduler_liveness"] == {"checked": False, "reason": "--skip-liveness"}


def test_install_status_remove_are_scoped_to_same_profile_namespace(tmp_path):
    root = tmp_path / ".hermes"
    office_home = root / "profiles" / "office-prod"
    reviewer_home = root / "profiles" / "reviewer"
    office_home.mkdir(parents=True)
    reviewer_home.mkdir(parents=True)

    office_env = _env_for(office_home, profile="office-prod")
    reviewer_env = _env_for(reviewer_home, profile="reviewer")

    install = _run(["install", "--schedule", "every 30m", "--deliver", "local"], env=office_env)
    install_payload = _json(install)
    assert install.returncode == 0, install.stderr
    assert install_payload["ok"] is True
    assert install_payload["state"] == "installed"
    assert install_payload["profile"]["active_profile"] == "office-prod"
    assert install_payload["runner_exists"] is True
    assert install_payload["installed_job_ids"]
    assert install_payload["delivery_targets"] == ["local"]
    assert install_payload["next_run_at"]
    assert install_payload["jobs"][0]["script"] == "office_watchdog_cron.py"
    assert install_payload["jobs"][0]["no_agent"] is True

    office_status = _run(["status"], env=office_env)
    office_status_payload = _json(office_status)
    assert office_status.returncode == 0
    assert office_status_payload["state"] == "installed"
    assert office_status_payload["installed_job_ids"] == install_payload["installed_job_ids"]

    reviewer_status = _run(["status"], env=reviewer_env)
    reviewer_payload = _json(reviewer_status)
    assert reviewer_status.returncode == 2
    assert reviewer_payload["state"] == "not_installed"
    assert reviewer_payload["profile"]["active_profile"] == "reviewer"
    assert reviewer_payload["jobs"] == []

    remove = _run(["remove"], env=office_env)
    remove_payload = _json(remove)
    assert remove.returncode == 0, remove.stderr
    assert remove_payload["state"] == "not_installed"
    assert remove_payload["rollback_verified"] is True
    assert remove_payload["jobs"] == []

    post_remove = _run(["status"], env=office_env)
    post_remove_payload = _json(post_remove)
    assert post_remove.returncode == 2
    assert post_remove_payload["state"] == "not_installed"
    assert post_remove_payload["jobs"] == []
