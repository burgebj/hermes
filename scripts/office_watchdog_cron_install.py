#!/usr/bin/env python3
"""Install, enable, disable, remove, or smoke-test the Office Watchdog cron job.

This script is intentionally conservative:
- it only copies a runner into the resolved Office profile's HERMES_HOME/scripts/;
- it creates a no-agent cron job that runs dry-run diagnostics only;
- disable pauses by default; remove requires an explicit subcommand;
- status/rollback evidence is profile-aware and fails closed when the intended
  profile has no installed watchdog job.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _reexec_with_repo_venv_if_needed() -> None:
    """Make `python3 scripts/...` work when system Python lacks repo deps.

    Reviewer/operator commands often use `python3` directly, while this repo's
    dependencies live in `.venv`/`venv`.  Re-exec once into the repo venv before
    importing modules that need PyYAML or other installed dependencies.
    """
    if os.environ.get("HERMES_OFFICE_CRON_INSTALL_REEXEC") == "1":
        return
    try:
        import yaml  # noqa: F401
        return
    except ModuleNotFoundError:
        pass
    for candidate in (ROOT / ".venv" / "bin" / "python", ROOT / "venv" / "bin" / "python"):
        if candidate.exists() and candidate.resolve() != Path(sys.executable).resolve():
            os.environ["HERMES_OFFICE_CRON_INSTALL_REEXEC"] = "1"
            os.execv(str(candidate), [str(candidate), *sys.argv])


_reexec_with_repo_venv_if_needed()

from hermes_constants import get_default_hermes_root, get_hermes_home  # noqa: E402

JOB_NAME = "Agent Office Watchdog (no-agent)"
RUNNER_NAME = "office_watchdog_cron.py"
RUNNER_SOURCE = ROOT / "scripts" / RUNNER_NAME
NOT_INSTALLED_EXIT = 2
INTENDED_OFFICE_PROFILE = "telegram"
INTENDED_OFFICE_PROFILE_RATIONALE = (
    "The production Office watchdog must live in a profile whose gateway is already "
    "running so Hermes cron can tick it. DevOps owns the runbook and rollback "
    "evidence, but the scheduler job is installed in the telegram gateway profile "
    "because that is the live local gateway namespace for launch signoff."
)


@dataclass(frozen=True)
class ProfileContext:
    requested_profile: str | None
    active_profile: str
    hermes_home: str
    hermes_root: str
    source: str


def _default_home(root: Path) -> Path:
    return root


def _profile_home(root: Path, profile: str) -> Path:
    if profile == "default":
        return _default_home(root)
    return root / "profiles" / profile


def _profile_name_from_home(home: Path, root: Path) -> str:
    try:
        rel = home.resolve().relative_to(root.resolve())
    except ValueError:
        return os.environ.get("HERMES_PROFILE", "custom") or "custom"
    parts = rel.parts
    if len(parts) >= 2 and parts[0] == "profiles":
        return parts[1]
    if parts == () or str(rel) == ".":
        return "default"
    return os.environ.get("HERMES_PROFILE", "custom") or "custom"


def _read_sticky_profile(root: Path) -> str | None:
    try:
        active_path = root / "active_profile"
        if active_path.exists():
            value = active_path.read_text(encoding="utf-8").strip()
            return value or None
    except OSError:
        return None
    return None


def _resolve_profile_context(args: argparse.Namespace) -> ProfileContext:
    """Resolve and pin the cron namespace before importing cron storage code."""
    explicit_home = getattr(args, "hermes_home", None)
    requested_profile = getattr(args, "profile", None) or os.environ.get("HERMES_OFFICE_PROFILE") or os.environ.get("HERMES_PROFILE")

    if explicit_home:
        home = Path(explicit_home).expanduser().resolve()
        os.environ["HERMES_HOME"] = str(home)
        root = get_default_hermes_root().resolve()
        profile = requested_profile or _profile_name_from_home(home, root)
        source = "--hermes-home"
    elif requested_profile:
        root = get_default_hermes_root().resolve()
        home = _profile_home(root, requested_profile).resolve()
        os.environ["HERMES_HOME"] = str(home)
        profile = requested_profile
        source = "--profile/env"
    elif os.environ.get("HERMES_HOME"):
        home = get_hermes_home().resolve()
        root = get_default_hermes_root().resolve()
        profile = _profile_name_from_home(home, root)
        source = "HERMES_HOME"
    else:
        root = get_default_hermes_root().resolve()
        sticky = _read_sticky_profile(root)
        profile = sticky or "default"
        home = _profile_home(root, profile).resolve()
        os.environ["HERMES_HOME"] = str(home)
        source = "active_profile" if sticky else "default"

    os.environ.setdefault("HERMES_PROFILE", profile)
    return ProfileContext(
        requested_profile=requested_profile,
        active_profile=profile,
        hermes_home=str(home),
        hermes_root=str(root),
        source=source,
    )


def _cron(**kwargs: Any) -> dict:
    # Import lazily after _resolve_profile_context() has pinned HERMES_HOME so
    # cron.jobs module-level paths point at the intended profile namespace.
    from tools.cronjob_tools import cronjob

    result = cronjob(**kwargs)
    return json.loads(result) if isinstance(result, str) else result


def _copy_runner() -> Path:
    scripts_dir = get_hermes_home() / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    dest = scripts_dir / RUNNER_NAME
    shutil.copy2(RUNNER_SOURCE, dest)
    dest.chmod(0o700)
    return dest


def _matching_jobs(include_disabled: bool = True) -> list[dict]:
    result = _cron(action="list", include_disabled=include_disabled)
    jobs = result.get("jobs", []) if result.get("success") else []
    return [j for j in jobs if j.get("name") == JOB_NAME or j.get("script") == RUNNER_NAME]


def _job_summary(job: dict) -> dict:
    return {
        "job_id": job.get("job_id"),
        "name": job.get("name"),
        "enabled": job.get("enabled"),
        "state": job.get("state"),
        "schedule": job.get("schedule"),
        "next_run_at": job.get("next_run_at"),
        "last_run_at": job.get("last_run_at"),
        "last_status": job.get("last_status"),
        "deliver": job.get("deliver"),
        "script": job.get("script"),
        "no_agent": bool(job.get("no_agent")),
        "workdir": job.get("workdir"),
    }


def _installed_jobs(jobs: list[dict]) -> list[dict]:
    return [j for j in jobs if j.get("enabled", True) and j.get("state") != "paused"]


def _run_status_command(command: list[str], timeout: int = 8) -> dict:
    try:
        proc = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return {"available": False, "command": command, "error": "command_not_found"}
    except subprocess.TimeoutExpired as exc:
        return {"available": True, "command": command, "timed_out": True, "stdout": exc.stdout or "", "stderr": exc.stderr or ""}
    return {
        "available": True,
        "command": command,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip()[-2000:],
        "stderr": proc.stderr.strip()[-2000:],
    }


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _runtime_gateway_pids() -> list[int]:
    try:
        from hermes_cli.gateway import find_gateway_pids

        return [int(pid) for pid in find_gateway_pids()]
    except Exception:
        return []


def _liveness_summary(cron_status: dict, gateway_status: dict, installed: list[dict]) -> dict:
    now = datetime.now().astimezone()
    next_times = [_parse_iso_datetime(j.get("next_run_at")) for j in installed]
    next_times = [t for t in next_times if t is not None]
    last_times = [_parse_iso_datetime(j.get("last_run_at")) for j in installed]
    last_times = [t for t in last_times if t is not None]
    pids = _runtime_gateway_pids()
    cron_stdout = str(cron_status.get("stdout") or "")
    gateway_stdout = str(gateway_status.get("stdout") or "")
    cron_reports_running = "Gateway is running" in cron_stdout and "will fire automatically" in cron_stdout
    gateway_status_reports_running = "Gateway is running" in gateway_stdout
    next_run_future = bool(next_times) and min(next_times) > now
    last_run_observed = bool(last_times)
    gateway_runtime_running = bool(pids)
    ok = gateway_runtime_running and cron_reports_running
    return {
        "ok": ok,
        "profile_alignment_ok": True,
        "gateway_runtime_running": gateway_runtime_running,
        "gateway_runtime_pids": pids,
        "gateway_status_reports_running": gateway_status_reports_running,
        "cron_reports_gateway_running": cron_reports_running,
        "next_run_future": next_run_future,
        "last_run_observed": last_run_observed,
        "most_recent_last_run_at": max(last_times).isoformat() if last_times else None,
        "earliest_next_run_at": min(next_times).isoformat() if next_times else None,
        "checked_at": now.isoformat(),
        "rationale": (
            "A stored cron job is not enough for launch signoff; the resolved profile must "
            "also have a live gateway runtime because Hermes cron ticks inside the gateway."
        ),
    }


def _scheduler_status(args: argparse.Namespace, installed: list[dict]) -> dict:
    if getattr(args, "skip_liveness", False):
        return {"checked": False, "reason": "--skip-liveness"}
    cron_status = _run_status_command(["hermes", "cron", "status"])
    gateway_status = _run_status_command(["hermes", "gateway", "status"])
    return {
        "checked": True,
        "summary": _liveness_summary(cron_status, gateway_status, installed),
        "cron_status": cron_status,
        "gateway_status": gateway_status,
    }


def _status_payload(args: argparse.Namespace, *, action: str = "status", changed: list[dict] | None = None) -> dict:
    profile = _resolve_profile_context(args)
    runner = get_hermes_home() / "scripts" / RUNNER_NAME
    jobs = [_job_summary(j) for j in _matching_jobs(include_disabled=True)]
    installed = _installed_jobs(jobs)
    runner_exists = runner.exists()
    installed_ok = runner_exists and bool(installed)
    scheduler_liveness = _scheduler_status(args, installed)
    liveness_ok = (
        not scheduler_liveness.get("checked")
        or bool(scheduler_liveness.get("summary", {}).get("ok"))
    )
    profile_alignment_ok = profile.active_profile == INTENDED_OFFICE_PROFILE
    profile_alignment_required = not getattr(args, "skip_liveness", False)
    if scheduler_liveness.get("checked") and scheduler_liveness.get("summary"):
        scheduler_liveness["summary"]["profile_alignment_ok"] = profile_alignment_ok
    state = "installed" if installed_ok else "not_installed"
    payload = {
        "ok": installed_ok and liveness_ok and (profile_alignment_ok or not profile_alignment_required),
        "action": action,
        "state": state,
        "deployment_profile": {
            "intended_profile": INTENDED_OFFICE_PROFILE,
            "resolved_profile": profile.active_profile,
            "profile_alignment_ok": profile_alignment_ok,
            "rationale": INTENDED_OFFICE_PROFILE_RATIONALE,
        },
        "profile": asdict(profile),
        "hermes_home": str(get_hermes_home()),
        "runner": str(runner),
        "runner_exists": runner_exists,
        "job_ids": [j.get("job_id") for j in jobs if j.get("job_id")],
        "installed_job_ids": [j.get("job_id") for j in installed if j.get("job_id")],
        "jobs": jobs,
        "delivery_targets": sorted({str(j.get("deliver", "local")) for j in jobs}),
        "next_run_at": min((j["next_run_at"] for j in installed if j.get("next_run_at")), default=None),
        "scheduler_liveness": scheduler_liveness,
    }
    if changed is not None:
        payload["changed"] = changed
    if not installed_ok:
        payload["reason"] = "Office watchdog cron runner/job is not installed in the resolved profile namespace."
    return payload


def _print_payload(payload: dict) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def cmd_install(args: argparse.Namespace) -> int:
    profile = _resolve_profile_context(args)
    dest = _copy_runner()
    existing = _matching_jobs(include_disabled=True)
    if existing and not args.replace:
        payload = _status_payload(args, action="install", changed=[])
        payload.update({"changed": False, "runner": str(dest), "profile": asdict(profile)})
        _print_payload(payload)
        return 0 if payload["ok"] else 1
    removed = []
    if existing and args.replace:
        for job in existing:
            removed.append(_cron(action="remove", job_id=job["job_id"]))
    result = _cron(
        action="create",
        name=JOB_NAME,
        schedule=args.schedule,
        prompt="Run the Agent Office Watchdog no-agent runner. Empty stdout means healthy/silent; non-empty stdout is a redacted alert.",
        script=RUNNER_NAME,
        no_agent=True,
        deliver=args.deliver,
        workdir=str(ROOT),
    )
    payload = _status_payload(args, action="install", changed=removed + [result])
    payload["cron_result"] = result
    payload["runner"] = str(dest)
    payload["ok"] = bool(result.get("success")) and bool(payload["ok"])
    _print_payload(payload)
    return 0 if payload["ok"] else 1


def cmd_status(args: argparse.Namespace) -> int:
    payload = _status_payload(args)
    _print_payload(payload)
    if payload["ok"]:
        return 0
    if payload["state"] == "not_installed":
        return 0 if args.allow_missing else NOT_INSTALLED_EXIT
    return 1


def cmd_disable(args: argparse.Namespace) -> int:
    _resolve_profile_context(args)
    changed = []
    for job in _matching_jobs(include_disabled=True):
        if job.get("state") != "paused":
            changed.append(_cron(action="pause", job_id=job["job_id"], reason="Office watchdog rollback/pause via install wrapper"))
    payload = _status_payload(args, action="disable", changed=changed)
    payload["ok"] = True
    _print_payload(payload)
    return 0


def cmd_enable(args: argparse.Namespace) -> int:
    _resolve_profile_context(args)
    changed = []
    for job in _matching_jobs(include_disabled=True):
        if job.get("state") == "paused" or not job.get("enabled", True):
            changed.append(_cron(action="resume", job_id=job["job_id"]))
    payload = _status_payload(args, action="enable", changed=changed)
    _print_payload(payload)
    if payload["ok"]:
        return 0
    return NOT_INSTALLED_EXIT if payload["state"] == "not_installed" else 1


def cmd_remove(args: argparse.Namespace) -> int:
    _resolve_profile_context(args)
    changed = []
    for job in _matching_jobs(include_disabled=True):
        changed.append(_cron(action="remove", job_id=job["job_id"]))
    payload = _status_payload(args, action="remove", changed=changed)
    payload["ok"] = payload["state"] == "not_installed"
    payload["rollback_verified"] = payload["ok"] and not payload["jobs"]
    _print_payload(payload)
    return 0 if payload["rollback_verified"] else 1


def cmd_smoke(args: argparse.Namespace) -> int:
    _resolve_profile_context(args)
    _copy_runner()
    cmd = [sys.executable, str(get_hermes_home() / "scripts" / RUNNER_NAME), "--always-print"]
    if args.json:
        cmd.append("--json")
    proc = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=60)
    payload = _status_payload(args, action="smoke")
    payload.update({"ok": proc.returncode in (0, 1, 2), "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    _print_payload(payload)
    return 0 if proc.returncode in (0, 1, 2) else proc.returncode


def _add_profile_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", help="Intended Hermes profile owning the Office watchdog cron job (default: HERMES_OFFICE_PROFILE, HERMES_PROFILE, HERMES_HOME, active_profile, then default)")
    parser.add_argument("--hermes-home", help="Explicit HERMES_HOME for the intended Office profile; overrides profile path resolution")
    parser.add_argument("--skip-liveness", action="store_true", help="Skip best-effort hermes cron/gateway status checks")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manage the Agent Office Watchdog no-agent cron deployment")
    _add_profile_args(parser)
    sub = parser.add_subparsers(dest="command", required=True)
    install = sub.add_parser("install", help="Copy runner and create the cron job if missing")
    install.add_argument("--schedule", default="every 30m")
    install.add_argument("--deliver", default="telegram")
    install.add_argument("--replace", action="store_true", help="Remove matching jobs and recreate")
    install.set_defaults(func=cmd_install)
    status = sub.add_parser("status", help="Show resolved profile, runner, matching cron jobs, and scheduler status")
    status.add_argument("--allow-missing", action="store_true", help="Return exit 0 even when the watchdog job is not installed")
    status.set_defaults(func=cmd_status)
    sub.add_parser("disable", help="Pause matching cron jobs").set_defaults(func=cmd_disable)
    sub.add_parser("enable", help="Resume paused matching cron jobs").set_defaults(func=cmd_enable)
    sub.add_parser("remove", help="Remove matching cron jobs and verify no stale job remains").set_defaults(func=cmd_remove)
    smoke = sub.add_parser("smoke", help="Copy runner and execute it once with --always-print")
    smoke.add_argument("--json", action="store_true")
    smoke.set_defaults(func=cmd_smoke)
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
