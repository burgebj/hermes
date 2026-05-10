"""Feishu OAuth 2.0 Device Flow authorization.

Implements RFC 8628 (Device Authorization Grant) for Feishu/Lark user identity:
  1. POST https://accounts.feishu.cn/oauth/v1/device_authorization
     → get device_code + verification_uri_complete + expires_in + interval
  2. Render verification_uri_complete as ASCII QR code in terminal
  3. POST https://open.feishu.cn/open-apis/authen/v2/oauth/token (poll)
     → get access_token + refresh_token on user scan-and-approve

Tokens are persisted to ~/.hermes/feishu_uat.json (mode 0600).

Entry point for ``hermes setup feishu-uat``:  feishu_qr_auth(client_id)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Awaitable, Callable, Optional, Tuple

import requests

from hermes_constants import display_hermes_home, get_hermes_home

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FEISHU_ACCOUNTS_BASE_URL = os.environ.get(
    "FEISHU_ACCOUNTS_BASE_URL", "https://accounts.feishu.cn"
).rstrip("/")

FEISHU_OPEN_BASE_URL = os.environ.get(
    "FEISHU_OPEN_BASE_URL", "https://open.feishu.cn"
).rstrip("/")

# Default scope for UAT — covers core OAPI tool families.
# WARNING: im:message:send_as_user is intentionally excluded from defaults —
# it is a privileged scope. Pass it explicitly via --scope if needed.
# TODO(worker-3): update feishu-uat-tools.md setup command to reflect this change.
FEISHU_DEFAULT_SCOPE = (
    # NOTE: Feishu deprecated the `docs:document*` scope namespace in favour
    # of `docx:document*`. Apps that pass the old names get a hard
    # invalid_scope rejection on the entire batch even when 9/10 scopes are
    # valid. The list below is the conservative set that ships clean against
    # any modern app config — callers wanting docx access should pass
    # `docx:document:readonly` / `docx:document:write_only` explicitly via
    # `/feishu_auth <scope...>`.
    "calendar:calendar "
    "drive:drive "
    "drive:export:readonly "
    "docs:document.comment:create "
    "docs:document.comment:write_only "
    "bitable:app "
    "wiki:wiki:readonly "
    "sheets:spreadsheet "
    "task:task:write "
    "task:task:read "
    "task:section:write "
    "task:section:read "
    "task:comment:write "
    "contact:user.base:readonly "
    "offline_access"
)

# Path to persisted UAT token file (legacy single-user single-file location)
FEISHU_UAT_PATH = get_hermes_home() / "feishu_uat.json"

# Per-user UAT directory: ~/.hermes/feishu_uat/<open_id>.json
# Multi-user mode (1 bot serving many users) writes one file per user_open_id.
FEISHU_UAT_DIR = get_hermes_home() / "feishu_uat"


def _per_user_uat_path(open_id: str) -> "Path":
    """Return the per-user UAT file path for a given Feishu open_id.

    Open_ids start with 'ou_' and consist of [A-Za-z0-9_-]; the function refuses
    anything else to avoid path traversal (slash, dot, null, etc.).
    """
    if not open_id or not isinstance(open_id, str):
        raise ValueError("open_id must be a non-empty string")
    # Defensive: reject anything that could escape the directory.
    if "/" in open_id or "\\" in open_id or ".." in open_id or "\0" in open_id:
        raise ValueError(f"open_id contains illegal characters: {open_id!r}")
    return FEISHU_UAT_DIR / f"{open_id}.json"

# Polling backoff cap in seconds (RFC 8628 §3.5)
_POLL_INTERVAL_CAP = 30


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class FeishuAuthError(Exception):
    """Raised when a Feishu OAuth API call fails or the flow cannot complete."""


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

_SENSITIVE_PATTERNS = [
    (re.compile(r"Bearer\s+\S+"), "[REDACTED]"),
    (re.compile(r"access_token=\S+"), "access_token=[REDACTED]"),
    (re.compile(r"device_code=\S+"), "device_code=[REDACTED]"),
    (re.compile(r"user_code=\S+"), "user_code=[REDACTED]"),
    (re.compile(r"refresh_token=\S+"), "refresh_token=[REDACTED]"),
]


def _safe_error_text(exc: BaseException) -> str:
    """Return str(exc) with sensitive token/code values redacted."""
    text = str(exc)
    for pattern, replacement in _SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _refresh_token_expires_in(data: dict, default: int = 2592000) -> int:
    """Return refresh-token TTL from Feishu v2 token responses.

    Feishu's current OAuth v2 docs name the field ``refresh_token_expires_in``.
    Older code/tests used ``refresh_expires_in``; accept both to stay backward
    compatible with saved fixtures and mocked responses.
    """
    raw = data.get("refresh_token_expires_in")
    if raw is None:
        raw = data.get("refresh_expires_in", default)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _scope_with_offline_access(scope: Optional[str]) -> str:
    """Return a normalized OAuth scope string that can receive refresh_token."""
    parts = [part for part in (scope or FEISHU_DEFAULT_SCOPE).split() if part]
    if "offline_access" not in parts:
        parts.append("offline_access")
    return " ".join(dict.fromkeys(parts))


# ---------------------------------------------------------------------------
# Internal HTTP helper
# ---------------------------------------------------------------------------

def _api_post(path: str, base_url: str, payload: dict) -> dict:
    """POST to a Feishu endpoint and return the parsed JSON body.

    Args:
        path: URL path (e.g. '/oauth/v1/device_authorization').
        base_url: Base URL of the Feishu endpoint host.
        payload: JSON body dict to send.

    Returns:
        Parsed response JSON as a dict.

    Raises:
        FeishuAuthError: On network errors or non-retryable API errors.
    """
    url = f"{base_url}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=15)
    except requests.RequestException as exc:
        raise FeishuAuthError(f"Network error calling {url}: {exc}") from exc

    # RFC 6749 / RFC 8628: 4xx responses MAY carry a JSON OAuth error body
    # (e.g. authorization_pending, slow_down). Feishu actually returns 400
    # for pending state. We must parse the JSON body before treating 4xx
    # as fatal, so the caller can distinguish recoverable from terminal errors.
    try:
        data = resp.json()
    except ValueError:
        data = None

    if not isinstance(data, dict):
        body = (resp.text or "")[:500]
        raise FeishuAuthError(
            f"HTTP {resp.status_code} from {url} — non-JSON body: {body}"
        )

    # RFC 6749 / Feishu error model: error field present means failure
    # "authorization_pending" and "slow_down" are handled by the caller
    error_code = data.get("error") or data.get("error_code")
    if error_code and error_code not in ("authorization_pending", "slow_down"):
        description = data.get("error_description", "unknown error")
        raise FeishuAuthError(
            f"API error [{path}]: {description} (error={error_code})"
        )
    return data


# ---------------------------------------------------------------------------
# Step 1: request device code
# ---------------------------------------------------------------------------

def begin_device_authorization(
    client_id: str,
    scope: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> dict:
    """Start a Feishu device-flow authorization.

    Args:
        client_id: Feishu app ID (FEISHU_APP_ID).
        scope: Space-separated OAuth scopes. Defaults to FEISHU_DEFAULT_SCOPE.
        client_secret: Feishu app secret (FEISHU_APP_SECRET). Required by the
            Feishu device_authorization endpoint even though RFC 8628 lists it
            as optional — Feishu returns 400 invalid_request without it.

    Returns:
        Dict with keys: device_code, user_code, verification_uri,
        verification_uri_complete, expires_in, interval.

    Raises:
        FeishuAuthError: If the API call fails or required fields are missing.
    """
    payload: dict = {"client_id": client_id}
    if client_secret:
        payload["client_secret"] = client_secret
    payload["scope"] = _scope_with_offline_access(scope)

    data = _api_post(
        "/oauth/v1/device_authorization",
        FEISHU_ACCOUNTS_BASE_URL,
        payload,
    )

    required = [
        "device_code",
        "user_code",
        "verification_uri",
        "verification_uri_complete",
        "expires_in",
        "interval",
    ]
    missing = [f for f in required if f not in data]
    if missing:
        raise FeishuAuthError(
            f"device_authorization response missing fields: {', '.join(missing)}"
        )

    return {
        "device_code": str(data["device_code"]).strip(),
        "user_code": str(data["user_code"]).strip(),
        "verification_uri": str(data["verification_uri"]).strip(),
        "verification_uri_complete": str(data["verification_uri_complete"]).strip(),
        "expires_in": int(data.get("expires_in", 1800)),
        "interval": max(int(data.get("interval", 3)), 2),
    }


# ---------------------------------------------------------------------------
# Step 3: poll for token
# ---------------------------------------------------------------------------

def poll_device_token(
    device_code: str,
    client_id: str,
    client_secret: Optional[str] = None,
) -> dict:
    """Poll the Feishu token endpoint once for a device code grant.

    Args:
        device_code: The device_code from begin_device_authorization().
        client_id: Feishu app ID.
        client_secret: Feishu app secret. Required by Feishu's token endpoint
            for confidential clients; without it the endpoint cannot
            authenticate the client and the flow can never succeed.

    Returns:
        Dict with keys: access_token?, refresh_token?, open_id?,
        error?, error_description?

    Raises:
        FeishuAuthError: On non-retryable API errors.
    """
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": client_id,
        "device_code": device_code,
    }
    if client_secret:
        payload["client_secret"] = client_secret

    # _api_post raises on hard errors; authorization_pending / slow_down pass through
    try:
        data = _api_post(
            "/open-apis/authen/v2/oauth/token",
            FEISHU_OPEN_BASE_URL,
            payload,
        )
    except FeishuAuthError:
        raise

    return {
        "access_token": str(data.get("access_token", "")).strip() or None,
        "refresh_token": str(data.get("refresh_token", "")).strip() or None,
        "open_id": str(data.get("open_id", "")).strip() or None,
        "expires_in": int(data.get("expires_in", 7200)),
        "refresh_expires_in": _refresh_token_expires_in(data),
        "token_type": str(data.get("token_type", "Bearer")).strip(),
        "scope": str(data.get("scope", "")).strip(),
        "error": str(data.get("error") or data.get("error_code", "")).strip() or None,
        "error_description": str(data.get("error_description", "")).strip() or None,
    }


# ---------------------------------------------------------------------------
# Polling loop
# ---------------------------------------------------------------------------

def wait_for_authorization_success(
    device_code: str,
    client_id: str,
    interval: int = 3,
    expires_in: int = 1800,
    on_waiting: Optional[callable] = None,
    client_secret: Optional[str] = None,
) -> Tuple[str, str, str, int, int]:
    """Block until Feishu device authorization succeeds or times out.

    Args:
        device_code: Device code from begin_device_authorization().
        client_id: Feishu app ID.
        interval: Initial poll interval in seconds.
        expires_in: Total timeout in seconds.
        on_waiting: Optional callback invoked on each pending poll iteration.
        client_secret: Feishu app secret (required by Feishu's token endpoint
            even though RFC 8628 device_code grant lists it as optional).

    Returns:
        Tuple of (access_token, refresh_token, open_id, expires_in, refresh_expires_in).

    Raises:
        FeishuAuthError: On authorization failure, denial, or timeout.
    """
    deadline = time.monotonic() + expires_in
    # 2-minute transient-error tolerance window
    retry_window = 120.0
    retry_start = 0.0
    current_interval = interval

    while time.monotonic() < deadline:
        time.sleep(current_interval)

        try:
            result = poll_device_token(
                device_code, client_id, client_secret=client_secret,
            )
        except FeishuAuthError:
            if retry_start == 0.0:
                retry_start = time.monotonic()
            if time.monotonic() - retry_start < retry_window:
                continue
            raise

        error = result.get("error")

        # Still waiting — user hasn't scanned yet
        if not error or error == "authorization_pending":
            retry_start = 0.0
            if on_waiting:
                on_waiting()
            continue

        # Server requests slower polling
        if error == "slow_down":
            current_interval = min(current_interval + 5, _POLL_INTERVAL_CAP)
            retry_start = 0.0
            if on_waiting:
                on_waiting()
            continue

        # Success — tokens present
        if result.get("access_token"):
            token = result["access_token"]
            refresh = result.get("refresh_token") or ""
            open_id = result.get("open_id") or ""
            tok_expires_in = int(result.get("expires_in") or 7200)
            tok_refresh_expires_in = _refresh_token_expires_in(result)
            return token, refresh, open_id, tok_expires_in, tok_refresh_expires_in

        # Authorization explicitly denied or expired
        if retry_start == 0.0:
            retry_start = time.monotonic()
        if time.monotonic() - retry_start < retry_window:
            continue
        description = result.get("error_description") or error
        raise FeishuAuthError(f"authorization failed: {description}")

    raise FeishuAuthError("authorization timed out — please retry 'hermes setup feishu-auth'")


# ---------------------------------------------------------------------------
# Token persistence
# ---------------------------------------------------------------------------

def save_uat(
    access_token: str,
    refresh_token: str,
    open_id: str,
    expires_in: int,
    refresh_expires_in: int,
    scope: str,
    app_id: str,
    per_user: bool = False,
) -> None:
    """Persist UAT tokens to disk (mode 0600).

    By default writes to the legacy single-file location
    (~/.hermes/feishu_uat.json) to preserve back-compat with single-user mode.
    When ``per_user=True``, writes to ~/.hermes/feishu_uat/<open_id>.json so
    multi-user (chat-mode device flow) deployments can keep one file per user.

    Args:
        access_token: Feishu user access token.
        refresh_token: Feishu refresh token.
        open_id: User open_id.
        expires_in: access_token TTL in seconds.
        refresh_expires_in: refresh_token TTL in seconds.
        scope: Granted OAuth scopes string.
        app_id: Feishu app ID that obtained these tokens.
        per_user: When True, write to ~/.hermes/feishu_uat/<open_id>.json
            instead of the legacy single-file location.
    """
    now_ms = int(time.time() * 1000)
    token_data = {
        "app_id": app_id,
        "user_open_id": open_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": now_ms + expires_in * 1000,
        "refresh_expires_at": now_ms + refresh_expires_in * 1000,
        "scope": scope,
        "granted_at": now_ms,
    }
    target_path = _per_user_uat_path(open_id) if per_user else FEISHU_UAT_PATH
    parent = target_path.parent
    parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(parent, 0o700)
    # Atomic write: write to a temp file then os.replace to avoid partial reads
    fd, tmp_path = tempfile.mkstemp(dir=parent)
    try:
        os.chmod(tmp_path, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(token_data, fh, indent=2)
        os.replace(tmp_path, target_path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    logger.info("Feishu UAT saved to %s", target_path)


def load_uat(open_id: Optional[str] = None) -> Optional[dict]:
    """Load stored UAT from disk.

    With ``open_id``, loads ~/.hermes/feishu_uat/<open_id>.json. Without it,
    loads the legacy single-file location ~/.hermes/feishu_uat.json. Returns
    ``None`` if the target file is missing or unreadable (the caller decides
    whether absence means "needs auth" or "no such user").

    Args:
        open_id: Optional Feishu user open_id. When supplied the per-user path
            is read; otherwise the legacy single-file path is read.
    """
    target_path = _per_user_uat_path(open_id) if open_id else FEISHU_UAT_PATH
    if not target_path.exists():
        return None
    try:
        with open(target_path, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Failed to load feishu UAT from %s: %s", target_path, exc)
        return None


def refresh_uat(client_id: str, client_secret: str) -> None:
    """Attempt to refresh the stored UAT using its refresh_token.

    On success, persists new tokens via save_uat() (atomic write).
    On 4xx or expired refresh_token, removes the stale token file and raises
    NeedAuthorizationError so the caller knows re-authorization is required.

    Args:
        client_id: Feishu app ID (FEISHU_APP_ID).
        client_secret: Feishu app secret (FEISHU_APP_SECRET).

    Raises:
        NeedAuthorizationError: If refresh fails or token file is missing.
        FeishuAuthError: On non-auth network/API errors.
    """
    from tools.feishu_oapi_client import NeedAuthorizationError

    data = load_uat()
    if not data:
        raise NeedAuthorizationError(reason="no token file; run 'hermes feishu-auth' first")

    refresh_token = data.get("refresh_token", "")
    if not refresh_token:
        raise NeedAuthorizationError(reason="no refresh_token in stored UAT")

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    try:
        resp_data = _api_post(
            "/open-apis/authen/v2/oauth/token",
            FEISHU_OPEN_BASE_URL,
            payload,
        )
    except FeishuAuthError as exc:
        # Treat refresh failure as expired — clean up and require re-auth
        logger.warning("refresh_uat failed: %s", _safe_error_text(exc))
        try:
            os.remove(FEISHU_UAT_PATH)
        except OSError:
            pass
        raise NeedAuthorizationError(
            user_open_id=data.get("user_open_id", "unknown"),
            reason="refresh_token expired or invalid; re-run 'hermes feishu-auth'",
        ) from exc

    new_access_token = str(resp_data.get("access_token", "")).strip()
    new_refresh_token = str(resp_data.get("refresh_token", "")).strip()
    if not new_access_token:
        try:
            os.remove(FEISHU_UAT_PATH)
        except OSError:
            pass
        raise NeedAuthorizationError(
            user_open_id=data.get("user_open_id", "unknown"),
            reason="refresh response missing access_token; re-run 'hermes feishu-auth'",
        )

    save_uat(
        access_token=new_access_token,
        refresh_token=new_refresh_token or refresh_token,
        open_id=data.get("user_open_id", ""),
        expires_in=int(resp_data.get("expires_in") or 7200),
        refresh_expires_in=_refresh_token_expires_in(resp_data),
        scope=str(resp_data.get("scope", "")).strip() or data.get("scope", ""),
        app_id=data.get("app_id", client_id),
    )
    logger.info("Feishu UAT refreshed for user %s", data.get("user_open_id", "unknown"))


def fetch_user_info(access_token: str) -> dict:
    """GET /authen/v1/user_info to resolve the calling UAT's open_id / name.

    Feishu's token endpoint does NOT include open_id in its response, so chat-mode
    device flow has to make this extra hop after a successful token exchange to
    know which file to persist the UAT under. Mirrors openclaw-lark's
    fetchUserInfo step.

    Args:
        access_token: A fresh user_access_token returned by the token endpoint.

    Returns:
        Dict with keys ``open_id`` (always), ``union_id`` / ``user_id`` / ``name``
        (when provided by Feishu).

    Raises:
        FeishuAuthError: On network error, non-zero code, or missing data envelope.
    """
    url = f"{FEISHU_OPEN_BASE_URL}/open-apis/authen/v1/user_info"
    try:
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
    except requests.RequestException as exc:
        raise FeishuAuthError(f"Network error calling {url}: {exc}") from exc

    try:
        body = resp.json()
    except ValueError as exc:
        raise FeishuAuthError(
            f"Non-JSON response from {url}: {(resp.text or '')[:200]}"
        ) from exc

    code = body.get("code")
    data = body.get("data") or {}
    if code != 0 or not data:
        msg = body.get("msg") or "unknown"
        raise FeishuAuthError(f"user_info failed: code={code} msg={msg}")

    return {
        "open_id": str(data.get("open_id") or "").strip(),
        "union_id": str(data.get("union_id") or "").strip() or None,
        "user_id": str(data.get("user_id") or "").strip() or None,
        "name": str(data.get("name") or "").strip() or None,
    }


def refresh_uat_for_user(
    user_open_id: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Refresh a per-user UAT (~/.hermes/feishu_uat/<open_id>.json).

    Used by the background refresh daemon (US-007). Unlike ``refresh_uat``
    (which destroys the legacy file on hard errors), this does NOT delete
    the per-user file — the daemon decides whether to mark it needs_reauth
    or just retry on the next tick. Concurrent refresh attempts on the same
    open_id are the caller's responsibility to serialize.

    Args:
        user_open_id: Feishu user open_id whose UAT should be refreshed.
        client_id: Feishu app ID.
        client_secret: Feishu app secret.

    Raises:
        NeedAuthorizationError: token file missing / refresh_token rejected.
        FeishuAuthError: transient network/API error.
    """
    from tools.feishu_oapi_client import NeedAuthorizationError

    target_path = _per_user_uat_path(user_open_id)
    if not target_path.exists():
        raise NeedAuthorizationError(
            user_open_id=user_open_id,
            reason=f"no per-user UAT file at {target_path}",
        )

    with open(target_path, encoding="utf-8") as fh:
        data = json.load(fh)

    refresh_token = data.get("refresh_token", "")
    if not refresh_token:
        raise NeedAuthorizationError(
            user_open_id=user_open_id,
            reason="no refresh_token in per-user UAT",
        )

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    resp_data = _api_post(
        "/open-apis/authen/v2/oauth/token",
        FEISHU_OPEN_BASE_URL,
        payload,
    )

    if resp_data.get("error"):
        raise NeedAuthorizationError(
            user_open_id=user_open_id,
            reason=f"refresh error: {resp_data.get('error')}",
        )

    new_access_token = str(resp_data.get("access_token", "")).strip()
    if not new_access_token:
        raise NeedAuthorizationError(
            user_open_id=user_open_id,
            reason="refresh response missing access_token",
        )

    new_refresh_token = str(resp_data.get("refresh_token", "")).strip() or refresh_token
    save_uat(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        open_id=user_open_id,
        expires_in=int(resp_data.get("expires_in") or 7200),
        refresh_expires_in=_refresh_token_expires_in(resp_data),
        scope=str(resp_data.get("scope", "")).strip() or data.get("scope", ""),
        app_id=data.get("app_id", client_id),
        per_user=True,
    )
    logger.info("Feishu UAT refreshed (per-user) for %s", user_open_id)


