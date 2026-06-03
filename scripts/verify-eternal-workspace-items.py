#!/usr/bin/env python3
"""Read-only verification for Blaze's Eternal Telegram workspace upgrades.

This script is intentionally focused: it prints a per-claim PASS/FAIL map for
workspace upgrade checklist items 2-9 without exposing secrets. If a Telegram
bot token is available in ~/.hermes/.env, it also verifies live group metadata
with getChat.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    import yaml
except Exception as exc:  # pragma: no cover
    print(f"yaml_import=FAIL {exc}")
    sys.exit(2)

HOME = Path.home()
REPO = Path(__file__).resolve().parents[1]
CONFIG = HOME / ".hermes/config.yaml"
ENV = HOME / ".hermes/.env"
BACKUP = HOME / ".hermes/config.yaml.bak-workspace-20260603T073242Z"
CHAT_ID = "-1003932124823"
THREAD_707 = f"{CHAT_ID}:707"
THREAD_708 = f"{CHAT_ID}:708"


def load_env(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def contains(path: Path, needle: str) -> bool:
    return needle in path.read_text(errors="replace")


def prompt_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except Exception:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def thread_id(topic: dict[str, Any]) -> str | None:
    target = str(topic.get("target") or "")
    match = re.search(r":(\d+)$", target)
    if match:
        return match.group(1)
    raw = topic.get("thread_id")
    return str(raw) if raw is not None else None


def pass_line(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    suffix = f" | {detail}" if detail else ""
    print(f"{name}: {status}{suffix}")
    return condition


def telegram_metadata() -> tuple[str, str, int | None]:
    env = load_env(ENV)
    token = env.get("TELEGRAM_BOT_TOKEN") or env.get("telegram_bot_token")
    if not token:
        return "", "", None
    url = f"https://api.telegram.org/bot{urllib.parse.quote(token)}/getChat?chat_id={urllib.parse.quote(CHAT_ID)}"
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode())
    if not payload.get("ok"):
        return "", "", None
    result = payload.get("result", {})
    pinned = result.get("pinned_message") or {}
    pinned_text = pinned.get("text") or pinned.get("caption") or ""
    return result.get("description") or "", pinned_text, pinned.get("message_id")


def main() -> int:
    cfg = yaml.safe_load(CONFIG.read_text())
    prompts = prompt_dict((cfg.get("telegram") or {}).get("channel_prompts"))
    workspace = cfg.get("workspace") or {}
    registry = workspace.get("topic_registry") or {}
    raw_topics = registry.get("topics") or {}
    if isinstance(raw_topics, dict):
        topics = [{**value, "_key": key} for key, value in raw_topics.items() if isinstance(value, dict)]
    else:
        topics = [topic for topic in raw_topics if isinstance(topic, dict)]
    display = cfg.get("display") or {}
    decision_records = workspace.get("decision_records") or {}

    description, pinned_text, pinned_message_id = telegram_metadata()
    live_text = f"{description}\n{pinned_text}"

    print("=== per-claim verification for Eternal workspace items 2-9 ===")
    results: list[bool] = []

    results.append(pass_line(
        "2.prompts_707_708_and_backup",
        THREAD_707 in prompts and THREAD_708 in prompts and BACKUP.exists(),
        f"keys={sorted(prompts.keys())}; backup={BACKUP}",
    ))
    results.append(pass_line(
        "2.existing_prompts_preserved",
        all(f"{CHAT_ID}:{n}" in prompts for n in (14, 15, 16, 17)),
        "threads=14,15,16,17",
    ))

    results.append(pass_line(
        "3.pinned_guide_group_description_updated",
        pinned_message_id == 18 and "Briefings & Alerts" in live_text and "Agent Workbench" in live_text,
        f"pinned_message_id={pinned_message_id}",
    ))
    results.append(pass_line(
        "3.stale_visible_names_absent",
        "#daily-briefing" not in live_text and "#group-meta" not in live_text,
        "visible names are Briefings & Alerts / Agent Workbench",
    ))

    results.append(pass_line(
        "4.whereami_support",
        contains(REPO / "gateway/run.py", "/whereami")
        and contains(REPO / "gateway/run.py", "_handle_whereami")
        and contains(REPO / "gateway/run.py", "Prompt:"),
        "gateway/run.py",
    ))

    results.append(pass_line(
        "5.friendly_names_send_targets",
        contains(REPO / "gateway/channel_directory.py", "topic_registry")
        and contains(REPO / "gateway/channel_directory.py", "alias"),
        "gateway/channel_directory.py resolves registry aliases",
    ))

    results.append(pass_line(
        "6.topic_drift_checker",
        contains(REPO / "hermes_cli/workspace.py", "check_topic_drift")
        and contains(REPO / "hermes_cli/main.py", "drift"),
        "python -m hermes_cli.main workspace drift",
    ))

    results.append(pass_line(
        "7.background_completion_routing",
        display.get("background_process_notification_target") == f"telegram:{CHAT_ID}:15",
        str(display.get("background_process_notification_target")),
    ))

    results.append(pass_line(
        "8.decision_auto_capture",
        bool(decision_records.get("enabled")) and (REPO / "gateway/decision_records.py").exists(),
        str(decision_records),
    ))

    results.append(pass_line(
        "9.ops_index_dashboard",
        contains(REPO / "hermes_cli/workspace.py", "ops-index")
        or contains(REPO / "hermes_cli/workspace.py", "ops_index"),
        "python -m hermes_cli.main workspace ops-index",
    ))

    results.append(pass_line(
        "registry_707_708_correct_internal_keys",
        any(topic.get("_key") == "briefings-alerts" and thread_id(topic) == "707" for topic in topics)
        and any(topic.get("_key") == "agent-workbench" and thread_id(topic) == "708" for topic in topics)
        and not any(topic.get("_key") in {"daily-briefing", "group-meta"} for topic in topics),
        ", ".join(f"{topic.get('_key')}->{thread_id(topic)}" for topic in topics),
    ))

    print("=== summary ===")
    passed = sum(1 for item in results if item)
    print(f"claims_passed={passed}/{len(results)}")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
