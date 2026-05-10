"""Google Workspace OAuth — PKCE flow for Gmail, Calendar, Drive, Sheets, Docs, Contacts.

This module provides a simple PKCE OAuth flow that lets users connect their
Google account to Hermes Agent without creating their own Google Cloud project.
A Nous Research-owned public Desktop OAuth client ships with Hermes; users
just need to authorize and they're done.

Users who prefer their own OAuth app can override via environment variables
or by providing a client_secret.json file.

Storage: ~/.hermes/google_token.json (same as existing google-workspace skill)

Client ID resolution order:
  1. HERMES_GOOGLE_WORKSPACE_CLIENT_ID / _CLIENT_SECRET env vars
  2. ~/.hermes/google_client_secret.json (user-provided, backward compat)
  3. Shipped Nous Research defaults (public desktop OAuth client)
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import http.server
import json
import logging
import os
import secrets
import stat
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from hermes_constants import get_hermes_home
from utils import atomic_replace

logger = logging.getLogger(__name__)


# =============================================================================
# OAuth client credential constants
# =============================================================================

ENV_CLIENT_ID = "HERMES_GOOGLE_WORKSPACE_CLIENT_ID"
ENV_CLIENT_SECRET = "HERMES_GOOGLE_WORKSPACE_CLIENT_SECRET"

# Placeholder — will be replaced with Nous Research verified app credentials.
# Until then, users must provide their own client_secret.json or env vars.
_NOUS_CLIENT_ID = "PLACEHOLDER.apps.googleusercontent.com"
_NOUS_CLIENT_SECRET = "GOCSPX-PLACEHOLDER"


# =============================================================================
# Scopes
# =============================================================================

SCOPES: List[str] = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
]


# =============================================================================
# Endpoints & constants
# =============================================================================

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v1/userinfo"

DEFAULT_REDIRECT_PORT = 8098
REDIRECT_HOST = "127.0.0.1"
CALLBACK_PATH = "/oauth2callback"

CALLBACK_WAIT_SECONDS = 300
TOKEN_REQUEST_TIMEOUT_SECONDS = 20.0
REFRESH_SKEW_SECONDS = 60
LOCK_TIMEOUT_SECONDS = 30.0


# =============================================================================
# Error type
# =============================================================================

class GoogleWorkspaceOAuthError(RuntimeError):
    """Raised for any failure in the Google Workspace OAuth flow."""

    def __init__(self, message: str, *, code: str = "google_workspace_oauth_error") -> None:
        super().__init__(message)
        self.code = code


# =============================================================================
# File paths
# =============================================================================

def credentials_path() -> Path:
    """Return the path to the Google Workspace token file (~/.hermes/google_token.json)."""
    return get_hermes_home() / "google_token.json"


def _client_secret_path() -> Path:
    """Return the path to a user-provided client_secret.json file."""
    return get_hermes_home() / "google_client_secret.json"


def _lock_path() -> Path:
    """Return the path to the lock file for cross-process synchronization."""
    return credentials_path().with_suffix(".json.lock")


# =============================================================================
# Cross-process file locking
# =============================================================================

_lock_state = threading.local()


@contextlib.contextmanager
def _credentials_lock(timeout_seconds: float = LOCK_TIMEOUT_SECONDS):
    """Cross-process lock around the credentials file (fcntl POSIX / msvcrt Windows)."""
    depth = getattr(_lock_state, "depth", 0)
    if depth > 0:
        _lock_state.depth = depth + 1
        try:
            yield
        finally:
            _lock_state.depth -= 1
        return

    lock_file_path = _lock_path()
    lock_file_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_file_path), os.O_CREAT | os.O_RDWR, 0o600)
    acquired = False
    try:
        try:
            import fcntl
        except ImportError:
            fcntl = None  # type: ignore[assignment]

        if fcntl is not None:
            deadline = time.monotonic() + max(0.0, float(timeout_seconds))
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    acquired = True
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError(
                            f"Timed out acquiring Google Workspace OAuth lock at {lock_file_path}."
                        )
                    time.sleep(0.05)
        else:
            try:
                import msvcrt  # type: ignore[import-not-found]

                deadline = time.monotonic() + max(0.0, float(timeout_seconds))
                while True:
                    try:
                        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                        acquired = True
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(
                                f"Timed out acquiring Google Workspace OAuth lock at {lock_file_path}."
                            )
                        time.sleep(0.05)
            except ImportError:
                # No locking mechanism available — proceed anyway
                acquired = True

        _lock_state.depth = 1
        yield
    finally:
        try:
            if acquired:
                try:
                    import fcntl

                    fcntl.flock(fd, fcntl.LOCK_UN)
                except ImportError:
                    try:
                        import msvcrt  # type: ignore[import-not-found]

                        try:
                            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                        except OSError:
                            pass
                    except ImportError:
                        pass
        finally:
            os.close(fd)
            _lock_state.depth = 0


# =============================================================================
# Client ID resolution
# =============================================================================

def get_client_credentials() -> Tuple[str, str]:
    """Resolve the OAuth client_id and client_secret.

    Resolution order:
      1. HERMES_GOOGLE_WORKSPACE_CLIENT_ID / _CLIENT_SECRET env vars
      2. ~/.hermes/google_client_secret.json (user-provided, backward compat)
      3. Shipped Nous Research defaults (public desktop OAuth client)

    Returns:
        Tuple of (client_id, client_secret).

    Raises:
        GoogleWorkspaceOAuthError: If no valid client credentials can be resolved.
    """
    # 1. Environment variables
    env_id = (os.getenv(ENV_CLIENT_ID) or "").strip()
    env_secret = (os.getenv(ENV_CLIENT_SECRET) or "").strip()
    if env_id:
        return env_id, env_secret

    # 2. User-provided client_secret.json
    secret_path = _client_secret_path()
    if secret_path.exists():
        try:
            data = json.loads(secret_path.read_text(encoding="utf-8"))
            # Support both "installed" and "web" client types
            client_info = data.get("installed") or data.get("web")
            if client_info:
                cid = client_info.get("client_id", "")
                csecret = client_info.get("client_secret", "")
                if cid:
                    logger.info("Using client credentials from %s", secret_path)
                    return cid, csecret
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning(
                "Failed to read client_secret.json at %s: %s", secret_path, exc
            )

    # 3. Shipped Nous Research defaults
    if _NOUS_CLIENT_ID and _NOUS_CLIENT_ID != "PLACEHOLDER.apps.googleusercontent.com":
        return _NOUS_CLIENT_ID, _NOUS_CLIENT_SECRET

    # Placeholder credentials are not usable — raise so callers get a clear error
    if _NOUS_CLIENT_ID.startswith("PLACEHOLDER"):
        raise GoogleWorkspaceOAuthError(
            "No usable Google OAuth client credentials found.\n"
            "The bundled Nous Research app is not yet verified. Please either:\n"
            "  1. Set HERMES_GOOGLE_WORKSPACE_CLIENT_ID and HERMES_GOOGLE_WORKSPACE_CLIENT_SECRET env vars\n"
            "  2. Place a google_client_secret.json in ~/.hermes/\n",
            code="google_workspace_oauth_no_client",
        )

    # If we only have the placeholder, still return it — caller can decide
    # whether to proceed or error out.
    return _NOUS_CLIENT_ID, _NOUS_CLIENT_SECRET


# =============================================================================
# PKCE
# =============================================================================

def _generate_pkce_pair() -> Tuple[str, str]:
    """Generate a (code_verifier, code_challenge) pair using S256.

    The verifier is a URL-safe random string between 43-128 characters.
    The challenge is SHA256(verifier) encoded as base64url (no padding).
    """
    # secrets.token_urlsafe(64) produces ~86 chars, well within 43-128 range
    verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


# =============================================================================
# Token I/O
# =============================================================================

def load_credentials() -> Optional[dict]:
    """Load the token payload from disk.

    Returns:
        The token dict if valid, or None if missing/corrupt.
        Token format:
        {
            "token": "access_token_value",
            "refresh_token": "...",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "...",
            "client_secret": "...",
            "scopes": [...],
            "expiry": "2026-05-08T12:00:00.000000Z",
            "type": "authorized_user"
        }
    """
    path = credentials_path()
    if not path.exists():
        return None
    try:
        with _credentials_lock():
            raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (json.JSONDecodeError, OSError, IOError) as exc:
        logger.warning("Failed to read Google Workspace token at %s: %s", path, exc)
        return None
    if not isinstance(data, dict):
        return None
    # Minimal validity: must have either a token or a refresh_token
    if not data.get("token") and not data.get("refresh_token"):
        return None
    return data


def _save_credentials(token_data: dict) -> Path:
    """Atomically write token data to disk with 0o600 permissions.

    Returns the path where the token was saved.
    """
    path = credentials_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Tighten parent dir permissions
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass

    # Ensure type field is present
    if not token_data.get("type"):
        token_data["type"] = "authorized_user"

    payload = json.dumps(token_data, indent=2, sort_keys=True) + "\n"

    with _credentials_lock():
        tmp_path = path.with_suffix(f".tmp.{os.getpid()}.{secrets.token_hex(4)}")
        try:
            fd = os.open(
                str(tmp_path),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                stat.S_IRUSR | stat.S_IWUSR,
            )
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            atomic_replace(tmp_path, path)
        finally:
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass
    return path


# =============================================================================
# HTTP helpers
# =============================================================================

def _post_form(url: str, data: Dict[str, str], timeout: float = TOKEN_REQUEST_TIMEOUT_SECONDS) -> Dict[str, Any]:
    """POST x-www-form-urlencoded and return parsed JSON response."""
    body = urllib.parse.urlencode(data).encode("ascii")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        code = "google_workspace_oauth_token_http_error"
        if "invalid_grant" in detail.lower():
            code = "google_workspace_oauth_invalid_grant"
        raise GoogleWorkspaceOAuthError(
            f"Google token endpoint returned HTTP {exc.code}: {detail or exc.reason}",
            code=code,
        ) from exc
    except urllib.error.URLError as exc:
        raise GoogleWorkspaceOAuthError(
            f"Google token request failed: {exc}",
            code="google_workspace_oauth_network_error",
        ) from exc


def _fetch_user_email(access_token: str, timeout: float = TOKEN_REQUEST_TIMEOUT_SECONDS) -> str:
    """Best-effort userinfo fetch for display. Failures return empty string."""
    try:
        request = urllib.request.Request(
            USERINFO_ENDPOINT + "?alt=json",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
        return str(data.get("email", "") or "")
    except Exception as exc:
        logger.debug("Userinfo fetch failed (non-fatal): %s", exc)
        return ""


# =============================================================================
# Token validation and refresh
# =============================================================================

def _is_token_expired(token_data: dict, skew_seconds: int = REFRESH_SKEW_SECONDS) -> bool:
    """Check if the access token is expired or about to expire."""
    expiry_str = token_data.get("expiry", "")
    if not expiry_str:
        return True
    try:
        # Parse ISO format expiry (e.g., "2026-05-08T12:00:00.000000Z")
        expiry_str = expiry_str.replace("Z", "+00:00")
        expiry_dt = datetime.fromisoformat(expiry_str)
        now = datetime.now(timezone.utc)
        # Add skew buffer
        return now >= (expiry_dt - timedelta(seconds=skew_seconds))
    except (ValueError, TypeError):
        return True


def refresh_token_if_needed(token_data: dict) -> dict:
    """Refresh the access token if expired. Saves updated token to disk.

    Args:
        token_data: The current token payload dict.

    Returns:
        The (potentially updated) token dict with a fresh access token.

    Raises:
        GoogleWorkspaceOAuthError: If refresh fails.
    """
    if not _is_token_expired(token_data):
        return token_data

    refresh_token = token_data.get("refresh_token", "")
    if not refresh_token:
        raise GoogleWorkspaceOAuthError(
            "Cannot refresh: no refresh_token in stored credentials. Re-run OAuth login.",
            code="google_workspace_oauth_refresh_token_missing",
        )

    client_id = token_data.get("client_id", "")
    client_secret = token_data.get("client_secret", "")
    token_uri = token_data.get("token_uri", TOKEN_ENDPOINT)

    if not client_id:
        # Fall back to resolved credentials
        client_id, client_secret = get_client_credentials()

    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    if client_secret:
        data["client_secret"] = client_secret

    try:
        resp = _post_form(token_uri, data)
    except GoogleWorkspaceOAuthError as exc:
        if exc.code == "google_workspace_oauth_invalid_grant":
            logger.warning(
                "Google Workspace refresh token invalid (revoked/expired). "
                "User must re-authenticate."
            )
        raise

    new_access = str(resp.get("access_token", "") or "").strip()
    if not new_access:
        raise GoogleWorkspaceOAuthError(
            "Refresh response did not include an access_token.",
            code="google_workspace_oauth_refresh_empty",
        )

    # Update token data
    token_data["token"] = new_access
    expires_in = int(resp.get("expires_in", 3600) or 3600)
    expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    token_data["expiry"] = expiry_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Google sometimes rotates refresh tokens
    new_refresh = str(resp.get("refresh_token", "") or "").strip()
    if new_refresh:
        token_data["refresh_token"] = new_refresh

    _save_credentials(token_data)
    logger.info("Google Workspace token refreshed successfully.")
    return token_data


def check_auth() -> bool:
    """Check if a valid Google Workspace token exists (refreshing if needed).

    Returns:
        True if the user has valid (or refreshable) credentials, False otherwise.
    """
    token_data = load_credentials()
    if token_data is None:
        return False

    # If token is not expired, we're good
    if not _is_token_expired(token_data):
        return True

    # Try to refresh
    if not token_data.get("refresh_token"):
        return False

    try:
        refresh_token_if_needed(token_data)
        return True
    except GoogleWorkspaceOAuthError as exc:
        logger.debug("Token refresh failed during check_auth: %s", exc)
        return False


# =============================================================================
# Callback server
# =============================================================================

class _OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback code."""

    expected_state: str = ""
    captured_code: Optional[str] = None
    captured_error: Optional[str] = None
    code_verifier: str = ""
    ready: Optional[threading.Event] = None

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        logger.debug("Google Workspace OAuth callback: " + format, *args)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != CALLBACK_PATH:
            self.send_response(404)
            self.end_headers()
            return

        params = urllib.parse.parse_qs(parsed.query)
        state = (params.get("state") or [""])[0]
        error = (params.get("error") or [""])[0]
        code = (params.get("code") or [""])[0]

        if state != type(self).expected_state:
            type(self).captured_error = "state_mismatch"
            self._respond_html(400, _ERROR_PAGE.format(
                message="State mismatch — aborting for safety."
            ))
        elif error:
            type(self).captured_error = error
            safe_err = (
                str(error)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            self._respond_html(400, _ERROR_PAGE.format(
                message=f"Authorization denied: {safe_err}"
            ))
        elif code:
            type(self).captured_code = code
            self._respond_html(200, _SUCCESS_PAGE)
        else:
            type(self).captured_error = "no_code"
            self._respond_html(400, _ERROR_PAGE.format(
                message="Callback received no authorization code."
            ))

        if type(self).ready is not None:
            type(self).ready.set()

    def _respond_html(self, status: int, body: str) -> None:
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


_SUCCESS_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Connected — Hermes Agent</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #041c1c;
  color: #ffe6cb;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
}
.card {
  border: 1px solid rgba(255, 230, 203, 0.15);
  background: rgba(255, 230, 203, 0.03);
  padding: 3rem 4rem;
  text-align: center;
  max-width: 480px;
}
.icon { font-size: 3rem; margin-bottom: 1rem; }
h1 {
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}
p { color: rgba(255, 230, 203, 0.7); font-size: 0.95rem; line-height: 1.6; }
.hint { margin-top: 1.5rem; font-size: 0.85rem; color: rgba(255, 230, 203, 0.4); }
</style></head>
<body>
<div class="card">
  <div class="icon">✓</div>
  <h1>Connected</h1>
  <p>Google Workspace is now connected to Hermes Agent.</p>
  <p class="hint">You can close this tab.</p>
