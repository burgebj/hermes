"""Inline keyboard builders for multi-agent workspace commands.

All callback_data values are kept ≤ 64 bytes (Telegram Bot API limit).

Pending state (alias+task for summon/swarm, text for TTS, media key for
media actions) is held in a module-level dict so the callback handler can
look up the full context without embedding it in the button payload.

Callback prefixes
-----------------
``ws:s:<cid>``          — summon: actually dispatch stored alias + task
``ws:r:<alias>``        — show route info for alias
``ws:guide``            — show workspace guide
``ws:cancel``           — cancel / dismiss keyboard
``ws:cl:<alias>``       — create standard checklist for alias
``ws:voice:<mode>``     — set voice mode (on / off / tts)
``ws:tts:<cid>``        — read stored text aloud via TTS
``ws:sw:<cid>``         — confirm swarm dispatch
``ws:m:a:<cid>``        — media: analyze
``ws:m:o:<cid>``        — media: OCR / summarize
``ws:m:d:<cid>``        — media: route to dev-logs
``ws:m:c:<cid>``        — media: add to checklist
"""

from __future__ import annotations

import hashlib
import threading
import uuid
from typing import Any, Optional

# -------------------------------------------------------------------------
# In-memory pending state store
# -------------------------------------------------------------------------

_lock = threading.Lock()
_pending: dict[str, dict[str, Any]] = {}
_MAX_ENTRIES = 500  # LRU-ish eviction


def _store(payload: dict[str, Any]) -> str:
    """Persist *payload* keyed by a short UUID.  Returns the key (cid)."""
    cid = uuid.uuid4().hex[:12]
    with _lock:
        if len(_pending) >= _MAX_ENTRIES:
            # Evict the oldest half
            keys = list(_pending.keys())
            for k in keys[: _MAX_ENTRIES // 2]:
                del _pending[k]
        _pending[cid] = payload
    return cid


def get_pending(cid: str) -> Optional[dict[str, Any]]:
    """Look up pending state by key.  Returns None if not found."""
    with _lock:
        return _pending.get(cid)


def pop_pending(cid: str) -> Optional[dict[str, Any]]:
    """Retrieve and remove pending state by key."""
    with _lock:
        return _pending.pop(cid, None)


# -------------------------------------------------------------------------
# Store helpers
# -------------------------------------------------------------------------

def store_summon(alias: str, task: str) -> str:
    return _store({"type": "summon", "alias": alias, "task": task})


def store_swarm(aliases: list[str], task: str) -> str:
    return _store({"type": "swarm", "aliases": aliases, "task": task})


def store_tts(text: str) -> str:
    return _store({"type": "tts", "text": text})


def store_media(
    chat_id: str,
    thread_id: Optional[str],
    media_type: str,
    media_path: Optional[str],
    caption: Optional[str],
) -> str:
    return _store(
        {
            "type": "media",
            "chat_id": chat_id,
            "thread_id": thread_id,
            "media_type": media_type,
            "media_path": media_path,
            "caption": caption,
        }
    )


# -------------------------------------------------------------------------
# Keyboard row builders
# -------------------------------------------------------------------------

def summon_keyboard_rows(
    alias: str, cid: str
) -> list[list[dict[str, str]]]:
    """Keyboard for /summon response.  cid stores alias+task."""
    a = alias[:18]
    return [
        [
            {"text": f"⚡ Summon @{a}", "callback_data": f"ws:s:{cid}"},
            {"text": "📍 Route info", "callback_data": f"ws:r:{a}"},
        ],
        [
            {"text": "📋 Checklist", "callback_data": f"ws:cl:{a}"},
            {"text": "📚 Guide", "callback_data": "ws:guide"},
            {"text": "✗ Cancel", "callback_data": "ws:cancel"},
        ],
    ]


def swarm_keyboard_rows(
    aliases: list[str], cid: str
) -> list[list[dict[str, str]]]:
    """Keyboard for /swarm response.  cid stores aliases+task."""
    return [
        [
            {"text": "🌐 Confirm Swarm", "callback_data": f"ws:sw:{cid}"},
            {"text": "✗ Cancel", "callback_data": "ws:cancel"},
        ],
        [
            {"text": "📚 Guide", "callback_data": "ws:guide"},
            {"text": "📋 Checklist", "callback_data": "ws:cl:swarm"},
        ],
    ]


def route_keyboard_rows(alias: str) -> list[list[dict[str, str]]]:
    """Keyboard for /route response."""
    a = alias[:18]
    return [
        [
            {"text": f"⚡ Summon @{a}", "callback_data": f"ws:s:{a}"},
            {"text": "📚 Guide", "callback_data": "ws:guide"},
            {"text": "✗ Cancel", "callback_data": "ws:cancel"},
        ],
    ]


def media_keyboard_rows(cid: str) -> list[list[dict[str, str]]]:
    """Keyboard for media messages (#media / #dev-logs lanes)."""
    return [
        [
            {"text": "🔍 Analyze", "callback_data": f"ws:m:a:{cid}"},
            {"text": "📝 OCR/Summarize", "callback_data": f"ws:m:o:{cid}"},
        ],
        [
            {"text": "📂 → dev-logs", "callback_data": f"ws:m:d:{cid}"},
            {"text": "☑️ Checklist", "callback_data": f"ws:m:c:{cid}"},
        ],
    ]


def tts_keyboard_rows(cid: str) -> list[list[dict[str, str]]]:
    """Keyboard for TTS confirmation."""
    return [
        [
            {"text": "🔊 Read aloud", "callback_data": f"ws:tts:{cid}"},
            {"text": "✗ Cancel", "callback_data": "ws:cancel"},
        ],
    ]


def voice_status_keyboard_rows() -> list[list[dict[str, str]]]:
    """Keyboard for /voice status response."""
    return [
        [
            {"text": "🔊 TTS All", "callback_data": "ws:voice:tts"},
            {"text": "🎙 Voice Only", "callback_data": "ws:voice:on"},
            {"text": "🔇 Off", "callback_data": "ws:voice:off"},
        ],
    ]
