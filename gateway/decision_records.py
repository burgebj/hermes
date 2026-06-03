"""Compact decision-record formatting for operator-visible changes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def format_decision_record(
    *,
    title: str,
    change_type: str,
    actor: str = "hermes",
    target: str = "",
    before: Any = None,
    after: Any = None,
    reason: str = "",
) -> str:
    """Return a compact Markdown decision record with secret-safe values."""
    from agent.redact import redact_sensitive_text

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"## Decision: {title}",
        f"- Time: {timestamp}",
        f"- Type: {change_type}",
        f"- Actor: {actor}",
    ]
    if target:
        lines.append(f"- Target: `{target}`")
    if before is not None:
        lines.append(f"- Before: `{redact_sensitive_text(str(before))}`")
    if after is not None:
        lines.append(f"- After: `{redact_sensitive_text(str(after))}`")
    if reason:
        lines.append(f"- Reason: {redact_sensitive_text(reason)}")
    return "\n".join(lines)


def decision_records_enabled(config: dict[str, Any]) -> bool:
    workspace = config.get("workspace") if isinstance(config, dict) else {}
    records = workspace.get("decision_records") if isinstance(workspace, dict) else {}
    return bool(isinstance(records, dict) and records.get("enabled"))