</div>
</body></html>
"""

_ERROR_PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>Connection Failed — Hermes Agent</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  background: #041c1c;
  color: #ffe6cb;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 2rem;
}}
.card {{
  border: 1px solid rgba(255, 100, 100, 0.3);
  background: rgba(255, 100, 100, 0.05);
  padding: 3rem 4rem;
  text-align: center;
  max-width: 480px;
}}
.icon {{ font-size: 3rem; margin-bottom: 1rem; }}
h1 {{
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}}
p {{ color: rgba(255, 230, 203, 0.7); font-size: 0.95rem; line-height: 1.6; }}
</style></head>
<body>
<div class="card">
  <div class="icon">✗</div>
  <h1>Connection Failed</h1>
  <p>{message}</p>
</div>
</body></html>
"""


# =============================================================================
# Server binding
# =============================================================================

def _bind_callback_server(preferred_port: int = DEFAULT_REDIRECT_PORT) -> Tuple[http.server.HTTPServer, int]:
    """Bind the callback HTTP server, falling back to an ephemeral port if needed."""
    try:
        server = http.server.HTTPServer((REDIRECT_HOST, preferred_port), _OAuthCallbackHandler)
        return server, preferred_port
    except OSError as exc:
        logger.info(
            "Preferred OAuth callback port %d unavailable (%s); requesting ephemeral port",
            preferred_port, exc,
        )
    server = http.server.HTTPServer((REDIRECT_HOST, 0), _OAuthCallbackHandler)
    return server, server.server_address[1]


