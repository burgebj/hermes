"""Webhook Tool — Manage outbound webhook subscriptions.

Allows agents to register, list, test, and remove webhook endpoints
for async task/cron completion callbacks.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

from tools.registry import registry

log = logging.getLogger(__name__)

WEBHOOK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "webhook_manage",
        "description": (
            "Manage outbound webhook subscriptions. Register URLs to receive "
            "HTTP POST callbacks when tasks or cron jobs complete. "
            "Supports HMAC-SHA256 signing for payload verification."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["register", "unregister", "list", "test"],
                    "description": "Action to perform.",
                },
                "url": {
                    "type": "string",
                    "description": "Webhook URL (for register action).",
                },
                "events": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Events to subscribe to: task.completed, task.failed, "
                                   "cron.completed, test.ping, or * for all.",
                },
                "secret": {
                    "type": "string",
                    "description": "HMAC-SHA256 secret for payload signing (optional).",
                },
                "webhook_id": {
                    "type": "string",
                    "description": "Webhook ID (for unregister/test actions).",
                },
            },
            "required": ["action"],
        },
    },
}


def _get_dispatcher():
    """Get or create the WebhookDispatcher singleton."""
    from hermes_constants import get_hermes_home
    from agent.webhook_dispatcher import WebhookDispatcher
    return WebhookDispatcher(get_hermes_home())


def _handle_webhook(args: Dict[str, Any]) -> str:
    """Handle webhook tool calls."""
    action = args.get("action", "list")

    try:
        dispatcher = _get_dispatcher()

        if action == "list":
            webhooks = dispatcher.list_webhooks()
            return json.dumps({"status": "ok", "webhooks": webhooks}, indent=2)

        if action == "register":
            url = args.get("url")
            if not url:
                return json.dumps({"status": "error", "message": "url is required"})
            events = args.get("events", ["task.completed"])
            secret = args.get("secret")
            webhook_id = dispatcher.register(url, events, secret)
            return json.dumps({
                "status": "ok",
                "webhook_id": webhook_id,
                "url": url,
                "events": events,
                "message": "Webhook registered successfully.",
            })

        if action == "unregister":
            webhook_id = args.get("webhook_id")
            if not webhook_id:
                return json.dumps({"status": "error", "message": "webhook_id is required"})
            success = dispatcher.unregister(webhook_id)
            if success:
                return json.dumps({"status": "ok", "message": f"Webhook {webhook_id} removed."})
            return json.dumps({"status": "error", "message": f"Webhook {webhook_id} not found."})

        if action == "test":
            webhook_id = args.get("webhook_id")
            if not webhook_id:
                return json.dumps({"status": "error", "message": "webhook_id is required"})
            result = dispatcher.test_webhook(webhook_id)
            return json.dumps({"status": "ok", "result": result}, indent=2)

        return json.dumps({"status": "error", "message": f"Unknown action: {action}"})

    except Exception as e:
        log.error("Webhook tool error: %s", e)
        return json.dumps({"status": "error", "message": str(e)})


# Register the tool
registry.register("webhook_manage", "messaging", WEBHOOK_SCHEMA, _handle_webhook)
