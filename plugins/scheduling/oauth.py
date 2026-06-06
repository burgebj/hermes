"""Shared OAuth2 helpers for the scheduling plugin.

The module is both importable by the scheduling clients and executable as a
small CLI:

    python -m plugins.scheduling.oauth --provider calendly --auth-url
    python -m plugins.scheduling.oauth --provider calendly --auth-code CODE
    python -m plugins.scheduling.oauth --provider calcom --check

Google Calendar intentionally reuses the existing Hermes Google OAuth token at
``${HERMES_HOME}/google_token.json`` instead of creating a second flow.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

from hermes_constants import get_hermes_home

PROVIDERS = {"calcom", "calendly", "google_calendar"}
DEFAULT_REDIRECT_URI = "http://localhost:1"


class OAuthError(RuntimeError):
    """Raised for OAuth setup, token, and refresh failures."""


def _strip_none(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return a copy without ``None`` values."""
    return {k: v for k, v in (data or {}).items() if v is not None}


def _now() -> int:
    return int(time.time())


def _client_secret_config(provider: str) -> Dict[str, str]:
    """Resolve OAuth endpoint and client configuration for a provider."""
    if provider == "calendly":
        return {
            "client_id": os.getenv("CALENDLY_CLIENT_ID", ""),
            "client_secret": os.getenv("CALENDLY_CLIENT_SECRET", ""),
            "authorize_url": os.getenv("CALENDLY_AUTHORIZE_URL", "https://auth.calendly.com/oauth/authorize"),
            "token_url": os.getenv("CALENDLY_TOKEN_URL", "https://auth.calendly.com/oauth/token"),
            "redirect_uri": os.getenv("CALENDLY_REDIRECT_URI", DEFAULT_REDIRECT_URI),
            "scope": os.getenv("CALENDLY_SCOPE", ""),
            "pkce": "true",
        }
    if provider == "calcom":
        return {
            "client_id": os.getenv("CALCOM_CLIENT_ID", ""),
            "client_secret": os.getenv("CALCOM_CLIENT_SECRET", ""),
            "authorize_url": os.getenv("CALCOM_AUTHORIZE_URL", "https://app.cal.com/oauth/authorize"),
            "token_url": os.getenv("CALCOM_TOKEN_URL", "https://api.cal.com/v1/oauth/token"),
            "redirect_uri": os.getenv("CALCOM_REDIRECT_URI", DEFAULT_REDIRECT_URI),
            "scope": os.getenv("CALCOM_SCOPE", ""),
            "pkce": os.getenv("CALCOM_OAUTH_PKCE", "false").lower(),
        }
    raise OAuthError(f"Unsupported OAuth provider: {provider}")


def _google_token_path() -> Path:
    return get_hermes_home() / "google_token.json"


def _google_client_secret_path() -> Path:
    return get_hermes_home() / "google_client_secret.json"


def _token_dir() -> Path:
    return get_hermes_home() / "scheduling_tokens"


def _pending_path(provider: str) -> Path:
    return _token_dir() / f"{provider}_pending.json"


def _extract_code_and_state(code_or_url: str) -> Tuple[str, Optional[str]]:
    """Accept either a raw authorization code or a redirect URL."""
    if not code_or_url.startswith("http"):
        return code_or_url, None
    parsed = urlparse(code_or_url)
    params = parse_qs(parsed.query)
    code = (params.get("code") or [""])[0]
    if not code:
        raise OAuthError("No 'code' parameter found in callback URL.")
    return code, (params.get("state") or [None])[0]


def _pkce_verifier() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


