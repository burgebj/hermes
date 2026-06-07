"""Mem0 plugin telemetry — anonymous usage tracking via PostHog.

Fire-and-forget events batched and flushed every 5 seconds or when the
queue reaches 10 events. Uses native urllib (no extra dependencies).

Disable with: MEM0_TELEMETRY=false
"""

from __future__ import annotations

import atexit
import hashlib
import json
import logging
import os
import random
import sys
import threading
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

POSTHOG_API_KEY = os.environ.get("MEM0_POSTHOG_KEY", "phc_hgJkUVJFYtmaJqrvf6CYN67TIQ8yhXAkWzUn9AMU4yX")
POSTHOG_HOST = "https://us.i.posthog.com/i/v0/e/"

FLUSH_INTERVAL_SECS = 5.0
FLUSH_THRESHOLD = 10

_DEFAULT_SAMPLE_RATE = 0.1
_LIFECYCLE_EVENTS = frozenset({"hermes.plugin.registered"})

_event_queue: list[Dict[str, Any]] = []
_queue_lock = threading.Lock()
_flush_timer: Optional[threading.Timer] = None
_exit_handler_installed = False
_telemetry_enabled: Optional[bool] = None


def _is_telemetry_enabled() -> bool:
    global _telemetry_enabled
    if _telemetry_enabled is not None:
        return _telemetry_enabled
    val = os.environ.get("MEM0_TELEMETRY", "true").lower()
    _telemetry_enabled = val not in ("false", "0", "no")
    return _telemetry_enabled


def _is_oss_mode(mode: str) -> bool:
    """True when the underlying mem0 SDK already reports its own PostHog events."""
    return mode == "oss"


def _get_sample_rate() -> float:
    raw = os.environ.get("MEM0_TELEMETRY_SAMPLE_RATE")
    if raw is None:
        return _DEFAULT_SAMPLE_RATE
    try:
        value = float(raw)
        if 0.0 <= value <= 1.0:
            return value
    except (TypeError, ValueError):
        pass
    return _DEFAULT_SAMPLE_RATE


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _get_distinct_id(api_key: str = "") -> str:
    if api_key:
        return _sha256(api_key)
    return "hermes-anon"


def _get_plugin_version() -> str:
    try:
        import importlib.metadata
        return importlib.metadata.version("mem0ai")
    except Exception:
        return "unknown"


def _flush() -> None:
    with _queue_lock:
        if not _event_queue:
            return
        batch = _event_queue.copy()
        _event_queue.clear()

    body = json.dumps({"api_key": POSTHOG_API_KEY, "batch": batch}).encode()
    try:
        req = urllib.request.Request(
            POSTHOG_HOST,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass


def _schedule_flush() -> None:
    global _flush_timer
    if _flush_timer and _flush_timer.is_alive():
        return
    _flush_timer = threading.Timer(FLUSH_INTERVAL_SECS, _flush)
    _flush_timer.daemon = True
    _flush_timer.start()


def _flush_async() -> None:
    """Best-effort flush in a daemon thread — never blocks process exit."""
    t = threading.Thread(target=_flush, daemon=True)
    t.start()


def _ensure_exit_handler() -> None:
    global _exit_handler_installed
    if _exit_handler_installed:
        return
    _exit_handler_installed = True
    atexit.register(_flush_async)


def capture_event(
    event_name: str,
    properties: Optional[Dict[str, Any]] = None,
    api_key: str = "",
    mode: str = "",
) -> None:
    if not _is_telemetry_enabled():
        return

    try:
        is_lifecycle = event_name in _LIFECYCLE_EVENTS
        if not is_lifecycle and _is_oss_mode(mode):
            return
        sample_rate = _get_sample_rate()

        if not is_lifecycle and random.random() >= sample_rate:
            return

        event = {
            "event": event_name,
            "distinct_id": _get_distinct_id(api_key),
            "properties": {
                "source": "HERMES",
                "client_source": "python",
                "client_version": _get_plugin_version(),
                "language": "python",
                "python_version": ".".join(str(x) for x in sys.version_info[:2]),
                "os": sys.platform,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "sample_rate": 1.0 if is_lifecycle else sample_rate,
                "$process_person_profile": False,
                "$lib": "posthog-python",
                **({"mode": mode} if mode else {}),
                **(properties or {}),
            },
        }

        with _queue_lock:
            _event_queue.append(event)
            queue_len = len(_event_queue)

        _ensure_exit_handler()

        if queue_len >= FLUSH_THRESHOLD:
            _flush()
        else:
            _schedule_flush()
    except Exception:
        pass


def capture_tool_event(
    tool_name: str,
    *,
    success: bool,
    latency_ms: float,
    api_key: str = "",
    mode: str = "",
    **extra: Any,
) -> None:
    capture_event(
        f"hermes.tool.{tool_name}",
        {"tool_name": tool_name, "success": success, "latency_ms": latency_ms, **extra},
        api_key=api_key,
        mode=mode,
    )