# =============================================================================
# Main login flow (interactive, opens browser)
# =============================================================================

def run_oauth_login() -> dict:
    """Run the full PKCE OAuth flow interactively.

    Uses the Hermes dashboard (localhost:9119) as the callback handler.
    The dashboard's /auth/google/callback route exchanges the code and
    saves the token. This function polls the dashboard session until
    it's approved.

    If the dashboard is not running, exits with instructions to start it or use --no-browser mode.

    Returns:
        The saved token data dict.

    Raises:
        GoogleWorkspaceOAuthError: On any failure during the flow.
    """
    client_id, client_secret = get_client_credentials()
    if not client_id:
        raise GoogleWorkspaceOAuthError(
            "No Google OAuth client credentials available.\n"
            "Either:\n"
            "  1. Set HERMES_GOOGLE_WORKSPACE_CLIENT_ID and "
            "HERMES_GOOGLE_WORKSPACE_CLIENT_SECRET env vars\n"
            "  2. Place a google_client_secret.json in ~/.hermes/\n",
            code="google_workspace_oauth_no_client",
        )

    # Try the dashboard flow first (preferred — single source of truth)
    dashboard_port = os.environ.get("HERMES_DASHBOARD_PORT", "9119")
    dashboard_url = f"http://127.0.0.1:{dashboard_port}"
    use_dashboard = _is_dashboard_running(dashboard_url)

    if use_dashboard:
        return _run_oauth_via_dashboard(client_id, dashboard_url)
    else:
        print("The Hermes dashboard is not running.")
        print("Start it with: hermes dashboard")
        print()
        print("Or use headless mode: hermes auth google-workspace login --no-browser")
        raise SystemExit(1)


