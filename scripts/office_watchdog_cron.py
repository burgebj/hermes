#!/usr/bin/env python3
"""Quiet no-agent cron runner for Agent Office Watchdog/Doctor.

Empty stdout means "healthy/silent" for Hermes no-agent cron jobs. Non-empty
stdout is a redacted operational alert that can be delivered to Telegram or the
configured cron target.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

def _repo_root() -> Path:
    """Resolve the Hermes Agent checkout when this script is copied to HERMES_HOME/scripts."""
    cwd = Path.cwd().resolve()
    if (cwd / "hermes_cli" / "office_superpowers.py").exists():
        return cwd
    from_env = Path(str(__import__("os").environ.get("HERMES_REPO_ROOT", ""))).expanduser()
    if str(from_env) and (from_env / "hermes_cli" / "office_superpowers.py").exists():
        return from_env.resolve()
    return Path(__file__).resolve().parents[1]


ROOT = _repo_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from hermes_cli.office_superpowers import (  # noqa: E402
    build_doctor_report,
    build_watchdog_report,
    format_watchdog_text,
    get_hermes_home,
    redact_obj,
)


def _has_doctor_alert(report: dict) -> bool:
    return str(report.get("overall_status") or "pass").lower() == "fail"


def build_cron_payload(*, board: str | None = None, outbox_path: str | None = None) -> dict:
    doctor = build_doctor_report(board=board, include_log_tail=False)
    watchdog = build_watchdog_report(board=board, dry_run=True, outbox_path=outbox_path)
    payload = {
        "schema_version": 1,
        "source": "office_watchdog_cron",
        "doctor_overall_status": doctor.get("overall_status"),
        "watchdog_summary": watchdog.get("summary", {}),
        "watchdog_findings": watchdog.get("findings", []),
        "alerts": [],
    }
    if _has_doctor_alert(doctor):
        payload["alerts"].append(
            {
                "severity": "critical",
                "issue_type": "office_doctor_failed",
                "recommendation": "run python3 scripts/office_doctor.py --json and inspect failing sections",
            }
        )
    payload["alerts"].extend(watchdog.get("findings", []))
    return redact_obj(payload)[0]


def format_cron_alert(payload: dict) -> str:
    alerts = payload.get("alerts") or []
    if not alerts:
        return ""
    lines = [
        "Agent Office Watchdog alert",
        f"doctor: {payload.get('doctor_overall_status')}",
        f"watchdog: {json.dumps(payload.get('watchdog_summary', {}), sort_keys=True)}",
    ]
    for item in alerts[:20]:
        lines.append(
            f"- {item.get('severity', 'warning')} {item.get('issue_type', 'unknown')} "
            f"task={item.get('task_id', '-')} :: {item.get('recommendation', 'inspect Office Doctor/Watchdog output')}"
        )
    if len(alerts) > 20:
        lines.append(f"... {len(alerts) - 20} more alert(s) truncated")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Quiet Agent Office no-agent cron watchdog")
    parser.add_argument("--board", default=None)
    parser.add_argument("--outbox-path", default=str(get_hermes_home() / "office" / "report-outbox.jsonl"))
    parser.add_argument("--json", action="store_true", help="Print JSON payload when alerts exist")
    parser.add_argument("--always-print", action="store_true", help="Print even when healthy; for smoke tests only")
    args = parser.parse_args(argv)

    payload = build_cron_payload(board=args.board, outbox_path=args.outbox_path)
    has_alerts = bool(payload.get("alerts"))
    if not has_alerts and not args.always_print:
        return 0
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        text = format_cron_alert(payload)
        if text:
            print(text, end="")
        elif args.always_print:
            print("Agent Office Watchdog smoke: no alerts")
    critical = any(str(a.get("severity")) == "critical" for a in payload.get("alerts", []))
    return 2 if critical else (1 if has_alerts else 0)


if __name__ == "__main__":
    raise SystemExit(main())
