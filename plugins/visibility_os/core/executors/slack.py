from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_home


def _load_env_token(name: str) -> str | None:
    token = os.getenv(name)
    if token:
        return token
    env_path = Path(get_hermes_home()) / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(errors="ignore").splitlines():
        if line.startswith(name + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'") or None
    return None


def execute_slack_action(action: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    if action.get("action_type") != "slack_message":
        raise RuntimeError(f"Unsupported Slack action type {action.get('action_type')}")
    text = payload.get("text") or payload.get("body")
    if not text:
        raise RuntimeError("Slack action requires text payload")
    token = _load_env_token("SLACK_BOT_TOKEN")
    if not token:
        raise RuntimeError("SLACK_BOT_TOKEN is not configured")
    body = json.dumps({"channel": action["target_location"], "text": text}).encode()
    req = urllib.request.Request(
        "https://slack.com/api/chat.postMessage",
        data=body,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if not data.get("ok"):
        raise RuntimeError(data.get("error") or "Slack API error")
    return {"ok": True, "ts": data.get("ts"), "channel": data.get("channel")}