def _is_dashboard_running(dashboard_url: str) -> bool:
    """Check if the Hermes dashboard is reachable."""
    try:
        req = urllib.request.Request(f"{dashboard_url}/api/health", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            return resp.status == 200
    except Exception:
        # Try a simpler check — just see if the port is open
        try:
            req = urllib.request.Request(dashboard_url, method="GET")
            with urllib.request.urlopen(req, timeout=2):
                return True
        except Exception:
            return False


def _run_oauth_via_dashboard(client_id: str, dashboard_url: str) -> dict:
    """Run OAuth flow using the dashboard's callback route and session management."""
    # Read the dashboard token from config for API auth
    dashboard_token = ""
    try:
        config_path = get_hermes_home() / "config.yaml"
        if config_path.exists():
            import yaml
            config = yaml.safe_load(config_path.read_text()) or {}
            dashboard_token = config.get("web", {}).get("token", "") or ""
    except Exception:
        pass

    # Call the dashboard's start endpoint
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "hermes-cli/1.0",
    }
    if dashboard_token:
        headers["Authorization"] = f"Bearer {dashboard_token}"

    start_req = urllib.request.Request(
        f"{dashboard_url}/api/providers/oauth/google-workspace/start",
        method="POST",
        headers=headers,
        data=b"{}",
    )
    try:
        with urllib.request.urlopen(start_req, timeout=10) as resp:
            start_data = json.loads(resp.read().decode())
    except Exception as exc:
        raise GoogleWorkspaceOAuthError(
            f"Failed to start OAuth session via dashboard: {exc}",
            code="google_workspace_oauth_dashboard_start_failed",
        )

    auth_url = start_data.get("auth_url", "")
    session_id = start_data.get("session_id", "")
    if not auth_url or not session_id:
        raise GoogleWorkspaceOAuthError(
            "Dashboard returned invalid start response",
            code="google_workspace_oauth_dashboard_invalid",
        )

    print()
    print("Opening your browser to connect your Google Workspace account…")
    print(f"If it does not open automatically, visit:\n  {auth_url}")
    print()

    try:
        import webbrowser
        webbrowser.open(auth_url, new=1, autoraise=True)
    except Exception as exc:
        logger.debug("webbrowser.open failed: %s", exc)

    # Poll the dashboard for session completion
    print("Waiting for authorization...")
    poll_url = f"{dashboard_url}/api/providers/oauth/google-workspace/poll/{session_id}"
    deadline = time.time() + CALLBACK_WAIT_SECONDS
    while time.time() < deadline:
        time.sleep(2)
        try:
            poll_req = urllib.request.Request(poll_url, method="GET")
            with urllib.request.urlopen(poll_req, timeout=5) as resp:
                poll_data = json.loads(resp.read().decode())
            status = poll_data.get("status", "")
            if status == "approved":
                # Token was saved by the dashboard callback — load and return it
                token_data = load_credentials()
                if token_data:
                    print("✓ Authorization complete!")
                    return token_data
                raise GoogleWorkspaceOAuthError(
                    "Session approved but token file not found",
                    code="google_workspace_oauth_token_missing",
                )
            elif status not in ("pending",):
                error_msg = poll_data.get("error_message", status)
                raise GoogleWorkspaceOAuthError(
                    f"Authorization failed: {error_msg}",
                    code="google_workspace_oauth_authorization_failed",
                )
        except GoogleWorkspaceOAuthError:
            raise
        except Exception:
            # Network blip — keep polling
            continue

    raise GoogleWorkspaceOAuthError(
        f"Timed out waiting for authorization after {CALLBACK_WAIT_SECONDS}s.",
        code="google_workspace_oauth_timeout",
    )


