"""Operator-safe routine visibility for Hermes cron + local service managers.

This module is intentionally read-only. It summarizes scheduled/daemonized
work without printing prompts, script stdout, credentials, or raw environment.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes_cli.config import get_hermes_home

_SECRETISH = re.compile(
    r"(?i)(api[_-]?key|token|secret|password|bearer|auth|credential|cookie)"
)


def _safe_text(value: Any, *, max_len: int = 90) -> str:
    """Return a single-line, secret-safe display string."""
    text = str(value or "").strip()
    if not text:
        return ""
    # Never display explicit secret-bearing assignments/URLs in this status view.
    if _SECRETISH.search(text):
        return "[redacted]"
    text = " ".join(text.split())
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _parse_dt(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _fmt_age(value: Any, *, now: datetime | None = None) -> str:
    dt = _parse_dt(value)
    if not dt:
        return "never"
    now = now or datetime.now(dt.tzinfo or timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    delta = now.astimezone(dt.tzinfo) - dt
    seconds = int(delta.total_seconds())
    suffix = "ago" if seconds >= 0 else "from now"
    seconds = abs(seconds)
    if seconds < 90:
        qty = f"{seconds}s"
    elif seconds < 5400:
        qty = f"{seconds // 60}m"
    elif seconds < 172800:
        qty = f"{seconds // 3600}h"
    else:
        qty = f"{seconds // 86400}d"
    return f"{qty} {suffix}"


def _fmt_schedule(schedule: Any) -> str:
    if isinstance(schedule, dict):
        return _safe_text(schedule.get("display") or schedule.get("expr") or schedule.get("kind"), max_len=32) or "?"
    return _safe_text(schedule, max_len=32) or "?"


def _latest_output_mtime(job_id: str) -> datetime | None:
    root = get_hermes_home() / "cron" / "output" / job_id
    if not root.exists():
        return None
    latest = 0.0
    try:
        for p in root.rglob("*"):
            if p.is_file():
                try:
                    latest = max(latest, p.stat().st_mtime)
                except OSError:
                    pass
    except OSError:
        return None
    if not latest:
        return None
    return datetime.fromtimestamp(latest, tz=timezone.utc).astimezone()


def _classify_job(job: dict[str, Any]) -> str:
    if job.get("no_agent"):
        return "no-agent"
    if job.get("script"):
        return "script+agent"
    if job.get("skills"):
        return "agent+skills"
    return "agent"


def _load_cron_jobs(include_disabled: bool) -> tuple[list[dict[str, Any]], str | None]:
    jobs_file = get_hermes_home() / "cron" / "jobs.json"
    if not jobs_file.exists():
        return [], None
    try:
        data = json.loads(jobs_file.read_text(encoding="utf-8"))
        jobs = data.get("jobs", [])
        if not isinstance(jobs, list):
            return [], "jobs.json has non-list jobs field"
        if not include_disabled:
            jobs = [j for j in jobs if isinstance(j, dict) and j.get("enabled", True)]
        return [j for j in jobs if isinstance(j, dict)], None
    except Exception as exc:
        return [], f"error reading jobs.json: {type(exc).__name__}: {exc}"


def _job_health(job: dict[str, Any], *, now: datetime) -> tuple[str, str]:
    enabled = bool(job.get("enabled", True))
    if not enabled:
        return "paused", "disabled"
    last_status = str(job.get("last_status") or "").strip().lower()
    if last_status and last_status not in {"ok", "success", "completed"}:
        return "bad", f"last={last_status}"
    next_dt = _parse_dt(job.get("next_run_at"))
    if next_dt and next_dt < now.astimezone(next_dt.tzinfo) and (now.astimezone(next_dt.tzinfo) - next_dt).total_seconds() > 900:
        return "warn", "overdue"
    latest_out = _latest_output_mtime(str(job.get("id") or ""))
    last_run = _parse_dt(job.get("last_run_at"))
    if enabled and last_run and not latest_out and job.get("deliver") != "local":
        return "warn", "no saved output"
    return "ok", "ok"


def _format_cron_section(*, include_disabled: bool, limit: int) -> list[str]:
    jobs, error = _load_cron_jobs(include_disabled)
    lines: list[str] = ["Hermes cron"]
    if error:
        lines.append(f"- ERROR: {error}")
        return lines
    active = [j for j in jobs if j.get("enabled", True)]
    disabled = len(jobs) - len(active)
    by_kind: dict[str, int] = {}
    bad_count = 0
    now = datetime.now(timezone.utc).astimezone()
    rows: list[tuple[str, dict[str, Any], str, str]] = []
    for job in jobs:
        kind = _classify_job(job)
        by_kind[kind] = by_kind.get(kind, 0) + 1
        health, reason = _job_health(job, now=now)
        if health in {"bad", "warn"}:
            bad_count += 1
        rows.append((health, job, kind, reason))
    rows.sort(
        key=lambda item: (
            {"bad": 0, "warn": 1, "ok": 2, "paused": 3}.get(item[0], 9),
            _parse_dt(item[1].get("next_run_at")) or datetime.max.replace(tzinfo=timezone.utc),
        )
    )
    summary = f"- {len(active)} active / {len(jobs)} total"
    if disabled:
        summary += f" / {disabled} disabled"
    if bad_count:
        summary += f" / {bad_count} attention"
    if by_kind:
        summary += " · " + ", ".join(f"{k}:{v}" for k, v in sorted(by_kind.items()))
    lines.append(summary)
    if not rows:
        lines.append("- no cron jobs")
        return lines
    for health, job, kind, reason in rows[: max(0, limit)]:
        marker = {"ok": "✓", "warn": "⚠", "bad": "✗", "paused": "○"}.get(health, "?")
        job_id = _safe_text(job.get("id"), max_len=16) or "?"
        name = _safe_text(job.get("name") or job.get("prompt") or "unnamed", max_len=48) or "unnamed"
        sched = _fmt_schedule(job.get("schedule"))
        deliver = _safe_text(job.get("deliver") or "origin", max_len=28) or "origin"
        script = _safe_text(job.get("script"), max_len=36)
        profile = _safe_text(job.get("profile") or "", max_len=20)
        last = _fmt_age(job.get("last_run_at"), now=now)
        nxt = _fmt_age(job.get("next_run_at"), now=now)
        bits = [f"{marker} {job_id}", name, sched, kind]
        if script:
            bits.append(f"script={script}")
        if profile:
            bits.append(f"profile={profile}")
        bits.extend([f"deliver={deliver}", f"last={last}", f"next={nxt}"])
        if reason != "ok":
            bits.append(reason)
        lines.append("- " + " · ".join(bits))
    if len(rows) > limit:
        lines.append(f"- … {len(rows) - limit} more; use --all/raise limit for full list")
    return lines


def _launchd_rows(limit: int) -> list[str]:
    if sys.platform != "darwin":
        return ["Launch services", "- not macOS/launchd"]
    home = Path.home()
    agents = home / "Library" / "LaunchAgents"
    lines = ["Launch services"]
    if not agents.exists():
        lines.append("- no LaunchAgents directory")
        return lines
    candidates: list[Path] = []
    patterns = ("hermes", "morpheus", "nathan", "oracle", "smith", "watchdog")
    try:
        for p in agents.glob("*.plist*"):
            name = p.name.lower()
            if any(s in name for s in patterns):
                candidates.append(p)
    except OSError as exc:
        lines.append(f"- error listing LaunchAgents: {exc}")
        return lines
    if not candidates:
        lines.append("- no Hermes-like LaunchAgents found")
        return lines

    loaded: dict[str, str] = {}
    try:
        out = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        ).stdout
        for line in out.splitlines()[1:]:
            parts = line.split(None, 2)
            if len(parts) >= 3:
                loaded[parts[2]] = parts[0]
    except Exception:
        loaded = {}

    by_label: dict[str, tuple[int, str]] = {}
    for p in sorted(candidates):
        disabled = ".disabled" in p.name or p.suffix.startswith(".disabled") or ".bak" in p.name
        label = p.stem
        if p.suffix == ".plist":
            label = p.name[:-6]
        try:
            text = p.read_text(encoding="utf-8", errors="replace")[:20000]
            m = re.search(r"<key>Label</key>\s*<string>([^<]+)</string>", text)
            if m:
                label = m.group(1)
        except Exception:
            pass
        pid = loaded.get(label)
        state = "disabled-file" if disabled else (f"loaded pid={pid}" if pid and pid != "-" else ("loaded" if pid == "-" else "not-loaded"))
        kind_priority = 0 if "gateway" in label else 1 if "watchdog" in label or "cron" in label else 2
        state_priority = 0 if pid else (2 if not disabled else 4)
        score = kind_priority * 10 + state_priority
        row = f"- {label} · {state}"
        prev = by_label.get(label)
        if prev is None or score < prev[0]:
            by_label[label] = (score, row)
    rows = sorted(by_label.values(), key=lambda x: (x[0], x[1]))
    for _, row in rows[: max(0, limit)]:
        lines.append(row)
    if len(rows) > limit:
        lines.append(f"- … {len(rows) - limit} more LaunchAgents")
    return lines


def build_routines_report(*, include_disabled: bool = False, limit: int = 12, include_launchd: bool = True) -> str:
    """Build a redacted, read-only routines report."""
    limit = max(1, min(int(limit or 12), 100))
    sections = [
        "## Routine status",
        "",
        *_format_cron_section(include_disabled=include_disabled, limit=limit),
    ]
    if include_launchd:
        sections.extend(["", *_launchd_rows(limit=max(6, min(limit, 30)))])
    sections.extend([
        "",
        "Notes: prompts, stdout, credential values, and raw env are intentionally omitted.",
    ])
    return "\n".join(sections)


def cmd_routines(args) -> None:
    print(
        build_routines_report(
            include_disabled=bool(getattr(args, "all", False)),
            limit=int(getattr(args, "limit", 12) or 12),
            include_launchd=not bool(getattr(args, "no_launchd", False)),
        )
    )
