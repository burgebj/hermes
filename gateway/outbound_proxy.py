"""Outbound proxy helpers for gateway → remote Hermes relay (proxy mode).

WSL and Windows often set ``HTTP_PROXY`` / ``HTTPS_PROXY`` to a host-only
forwarder.  aiohttp may then route relay traffic incorrectly or hang until
read timeout.  Use :func:`relay_client_session_proxy_bundle` with optional
direct retry (see ``HERMES_GATEWAY_OUTBOUND_NO_PROXY``).
"""

from __future__ import annotations

import logging
import os
import platform
from typing import Any, Tuple

logger = logging.getLogger(__name__)

_DEFAULT_SOCK_READ_SEC = 1800.0


def gateway_relay_timeout_multiplier() -> float:
    """Parse ``HERMES_PROXY_TIMEOUT_MULTIPLIER`` (default ``1.0``)."""
    raw = (os.getenv("HERMES_PROXY_TIMEOUT_MULTIPLIER") or "1.0").strip()
    try:
        m = float(raw)
    except ValueError:
        logger.warning("Invalid HERMES_PROXY_TIMEOUT_MULTIPLIER=%r; using 1.0", raw)
        return 1.0
    if m <= 0:
        logger.warning("HERMES_PROXY_TIMEOUT_MULTIPLIER must be > 0; using 1.0")
        return 1.0
    return m


def gateway_relay_sock_read_seconds(default: float = _DEFAULT_SOCK_READ_SEC) -> float:
    """``sock_read`` for relay ``ClientTimeout``, scaled by multiplier env."""
    return default * gateway_relay_timeout_multiplier()


def is_wsl_environment() -> bool:
    """Best-effort WSL2 detection (used for tests / diagnostics)."""
    if (os.environ.get("WSL_DISTRO_NAME") or "").strip():
        return True
    rel = getattr(platform.uname(), "release", "") or ""
    return "microsoft" in rel.lower()


def gateway_outbound_no_proxy() -> bool:
    """When true, relay uses no env-derived proxy (``trust_env=False``)."""
    v = (os.getenv("HERMES_GATEWAY_OUTBOUND_NO_PROXY") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def gateway_relay_disable_proxy_fallback() -> bool:
    """When true, skip the direct (no-proxy) retry after a connection failure."""
    v = (os.getenv("HERMES_GATEWAY_RELAY_NO_DIRECT_FALLBACK") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def relay_client_session_proxy_bundle() -> Tuple[bool, dict[str, Any], dict[str, Any]]:
    """Return ``(trust_env, session_kwargs, request_kwargs)`` for aiohttp relay.

    ``session_kwargs`` are merged into ``ClientSession`` (besides ``timeout`` /
    ``trust_env``).  ``request_kwargs`` are merged into ``session.post(...)``.
    """
    if gateway_outbound_no_proxy():
        return False, {}, {}
    from gateway.platforms.base import proxy_kwargs_for_aiohttp, resolve_proxy_url

    sess_kw, req_kw = proxy_kwargs_for_aiohttp(resolve_proxy_url())
    return True, sess_kw, req_kw