def _run_oauth_standalone(client_id: str, client_secret: str) -> dict:
    """Fallback: run OAuth with a standalone local HTTP server (no dashboard)."""

    verifier, challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    server, port = _bind_callback_server(DEFAULT_REDIRECT_PORT)
    redirect_uri = f"http://{REDIRECT_HOST}:{port}{CALLBACK_PATH}"

    # Configure the handler class state
    _OAuthCallbackHandler.expected_state = state
    _OAuthCallbackHandler.captured_code = None
    _OAuthCallbackHandler.captured_error = None
    _OAuthCallbackHandler.code_verifier = verifier
    ready = threading.Event()
    _OAuthCallbackHandler.ready = ready

    # Build authorization URL
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = AUTH_ENDPOINT + "?" + urllib.parse.urlencode(params)

    # Start callback server
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    print()
    print("Opening your browser to connect your Google Workspace account…")
    print(f"If it does not open automatically, visit:\n  {auth_url}")
    print()

    try:
        import webbrowser
        webbrowser.open(auth_url, new=1, autoraise=True)
    except Exception as exc:
        logger.debug("webbrowser.open failed: %s", exc)

    # Wait for callback
    code: Optional[str] = None
    try:
        if ready.wait(timeout=CALLBACK_WAIT_SECONDS):
            code = _OAuthCallbackHandler.captured_code
            error = _OAuthCallbackHandler.captured_error
            if error:
                raise GoogleWorkspaceOAuthError(
                    f"Authorization failed: {error}",
                    code="google_workspace_oauth_authorization_failed",
                )
        else:
            raise GoogleWorkspaceOAuthError(
                f"Timed out waiting for OAuth callback after {CALLBACK_WAIT_SECONDS}s. "
                "Try run_oauth_login_headless() for environments without a browser.",
                code="google_workspace_oauth_timeout",
            )
    finally:
        try:
            server.shutdown()
        except Exception:
            pass
        try:
            server.server_close()
        except Exception:
            pass
        server_thread.join(timeout=2.0)

    if not code:
        raise GoogleWorkspaceOAuthError(
            "No authorization code received. Aborting.",
            code="google_workspace_oauth_no_code",
        )

    # Exchange code for tokens
    return exchange_code(code, state, verifier, redirect_uri=redirect_uri)