# ---------------------------------------------------------------------------
# Chat-mode device flow (multi-user / per-user)
# ---------------------------------------------------------------------------
#
# Sync ``feishu_qr_auth(...)`` is the CLI entry point — it prints a QR code,
# blocks the terminal, and writes to the legacy single-user UAT path.
#
# ``chat_mode_device_flow(...)`` is the async multi-user entry point — it does
# NOT print to stdout. Callers (e.g. the feishu gateway adapter) supply async
# callbacks so the verification URI / user_code / success / error events can be
# rendered as Feishu cards back to the requesting chat user. On success, the
# UAT is persisted to the per-user file ``~/.hermes/feishu_uat/<open_id>.json``
# (NOT the legacy single-file path).

# Terminal poll error codes (RFC 6749 §5.2 + RFC 8628 §3.5).
_TERMINAL_POLL_ERRORS = frozenset({
    "access_denied",       # User denied authorization
    "expired_token",       # device_code expired before user authorized
    "invalid_grant",       # device_code rejected by server
    "invalid_client",      # client credentials wrong
    "unauthorized_client", # app not configured for device_code grant
    "server_error",        # 5xx from authorization server
    "invalid_request",     # malformed payload
})


async def chat_mode_device_flow(
    client_id: str,
    client_secret: str,
    scope: Optional[str],
    on_verification_url: Callable[[str, str, int], Awaitable[None]],
    on_success: Callable[[str, str], Awaitable[None]],
    on_error: Callable[[str], Awaitable[None]],
    cancel_event: Optional[asyncio.Event] = None,
) -> Optional[Tuple[str, str, str]]:
    """Run a Feishu OAuth 2.0 device flow without any terminal output.

    Designed for multi-user chat-driven UX (`/feishu_auth` slash command from
    a Feishu bot). The caller wires async callbacks so the verification URI
    can be rendered as a card to the requesting user, and success/failure can
    be reported back to the same chat.

    On success, the UAT is persisted to ~/.hermes/feishu_uat/<open_id>.json
    (per-user mode) — NOT the legacy single-file location.

    Args:
        client_id: Feishu app ID.
        client_secret: Feishu app secret (Feishu requires it on both
            device_authorization and token endpoints).
        scope: Optional space-separated scope override; defaults to
            FEISHU_DEFAULT_SCOPE when None.
        on_verification_url: Async callback invoked with
            (verification_uri_complete, user_code, expires_in_seconds) once the
            device code is obtained, before polling begins.
        on_success: Async callback invoked with (user_open_id, granted_scope)
            after a successful token exchange and UAT persist.
        on_error: Async callback invoked with a single human-readable reason
            string when the flow fails or is cancelled.
        cancel_event: Optional asyncio.Event a caller can set to abort the
            poll loop early (between sleep and next poll).

    Returns:
        (access_token, refresh_token, user_open_id) on success, or None on
        any failure / cancellation / timeout. on_success / on_error is always
        invoked exactly once before returning.
    """
    # Step 1: device authorization (network call → run in thread pool)
    try:
        auth_data = await asyncio.to_thread(
            begin_device_authorization, client_id, scope, client_secret
        )
    except FeishuAuthError as exc:
        await on_error(f"init failed: {exc}")
        return None

    verification_uri = auth_data["verification_uri_complete"]
    user_code = auth_data["user_code"]
    expires_in = int(auth_data.get("expires_in", 1800))
    interval = max(int(auth_data.get("interval", 5)), 2)
    device_code = auth_data["device_code"]

    # Notify caller — they render the URL/user_code as a card to the chat user.
    try:
        await on_verification_url(verification_uri, user_code, expires_in)
    except Exception as exc:  # caller's renderer must not break the flow
        logger.warning("on_verification_url callback raised: %s", exc)

    # Step 2: poll loop with slow_down handling and cancellation support.
    deadline = time.monotonic() + expires_in
    current_interval = interval
    token_data: Optional[dict] = None

    while time.monotonic() < deadline:
        if cancel_event is not None and cancel_event.is_set():
            await on_error("cancelled by user")
            return None

        await asyncio.sleep(current_interval)

        if cancel_event is not None and cancel_event.is_set():
            await on_error("cancelled by user")
            return None

        try:
            result = await asyncio.to_thread(
                poll_device_token, device_code, client_id, client_secret
            )
        except FeishuAuthError as exc:
            # Transient network/HTTP error — keep polling within the deadline.
            logger.debug("chat-mode poll transient error: %s", exc)
            continue

        error = result.get("error")

        # Success: token endpoint returned access_token (and no error).
        if result.get("access_token") and not error:
            token_data = result
            break

        # Still waiting for user to scan/approve.
        if not error or error == "authorization_pending":
            continue

        # Server asks us to slow down.
        if error == "slow_down":
            current_interval = min(current_interval + 5, _POLL_INTERVAL_CAP)
            continue

        # Terminal error.
        if error in _TERMINAL_POLL_ERRORS:
            description = result.get("error_description") or error
            await on_error(f"{error}: {description}")
            return None

        # Unknown error treated as terminal (avoid infinite loop on edge cases).
        description = result.get("error_description") or "unknown error"
        await on_error(f"{error}: {description}")
        return None

    if token_data is None:
        await on_error("authorization timed out — please retry")
        return None

    access_token = (token_data.get("access_token") or "").strip()
    refresh_token = (token_data.get("refresh_token") or "").strip()
    open_id = (token_data.get("open_id") or "").strip()
    expires_in_t = int(token_data.get("expires_in", 7200))
    refresh_expires_in_t = _refresh_token_expires_in(token_data)
    granted_scope = _scope_with_offline_access(token_data.get("scope") or scope)

    if not access_token:
        await on_error("token response missing access_token")
        return None

    # Feishu's v2 token endpoint does NOT include open_id in its response —
    # we have to GET /authen/v1/user_info with the new access_token to learn
    # who the user is. Mirrors openclaw-lark's fetchUserInfo step.
    if not open_id:
        try:
            user_info = await asyncio.to_thread(fetch_user_info, access_token)
            open_id = (user_info.get("open_id") or "").strip()
        except FeishuAuthError as exc:
            await on_error(f"user_info lookup failed: {exc}")
            return None

    if not open_id:
        await on_error("user_info response missing open_id")
        return None

    # Step 3: persist per-user UAT.
    try:
        await asyncio.to_thread(
            save_uat,
            access_token=access_token,
            refresh_token=refresh_token,
            open_id=open_id,
            expires_in=expires_in_t,
            refresh_expires_in=refresh_expires_in_t,
            scope=granted_scope,
            app_id=client_id,
            per_user=True,
        )
    except Exception as exc:
        await on_error(f"failed to save UAT: {exc}")
        return None

    try:
        await on_success(open_id, granted_scope)
    except Exception as exc:
        logger.warning("on_success callback raised: %s", exc)

    return access_token, refresh_token, open_id