class OAuth2Manager:
    """Manage OAuth2 tokens for Cal.com, Calendly, and Google Calendar."""

    def __init__(self, provider: str) -> None:
        if provider not in PROVIDERS:
            raise OAuthError(f"provider must be one of: {', '.join(sorted(PROVIDERS))}")
        self.provider = provider

    @property
    def token_path(self) -> Path:
        """Return the token path for this provider."""
        if self.provider == "google_calendar":
            return _google_token_path()
        return _token_dir() / f"{self.provider}.json"

    def check(self) -> Dict[str, Any]:
        """Return auth status without raising for missing credentials."""
        if self.provider == "google_calendar":
            exists = self.token_path.exists()
            return {
                "success": True,
                "provider": self.provider,
                "authenticated": exists,
                "token_path": str(self.token_path),
                "message": "Using existing Google OAuth token." if exists else "No google_token.json found.",
            }
        if self.provider == "calcom" and os.getenv("CALCOM_API_KEY"):
            return {
                "success": True,
                "provider": self.provider,
                "authenticated": True,
                "auth_type": "api_key",
                "token_path": str(self.token_path),
            }
        token = self.load_token(refresh_if_expiring=True, raise_on_missing=False)
        return {
            "success": True,
            "provider": self.provider,
            "authenticated": bool(token),
            "auth_type": "oauth" if token else None,
            "token_path": str(self.token_path),
        }

    def authorization_url(self) -> Dict[str, Any]:
        """Create and persist an OAuth state, returning the authorization URL."""
        if self.provider == "google_calendar":
            return {
                "success": False,
                "provider": self.provider,
                "error": "Google Calendar reuses ~/.hermes/google_token.json; no scheduling OAuth flow is created.",
            }

        config = _client_secret_config(self.provider)
        if not config["client_id"]:
            raise OAuthError(f"{self.provider} OAuth requires a client id environment variable.")

        state = secrets.token_urlsafe(24)
        code_verifier = _pkce_verifier() if config["pkce"] in {"1", "true", "yes", "on"} else None
        params: Dict[str, Any] = {
            "response_type": "code",
            "client_id": config["client_id"],
            "redirect_uri": config["redirect_uri"],
            "state": state,
        }
        if config["scope"]:
            params["scope"] = config["scope"]
        if code_verifier:
            params["code_challenge"] = _pkce_challenge(code_verifier)
            params["code_challenge_method"] = "S256"

        _token_dir().mkdir(parents=True, exist_ok=True)
        _pending_path(self.provider).write_text(json.dumps({
            "state": state,
            "redirect_uri": config["redirect_uri"],
            "code_verifier": code_verifier,
            "created_at": _now(),
        }, indent=2))
        return {
            "success": True,
            "provider": self.provider,
            "auth_url": f"{config['authorize_url']}?{urlencode(params)}",
            "redirect_uri": config["redirect_uri"],
            "pkce": bool(code_verifier),
        }

    def exchange_code(self, code_or_url: str) -> Dict[str, Any]:
        """Exchange an authorization code for tokens and store them."""
        if self.provider == "google_calendar":
            return {
                "success": False,
                "provider": self.provider,
                "error": "Google Calendar reuses ~/.hermes/google_token.json; use the existing Google OAuth setup.",
            }

        pending_file = _pending_path(self.provider)
        if not pending_file.exists():
            raise OAuthError("No pending OAuth session found. Run auth_url first.")
        pending = json.loads(pending_file.read_text())
        code, returned_state = _extract_code_and_state(code_or_url)
        if returned_state and returned_state != pending.get("state"):
            raise OAuthError("OAuth state mismatch. Run auth_url again.")

        config = _client_secret_config(self.provider)
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": pending.get("redirect_uri") or config["redirect_uri"],
            "client_id": config["client_id"],
            "client_secret": config["client_secret"] or None,
            "code_verifier": pending.get("code_verifier"),
        }
        token = self._token_request(config["token_url"], payload)
        self.save_token(token)
        pending_file.unlink(missing_ok=True)
        return {
            "success": True,
            "provider": self.provider,
            "token_path": str(self.token_path),
            "expires_at": token.get("expires_at"),
            "has_refresh_token": bool(token.get("refresh_token")),
        }

    def revoke(self) -> Dict[str, Any]:
        """Delete locally stored scheduling OAuth tokens."""
        if self.provider == "google_calendar":
            return {
                "success": False,
                "provider": self.provider,
                "error": "Refusing to delete shared google_token.json from the scheduling plugin.",
            }
        existed = self.token_path.exists()
        self.token_path.unlink(missing_ok=True)
        _pending_path(self.provider).unlink(missing_ok=True)
        return {"success": True, "provider": self.provider, "revoked": existed}

    def load_token(self, *, refresh_if_expiring: bool = True, raise_on_missing: bool = True) -> Optional[Dict[str, Any]]:
        """Load a token and refresh it if it is expired or nearly expired."""
        if not self.token_path.exists():
            if raise_on_missing:
                raise OAuthError(f"No token found for {self.provider} at {self.token_path}")
            return None
        try:
            token = json.loads(self.token_path.read_text())
        except Exception as exc:
            raise OAuthError(f"Could not read token for {self.provider}: {exc}") from exc

        if refresh_if_expiring and self._expires_soon(token):
            token = self.refresh_token(token)
        return token

    def save_token(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Persist a normalized token payload."""
        normalized = dict(token)
        if normalized.get("expires_in") and not normalized.get("expires_at"):
            normalized["expires_at"] = _now() + int(normalized["expires_in"])
        _token_dir().mkdir(parents=True, exist_ok=True)
        self.token_path.write_text(json.dumps(normalized, indent=2))
        return normalized

    def refresh_token(self, token: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Refresh and persist an OAuth token."""
        token = token or self.load_token(refresh_if_expiring=False)
        if self.provider == "google_calendar":
            refreshed = self._refresh_google_token(token or {})
        else:
            config = _client_secret_config(self.provider)
            refresh_token = (token or {}).get("refresh_token")
            if not refresh_token:
                raise OAuthError(f"No refresh token stored for {self.provider}. Re-authenticate.")
            refreshed = self._token_request(config["token_url"], {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": config["client_id"],
                "client_secret": config["client_secret"] or None,
            })
            if not refreshed.get("refresh_token"):
                refreshed["refresh_token"] = refresh_token
        return self.save_token({**(token or {}), **refreshed})

    def access_token(self) -> str:
        """Return a current access token or raise ``OAuthError``."""
        token = self.load_token(refresh_if_expiring=True)
        access_token = (token or {}).get("access_token") or (token or {}).get("token")
        if not access_token:
            raise OAuthError(f"No access token stored for {self.provider}.")
        return str(access_token)

    def _expires_soon(self, token: Dict[str, Any]) -> bool:
        expires_at = token.get("expires_at") or token.get("expiry")
        if isinstance(expires_at, str):
            try:
                from datetime import datetime
                expires_at = int(datetime.fromisoformat(expires_at.replace("Z", "+00:00")).timestamp())
            except Exception:
                return False
        if not expires_at:
            return False
        return int(expires_at) <= _now() + 120

    def _token_request(self, token_url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = httpx.post(
            token_url,
            data=_strip_none(payload),
            headers={"Accept": "application/json"},
            timeout=30.0,
        )
        if response.status_code >= 400:
            raise OAuthError(f"Token request failed ({response.status_code}): {response.text}")
        data = response.json()
        if data.get("expires_in") and not data.get("expires_at"):
            data["expires_at"] = _now() + int(data["expires_in"])
        return data

    def _refresh_google_token(self, token: Dict[str, Any]) -> Dict[str, Any]:
        refresh_token = token.get("refresh_token")
        if not refresh_token:
            raise OAuthError("google_token.json does not contain a refresh_token.")
        if not _google_client_secret_path().exists():
            raise OAuthError(f"No Google client secret found at {_google_client_secret_path()}")
        secret = json.loads(_google_client_secret_path().read_text())
        client = secret.get("installed") or secret.get("web") or secret
        client_id = client.get("client_id")
        client_secret = client.get("client_secret")
        token_uri = client.get("token_uri") or "https://oauth2.googleapis.com/token"
        if not client_id or not client_secret:
            raise OAuthError("google_client_secret.json is missing client_id/client_secret.")
        return self._token_request(token_uri, {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        })


def run_cli(argv: Optional[list[str]] = None) -> Dict[str, Any]:
    """Run the OAuth CLI and return a structured result."""
    parser = argparse.ArgumentParser(description="Scheduling OAuth setup helper")
    parser.add_argument("--provider", choices=sorted(PROVIDERS), required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--auth-url", action="store_true")
    group.add_argument("--auth-code")
    group.add_argument("--revoke", action="store_true")
    args = parser.parse_args(argv)

    manager = OAuth2Manager(args.provider)
    if args.check:
        return manager.check()
    if args.auth_url:
        return manager.authorization_url()
    if args.auth_code:
        return manager.exchange_code(args.auth_code)
    if args.revoke:
        return manager.revoke()
    raise OAuthError("No OAuth action selected.")


def main() -> None:
    """CLI entrypoint that prints a JSON result."""
    try:
        result = run_cli()
    except Exception as exc:
        result = {"success": False, "error": str(exc)}
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
