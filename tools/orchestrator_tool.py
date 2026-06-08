"""Orchestrator Tool — Async multi-agent task management.

Allows agents to submit, monitor, and manage async delegated tasks
with dependency tracking and progress monitoring.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from tools.registry import registry

log = logging.getLogger(__name__)

ORCHESTRATOR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "orchestrator",
        "description": (
            "Manage async multi-agent tasks with dependency tracking. "
            "Submit fire-and-forget tasks, check progress, wait for completion, "
            "or cancel running tasks. Supports DAG-based task dependencies."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["submit", "status", "wait", "cancel", "summary"],
                    "description": "Action: submit new task, check status, "
                                   "wait for completion, cancel task, or get summary.",
                },
                "goal": {
                    "type": "string",
                    "description": "Task goal/prompt (for submit action).",
                },
                "context": {
                    "type": "string",
                    "description": "Additional context for the task (for submit).",
                },
                "depends_on": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Task IDs this task depends on (for submit).",
                },
                "toolsets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Toolsets to enable for this task (for submit).",
                },
                "task_id": {
                    "type": "string",
                    "description": "Task ID (for status/wait/cancel).",
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds for wait action (default: 300).",
                    "default": 300,
                },
            },
            "required": ["action"],
        },
    },
}

# Global orchestrator instance (initialized per-session)
_orchestrator_instance = None


def _get_orchestrator():
    """Get or create the Orchestrator singleton."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        from agent.orchestrator import Orchestrator
        from hermes_constants import get_hermes_home

        def agent_factory(toolsets=None, skip_memory=True):
            from run_agent import AIAgent
            return AIAgent(enabled_toolsets=toolsets, skip_memory=skip_memory)

        # Try to get webhook dispatcher
        webhook_dispatcher = None
        try:
            from agent.webhook_dispatcher import WebhookDispatcher
            webhook_dispatcher = WebhookDispatcher(get_hermes_home())
        except Exception:
            pass

        _orchestrator_instance = Orchestrator(
            agent_factory=agent_factory,
            webhook_dispatcher=webhook_dispatcher,
        )
    return _orchestrator_instance


def _handle_orchestrator(args: Dict[str, Any]) -> str:
    """Handle orchestrator tool calls."""
    action = args.get("action", "summary")

    try:
        orch = _get_orchestrator()

        if action == "submit":
            goal = args.get("goal")
            if not goal:
                return json.dumps({"status": "error", "message": "goal is required"})
            task_id = orch.submit(
                goal=goal,
                context=args.get("context", ""),
                depends_on=args.get("depends_on"),
                toolsets=args.get("toolsets"),
            )
            return json.dumps({
                "status": "ok",
                "task_id": task_id,
                "message": f"Task submitted: {task_id}",
            })

        if action == "status":
            task_id = args.get("task_id")
            statuses = orch.get_status(task_id)
            return json.dumps({"status": "ok", "tasks": statuses}, indent=2)

        if action == "wait":
            task_id = args.get("task_id")
            if not task_id:
                return json.dumps({"status": "error", "message": "task_id is required"})
            timeout = args.get("timeout", 300)
            result = orch.wait(task_id, timeout=timeout)
            return json.dumps({"status": "ok", "result": result}, indent=2)

        if action == "cancel":
            task_id = args.get("task_id")
            if not task_id:
                return json.dumps({"status": "error", "message": "task_id is required"})
            success = orch.cancel(task_id)
            if success:
                return json.dumps({"status": "ok", "message": f"Task {task_id} cancelled."})
            return json.dumps({"status": "error", "message": f"Cannot cancel task {task_id}"})

        if action == "summary":
            summary = orch.summary()
            return json.dumps({"status": "ok", "summary": summary}, indent=2)

        return json.dumps({"status": "error", "message": f"Unknown action: {action}"})

    except Exception as e:
        log.error("Orchestrator tool error: %s", e)
        return json.dumps({"status": "error", "message": str(e)})


# Register the tool
registry.register("orchestrator", "delegation", ORCHESTRATOR_SCHEMA, _handle_orchestrator)
