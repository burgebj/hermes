from __future__ import annotations

from typing import Any

from ..actions import execute_action_guard, mark_executed, mark_failed
from ..audit import record_event
from ..language_guard import validate_message
from .github import execute_github_action
from .hermes import execute_hermes_action
from .slack import execute_slack_action


def execute_approved_action(action_id: str, *, actor: str = "human") -> dict[str, Any]:
    action = execute_action_guard(action_id)
    record_event(action_id=action_id, event_type="execution_attempt_started", actor=actor, before_state=action, after_state={"target_system": action["target_system"], "action_type": action["action_type"]})
    try:
        payload = action.get("final_payload") or action.get("proposed_payload") or {}
        text = payload.get("text") or payload.get("body") or ""
        if text:
            validate_message(text, status=action["status"], evidence_links=action.get("evidence_links") or [], team_visible=action["target_system"] in {"slack", "github"})
        if action["target_system"] == "github":
            result = execute_github_action(action, payload)
        elif action["target_system"] == "slack":
            result = execute_slack_action(action, payload)
        elif action["target_system"] == "hermes":
            result = execute_hermes_action(action, payload)
        else:
            raise RuntimeError(f"No executor for target system {action['target_system']}")
        return mark_executed(action_id, actor=actor, execution_result=result)
    except Exception as exc:
        mark_failed(action_id, actor="system", error=str(exc))
        raise
