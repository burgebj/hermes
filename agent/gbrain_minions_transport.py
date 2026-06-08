from __future__ import annotations

from typing import Any

import requests


def _headers(api_key: str | None = None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _post_json(payload: dict[str, Any], *, url: str, api_key: str | None = None, timeout: float = 30) -> dict[str, Any]:
    if not url or not str(url).strip():
        raise ValueError("URL is required")
    response = requests.post(
        str(url).strip(),
        json=payload,
        headers=_headers(api_key),
        timeout=timeout,
    )
    response.raise_for_status()
    try:
        return response.json()
    except Exception:
        return {"ok": True, "raw": getattr(response, "text", "")}


def post_enqueue_envelope(
    envelope: dict[str, Any],
    *,
    url: str,
    api_key: str | None = None,
    timeout: float = 30,
) -> dict[str, Any]:
    return _post_json(envelope, url=url, api_key=api_key, timeout=timeout)


def post_completion_envelope(
    envelope: dict[str, Any],
    *,
    url: str,
    api_key: str | None = None,
    timeout: float = 30,
) -> dict[str, Any]:
    return _post_json(envelope, url=url, api_key=api_key, timeout=timeout)
