"""WhatsApp-specific messaging actions.

This tool intentionally keeps WhatsApp-only semantics out of the generic
``send_message`` tool. It exposes bridge primitives that require WhatsApp
message/status identifiers and therefore should be used only when the user has
explicitly requested the external action.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agent.redact import redact_sensitive_text
from gateway.config import Platform, load_gateway_config
from tools.registry import registry, tool_error


WHATSAPP_ACTION_SCHEMA = {
    "name": "whatsapp_action",
    "description": (
        "Perform advanced WhatsApp-only actions through the local WhatsApp bridge: "
        "react to a cached message, privately reply to a cached status, react to a "
        "cached status, or post a text status to an explicit recipient list. Use "
        "only after the user explicitly asks for the WhatsApp side effect. Set "
        "dry_run=true to inspect the exact bridge endpoint/payload without sending."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["react_message", "status_reply", "status_react", "post_text_status"],
                "description": "WhatsApp action to perform.",
            },
            "chat_id": {
                "type": "string",
                "description": "WhatsApp chat JID for react_message, e.g. 5215514706713@s.whatsapp.net or 120...@g.us.",
            },
            "message_id": {
                "type": "string",
                "description": "Cached WhatsApp message id for react_message.",
            },
            "status_message_id": {
                "type": "string",
                "description": "Cached WhatsApp status/story message id for status_reply or status_react.",
            },
            "status_author_jid": {
                "type": "string",
                "description": "Optional author JID for a status/story when the cached message lacks participant metadata.",
            },
            "message": {
                "type": "string",
                "description": "Text for status_reply or post_text_status.",
            },
            "emoji": {
                "type": "string",
                "description": "Emoji reaction for react_message or status_react. Empty string removes a reaction.",
            },
            "status_jid_list": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Explicit WhatsApp recipient JIDs for post_text_status. Required and non-empty; there is no all-contacts default.",
            },
            "background_color": {
                "type": "string",
                "description": "Optional WhatsApp text status background color, e.g. #315575.",
            },
            "font": {
                "type": "integer",
                "description": "Optional WhatsApp text status font id.",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, return endpoint and payload without calling the bridge.",
            },
        },
        "required": ["action"],
    },
}


def _error(message: str) -> str:
    return json.dumps({"error": redact_sensitive_text(message)})


def _check_whatsapp_action() -> bool:
    try:
        config = load_gateway_config()
        return bool(config and config.platforms.get(Platform.WHATSAPP))
    except Exception:
        return False


def _whatsapp_extra() -> Dict[str, Any] | None:
    config = load_gateway_config()
    platform_cfg = config.platforms.get(Platform.WHATSAPP) if config else None
    if not platform_cfg:
        return None
    return dict(platform_cfg.extra or {})


def _require_string(args: Dict[str, Any], key: str) -> str | None:
    value = args.get(key)
    if value is None:
        return None
    value = str(value)
    return value if value != "" else None


def _build_action(args: Dict[str, Any]) -> tuple[str, Dict[str, Any]] | str:
    action = str(args.get("action") or "").strip()

    if action == "react_message":
        chat_id = _require_string(args, "chat_id")
        message_id = _require_string(args, "message_id")
        if not chat_id or not message_id or "emoji" not in args:
            return "react_message requires chat_id, message_id, and emoji"
        return "react", {"chatId": chat_id, "messageId": message_id, "emoji": str(args.get("emoji") or "")}

    if action == "status_reply":
        status_message_id = _require_string(args, "status_message_id")
        message = _require_string(args, "message")
        if not status_message_id or not message:
            return "status_reply requires status_message_id and message"
        payload: Dict[str, Any] = {"statusMessageId": status_message_id, "message": message}
        if author := _require_string(args, "status_author_jid"):
            payload["statusAuthorJid"] = author
        return "status-reply", payload

    if action == "status_react":
        status_message_id = _require_string(args, "status_message_id")
        if not status_message_id or "emoji" not in args:
            return "status_react requires status_message_id and emoji"
        payload = {"statusMessageId": status_message_id, "emoji": str(args.get("emoji") or "")}
        if author := _require_string(args, "status_author_jid"):
            payload["statusAuthorJid"] = author
        return "status-react", payload

    if action == "post_text_status":
        message = _require_string(args, "message")
        status_jid_list = args.get("status_jid_list")
        if not message:
            return "post_text_status requires message"
        if not isinstance(status_jid_list, list) or not [x for x in status_jid_list if str(x).strip()]:
            return "post_text_status requires an explicit non-empty status_jid_list"
        payload = {
            "text": message,
            "statusJidList": [str(x).strip() for x in status_jid_list if str(x).strip()],
        }
        if background_color := _require_string(args, "background_color"):
            payload["backgroundColor"] = background_color
        if args.get("font") is not None:
            payload["font"] = int(args["font"])
        return "post-status", payload

    return f"Unknown WhatsApp action: {action}"


async def _post_bridge(extra: Dict[str, Any], endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        import aiohttp
    except ImportError:
        return {"error": "aiohttp not installed. Run: pip install aiohttp"}

    bridge_port = extra.get("bridge_port", 3000)
    url = f"http://127.0.0.1:{bridge_port}/{endpoint.lstrip('/')}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = {"error": await resp.text()}
                if resp.status == 200:
                    return {
                        "success": True,
                        "platform": "whatsapp",
                        "endpoint": endpoint,
                        "message_id": data.get("messageId"),
                        "raw_response": data,
                    }
                return {"error": f"WhatsApp bridge error ({resp.status}): {redact_sensitive_text(str(data))}"}
    except Exception as exc:
        return {"error": f"WhatsApp action failed: {redact_sensitive_text(str(exc))}"}


def whatsapp_action_tool(args: Dict[str, Any], **_kw) -> str:
    extra = _whatsapp_extra()
    if extra is None:
        return tool_error("WhatsApp is not configured in the gateway")

    built = _build_action(args)
    if isinstance(built, str):
        return _error(built)
    endpoint, payload = built

    if args.get("dry_run") is True:
        return json.dumps({
            "success": True,
            "dry_run": True,
            "platform": "whatsapp",
            "endpoint": endpoint,
            "payload": payload,
        })

    from model_tools import _run_async

    return json.dumps(_run_async(_post_bridge(extra, endpoint, payload)))


registry.register(
    name="whatsapp_action",
    toolset="messaging",
    schema=WHATSAPP_ACTION_SCHEMA,
    handler=whatsapp_action_tool,
    check_fn=_check_whatsapp_action,
    emoji="💬",
)
