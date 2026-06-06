"""Hermes plugin: inbound guess interception + slash command surface.

The plugin registers two surfaces:

1. ``pre_gateway_dispatch`` — fired by ``gateway/run.py`` for every inbound
   :class:`MessageEvent` before auth and agent dispatch. We use it to:

   * Detect plain-text messages that should be treated as guesses for an
     active challenge (DM with active challenge, OR group reply to the
     challenge image).
   * Score the guess via ``scripts.challenge.handle_guess``.
   * Send the reply directly through the platform adapter.
   * Return ``{"action": "skip", "reason": "otdat-guess"}`` so the gateway
     drops the message without invoking the agent.

2. ``/on-this-day-art-trivia`` slash command — same routing logic as the
   hook handler, registered through ``ctx.register_command`` so plugins
   without hook installation still work.

The plugin is silent for messages that aren't guesses; ``action: allow`` is
returned implicitly by returning ``None``.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Make scripts/ importable. The skill is installed at
# ~/.hermes/skills/on-this-day-art-trivia/scripts/.
_HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))
_SKILL_DIR = _HERMES_HOME / "skills" / "on-this-day-art-trivia"
if str(_SKILL_DIR) not in sys.path and _SKILL_DIR.exists():
    sys.path.insert(0, str(_SKILL_DIR))

try:
    from scripts import challenge as _challenge  # type: ignore
except Exception as _err:  # pragma: no cover — install-time misconfig
    logger.warning("on_this_day_art_trivia: skill scripts not importable: %s", _err)
    _challenge = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _is_command(text: Optional[str]) -> bool:
    return bool(text) and text.lstrip().startswith("/")


def _platform_name(event: Any) -> str:
    src = getattr(event, "source", None)
    plat = getattr(src, "platform", None)
    return str(getattr(plat, "value", plat) or "telegram")


def _chat_type(event: Any) -> str:
    src = getattr(event, "source", None)
    return str(getattr(src, "chat_type", "dm") or "dm")


def _chat_id(event: Any) -> Optional[str]:
    src = getattr(event, "source", None)
    chat_id = getattr(src, "chat_id", None)
    return str(chat_id) if chat_id is not None else None


def _user_id(event: Any) -> Optional[str]:
    src = getattr(event, "source", None)
    user_id = getattr(src, "user_id", None)
    return str(user_id) if user_id is not None else None


def _user_name(event: Any) -> Optional[str]:
    src = getattr(event, "source", None)
    name = getattr(src, "user_name", None)
    return str(name) if name else None


def _reply_to_message_id(event: Any) -> Optional[str]:
    """Best-effort: pull the message-id this inbound message replies to.

    Hermes adapters expose this differently. We probe a few field names that
    Telegram and WhatsApp adapters use, falling back to ``None`` when none
    of them are populated.
    """
    for attr in ("reply_to_message_id", "reply_to", "in_reply_to", "quoted_message_id"):
        val = getattr(event, attr, None)
        if val is None:
            src = getattr(event, "source", None)
            val = getattr(src, attr, None)
        if val:
            return str(val)
    metadata = getattr(event, "metadata", None) or {}
    if isinstance(metadata, dict):
        for key in ("reply_to_message_id", "reply_to", "in_reply_to_message_id"):
            v = metadata.get(key)
            if v:
                return str(v)
    return None


# --------------------------------------------------------------------------- #
# Inbound interception
# --------------------------------------------------------------------------- #

def _on_pre_gateway_dispatch(event: Any = None, gateway: Any = None, **_: Any):
    """Intercept inbound messages that should be scored as guesses."""
    if _challenge is None or event is None:
        return None

    text = (getattr(event, "text", "") or "").strip()
    if not text:
        return None

    # Slash commands flow through the normal dispatcher (the hook handles
    # /on-this-day-art-trivia). Don't double-handle.
    if _is_command(text):
        return None

    platform = _platform_name(event)
    chat_id = _chat_id(event)
    user_id = _user_id(event)
    if not chat_id or not user_id:
        return None

    chat_type = _chat_type(event)

    # Locate the active challenge if any.
    try:
        from scripts import state as _state  # type: ignore
    except Exception as exc:  # pragma: no cover
        logger.warning("on_this_day_art_trivia state import failed: %s", exc)
        return None

    active = _state.get_active_challenge_for_chat(platform, chat_id)
    if not active:
        return None

    # Group routing rule: only intercept replies to the challenge image.
    if chat_type == "group":
        replied_to = _reply_to_message_id(event)
        target = active.get("telegram_message_id")
        if not (target and replied_to and str(replied_to) == str(target)):
            return None

    # Score the guess.
    try:
        result = _challenge.handle_guess(
            platform=platform,
            chat_id=chat_id,
            user_id=user_id,
            user_display_name=_user_name(event),
            guess_text=text,
            challenge_id=int(active["challenge_id"]),
        )
    except Exception as exc:
        logger.warning("guess handling failed: %s", exc)
        return None

    if result is None:
        return None

    _send_reply(gateway, event, result.reply_text, replied_to_msg_id=active.get("telegram_message_id"))
    return {"action": "skip", "reason": "otdat-guess"}


def _send_reply(
    gateway: Any,
    event: Any,
    text: str,
    *,
    replied_to_msg_id: Optional[str] = None,
) -> None:
    """Best-effort: deliver *text* through whichever surface is available.

    Tries (1) the gateway's adapter for the message's platform, (2) direct
    Telegram Bot API as a fallback. Failures are logged but never raised —
    the inbound dispatch is still consumed so the user is not double-replied.
    """
    src = getattr(event, "source", None)
    platform_obj = getattr(src, "platform", None)
    chat_id = getattr(src, "chat_id", None)

    # 1. Adapter path.
    try:
        adapters = getattr(gateway, "adapters", None) or {}
        adapter = adapters.get(platform_obj) if platform_obj is not None else None
        if adapter is not None and chat_id is not None:
            send = getattr(adapter, "send", None)
            if callable(send):
                import asyncio as _asyncio
                coro = send(chat_id, text)
                if _asyncio.iscoroutine(coro):
                    loop = _asyncio.get_event_loop()
                    if loop.is_running():
                        _asyncio.ensure_future(coro)
                    else:  # pragma: no cover — only on synchronous test paths
                        loop.run_until_complete(coro)
                return
    except Exception as exc:
        logger.debug("adapter send failed, falling back to telegram_api: %s", exc)

    # 2. Telegram Bot API fallback.
    if str(getattr(platform_obj, "value", platform_obj) or "") == "telegram":
        try:
            from scripts import telegram_api  # type: ignore
            telegram_api.send_message(
                str(chat_id) if chat_id is not None else "",
                text,
                reply_to_message_id=replied_to_msg_id,
            )
        except Exception as exc:
            logger.warning("telegram fallback send failed: %s", exc)


# --------------------------------------------------------------------------- #
# Slash command (mirror of the hook, in case the hook is not installed)
# --------------------------------------------------------------------------- #

HELP_TEXT = """\
On This Day — Art Trivia

  /on-this-day-art-trivia                   Start a new challenge
  /on-this-day-art-trivia guess <answer>    Submit a guess
  /on-this-day-art-trivia hint              Get a hint
  /on-this-day-art-trivia reveal            Reveal the answer (resets streak)
  /on-this-day-art-trivia stats             Your stats
  /on-this-day-art-trivia achievements      Your achievements
  /on-this-day-art-trivia subscribe         Receive a daily challenge here
  /on-this-day-art-trivia unsubscribe       Stop daily delivery
  /on-this-day-art-trivia leaderboard       Top players
  /on-this-day-art-trivia help              Show this help
