"""Feishu OAPI unified client — dual-identity (TAT + UAT) factory.

Provides ``FeishuClient`` with three factory methods:
  - ``for_tenant()``     — build a TAT (tenant_access_token) lark Client
  - ``for_user()``       — build a lark Client + RequestOption carrying UAT
  - ``from_credentials(app_id, app_secret)`` — ephemeral, uncached

Four semantic error classes surface auth failures to callers:
  - ``NeedAuthorizationError``      — no UAT on disk, need device flow
  - ``AppScopeMissingError``        — app missing API scope (errcode 99991672)
  - ``UserAuthRequiredError``       — user not authorized (errcode 99991679)
  - ``UserScopeInsufficientError``  — token valid but scope insufficient

Token management:
  - ``_load_uat()`` reads ~/.hermes/feishu_uat.json or per-user
    ~/.hermes/feishu_uat/<open_id>.json; if access_token expires within 60 s,
    it attempts a refresh_token exchange before raising NeedAuthorizationError.
  - TOOLS_METADATA is a registry for Phase 2 workers to declare per-tool
    scopes and preferred identity.  Starts empty; workers append entries.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FEISHU_UAT_PATH = get_hermes_home() / "feishu_uat.json"

# Per-user UAT directory: ~/.hermes/feishu_uat/<open_id>.json
# Multi-user (chat-mode device flow) deployments write one file per open_id.
FEISHU_UAT_DIR = get_hermes_home() / "feishu_uat"

# Per-task sender open_id propagation (US-004).
# The feishu adapter sets this ContextVar before invoking the LLM agent's tool
# handler for an inbound message; UAT factory methods read it when callers do
# not pass an explicit user_open_id, enabling multi-user routing without
# modifying every tool's signature. ContextVar is naturally task-isolated under
# asyncio so concurrent inbound messages do not bleed open_id into each other.
current_sender_open_id: "contextvars.ContextVar[Optional[str]]" = contextvars.ContextVar(
    "current_sender_open_id", default=None
)


@contextlib.contextmanager
def sender_open_id_scope(open_id: Optional[str]):
    """Set ``current_sender_open_id`` for the duration of the with-block.

    Resets the contextvar in finally so leakage across requests is impossible
    even if an exception escapes. ``open_id=None`` is a no-op (used when the
    inbound event has no resolvable sender, e.g. card actions on a synthetic
    event).
    """
    if open_id is None:
        yield
        return
    token = current_sender_open_id.set(open_id)
    try:
        yield
    finally:
        current_sender_open_id.reset(token)


def _per_user_uat_path_oapi(open_id: str) -> "Path":
    """Return per-user UAT path; reject anything that could escape the dir."""
    if not open_id or not isinstance(open_id, str):
        raise ValueError("open_id must be a non-empty string")
    if "/" in open_id or "\\" in open_id or ".." in open_id or "\0" in open_id:
        raise ValueError(f"open_id contains illegal characters: {open_id!r}")
    return FEISHU_UAT_DIR / f"{open_id}.json"


def _find_latest_valid_uat_path(skip: Optional["Path"] = None) -> Optional["Path"]:
    """Return the freshest UAT file in FEISHU_UAT_DIR whose access_token is
    not yet within the expiry headroom. Returns None when nothing usable
    exists. ``skip`` is excluded from the candidate set (avoid recursion when
    the caller's primary lookup just missed).
    """
    if not FEISHU_UAT_DIR.exists():
        return None
    now_ms = int(time.time() * 1000)
    headroom_ms = _ACCESS_TOKEN_EXPIRY_HEADROOM_S * 1000
    candidates: list[tuple[float, "Path"]] = []
    for entry in FEISHU_UAT_DIR.iterdir():
        if not entry.is_file() or entry.suffix != ".json" or entry.name.startswith("."):
            continue
        if skip is not None and entry == skip:
            continue
        try:
            with open(entry, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError):
            continue
        if not data.get("access_token"):
            continue
        if int(data.get("expires_at", 0)) <= now_ms + headroom_ms:
            continue
        candidates.append((entry.stat().st_mtime, entry))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def _try_refresh_uat(
    *,
    open_id: Optional[str],
    target_path: "Path",
    data: dict,
) -> Optional[dict]:
    """Refresh an expiring UAT file in-place and return the reloaded data."""
    if not data.get("refresh_token"):
        return None
    app_id, app_secret, _domain = _resolve_feishu_credentials()
    if not (app_id and app_secret):
        return None
    try:
        if open_id:
            from hermes_cli.feishu_auth import refresh_uat_for_user

            refresh_uat_for_user(open_id, app_id, app_secret)
        else:
            from hermes_cli.feishu_auth import refresh_uat

            refresh_uat(app_id, app_secret)
        logger.info("UAT auto-refreshed for user %s", data.get("user_open_id") or open_id or "unknown")
        with open(target_path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:
        logger.debug("Auto-refresh failed: %s", exc)
        return None

# Access token refresh headroom — treat token as expired this many seconds early
_ACCESS_TOKEN_EXPIRY_HEADROOM_S = 60

# Feishu error codes that map to semantic auth errors
_ERRCODE_APP_SCOPE_MISSING = 99991672
_ERRCODE_USER_SCOPE_INSUFFICIENT = 99991679
_ERRCODE_TOKEN_INVALID = 99991668
_ERRCODE_TOKEN_EXPIRED = 99991677

# Registry for Phase 2 tool families to declare per-tool identity preference.
# Key: tool name (e.g. "feishu_calendar_list_events")
# Value: dict with optional keys:
#   "identity": "user" | "tenant"  (default "user")
#   "scopes": list[str]
TOOLS_METADATA: dict[str, dict] = {
    "feishu_get_my_user_info": {
        "identity": "user",
        "scopes": ["authen:user.employee_id:read"],
    },
}


def _resolve_feishu_credentials() -> tuple[str, str, str]:
    """Resolve (app_id, app_secret, domain) with env→.env→config.yaml fallback.

    Mirrors gateway/platforms/feishu.py so UAT tools share a single credential
    source with the gateway adapter without requiring duplication in .env.
    """
    app_id = os.getenv("FEISHU_APP_ID", "").strip()
    app_secret = os.getenv("FEISHU_APP_SECRET", "").strip()
    domain = os.getenv("FEISHU_DOMAIN", "").strip().lower()
    if not (app_id and app_secret) or not domain:
        from hermes_cli.config import get_env_value
        app_id = app_id or (get_env_value("FEISHU_APP_ID") or "").strip()
        app_secret = app_secret or (get_env_value("FEISHU_APP_SECRET") or "").strip()
        domain = domain or (get_env_value("FEISHU_DOMAIN") or "").strip().lower()
    if not domain:
        domain = "feishu"
    return app_id, app_secret, domain


# ---------------------------------------------------------------------------
# Semantic error classes
# ---------------------------------------------------------------------------

class NeedAuthorizationError(Exception):
    """No valid UAT on disk — user must run 'hermes feishu-uat' device flow.

    Args:
        user_open_id: Open ID of the user who needs authorization, if known.
        reason: Human-readable explanation of why authorization is needed.
    """

    def __init__(self, user_open_id: str = "unknown", reason: str = "") -> None:
        msg = f"need_user_authorization: {user_open_id}"
        if reason:
            msg += f" ({reason})"
        super().__init__(msg)
        self.user_open_id = user_open_id
        self.reason = reason


class AppScopeMissingError(Exception):
    """App (bot) is missing an API scope — admin must enable it in Feishu console.

    Triggered by Feishu errcode 99991672.

    Args:
        app_id: The Feishu app ID.
        api_name: The API or tool name that triggered the error.
        missing_scopes: List of scope strings that are absent.
    """

    def __init__(
        self, app_id: str, api_name: str, missing_scopes: list[str]
    ) -> None:
        scopes_str = ", ".join(missing_scopes)
        super().__init__(
            f"App '{app_id}' missing scopes [{scopes_str}] for API '{api_name}'. "
            "Admin must enable in Feishu console."
        )
        self.app_id = app_id
        self.api_name = api_name
        self.missing_scopes = missing_scopes


class UserAuthRequiredError(Exception):
    """User has not authorized the app or required scopes are insufficient.

    Triggered by Feishu errcode 99991679.

    Args:
        user_open_id: Open ID of the user.
        api_name: The API or tool name that triggered the error.
        required_scopes: Scopes that are required.
        app_id: The Feishu app ID.
    """

    def __init__(
        self,
        user_open_id: str,
        api_name: str,
        required_scopes: list[str],
        app_id: str = "",
    ) -> None:
        scopes_str = ", ".join(required_scopes)
        super().__init__(
            f"User '{user_open_id}' missing scopes [{scopes_str}] for '{api_name}'"
        )
        self.user_open_id = user_open_id
        self.api_name = api_name
        self.required_scopes = required_scopes
        self.app_id = app_id


class UserScopeInsufficientError(Exception):
    """UAT is valid but lacks specific scopes — incremental authorization needed.

    Args:
        user_open_id: Open ID of the user.
        api_name: The API or tool name that triggered the error.
        missing_scopes: Scopes absent from the current token.
    """

    def __init__(
        self, user_open_id: str, api_name: str, missing_scopes: list[str]
    ) -> None:
        scopes_str = ", ".join(missing_scopes)
        super().__init__(
            f"User '{user_open_id}' insufficient scopes [{scopes_str}] "
            f"for '{api_name}'. Re-run 'hermes feishu-uat' to re-authorize."
        )
        self.user_open_id = user_open_id
        self.api_name = api_name
        self.missing_scopes = missing_scopes


# ---------------------------------------------------------------------------
# Feishu errcode → semantic error helper
# ---------------------------------------------------------------------------

def raise_for_feishu_errcode(
    code: int,
    msg: str = "",
    *,
    app_id: str = "",
    api_name: str = "",
    user_open_id: str = "unknown",
) -> None:
    """Raise a semantic error if *code* maps to a known auth failure.

    Args:
        code: Feishu API response code (0 = success).
        msg: Response message string for logging.
        app_id: Feishu app ID (for AppScopeMissingError).
        api_name: Name of the tool/API (for error context).
        user_open_id: User open ID (for user-level errors).

    Raises:
        AppScopeMissingError: errcode 99991672.
        UserAuthRequiredError: errcode 99991679.
        NeedAuthorizationError: errcode 99991668 or 99991677 (token invalid/expired).
    """
    if code == _ERRCODE_APP_SCOPE_MISSING:
        raise AppScopeMissingError(app_id, api_name, [msg or "unknown scope"])
    if code == _ERRCODE_USER_SCOPE_INSUFFICIENT:
        raise UserAuthRequiredError(user_open_id, api_name, [], app_id)
    if code in (_ERRCODE_TOKEN_INVALID, _ERRCODE_TOKEN_EXPIRED):
        raise NeedAuthorizationError(
            user_open_id,
            reason=f"token invalid or expired (errcode={code}); re-run 'hermes feishu-uat'",
        )


# ---------------------------------------------------------------------------
# UAT loader
# ---------------------------------------------------------------------------

def _load_uat(open_id: Optional[str] = None) -> dict:
    """Load UAT from disk and validate freshness.

    With ``open_id``, reads ~/.hermes/feishu_uat/<open_id>.json (per-user mode).
    Without it, falls back to the legacy single-file path ~/.hermes/feishu_uat.json
    so single-user deployments continue to work unchanged.

    Args:
        open_id: Optional Feishu user open_id for the per-user UAT file.

    Returns:
        Token dict with at least access_token, refresh_token, user_open_id.

    Raises:
        NeedAuthorizationError: File missing, unreadable, or access_token
            expires within _ACCESS_TOKEN_EXPIRY_HEADROOM_S seconds.
    """
    target_path = _per_user_uat_path_oapi(open_id) if open_id else FEISHU_UAT_PATH
    if not target_path.exists():
        # Cross-context fallback applies only to per-user lookups (open_id given).
        # Legacy single-file lookups (open_id is None) keep strict semantics so
        # callers asking "is there ANY UAT" get the original NeedAuthorization
        # error instead of being silently routed to a per-user file.
        fallback = (
            _find_latest_valid_uat_path(skip=target_path) if open_id else None
        )
        if fallback is not None:
            logger.info(
                "[feishu] _load_uat fallback: %s missing, using freshest UAT %s",
                target_path.name, fallback.name,
            )
            target_path = fallback
        else:
            raise NeedAuthorizationError(
                user_open_id=open_id or "unknown",
                reason=f"no token file at {target_path}; run 'hermes feishu-auth' or send /feishu_auth",
            )

    try:
        with open(target_path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (json.JSONDecodeError, OSError) as exc:
        raise NeedAuthorizationError(
            user_open_id=open_id or "unknown",
            reason=f"token file unreadable: {exc}",
        ) from exc

    access_token = data.get("access_token", "")
    if not access_token:
        raise NeedAuthorizationError(
            user_open_id=open_id or "unknown",
            reason="token file has no access_token; re-run 'hermes feishu-auth'",
        )

    expires_at_ms = data.get("expires_at", 0)
    now_ms = int(time.time() * 1000)
    headroom_ms = _ACCESS_TOKEN_EXPIRY_HEADROOM_S * 1000

    if now_ms >= expires_at_ms - headroom_ms:
        user_open_id = data.get("user_open_id", "unknown")
        refreshed = _try_refresh_uat(open_id=open_id, target_path=target_path, data=data)
        if refreshed is not None:
            logger.info(
                "[feishu] _load_uat for_user access_token sender=%s path=%s refreshed=True",
                refreshed.get("user_open_id") or refreshed.get("open_id") or open_id or "unknown",
                target_path.name,
            )
            return refreshed
        # Cross-context fallback (per-user lookups only — legacy single-file
        # callers keep strict expiry semantics).
        if open_id:
            fallback = _find_latest_valid_uat_path(skip=target_path)
            if fallback is not None:
                logger.info(
                    "[feishu] _load_uat fallback: %s expired, using freshest UAT %s",
                    target_path.name, fallback.name,
                )
                with open(fallback, encoding="utf-8") as fh:
                    fallback_data = json.load(fh)
                logger.info(
                    "[feishu] _load_uat for_user access_token sender=%s path=%s fallback=True",
                    fallback_data.get("user_open_id") or fallback_data.get("open_id") or open_id or "unknown",
                    fallback.name,
                )
                return fallback_data
        raise NeedAuthorizationError(
            user_open_id=user_open_id,
            reason="access_token expired or expiring soon; re-run 'hermes feishu-auth'",
        )

    logger.info(
        "[feishu] _load_uat for_user access_token sender=%s path=%s",
        data.get("user_open_id") or data.get("open_id") or open_id or "unknown",
        target_path.name,
    )
    return data


# ---------------------------------------------------------------------------
# FeishuClient
# ---------------------------------------------------------------------------

class FeishuClient:
    """Feishu SDK client wrapper with TAT / UAT dual-identity support.

    Do not instantiate directly — use the class-level factory methods:
      ``FeishuClient.for_tenant()``      — TAT (bot identity)
      ``FeishuClient.for_user()``        — UAT (user identity, loads from disk)
      ``FeishuClient.from_credentials(app_id, app_secret)`` — ephemeral

    After construction the ``sdk`` attribute holds the raw ``lark.Client``.
    For UAT calls, pass ``self.request_option`` as the second argument to
    SDK methods, or inject it into ``BaseRequest`` via RequestOption:
      ``RequestOption.builder().user_access_token(client.access_token).build()``
    """

    _cache: dict[str, "FeishuClient"] = {}

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        *,
        account_id: str = "default",
        domain: str = "feishu",
        access_token: str = "",
        user_open_id: str = "",
        ephemeral: bool = False,
    ) -> None:
        self.app_id = app_id
        self.app_secret = app_secret
        self.account_id = account_id
        self.domain = domain
        self.access_token = access_token
        self.user_open_id = user_open_id
        self.ephemeral = ephemeral
        self.sdk = self._build_sdk()

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def for_tenant(cls) -> "FeishuClient":
        """Create or reuse a TAT (tenant_access_token) lark Client.

        Reads FEISHU_APP_ID and FEISHU_APP_SECRET from env, ~/.hermes/.env, or
        platforms.feishu.extra in ~/.hermes/config.yaml (in that order).

        Returns:
            FeishuClient configured for tenant identity.

        Raises:
            ValueError: If FEISHU_APP_ID or FEISHU_APP_SECRET are unset.
        """
        app_id, app_secret, domain = _resolve_feishu_credentials()

        if not app_id or not app_secret:
            raise ValueError(
                "FEISHU_APP_ID and FEISHU_APP_SECRET must be set. "
                "Run 'hermes setup' to configure the Feishu bot."
            )

        cache_key = f"tenant:default:{app_id}"
        existing = cls._cache.get(cache_key)
        if existing and existing.app_secret == app_secret:
            return existing

        instance = cls(
            app_id=app_id,
            app_secret=app_secret,
            account_id="default",
            domain=domain,
        )
        cls._cache[cache_key] = instance
        return instance

    @classmethod
    def for_user(cls, user_open_id: Optional[str] = None) -> "FeishuClient":
        """Create a UAT (user_access_token) lark Client from disk storage.

        With ``user_open_id``, loads ~/.hermes/feishu_uat/<user_open_id>.json
        (per-user / multi-user mode). Without it, loads the legacy single-file
        path ~/.hermes/feishu_uat.json (single-user / CLI mode).

        The ``access_token`` attribute holds the raw UAT string; pass it to
        ``RequestOption.builder().user_access_token(...)`` for SDK calls that
        support USER token type.

        Args:
            user_open_id: Optional Feishu user open_id used to select the
                per-user UAT file in chat-mode (multi-user) deployments.

        Returns:
            FeishuClient with access_token set.

        Raises:
            NeedAuthorizationError: Token missing, expired, or expiring soon.
            ValueError: If FEISHU_APP_ID / FEISHU_APP_SECRET unset.
        """
        app_id, app_secret, domain = _resolve_feishu_credentials()

        if not app_id or not app_secret:
            raise ValueError(
                "FEISHU_APP_ID and FEISHU_APP_SECRET must be set. "
                "Run 'hermes setup' to configure the Feishu bot."
            )

        # US-004: when no explicit open_id is passed, fall back to the
        # contextvar set by the feishu adapter for the current message. If
        # the contextvar is also unset, _load_uat receives None and reads
        # the legacy single-file path (single-user / CLI mode).
        if user_open_id is None:
            user_open_id = current_sender_open_id.get()

        uat_data = _load_uat(open_id=user_open_id)
        access_token = uat_data["access_token"]
        loaded_open_id = uat_data.get("user_open_id", "")

        return cls(
            app_id=app_id,
            app_secret=app_secret,
            domain=domain,
            access_token=access_token,
            user_open_id=loaded_open_id,
            ephemeral=True,
        )

    @classmethod
    def from_credentials(
        cls,
        app_id: str,
        app_secret: str,
        *,
        domain: str = "feishu",
        account_id: str = "ephemeral",
    ) -> "FeishuClient":
        """Create an ephemeral client from explicit credentials (not cached).

        Args:
            app_id: Feishu app ID.
            app_secret: Feishu app secret.
            domain: "feishu" or "lark".
            account_id: Logical account label (for logging only).

        Returns:
            FeishuClient not registered in the instance cache.
        """
        return cls(
            app_id=app_id,
            app_secret=app_secret,
            account_id=account_id,
            domain=domain,
            ephemeral=True,
        )

    # ------------------------------------------------------------------
    # SDK builder
    # ------------------------------------------------------------------

    def _build_sdk(self) -> Any:
        """Build and return the underlying lark.Client instance.

        Returns:
            lark.Client, or None if lark_oapi is not installed.
        """
        try:
            import lark_oapi as lark
            from lark_oapi.core.const import FEISHU_DOMAIN, LARK_DOMAIN
        except ImportError:
            logger.warning("lark_oapi not installed — FeishuClient SDK unavailable")
            return None

        sdk_domain = LARK_DOMAIN if self.domain == "lark" else FEISHU_DOMAIN
        return (
            lark.Client.builder()
            .app_id(self.app_id)
            .app_secret(self.app_secret)
            .domain(sdk_domain)
            .log_level(lark.LogLevel.WARNING)
            .build()
        )

    # ------------------------------------------------------------------
    # RequestOption helper for UAT calls
    # ------------------------------------------------------------------

    def build_user_request_option(self) -> Any:
        """Build a RequestOption injecting this client's UAT.

        Use this as the second argument to SDK service methods that accept
        a RequestOption, e.g.:
          ``client.calendar.v4.event.list(request, client.build_user_request_option())``

        Returns:
            lark_oapi.RequestOption, or None if lark_oapi is unavailable or
            no access_token is set.
        """
        if not self.access_token:
            return None
        try:
            from lark_oapi import RequestOption
            return (
                RequestOption.builder()
                .user_access_token(self.access_token)
                .build()
            )
        except ImportError:
            return None

    # ------------------------------------------------------------------
    # BaseRequest helper for raw HTTP UAT calls
    # ------------------------------------------------------------------

    def do_request(
        self,
        method: str,
        uri: str,
        *,
        paths: Optional[dict] = None,
        queries: Optional[list] = None,
        body: Optional[dict] = None,
        use_uat: bool = False,
    ) -> tuple[int, str, dict]:
        """Execute a BaseRequest and return (code, msg, data_dict).

        Args:
            method: HTTP method string "GET", "POST", "PUT", "DELETE", or "PATCH".
            uri: Feishu open-api URI, e.g. "/open-apis/calendar/v4/events".
            paths: Path parameter substitutions dict.
            queries: List of (key, value) query parameter tuples.
            body: JSON body dict for methods that accept request bodies.
            use_uat: If True, inject UAT via RequestOption instead of TAT.

        Returns:
            Tuple of (code, msg, data_dict) where code=0 means success.

        Raises:
            RuntimeError: If lark_oapi is not installed.
        """
        try:
            from lark_oapi import AccessTokenType, RequestOption
            from lark_oapi.core.enum import HttpMethod
            from lark_oapi.core.model.base_request import BaseRequest
        except ImportError as exc:
            raise RuntimeError("lark_oapi not installed") from exc

        if use_uat and not self.access_token:
            raise NeedAuthorizationError(
                user_open_id=self.user_open_id or "unknown",
                reason="do_request called with use_uat=True but no access_token loaded; "
                       "call FeishuClient.for_user() or run 'hermes feishu-auth'",
            )

        method_map = {
            "GET": HttpMethod.GET,
            "POST": HttpMethod.POST,
            "PUT": HttpMethod.PUT,
            "DELETE": HttpMethod.DELETE,
            "PATCH": HttpMethod.PATCH,
        }
        http_method = method_map.get(method.upper())
        if http_method is None:
            raise ValueError(f"Unsupported Feishu HTTP method: {method}")

        builder = (
            BaseRequest.builder()
            .http_method(http_method)
            .uri(uri)
        )

        if use_uat:
            builder = builder.token_types({AccessTokenType.USER})
        else:
            builder = builder.token_types({AccessTokenType.TENANT})

        if paths:
            builder = builder.paths(paths)
        if queries:
            builder = builder.queries(queries)
        if body is not None:
            builder = builder.body(body)

        request = builder.build()

        if use_uat:
            opt = (
                RequestOption.builder()
                .user_access_token(self.access_token)
                .build()
            )
            response = self.sdk.request(request, opt)
        else:
            response = self.sdk.request(request)

        code = getattr(response, "code", None)
        msg = getattr(response, "msg", "")

        data: dict = {}
        raw = getattr(response, "raw", None)
        if raw and hasattr(raw, "content"):
            try:
                body_json = json.loads(raw.content)
                data = body_json.get("data", {})
                if code is None:
                    code = body_json.get("code", -1)
                if not msg:
                    msg = body_json.get("msg", "")
            except (json.JSONDecodeError, AttributeError):
                pass
        if not data:
            resp_data = getattr(response, "data", None)
            if isinstance(resp_data, dict):
                data = resp_data
            elif resp_data and hasattr(resp_data, "__dict__"):
                data = vars(resp_data)

        return (code if code is not None else -1), msg, data

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def dispose(self) -> None:
        """Remove this client from the instance cache."""
        cache_key = f"tenant:{self.account_id}:{self.app_id}"
        self._cache.pop(cache_key, None)

    def __repr__(self) -> str:
        mode = "UAT" if self.access_token else "TAT"
        return (
            f"<FeishuClient app_id={self.app_id!r} "
            f"domain={self.domain!r} mode={mode}>"
        )
