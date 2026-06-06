"""Telegram group operations tool.

Provides a small, native Telegram Bot API surface for group operations that
are not covered by plain text delivery: polls, stopping polls, and message
pinning. All calls are explicit-target only and require a configured Telegram
bot token.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from agent.redact import redact_sensitive_text
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

_TELEGRAM_GROUP_TARGET_RE = re.compile(r"^\s*(?:telegram:)?(-?\d+)(?::(\d+))?\s*$")
_TELEGRAM_BOT_TOKEN_RE = re.compile(r"\b(\d{6,12}):([A-Za-z0-9_-]{20,})\b")
_POLL_MIN_OPTIONS = 2
_POLL_MAX_OPTIONS = 10
_POLL_MAX_QUESTION_CHARS = 300
_POLL_MAX_OPTION_CHARS = 100
_POLL_MIN_OPEN_PERIOD_SECONDS = 5
_POLL_MAX_OPEN_PERIOD_SECONDS = 600
_OWNER_STATUSES = {"creator", "owner"}


TELEGRAM_GROUP_OPS_SCHEMA = {
    "name": "telegram_group_ops",
    "description": (
        "Perform native Telegram Bot API group operations for a configured "
        "Telegram bot: discover bot capabilities, send a poll, stop a poll, "
        "pin a message, or unpin a message. Requires an explicit Telegram "
        "group or supergroup target such as 'telegram:-1001234567890' or "
        "'telegram:-1001234567890:17585'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "capabilities",
                    "send_poll",
                    "stop_poll",
                    "pin_message",
                    "unpin_message",
                ],
                "description": "Operation to perform.",
            },
            "target": {
                "type": "string",
                "description": (
                    "Explicit Telegram group target. Format: "
                    "'telegram:<chat_id>' or 'telegram:<chat_id>:<topic_id>'. "
                    "Chat IDs must be negative Telegram group or supergroup IDs."
                ),
            },
            "message_id": {
                "type": "integer",
                "description": (
                    "Telegram message id for stop_poll, pin_message, and "
                    "optionally unpin_message."
                ),
            },
            "question": {
                "type": "string",
                "description": "Poll question for send_poll.",
            },
            "options": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Poll options for send_poll. Telegram allows 2 to 10 options.",
            },
            "is_anonymous": {
                "type": "boolean",
                "description": "Whether poll votes are anonymous. Defaults to false.",
            },
            "allows_multiple_answers": {
                "type": "boolean",
                "description": "Whether voters may choose more than one option. Defaults to false.",
            },
            "open_period": {
                "type": "integer",
                "description": "Optional poll open period in seconds, from 5 to 600.",
            },
            "disable_notification": {
                "type": "boolean",
                "description": (
                    "Whether the Telegram client should send the operation "
                    "silently when supported. Defaults to false for polls and "
                    "true for pins."
                ),
            },
        },
        "required": ["action", "target"],
    },
}


def _sanitize_error_text(text: Any) -> str:
    redacted = redact_sensitive_text(str(text))
    return _TELEGRAM_BOT_TOKEN_RE.sub(r"\1:***", redacted)


def _parse_target(target: str) -> tuple[int, int | None]:
    match = _TELEGRAM_GROUP_TARGET_RE.fullmatch(str(target or ""))
    if not match:
        raise ValueError(
            "target must be 'telegram:<negative_chat_id>' or "
            "'telegram:<negative_chat_id>:<topic_id>'"
        )

    chat_id = int(match.group(1))
    if chat_id >= 0:
        raise ValueError("target must use a negative Telegram group or supergroup chat id")

    thread_id = None
    if match.group(2) is not None:
        thread_id = int(match.group(2))
        if thread_id <= 0:
            raise ValueError("topic_id must be a positive integer")

    return chat_id, thread_id


def _require_message_id(args: dict[str, Any], action: str) -> int:
    value = args.get("message_id")
    if value is None:
        raise ValueError(f"message_id is required for {action}")
    try:
        message_id = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("message_id must be an integer") from exc
    if message_id <= 0:
        raise ValueError("message_id must be a positive integer")
    return message_id


def _validate_poll_args(args: dict[str, Any]) -> tuple[str, list[str], int | None]:
    question = str(args.get("question") or "").strip()
    if not question:
        raise ValueError("question is required for send_poll")
    if len(question) > _POLL_MAX_QUESTION_CHARS:
        raise ValueError(f"question must be at most {_POLL_MAX_QUESTION_CHARS} characters")

    raw_options = args.get("options")
    if not isinstance(raw_options, list):
        raise ValueError("options must be an array of strings")

    options = [str(option).strip() for option in raw_options]
    if not (_POLL_MIN_OPTIONS <= len(options) <= _POLL_MAX_OPTIONS):
        raise ValueError("options must contain 2 to 10 choices")
    if any(not option for option in options):
        raise ValueError("poll options must not be empty")
    if any(len(option) > _POLL_MAX_OPTION_CHARS for option in options):
        raise ValueError(f"poll options must be at most {_POLL_MAX_OPTION_CHARS} characters")

    open_period = args.get("open_period")
    if open_period is not None:
        try:
            open_period = int(open_period)
        except (TypeError, ValueError) as exc:
            raise ValueError("open_period must be an integer") from exc
        if not (_POLL_MIN_OPEN_PERIOD_SECONDS <= open_period <= _POLL_MAX_OPEN_PERIOD_SECONDS):
            raise ValueError("open_period must be between 5 and 600 seconds")

    return question, options, open_period


def _telegram_config():
    from gateway.config import Platform, load_gateway_config

    config = load_gateway_config()
    pconfig = config.platforms.get(Platform.TELEGRAM)
    token = (
        (getattr(pconfig, "token", None) if pconfig else None)
        or os.getenv("TELEGRAM_BOT_TOKEN")
        or ""
    ).strip()
    if not pconfig or not getattr(pconfig, "enabled", False) or not token:
        return config, pconfig, "Telegram platform is not configured with a bot token"
    pconfig.token = token
    return config, pconfig, None


def _check_telegram_group_ops_requirements() -> bool:
    try:
        from gateway.platforms.telegram import check_telegram_requirements

        if not check_telegram_requirements():
            return False
        _, _, error = _telegram_config()
        return error is None
    except Exception:
        return False


def _make_bot(token: str):
    from gateway.platforms.telegram import check_telegram_requirements

    if not check_telegram_requirements():
        raise RuntimeError("python-telegram-bot is not installed")

    from telegram import Bot

    try:
        from gateway.platforms.base import resolve_proxy_url

        proxy_url = resolve_proxy_url("TELEGRAM_PROXY", target_hosts=["api.telegram.org"])
    except Exception:
        proxy_url = None

    if not proxy_url:
        return Bot(token=token)

    try:
        from telegram.request import HTTPXRequest

        return Bot(
            token=token,
            request=HTTPXRequest(proxy=proxy_url),
            get_updates_request=HTTPXRequest(proxy=proxy_url),
        )
    except Exception as exc:
        logger.warning(
            "telegram_group_ops: failed to attach Telegram proxy: %s",
            _sanitize_error_text(exc),
        )
        return Bot(token=token)


def _attr(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _status_value(status: Any) -> str:
    value = getattr(status, "value", status)
    return str(value or "").lower()


def _permission(member: Any, name: str) -> bool:
    if _status_value(_attr(member, "status")) in _OWNER_STATUSES:
        return True
    return bool(_attr(member, name, False))


async def _get_capabilities(bot, chat_id: int) -> dict[str, Any]:
    me = await bot.get_me()
    bot_id = _attr(me, "id")
    member = await bot.get_chat_member(chat_id=chat_id, user_id=bot_id)
    status = _status_value(_attr(member, "status"))

    return {
        "success": True,
        "action": "capabilities",
        "chat_id": str(chat_id),
        "bot_id": str(bot_id) if bot_id is not None else None,
        "bot_username": _attr(me, "username"),
        "status": status,
        "can_pin_messages": _permission(member, "can_pin_messages"),
        "can_manage_topics": _permission(member, "can_manage_topics"),
        "can_manage_chat": _permission(member, "can_manage_chat"),
        "can_delete_messages": _permission(member, "can_delete_messages"),
        "can_restrict_members": _permission(member, "can_restrict_members"),
        "can_promote_members": _permission(member, "can_promote_members"),
        "can_invite_users": _permission(member, "can_invite_users"),
    }


def _thread_kwargs(thread_id: int | None) -> dict[str, int]:
    if thread_id is None:
        return {}
    try:
        from gateway.platforms.telegram import TelegramAdapter

        effective_thread_id = TelegramAdapter._message_thread_id_for_send(str(thread_id))
    except Exception:
        effective_thread_id = None if str(thread_id) == "1" else int(thread_id)
    if effective_thread_id is None:
        return {}
    return {"message_thread_id": effective_thread_id}


async def _run_send_poll(bot, args: dict[str, Any], chat_id: int, thread_id: int | None) -> dict[str, Any]:
    question, options, open_period = _validate_poll_args(args)
    kwargs: dict[str, Any] = {
        "chat_id": chat_id,
        "question": question,
        "options": options,
        "is_anonymous": bool(args.get("is_anonymous", False)),
        "allows_multiple_answers": bool(args.get("allows_multiple_answers", False)),
        "disable_notification": bool(args.get("disable_notification", False)),
        **_thread_kwargs(thread_id),
    }
    if open_period is not None:
        kwargs["open_period"] = open_period

    message = await bot.send_poll(**kwargs)
    poll = _attr(message, "poll")
    return {
        "success": True,
        "action": "send_poll",
        "chat_id": str(chat_id),
        "thread_id": str(thread_id) if thread_id is not None else None,
        "message_id": _attr(message, "message_id"),
        "poll_id": _attr(poll, "id"),
        "question": question,
        "options": options,
        "is_anonymous": kwargs["is_anonymous"],
        "allows_multiple_answers": kwargs["allows_multiple_answers"],
    }


async def _run_stop_poll(bot, args: dict[str, Any], chat_id: int) -> dict[str, Any]:
    message_id = _require_message_id(args, "stop_poll")
    poll = await bot.stop_poll(chat_id=chat_id, message_id=message_id)
    return {
        "success": True,
        "action": "stop_poll",
        "chat_id": str(chat_id),
        "message_id": message_id,
        "poll_id": _attr(poll, "id"),
        "is_closed": _attr(poll, "is_closed"),
        "total_voter_count": _attr(poll, "total_voter_count"),
    }


async def _run_pin_message(bot, args: dict[str, Any], chat_id: int) -> dict[str, Any]:
    message_id = _require_message_id(args, "pin_message")
    capabilities = await _get_capabilities(bot, chat_id)
    if not capabilities.get("can_pin_messages"):
        return {
            "success": False,
            "error": "Telegram bot is not allowed to pin messages in this chat",
            "capabilities": capabilities,
        }

    ok = await bot.pin_chat_message(
        chat_id=chat_id,
        message_id=message_id,
        disable_notification=bool(args.get("disable_notification", True)),
    )
    return {
        "success": bool(ok),
        "action": "pin_message",
        "chat_id": str(chat_id),
        "message_id": message_id,
        "capabilities": capabilities,
    }


async def _run_unpin_message(bot, args: dict[str, Any], chat_id: int) -> dict[str, Any]:
    capabilities = await _get_capabilities(bot, chat_id)
    if not capabilities.get("can_pin_messages"):
        return {
            "success": False,
            "error": "Telegram bot is not allowed to unpin messages in this chat",
            "capabilities": capabilities,
        }

    kwargs: dict[str, Any] = {"chat_id": chat_id}
    if args.get("message_id") is not None:
        kwargs["message_id"] = _require_message_id(args, "unpin_message")

    ok = await bot.unpin_chat_message(**kwargs)
    return {
        "success": bool(ok),
        "action": "unpin_message",
        "chat_id": str(chat_id),
        "message_id": kwargs.get("message_id"),
        "capabilities": capabilities,
    }


async def _run_action(args: dict[str, Any]) -> dict[str, Any]:
    action = str(args.get("action") or "").strip()
    chat_id, thread_id = _parse_target(str(args.get("target") or ""))

    _, pconfig, config_error = _telegram_config()
    if config_error:
        raise RuntimeError(config_error)

    bot = _make_bot(pconfig.token)

    if action == "capabilities":
        return await _get_capabilities(bot, chat_id)
    if action == "send_poll":
        return await _run_send_poll(bot, args, chat_id, thread_id)
    if action == "stop_poll":
        return await _run_stop_poll(bot, args, chat_id)
    if action == "pin_message":
        return await _run_pin_message(bot, args, chat_id)
    if action == "unpin_message":
        return await _run_unpin_message(bot, args, chat_id)

    raise ValueError(
        "action must be one of: capabilities, send_poll, stop_poll, pin_message, unpin_message"
    )


async def telegram_group_ops_tool(args, **_kwargs):
    try:
        result = await _run_action(dict(args or {}))
        if isinstance(result, dict) and result.get("error"):
            result["error"] = _sanitize_error_text(result["error"])
        return tool_result(result)
    except Exception as exc:
        logger.exception("telegram_group_ops failed: %s", _sanitize_error_text(exc))
        return tool_error(_sanitize_error_text(f"telegram_group_ops failed: {exc}"))


registry.register(
    name="telegram_group_ops",
    toolset="telegram_group_ops",
    schema=TELEGRAM_GROUP_OPS_SCHEMA,
    handler=telegram_group_ops_tool,
    check_fn=_check_telegram_group_ops_requirements,
    requires_env=["TELEGRAM_BOT_TOKEN"],
    is_async=True,
    description="Native Telegram group operations: polls, stop-poll, pins, unpins, and capability discovery.",
    max_result_size_chars=20000,
)