# =============================================================================
# Headless login flow
# =============================================================================

def run_oauth_login_headless() -> Tuple[str, str, str]:
    """Generate an OAuth URL for headless environments (no browser available).

    Returns:
        Tuple of (auth_url, state, code_verifier) — the caller should present
        the URL to the user and later call exchange_code() with the received
        authorization code.

    Raises:
        GoogleWorkspaceOAuthError: If client credentials are unavailable.
    """
    client_id, client_secret = get_client_credentials()
    if not client_id:
        raise GoogleWorkspaceOAuthError(
            "No Google OAuth client credentials available.\n"
            "Set HERMES_GOOGLE_WORKSPACE_CLIENT_ID env var or provide a "
            "google_client_secret.json in ~/.hermes/",
            code="google_workspace_oauth_no_client",
        )

    verifier, challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(16)

    # In headless mode, use localhost:1 as redirect — Google will redirect there,
    # the page will fail to load, and the user copies the URL from the address bar.
    # This avoids needing a local server to be reachable.
    redirect_uri = "http://localhost:1"

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = AUTH_ENDPOINT + "?" + urllib.parse.urlencode(params)

    return auth_url, state, verifier


# =============================================================================
# Code exchange
# =============================================================================

def exchange_code(
    code: str,
    state: str,
    code_verifier: str,
    *,
    redirect_uri: Optional[str] = None,
) -> dict:
    """Exchange an authorization code for access + refresh tokens.

    Args:
        code: The authorization code from Google's callback.
        state: The state parameter (for logging/verification; already verified
               by the callback handler if using run_oauth_login).
        code_verifier: The PKCE code verifier generated for this flow.
        redirect_uri: The redirect URI used in the authorization request.
                     Defaults to the standard localhost callback URI.

    Returns:
        The saved token data dict.

    Raises:
        GoogleWorkspaceOAuthError: If the token exchange fails.
    """
    if redirect_uri is None:
        redirect_uri = f"http://{REDIRECT_HOST}:{DEFAULT_REDIRECT_PORT}{CALLBACK_PATH}"

    client_id, client_secret = get_client_credentials()

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": code_verifier,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        data["client_secret"] = client_secret

    resp = _post_form(TOKEN_ENDPOINT, data)

    access_token = str(resp.get("access_token", "") or "").strip()
    refresh_token = str(resp.get("refresh_token", "") or "").strip()
    expires_in = int(resp.get("expires_in", 3600) or 3600)

    if not access_token:
        raise GoogleWorkspaceOAuthError(
            "Token exchange response missing access_token.",
            code="google_workspace_oauth_incomplete_response",
        )
    if not refresh_token:
        raise GoogleWorkspaceOAuthError(
            "Token exchange response missing refresh_token. "
            "Ensure 'access_type=offline' and 'prompt=consent' are in the auth URL.",
            code="google_workspace_oauth_no_refresh_token",
        )

    # Compute expiry timestamp
    expiry_dt = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    expiry_str = expiry_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    # Best-effort email fetch
    email = _fetch_user_email(access_token)

    # Build token payload compatible with existing google-workspace skill
    token_data: Dict[str, Any] = {
        "token": access_token,
        "refresh_token": refresh_token,
        "token_uri": TOKEN_ENDPOINT,
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": SCOPES,
        "expiry": expiry_str,
        "type": "authorized_user",
    }

    # Store email if we got it (not part of standard token format but useful)
    if email:
        token_data["account"] = email

    saved_path = _save_credentials(token_data)
    logger.info("Google Workspace credentials saved to %s (account: %s)", saved_path, email or "unknown")

    return token_data


