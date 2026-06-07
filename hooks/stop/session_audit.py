#!/usr/bin/env python3
"""
Post-session audit hook — writes a YAML audit record on every session-end event.

If the stop payload contains an 'improvement' field, also writes an evolution
proposal to a separate directory.

Fails loudly (stderr + non-zero exit) on any write failure. Never silent.
Stdlib only: json, os, sys, pathlib, datetime.

Configuration:
  HERMES_AUDIT_DIR     — directory for audit YAML files (default: ~/.hermes/audits)
  HERMES_PROPOSALS_DIR — directory for evolution proposal YAML files
                         (default: ~/.hermes/proposals)

Usage:
  As a Claude Code stop hook:
    Add to .claude/settings.json:
      {"hooks": {"Stop": [{"hooks": [{"type": "command",
        "command": "python3 ~/.hermes/hooks/session_audit.py"}]}]}}

  As a Hermes shell hook (on_session_finalize event):
    Add to ~/.hermes/config.yaml:
      hooks:
        on_session_finalize:
          - python3 ~/.hermes/hooks/session_audit.py
"""
import json
import os
import pathlib
import sys
from datetime import datetime, timezone


def _yaml_scalar(value):
    if value is None or value == "":
        return '""'
    s = str(value)
    if any(c in s for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|',
                             '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    if '\n' in s:
        lines = s.split('\n')
        indented = '\n  '.join(lines)
        return '|\n  ' + indented
    return s


def _yaml_list(items):
    if not items:
        return "[]"
    lines = [""]
    for item in items:
        lines.append(f"  - {_yaml_scalar(item)}")
    return "\n".join(lines)


def _build_yaml(fields):
    lines = []
    for key, value in fields:
        if isinstance(value, list):
            lines.append(f"{key}: {_yaml_list(value)}")
        else:
            lines.append(f"{key}: {_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        payload = {}

    session_id = payload.get("session_id", "unknown")
    improvement = (
        payload.get("improvement")
        or payload.get("tool_input", {}).get("improvement")
        or ""
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")

    audit_dir = pathlib.Path(
        os.environ.get("HERMES_AUDIT_DIR",
                       str(pathlib.Path.home() / ".hermes" / "audits"))
    )
    proposals_dir = pathlib.Path(
        os.environ.get("HERMES_PROPOSALS_DIR",
                       str(pathlib.Path.home() / ".hermes" / "proposals"))
    )

    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"[session_audit] FAILED to create audit dir {audit_dir}: {exc}",
              file=sys.stderr)
        sys.exit(1)

    audit_fields = [
        ("session_id", session_id),
        ("goal", ""),
        ("outcome", ""),
        ("tools_called", []),
        ("entropy_events", []),
        ("decisions_made", []),
        ("what_worked", ""),
        ("what_failed", ""),
        ("open_threads", []),
        ("improvement", improvement),
    ]

    audit_content = _build_yaml(audit_fields)
    audit_path = audit_dir / f"{timestamp}.yaml"

    try:
        audit_path.write_text(audit_content, encoding="utf-8")
        print(f"[session_audit] Audit written: {audit_path}", flush=True)
    except OSError as exc:
        print(f"[session_audit] FAILED to write audit {audit_path}: {exc}",
              file=sys.stderr)
        sys.exit(1)

    if improvement:
        try:
            proposals_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(
                f"[session_audit] FAILED to create proposals dir {proposals_dir}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

        proposal_path = proposals_dir / f"{timestamp}_proposal.yaml"
        proposal_fields = [
            ("session_id", session_id),
            ("improvement", improvement),
            ("timestamp", timestamp),
        ]
        try:
            proposal_path.write_text(_build_yaml(proposal_fields), encoding="utf-8")
            print(f"[session_audit] Proposal written: {proposal_path}", flush=True)
        except OSError as exc:
            print(
                f"[session_audit] FAILED to write proposal {proposal_path}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
