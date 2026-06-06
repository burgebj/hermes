"""Cross-session rate limit guard for Nous Portal.

Writes rate limit state to a shared file so all sessions (CLI, gateway,
cron, auxiliary) can check whether Nous Portal is currently rate-limited
before making requests.  Prevents retry amplification when RPH is tapped.

Each 429 from Nous triggers up to 9 API calls per conversation turn
(3 SDK retries x 3 Hermes retries), and every one of those calls counts
against RPH.  By recording the rate limit state on first 429 and checking
it before subsequent attempts, we eliminate the amplification effect.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from typing import Any, Mapping, Optional
from utils import atomic_replace

logger = logging.getLogger(__name__)

_STATE_SUBDIR = "rate_limits"
_STATE_FILENAME = "nous.json"


def _state_path() -> str:
    """Return the path to the Nous rate limit state file."""
    from agent.provider_rate_guard import _state_path as _pg_state_path
    return _pg_state_path("nous")


def _parse_reset_seconds(headers: Optional[Mapping[str, str]]) -> Optional[float]:
    """Shim: delegate to provider_rate_guard._parse_reset_seconds."""
    from agent.provider_rate_guard import _parse_reset_seconds as _pg_parse
    return _pg_parse(headers)


def record_nous_rate_limit(
    *,
    headers: Optional[Mapping[str, str]] = None,
    error_context: Optional[dict[str, Any]] = None,
    default_cooldown: float = 300.0,
) -> None:
    """Record that Nous Portal is rate-limited (shim — delegates to provider_rate_guard)."""
    from agent.provider_rate_guard import record_rate_limit
    return record_rate_limit(
        "nous",
        headers=headers,
        error_context=error_context,
        default_cooldown=default_cooldown,
    )


def nous_rate_limit_remaining() -> Optional[float]:
    """Check if Nous Portal is currently rate-limited (shim — delegates to provider_rate_guard)."""
    from agent.provider_rate_guard import rate_limit_remaining
    return rate_limit_remaining("nous")


def clear_nous_rate_limit() -> None:
    """Clear the Nous rate limit state (shim — delegates to provider_rate_guard)."""
    from agent.provider_rate_guard import clear_rate_limit
    return clear_rate_limit("nous")


def format_remaining(seconds: float) -> str:
    """Format seconds remaining into human-readable duration (shim — delegates to provider_rate_guard)."""
    from agent.provider_rate_guard import format_remaining as _fmt
    return _fmt(seconds)


# Buckets with reset windows shorter than this are treated as transient
# (upstream jitter, secondary throttling) rather than a genuine quota
# exhaustion worth a cross-session breaker trip.
_MIN_RESET_FOR_BREAKER_SECONDS = 60.0


def is_genuine_nous_rate_limit(
    *,
    headers: Optional[Mapping[str, str]] = None,
    last_known_state: Optional[Any] = None,
) -> bool:
    """Decide whether a 429 from Nous Portal is a real account rate limit.

    Nous Portal multiplexes multiple upstream providers (DeepSeek, Kimi,
    MiMo, Hermes, ...) behind one endpoint.  A 429 can mean either:

      (a) The caller's own RPM / RPH / TPM / TPH bucket on Nous is
          exhausted — a genuine rate limit that will last until the
          bucket resets.
      (b) The upstream provider is out of capacity for a specific model
          — transient, clears in seconds, and has nothing to do with
          the caller's quota on Nous.

    Tripping the cross-session breaker on (b) blocks ALL Nous requests
    (and all models, since Nous is one provider key) for minutes even
    though the caller's account is healthy and a different model would
    have worked.  That's the bug users hit when DeepSeek V4 Pro 429s
    trigger a breaker that then blocks Kimi 2.6 and MiMo V2.5 Pro.

    We tell the two apart by looking at:

      1. The 429 response's own ``x-ratelimit-*`` headers.  Nous emits
         the full suite on every response including 429s.  An exhausted
         bucket (``remaining == 0`` with a reset window >= 60s) is
         proof of (a).
      2. The last-known-good rate-limit state captured by
         ``_capture_rate_limits()`` on the previous successful
         response.  If any bucket there was already near-exhausted with
         a substantial reset window, the current 429 is almost
         certainly (a) continuing from that condition.

    If neither signal fires, we treat the 429 as (b): fail the single
    request, let the retry loop or model-switch proceed, and do NOT
    write the cross-session breaker file.

    Returns True when the evidence points at (a).
    """
    # Signal 1: current 429 response headers.
    state = _parse_buckets_from_headers(headers)
    if _has_exhausted_bucket(state):
        return True

    # Signal 2: last-known-good state from a recent successful response.
    # Accepts either a RateLimitState (dataclass from rate_limit_tracker)
    # or a dict of bucket snapshots.
    if last_known_state is not None and _has_exhausted_bucket_in_object(last_known_state):
        return True

    return False


def _parse_buckets_from_headers(
    headers: Optional[Mapping[str, str]],
) -> dict[str, tuple[Optional[int], Optional[float]]]:
    """Extract (remaining, reset_seconds) per bucket from x-ratelimit-* headers.

    Returns empty dict when no rate-limit headers are present.
    """
    if not headers:
        return {}

    lowered = {k.lower(): v for k, v in headers.items()}
    if not any(k.startswith("x-ratelimit-") for k in lowered):
        return {}

    def _maybe_int(raw: Optional[str]) -> Optional[int]:
        if raw is None:
            return None
        try:
            return int(float(raw))
        except (TypeError, ValueError):
            return None

    def _maybe_float(raw: Optional[str]) -> Optional[float]:
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    result: dict[str, tuple[Optional[int], Optional[float]]] = {}
    for tag in ("requests", "requests-1h", "tokens", "tokens-1h"):
        remaining = _maybe_int(lowered.get(f"x-ratelimit-remaining-{tag}"))
        reset = _maybe_float(lowered.get(f"x-ratelimit-reset-{tag}"))
        if remaining is not None or reset is not None:
            result[tag] = (remaining, reset)
    return result


def _has_exhausted_bucket(
    buckets: Mapping[str, tuple[Optional[int], Optional[float]]],
) -> bool:
    """Return True when any bucket has remaining == 0 AND a meaningful reset window."""
    for remaining, reset in buckets.values():
        if remaining is None or remaining > 0:
            continue
        if reset is None:
            continue
        if reset >= _MIN_RESET_FOR_BREAKER_SECONDS:
            return True
    return False


def _has_exhausted_bucket_in_object(state: Any) -> bool:
    """Check a RateLimitState-like object for an exhausted bucket.

    Accepts the dataclass from ``agent.rate_limit_tracker`` (buckets
    exposed as attributes ``requests_min``, ``requests_hour``,
    ``tokens_min``, ``tokens_hour``) and falls back gracefully for any
    object missing those attributes.
    """
    for attr in ("requests_min", "requests_hour", "tokens_min", "tokens_hour"):
        bucket = getattr(state, attr, None)
        if bucket is None:
            continue
        limit = getattr(bucket, "limit", 0) or 0
        remaining = getattr(bucket, "remaining", 0) or 0
        # Prefer the adjusted "remaining_seconds_now" property when present;
        # fall back to raw reset_seconds.
        reset = getattr(bucket, "remaining_seconds_now", None)
        if reset is None:
            reset = getattr(bucket, "reset_seconds", 0.0) or 0.0
        if limit <= 0:
            continue
        if remaining > 0:
            continue
        if reset >= _MIN_RESET_FOR_BREAKER_SECONDS:
            return True
    return False