# ---------------------------------------------------------------------------
# QR code rendering (copied pattern from dingtalk_auth.py)
# ---------------------------------------------------------------------------

def _ensure_qrcode_installed() -> bool:
    """Try to import qrcode; auto-install via uv/pip if missing.

    Returns:
        True if qrcode is available after the call.
    """
    try:
        import qrcode  # noqa: F401
        return True
    except ImportError:
        pass

    import subprocess

    for cmd in (
        [sys.executable, "-m", "uv", "pip", "install", "qrcode"],
        [sys.executable, "-m", "pip", "install", "-q", "qrcode"],
    ):
        try:
            subprocess.check_call(
                cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            import qrcode  # noqa: F401,F811
            return True
        except (subprocess.CalledProcessError, ImportError, FileNotFoundError):
            continue
    return False


def render_qr_to_terminal(url: str) -> bool:
    """Render *url* as a compact half-block QR code in the terminal.

    Args:
        url: The URL to encode as a QR code.

    Returns:
        True if the QR code was printed, False if qrcode is unavailable.
    """
    try:
        import qrcode
    except ImportError:
        return False

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    matrix = qr.get_matrix()
    rows = len(matrix)
    lines: list[str] = []

    TOP_HALF = "▀"    # ▀
    BOTTOM_HALF = "▄" # ▄
    FULL_BLOCK = "█"  # █
    EMPTY = " "

    for r in range(0, rows, 2):
        line_chars: list[str] = []
        for c in range(len(matrix[r])):
            top = matrix[r][c]
            bottom = matrix[r + 1][c] if r + 1 < rows else False
            if top and bottom:
                line_chars.append(FULL_BLOCK)
            elif top:
                line_chars.append(TOP_HALF)
            elif bottom:
                line_chars.append(BOTTOM_HALF)
            else:
                line_chars.append(EMPTY)
        lines.append("    " + "".join(line_chars))

    print("\n".join(lines))
    return True


# ---------------------------------------------------------------------------
# High-level entry point
# ---------------------------------------------------------------------------

def feishu_qr_auth(
    client_id: str,
    scope: Optional[str] = None,
    client_secret: Optional[str] = None,
) -> Optional[Tuple[str, str]]:
    """Run the interactive QR-code Feishu device-flow authorization.

    Args:
        client_id: Feishu app ID (FEISHU_APP_ID env var value).
        scope: Override OAuth scopes. Defaults to FEISHU_DEFAULT_SCOPE.
        client_secret: Feishu app secret (required by Feishu's device_authorization
            endpoint even though RFC 8628 lists it as optional).

    Returns:
        (access_token, refresh_token) on success, or None on failure/cancel.
    """
    from hermes_cli.setup import print_info, print_success, print_warning, print_error

    print()
    print_info("  Initializing Feishu user authorization (OAuth device flow)...")

    try:
        auth_data = begin_device_authorization(client_id, scope, client_secret=client_secret)
    except FeishuAuthError as exc:
        print_error(f"  Authorization init failed: {exc}")
        return None

    url = auth_data["verification_uri_complete"]
    user_code = auth_data["user_code"]

    if not _ensure_qrcode_installed():
        print_warning("  qrcode library install failed, will show link only.")

    print()
    print_info("  Please scan the QR code below with Feishu to authorize:")
    if user_code:
        print_info(f"  User Code: {user_code}")
    print()

    if not render_qr_to_terminal(url):
        print_warning("  QR code render failed, please open the link below:")

    print()
    print_info(f"  Or open this link manually: {url}")
    print()
    print_info("  Waiting for authorization... (timeout: 30 minutes)")

    dot_count = 0

    def _on_waiting() -> None:
        nonlocal dot_count
        dot_count += 1
        if dot_count % 10 == 0:
            sys.stdout.write(".")
            sys.stdout.flush()

    try:
        access_token, refresh_token, open_id, tok_expires_in, tok_refresh_expires_in = (
            wait_for_authorization_success(
                device_code=auth_data["device_code"],
                client_id=client_id,
                interval=auth_data["interval"],
                expires_in=auth_data["expires_in"],
                on_waiting=_on_waiting,
                client_secret=client_secret,
            )
        )
    except FeishuAuthError as exc:
        print()
        print_error(f"  Authorization failed: {exc}")
        return None

    # Persist tokens using real expires_in values from the token response
    try:
        save_uat(
            access_token=access_token,
            refresh_token=refresh_token,
            open_id=open_id,
            expires_in=tok_expires_in,
            refresh_expires_in=tok_refresh_expires_in,
            scope=_scope_with_offline_access(scope),
            app_id=client_id,
        )
    except OSError as exc:
        print_warning(f"  Token save failed: {exc}")

    print()
    print_success("  Feishu user authorization successful!")
    print_success(f"  Open ID:      {open_id or '(not returned)'}")
    print_success(
        f"  Access Token: {access_token[:8]}{'*' * max(0, len(access_token) - 8)}"
    )
    print_success(f"  Tokens saved to: {display_hermes_home()}/feishu_uat.json")

    return access_token, refresh_token


# ---------------------------------------------------------------------------
# CLI entry point (called by hermes_cli/main.py cmd_feishu_auth_setup)
# ---------------------------------------------------------------------------

def cmd_feishu_auth_setup(args) -> None:
    """Handle ``hermes feishu-auth`` CLI command.

    Previously named cmd_feishu_uat_setup. The subcommand was renamed from
    feishu-uat to feishu-auth for consistency with dingtalk-auth naming.

    Args:
        args: Parsed argparse namespace.
    """
    from hermes_cli.config import get_env_value
    from hermes_cli.setup import print_info, print_success, print_warning, print_error

    client_id = get_env_value("FEISHU_APP_ID") or ""
    if not client_id:
        print_error(
            "  FEISHU_APP_ID is not set. Run 'hermes setup' first to configure"
            " the Feishu bot credentials before authorizing user identity."
        )
        return

    client_secret = get_env_value("FEISHU_APP_SECRET") or ""
    if not client_secret:
        print_error(
            "  FEISHU_APP_SECRET is not set. Feishu's device_authorization"
            " endpoint rejects requests without it (HTTP 400 invalid_request)."
        )
        return

    # Check for existing token
    existing = load_uat()
    if existing:
        now_ms = int(time.time() * 1000)
        expires_at = existing.get("expires_at", 0)
        refresh_expires_at = existing.get("refresh_expires_at", 0)
        open_id = existing.get("user_open_id", "(unknown)")

        if now_ms < expires_at:
            remaining_min = (expires_at - now_ms) // 60000
            print_success(
                f"  Feishu UAT already valid for user {open_id}"
                f" (~{remaining_min} min remaining)."
            )
        elif now_ms < refresh_expires_at:
            print_warning(
                f"  Access token expired for user {open_id},"
                " but refresh token is still valid."
            )
        else:
            print_warning(f"  All tokens expired for user {open_id}.")

        scope = getattr(args, "scope", None) or ""
        force = getattr(args, "force", False)
        if not force:
            try:
                from hermes_cli.setup import prompt_yes_no
                if not prompt_yes_no("  Re-authorize Feishu user identity?", False):
                    return
            except Exception:
                print_info("  Run with --force to re-authorize.")
                return
    else:
        scope = getattr(args, "scope", None) or ""

    scope = scope.strip() or None
    result = feishu_qr_auth(client_id=client_id, scope=scope, client_secret=client_secret)
    if result is None:
        import sys
        sys.exit(1)
