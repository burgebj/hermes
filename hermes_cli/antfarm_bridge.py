"""Hermes operator bridge for Antfarm Software Factory commands.

Hermes is the operator/control plane. Antfarm remains runtime truth. This
module keeps that boundary explicit by invoking the Antfarm operator CLI for
factory mutations, then optionally annotating Hermes Kanban cards with the
returned FactoryItem/audit identifiers.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import Any, Optional


def _antfarm_bin() -> str:
    return os.environ.get("ANTFARM_BIN", "antfarm")


def _run_antfarm(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        [_antfarm_bin(), "factory", "operator", *args],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit {proc.returncode}"
        raise RuntimeError(f"antfarm operator command failed: {detail}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"antfarm operator returned non-JSON output: {proc.stdout[:500]}") from exc


def _add_optional_flag(cmd: list[str], flag: str, value: Optional[str]) -> None:
    if value:
        cmd.extend([flag, value])


def _bind_kanban_task(*, board: Optional[str], task_id: Optional[str], factory_item_id: str, audit_event_id: str, author: str) -> None:
    if not task_id:
        return
    from hermes_cli import kanban_db as kb

    kb.init_db(board=board)
    conn = kb.connect(board=board)
    body = (
        f"FactoryItem linked: {factory_item_id}\n"
        f"Antfarm dashboard_audit_event: {audit_event_id}"
    )
    kb.add_comment(conn, task_id, author, body)


def build_parser(parent_subparsers: argparse._SubParsersAction) -> argparse.ArgumentParser:
    parser = parent_subparsers.add_parser(
        "antfarm",
        help="Operate Antfarm Software Factory through the orchestrator bridge",
        description=(
            "Hermes-side operator commands for Antfarm Software Factory. "
            "Mutations invoke `antfarm factory operator ...`; Hermes does not "
            "write Antfarm runtime DB tables directly."
        ),
    )
    sub = parser.add_subparsers(dest="antfarm_action")

    p_intake = sub.add_parser("intake", help="Create or link an Antfarm FactoryItem")
    p_intake.add_argument("--title", required=True)
    p_intake.add_argument("--factory-item-id", default=None)
    p_intake.add_argument("--description", default=None)
    p_intake.add_argument("--repo", default=None)
    p_intake.add_argument("--issue-url", default=None)
    p_intake.add_argument("--priority", default=None)
    p_intake.add_argument("--kanban-task", default=None)
    p_intake.add_argument("--board", default=None)
    p_intake.add_argument("--operator", default="hermes")

    p_gate = sub.add_parser("approve-gate", help="Approve or waive a factory gate")
    p_gate.add_argument("--factory-item-id", required=True)
    p_gate.add_argument("--factory-run-id", default=None)
    p_gate.add_argument("--gate", required=True)
    p_gate.add_argument("--evidence-url", default=None)
    p_gate.add_argument("--operator", default="hermes")

    for name in ("pause-run", "resume-run", "retry-run"):
        p_run = sub.add_parser(name, help=f"{name.replace('-', ' ')} through Antfarm orchestrator")
        p_run.add_argument("--factory-run-id", required=True)
        p_run.add_argument("--expected-updated-at", default=None)
        p_run.add_argument("--reason", default=None)
        p_run.add_argument("--operator", default="hermes")

    p_audit = sub.add_parser("audit", help="List Antfarm dashboard audit events")
    p_audit.add_argument("--factory-item-id", default=None)
    p_audit.add_argument("--factory-run-id", default=None)
    p_audit.add_argument("--limit", default=None)

    return parser


def antfarm_command(args: argparse.Namespace) -> int:
    action = getattr(args, "antfarm_action", None)
    if not action:
        print("Missing antfarm action. Use `hermes antfarm --help`.", file=sys.stderr)
        return 2

    try:
        if action == "intake":
            cmd = ["intake", "--title", args.title, "--operator", args.operator, "--source", "hermes-kanban"]
            _add_optional_flag(cmd, "--factory-item-id", args.factory_item_id)
            _add_optional_flag(cmd, "--description", args.description)
            _add_optional_flag(cmd, "--repo", args.repo)
            _add_optional_flag(cmd, "--issue-url", args.issue_url)
            _add_optional_flag(cmd, "--priority", args.priority)
            _add_optional_flag(cmd, "--external-ref", f"kanban:{args.kanban_task}" if args.kanban_task else None)
            result = _run_antfarm(cmd)
            factory_item_id = str(result.get("factory_item_id") or "")
            audit_event_id = str(result.get("audit_event_id") or "")
            if factory_item_id and audit_event_id:
                _bind_kanban_task(
                    board=args.board,
                    task_id=args.kanban_task,
                    factory_item_id=factory_item_id,
                    audit_event_id=audit_event_id,
                    author=args.operator,
                )
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0

        if action == "approve-gate":
            cmd = [
                "approve-gate",
                "--factory-item-id", args.factory_item_id,
                "--gate", args.gate,
                "--operator", args.operator,
            ]
            _add_optional_flag(cmd, "--factory-run-id", args.factory_run_id)
            _add_optional_flag(cmd, "--evidence-url", args.evidence_url)
            print(json.dumps(_run_antfarm(cmd), indent=2, ensure_ascii=False))
            return 0

        if action in {"pause-run", "resume-run", "retry-run"}:
            cmd = [action, "--factory-run-id", args.factory_run_id, "--operator", args.operator]
            _add_optional_flag(cmd, "--expected-updated-at", args.expected_updated_at)
            _add_optional_flag(cmd, "--reason", args.reason)
            print(json.dumps(_run_antfarm(cmd), indent=2, ensure_ascii=False))
            return 0

        if action == "audit":
            cmd = ["audit"]
            _add_optional_flag(cmd, "--factory-item-id", args.factory_item_id)
            _add_optional_flag(cmd, "--factory-run-id", args.factory_run_id)
            _add_optional_flag(cmd, "--limit", args.limit)
            print(json.dumps(_run_antfarm(cmd), indent=2, ensure_ascii=False))
            return 0

        print(f"Unknown antfarm action: {action}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