"""


def _slash_handler(raw_args: str, event: Any = None, **_: Any) -> Optional[str]:
    if _challenge is None:
        return "on-this-day-art-trivia is not installed correctly."

    parts = (raw_args or "").strip().split(maxsplit=1)
    sub = parts[0].lower() if parts else ""
    rest = parts[1] if len(parts) > 1 else ""

    platform = _platform_name(event) if event is not None else "telegram"
    user_id = (_user_id(event) if event is not None else None) or "unknown"
    chat_id = (_chat_id(event) if event is not None else None) or user_id
    scope = "group" if (event is not None and _chat_type(event) == "group") else "dm"

    if sub in ("", "play", "start", "new"):
        res = _challenge.start_challenge(
            platform=platform, chat_id=chat_id, user_id=user_id,
            user_display_name=(_user_name(event) if event is not None else None),
            scope=scope,
        )
        if res is None:
            return "I couldn't find a usable historic event for today. Try again later."
        if res.delivered:
            return "Your challenge is in the chat. Reply with your guess."
        return f"{res.surface_caption}\n\n(Image delivery unavailable; reply with your guess.)"

    if sub == "guess":
        if not rest:
            return "Usage: /on-this-day-art-trivia guess <answer>"
        gres = _challenge.handle_guess(
            platform=platform, chat_id=chat_id, user_id=user_id,
            user_display_name=(_user_name(event) if event is not None else None),
            guess_text=rest,
        )
        if gres is None:
            return "No active challenge in this chat. Start one with /on-this-day-art-trivia."
        return gres.reply_text

    if sub == "hint":
        return _challenge.handle_hint(platform=platform, chat_id=chat_id) or "No active challenge."

    if sub == "reveal":
        return _challenge.handle_reveal(platform=platform, chat_id=chat_id, user_id=user_id) or "No active challenge."

    if sub == "stats":
        return _challenge.render_stats(platform=platform, user_id=user_id)

    if sub == "achievements":
        return _challenge.render_achievements(platform=platform, user_id=user_id)

    if sub == "leaderboard":
        return _challenge.render_leaderboard(platform=platform)

    if sub == "subscribe":
        return _challenge.subscribe(platform=platform, user_id=user_id, chat_id=chat_id, scope=scope)

    if sub == "unsubscribe":
        return _challenge.unsubscribe(platform=platform, user_id=user_id, chat_id=chat_id)

    if sub in ("help", "-h", "--help", "?"):
        return HELP_TEXT

    return f"Unknown subcommand: {sub}\n\n{HELP_TEXT}"


# --------------------------------------------------------------------------- #
# Plugin registration
# --------------------------------------------------------------------------- #

def register(ctx) -> None:
    ctx.register_hook("pre_gateway_dispatch", _on_pre_gateway_dispatch)
    register_command = getattr(ctx, "register_command", None)
    if callable(register_command):
        register_command(
            "on-this-day-art-trivia",
            handler=_slash_handler,
            description="Play the on-this-day-art-trivia history guessing game.",
        )
