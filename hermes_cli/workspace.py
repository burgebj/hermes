"""Workspace/topic registry CLI helpers."""

from __future__ import annotations

import copy
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from hermes_cli.config import get_hermes_home, load_config, save_config


_ETERNAL_PROMPTS = {
    "-1003932124823": "You are in the Eternal root chat. Use this for group-level chat and routing diagnostics.",
    "-1003932124823:1": "You are in the #general topic. Full conversational mode for chat, tasks, and requests.",
    "-1003932124823:14": "You are in the #alerts topic. Respond tersely — acknowledge alerts or suggest a quick fix.",
    "-1003932124823:15": "You are in the #dev-logs topic. Treat posts as build/CI output and error reports; summarize failures and next commands.",
    "-1003932124823:16": "You are in the #media topic. Images, videos, screenshots, and generated assets are shared here.",
    "-1003932124823:17": "You are in the #decisions topic. Log important config changes and decisions in compact durable records.",
    "-1003932124823:707": (
        "You are in the Briefings & Alerts topic. Use it for scheduled briefings, "
        "cron output, ecosystem reports, and recurring summaries. Keep updates "
        "concise and action-oriented."
    ),
    "-1003932124823:708": (
        "You are in the Agent Workbench topic. Use it for agent/Codex work, "
        "Telegram workspace admin, topic registry maintenance, and routing diagnostics."
    ),
}


def _ensure_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        value = {}
        parent[key] = value
    return value


def _backup_config() -> Path | None:
    path = get_hermes_home() / "config.yaml"
    if not path.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = path.with_name(f"config.yaml.bak-workspace-{stamp}")
    shutil.copy2(path, backup)
    return backup


def _coerce_prompt_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            import json

            parsed = json.loads(value)
        except Exception:
            return {}
        return dict(parsed) if isinstance(parsed, dict) else {}
    return {}


def build_eternal_example_config(config: dict[str, Any]) -> dict[str, Any]:
    """Return config with Blaze's Eternal registry/prompts merged in safely."""
    from gateway.topic_registry import ETERNAL_EXAMPLE_TOPICS

    updated = copy.deepcopy(config)
    workspace = _ensure_dict(updated, "workspace")
    registry = _ensure_dict(workspace, "topic_registry")
    topics = _ensure_dict(registry, "topics")

    # Older Eternal examples used placeholder keys from inferred topic roles.
    # Migrate by target so the live config does not keep confusing internal
    # keys like ``daily-briefing`` / ``group-meta`` after the visible Telegram
    # names were corrected to Briefings & Alerts / Agent Workbench.
    target_to_alias = {entry["target"]: alias for alias, entry in ETERNAL_EXAMPLE_TOPICS.items()}
    for old_alias, existing in list(topics.items()):
        if not isinstance(existing, dict):
            continue
        target = existing.get("target")
        new_alias = target_to_alias.get(target)
        if not new_alias or new_alias == old_alias:
            continue
        migrated = topics.setdefault(new_alias, {})
        if isinstance(migrated, dict):
            migrated.update(existing)
            migrated["alias"] = new_alias
        topics.pop(old_alias, None)

    for alias, entry in ETERNAL_EXAMPLE_TOPICS.items():
        desired = {"alias": alias, **entry}
        existing = topics.get(alias)
        if not isinstance(existing, dict):
            topics[alias] = desired
        else:
            existing.update(desired)

    telegram = _ensure_dict(updated, "telegram")
    prompts = _coerce_prompt_dict(telegram.get("channel_prompts"))
    telegram["channel_prompts"] = prompts
    for key, prompt in _ETERNAL_PROMPTS.items():
        prompts.setdefault(key, prompt)
    return updated


def workspace_command(args) -> int:
    from gateway.topic_registry import (
        check_topic_drift,
        generate_ops_index,
        generate_workspace_guide,
        load_topic_registry,
    )

    sub = getattr(args, "workspace_command", None)
    if sub in {None, "list"}:
        registry = load_topic_registry()
        if not registry:
            print("No workspace topics configured.")
            return 0
        for entry in sorted(registry.values(), key=lambda e: e.display_name):
            purpose = f" — {entry.purpose}" if entry.purpose else ""
            print(f"{entry.display_name}: {entry.ref.full}{purpose}")
        return 0

    if sub == "guide":
        print(generate_workspace_guide())
        return 0

    if sub == "ops-index":
        print(generate_ops_index())
        return 0

    if sub == "drift":
        issues = check_topic_drift()
        if not issues:
            print("No workspace topic drift detected.")
            return 0
        print("Workspace topic drift:")
        for issue in issues:
            print(f"- {issue}")
        return 1

    if sub == "eternal-example":
        config = load_config()
        updated = build_eternal_example_config(config)
        if not getattr(args, "apply", False):
            print("Dry run. This would add missing Eternal registry entries and topic prompts, including topics 707/708.")
            print("Run `hermes workspace eternal-example --apply` to update config.yaml with a backup.")
            return 0
        backup = _backup_config()
        save_config(updated)
        if backup:
            print(f"Updated config.yaml. Backup: {backup}")
        else:
            print("Wrote config.yaml.")
        return 0

    print(f"Unknown workspace subcommand: {sub}")
    return 2
