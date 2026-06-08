"""Shared helpers for direct xAI HTTP integrations."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Dict


@contextmanager
def _active_profile_home_scope():
    """Scope ``get_hermes_home()`` to the active profile when the process env
    points at the *root* Hermes home.

    xAI credential probes resolve the auth store from
    ``get_hermes_home() / "auth.json"``. When a named profile is active but
    ``HERMES_HOME`` resolves to the root — e.g. the multi-profile dashboard
    process, or a lazy tool-gate re-check after the per-invocation profile env
    mutation is no longer in effect — the named profile's xAI credential (under
    ``<root>/profiles/<name>/auth.json``) is missed and the xAI tools get gated
    out. This recovers the active profile from the sticky ``active_profile``
    file and scopes the home to it via the existing ``set_hermes_home_override``
    ContextVar, so the auth layer's profile->global fallback resolves the right
    store. No-op when already inside a profile, when no / ``default`` profile is
    active, or on any error.
    """
    token = None
    reset = None
    try:
        from hermes_constants import (
            get_default_hermes_root,
            get_hermes_home,
            reset_hermes_home_override,
            set_hermes_home_override,
        )

        if get_hermes_home().resolve() == get_default_hermes_root().resolve():
            from hermes_cli.profiles import get_active_profile, get_profile_dir

            active = (get_active_profile() or "").strip()
            if active and active != "default":
                profile_dir = get_profile_dir(active)
                if profile_dir.is_dir():
                    token = set_hermes_home_override(str(profile_dir))
                    reset = reset_hermes_home_override
    except Exception:
        token = None
        reset = None
    try:
        yield
    finally:
        if token is not None and reset is not None:
            try:
                reset(token)
            except Exception:
                pass


def has_xai_credentials() -> bool:
    """Cheap probe — return True when xAI credentials are *likely* usable.

    Deliberately avoids :func:`resolve_xai_http_credentials` so callers in
    hot-paint paths (``hermes tools`` repaint, tool-registration scans,
    ``WebSearchProvider.is_available()``) don't incur disk locks or — in
    the OAuth path — a network token refresh. The ABC contract on
    :meth:`agent.web_search_provider.WebSearchProvider.is_available`
    explicitly forbids network calls for exactly this reason.

    Resolution order, fast-to-slow:

    1. ``XAI_API_KEY`` env var (cheapest; covers explicit-key users).
    2. The active profile's ``auth.json`` has a non-empty xAI access token —
       either ``providers.xai-oauth.tokens.access_token`` or a
       ``credential_pool["xai-oauth"]`` entry (single file read, no expiry
       check, no refresh). Profile scoping handled by
       :func:`_active_profile_home_scope`.

    Returns False on any exception so a corrupted auth store can't block
    other availability scans. Truthful refresh + expiry handling happens
    in ``search()`` (or whichever caller actually makes the request).
    """
    if os.environ.get("XAI_API_KEY", "").strip():
        return True
    try:
        from hermes_constants import get_hermes_home

        with _active_profile_home_scope():
            auth_path = get_hermes_home() / "auth.json"
            if not auth_path.exists():
                return False
            store = json.loads(auth_path.read_text())
        providers = store.get("providers") if isinstance(store, dict) else None
        xai_state = providers.get("xai-oauth") if isinstance(providers, dict) else None
        tokens = xai_state.get("tokens") if isinstance(xai_state, dict) else None
        access_token = tokens.get("access_token") if isinstance(tokens, dict) else None
        if str(access_token or "").strip():
            return True
        # Also honor a credential-pool entry (e.g. `hermes auth add`, source
        # "manual") that has no providers.xai-oauth.tokens singleton.
        pool = store.get("credential_pool") if isinstance(store, dict) else None
        xai_pool = pool.get("xai-oauth") if isinstance(pool, dict) else None
        if isinstance(xai_pool, list):
            for entry in xai_pool:
                if isinstance(entry, dict) and str(
                    entry.get("access_token") or entry.get("runtime_api_key") or ""
                ).strip():
                    return True
        return False
    except Exception:
        return False


def get_env_value(name: str, default=None):
    """Read ``name`` from ``~/.hermes/.env`` first, then ``os.environ``.

    Wraps :func:`hermes_cli.config.get_env_value` so tests can patch
    ``tools.xai_http.get_env_value`` to inject dotenv-only secrets into the
    xAI credential resolver.
    """
    try:
        from hermes_cli.config import get_env_value as _hermes_get_env_value

        value = _hermes_get_env_value(name)
        if value is not None:
            return value
    except Exception:
        pass
    return os.environ.get(name, default)


def hermes_xai_user_agent() -> str:
    """Return a stable Hermes-specific User-Agent for xAI HTTP calls."""
    try:
        from hermes_cli import __version__
    except Exception:
        __version__ = "unknown"
    return f"Hermes-Agent/{__version__}"


def resolve_xai_http_credentials(*, force_refresh: bool = False) -> Dict[str, str]:
    """Resolve xAI HTTP bearer credentials, scoped to the active Hermes profile.

    Thin wrapper that applies :func:`_active_profile_home_scope` so a named
    profile's credential is found even when ``HERMES_HOME`` resolves to the
    root (multi-profile dashboard, lazy tool-gate re-checks, sudo re-entry).
    """
    with _active_profile_home_scope():
        return _resolve_xai_http_credentials(force_refresh=force_refresh)


def _resolve_xai_http_credentials(*, force_refresh: bool = False) -> Dict[str, str]:
    """Resolve bearer credentials for direct xAI HTTP endpoints.

    Prefers Hermes-managed xAI OAuth credentials when available, then falls back
    to ``XAI_API_KEY`` resolved via ``hermes_cli.config.get_env_value`` so keys
    stored in ``~/.hermes/.env`` (the standard Hermes location) are honored —
    not just ones already exported into ``os.environ``. This keeps direct xAI
    endpoints (images, TTS, STT, etc.) aligned with the main runtime auth model
    and preserves the regression contract from PR #17140 / #17163.

    Set ``force_refresh=True`` to bypass the resolver's JWT-exp shortcut and
    perform an unconditional OAuth refresh. Callers should use this only as a
    reactive remediation after a server 401 (mid-window revocation, opaque
    tokens where the proactive JWT check is a no-op, etc.), not as a default —
    the auth-store lock is held for the duration of the refresh.
    """
    if not force_refresh:
        try:
            from hermes_cli.runtime_provider import resolve_runtime_provider

            runtime = resolve_runtime_provider(requested="xai-oauth")
            access_token = str(runtime.get("api_key") or "").strip()
            base_url = str(runtime.get("base_url") or "").strip().rstrip("/")
            if access_token:
                return {
                    "provider": "xai-oauth",
                    "api_key": access_token,
                    "base_url": base_url or "https://api.x.ai/v1",
                }
        except Exception:
            pass

    try:
        from hermes_cli.auth import resolve_xai_oauth_runtime_credentials

        creds = resolve_xai_oauth_runtime_credentials(force_refresh=force_refresh)
        access_token = str(creds.get("api_key") or "").strip()
        base_url = str(creds.get("base_url") or "").strip().rstrip("/")
        if access_token:
            return {
                "provider": "xai-oauth",
                "api_key": access_token,
                "base_url": base_url or "https://api.x.ai/v1",
            }
    except Exception:
        pass

    api_key = str(get_env_value("XAI_API_KEY") or "").strip()
    base_url = str(get_env_value("XAI_BASE_URL") or "https://api.x.ai/v1").strip().rstrip("/")
    return {
        "provider": "xai",
        "api_key": api_key,
        "base_url": base_url,
    }
