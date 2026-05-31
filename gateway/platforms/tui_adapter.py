"""HTTP-based platform adapter for TUI/CLI notification delivery.

This adapter registers with the gateway's adapter system so that
_kanban_notifier_watcher (and any other gateway-side event source) can
deliver events to connected TUI/CLI sessions via ``adapter.send()``.

Unlike the previous file-based adapter that polled a JSON-lines file,
this adapter POSTs events directly to the TUI server's HTTP endpoint.
Event-driven — no polling, no files, no queues.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import BasePlatformAdapter, SendResult

logger = logging.getLogger(__name__)

_HERMES_HOME = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
_PORT_FILE = _HERMES_HOME / "tui_notify_port"


def _read_tui_port() -> int:
    """Read the TUI notification HTTP port from the port file."""
    try:
        return int(_PORT_FILE.read_text().strip())
    except (OSError, ValueError):
        return 0


def _post_event(chat_id: str, content: str, metadata: dict | None = None) -> None:
    """POST a notification event to the TUI server's HTTP endpoint."""
    port = _read_tui_port()
    if not port:
        logger.debug("tui_adapter: TUI notification port not found")
        return
    payload = json.dumps({
        "chat_id": chat_id,
        "content": content,
        "metadata": metadata or {},
    }, ensure_ascii=False).encode("utf-8")
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/notify",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
    except Exception as exc:
        logger.debug("tui_adapter: POST failed: %s", exc)


class TUIAdapter(BasePlatformAdapter):
    """Platform adapter that delivers messages via HTTP POST to the TUI.

    The gateway's kanban notifier calls ``adapter.send(chat_id, msg)``
    which POSTs the event to the TUI server's local HTTP endpoint.
    The TUI server dispatches events directly to active sessions.
    """

    def __init__(self, config: PlatformConfig, platform: Platform):
        super().__init__(config, platform)

    async def send(
        self,
        chat_id: str,
        content: str,
        reply_to: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SendResult:
        """POST the event to the TUI server."""
        try:
            _post_event(chat_id, content, metadata)
            return SendResult(success=True)
        except Exception as exc:
            logger.warning("tui_adapter: POST failed: %s", exc)
            return SendResult(success=False, error=str(exc))

    async def connect(self) -> bool:
        """No external connection needed — HTTP POST only."""
        self._running = True
        return True

    async def disconnect(self) -> None:
        """No external connection to tear down."""
        self._running = False

    async def get_chat_info(self, chat_id: str) -> Dict[str, Any]:
        """Return minimal chat info for the TUI platform."""
        return {"chat_id": chat_id, "platform": "tui", "type": "direct"}

    async def start(self) -> None:
        """No external connection needed — HTTP POST only."""
        self._running = True

    async def stop(self) -> None:
        self._running = False