# =============================================================================
# Auth status
# =============================================================================

def get_auth_status() -> dict:
    """Return a status dict describing the current Google Workspace auth state.

    Returns:
        Dict with keys:
            - logged_in (bool): Whether valid credentials exist
            - email (str): The account email if available
            - token_path (str): Path to the token file
            - scopes (list): Scopes the token was granted for
            - expiry (str): Token expiry timestamp
            - has_refresh_token (bool): Whether a refresh token is stored
            - client_source (str): Where the client credentials came from
    """
    path = credentials_path()
    status: Dict[str, Any] = {
        "logged_in": False,
        "email": "",
        "token_path": str(path),
        "scopes": [],
        "expiry": "",
        "has_refresh_token": False,
        "client_source": "none",
    }

    # Determine client credential source
    env_id = (os.getenv(ENV_CLIENT_ID) or "").strip()
    if env_id:
        status["client_source"] = "environment"
    elif _client_secret_path().exists():
        status["client_source"] = "client_secret_file"
    elif _NOUS_CLIENT_ID != "PLACEHOLDER.apps.googleusercontent.com":
        status["client_source"] = "nous_default"
    else:
        status["client_source"] = "placeholder"

    token_data = load_credentials()
    if token_data is None:
        return status

    status["email"] = token_data.get("account", "")
    status["scopes"] = token_data.get("scopes", [])
    status["expiry"] = token_data.get("expiry", "")
    status["has_refresh_token"] = bool(token_data.get("refresh_token"))

    # Check if we're actually logged in (token valid or refreshable)
    status["logged_in"] = check_auth()

    return status


