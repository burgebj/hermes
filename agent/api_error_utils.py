"""Shared API error classification and display helpers."""

from __future__ import annotations

import re
from typing import Any, Callable, Optional


def _api_error_object(error: BaseException) -> Optional[dict[str, Any]]:
    """Return the provider error object from nested or flat SDK bodies."""
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return None
    nested_error = body.get("error")
    return nested_error if isinstance(nested_error, dict) else body


def is_usage_limit_reached_error(error: BaseException) -> bool:
    """Return True for provider account usage-limit payloads.

    These errors are distinct from transient rate limits: the provider is
    reporting that the account has exhausted its current usage window.
    """
    err_obj = _api_error_object(error)
    return bool(err_obj and err_obj.get("type") == "usage_limit_reached")


def summarize_api_error(
    error: BaseException,
    *,
    detail_decorator: Optional[Callable[[str], str]] = None,
) -> str:
    """Extract a compact human-readable one-liner from an API error."""
    raw = str(error)

    if isinstance(error, ValueError) and "expected ident at line" in raw.lower():
        return f"Malformed provider streaming response: {raw[:300]}"

    if "<!DOCTYPE" in raw or "<html" in raw:
        match = re.search(r"<title[^>]*>([^<]+)</title>", raw, re.IGNORECASE)
        title = match.group(1).strip() if match else "HTML error page (title not found)"
        ray = re.search(r"Cloudflare Ray ID:\s*<strong[^>]*>([^<]+)</strong>", raw)
        ray_id = ray.group(1).strip() if ray else None
        status_code = getattr(error, "status_code", None)
        parts = []
        if status_code:
            parts.append(f"HTTP {status_code}")
        parts.append(title)
        if ray_id:
            parts.append(f"Ray {ray_id}")
        return " — ".join(parts)

    err_obj = _api_error_object(error)
    if err_obj is not None:
        msg = err_obj.get("message")
        if msg:
            status_code = getattr(error, "status_code", None)
            prefix = f"HTTP {status_code}: " if status_code else ""
            details = []
            if err_obj.get("type") == "usage_limit_reached":
                resets_in = err_obj.get("resets_in_seconds")
                if isinstance(resets_in, (int, float)) and resets_in > 0:
                    seconds = int(resets_in)
                    hours, rem = divmod(seconds, 3600)
                    minutes, _ = divmod(rem, 60)
                    details.append(
                        f"resets_in_seconds={seconds}; reset_hhmm={hours:02d}:{minutes:02d}"
                    )
                resets_at = err_obj.get("resets_at")
                if resets_at:
                    details.append(f"resets_at={resets_at}")
                plan_type = err_obj.get("plan_type")
                if plan_type:
                    details.append(f"plan={plan_type}")
            suffix = f" ({'; '.join(details)})" if details else ""
            detail = f"{prefix}{str(msg)[:300]}{suffix}"
            return detail_decorator(detail) if detail_decorator else detail

    status_code = getattr(error, "status_code", None)
    prefix = f"HTTP {status_code}: " if status_code else ""
    detail = f"{prefix}{raw[:500]}"
    return detail_decorator(detail) if detail_decorator else detail


def usage_limit_error_message(
    error: BaseException,
    *,
    detail_decorator: Optional[Callable[[str], str]] = None,
) -> str:
    """Return the canonical user-facing usage-limit error message."""
    return f"API usage limit reached: {summarize_api_error(error, detail_decorator=detail_decorator)}"
