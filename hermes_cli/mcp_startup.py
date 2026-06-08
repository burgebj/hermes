"""Shared CLI/TUI-safe helpers for background MCP discovery."""

from __future__ import annotations

import os
import threading
from typing import Optional

_DEFAULT_MCP_DISCOVERY_WAIT = 3.0
_MCP_DISCOVERY_WAIT_ENV = "HERMES_MCP_DISCOVERY_WAIT"

_mcp_discovery_lock = threading.Lock()
_mcp_discovery_started = False
_mcp_discovery_thread: Optional[threading.Thread] = None


def _has_configured_mcp_servers() -> bool:
    """Cheap config probe so non-MCP users avoid importing the MCP stack."""
    try:
        from hermes_cli.config import read_raw_config

        mcp_servers = (read_raw_config() or {}).get("mcp_servers")
        return isinstance(mcp_servers, dict) and len(mcp_servers) > 0
    except Exception:
        # Be conservative: if config probing fails, try discovery in the
        # background so startup still can't block.
        return True


def start_background_mcp_discovery(*, logger, thread_name: str) -> None:
    """Spawn one shared background MCP discovery thread for this process."""
    global _mcp_discovery_started, _mcp_discovery_thread

    with _mcp_discovery_lock:
        if _mcp_discovery_started:
            return
        _mcp_discovery_started = True
        if not _has_configured_mcp_servers():
            return

        def _discover() -> None:
            try:
                from tools.mcp_tool import discover_mcp_tools

                discover_mcp_tools()
            except Exception:
                logger.debug("Background MCP tool discovery failed", exc_info=True)

        thread = threading.Thread(
            target=_discover,
            name=thread_name,
            daemon=True,
        )
        _mcp_discovery_thread = thread
        thread.start()


def _configured_mcp_discovery_wait() -> float:
    """Return the bounded first-snapshot wait for background MCP discovery."""
    raw = os.environ.get(_MCP_DISCOVERY_WAIT_ENV)
    if raw is None or raw.strip() == "":
        return _DEFAULT_MCP_DISCOVERY_WAIT
    try:
        timeout = float(raw)
    except ValueError:
        return _DEFAULT_MCP_DISCOVERY_WAIT
    return max(0.0, timeout)


def wait_for_mcp_discovery(timeout: float | None = None) -> None:
    """Wait for background MCP discovery before the first tool snapshot.

    Headless one-shot sessions snapshot tools once, so the default wait is long
    enough for normal stdio/container MCP cold starts. Users with slower servers
    can tune it with ``HERMES_MCP_DISCOVERY_WAIT``; explicit test/caller timeouts
    still take precedence.
    """
    thread = _mcp_discovery_thread
    if thread is None or not thread.is_alive():
        return
    thread.join(timeout=_configured_mcp_discovery_wait() if timeout is None else timeout)