# =============================================================================
# Revocation
# =============================================================================

def revoke() -> bool:
    """Revoke the Google Workspace token and delete the local file.

    Attempts to revoke the token with Google's servers first, then deletes
    the local token file regardless of whether remote revocation succeeded.

    Returns:
        True if the token was successfully revoked (or no token existed),
        False if remote revocation failed (local file is still deleted).
    """
    token_data = load_credentials()
    if token_data is None:
        logger.info("No Google Workspace token to revoke.")
        return True

    revoked_remotely = False
    # Try to revoke with Google
    token_to_revoke = token_data.get("token") or token_data.get("refresh_token", "")
    if token_to_revoke:
        try:
            data = {"token": token_to_revoke}
            body = urllib.parse.urlencode(data).encode("ascii")
            request = urllib.request.Request(
                REVOKE_ENDPOINT,
                data=body,
                method="POST",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(request, timeout=TOKEN_REQUEST_TIMEOUT_SECONDS) as response:
                if response.status == 200:
                    revoked_remotely = True
                    logger.info("Google Workspace token revoked with Google.")
        except Exception as exc:
            logger.warning("Remote token revocation failed (token may already be invalid): %s", exc)

    # Delete local file regardless
    path = credentials_path()
    with _credentials_lock():
        try:
            path.unlink()
            logger.info("Deleted Google Workspace token at %s", path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            logger.warning("Failed to delete token file at %s: %s", path, exc)

    return revoked_remotely
