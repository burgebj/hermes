#!/usr/bin/env python3
"""Square OAuth2 setup for Hermes Agent.

Fully non-interactive — designed to be driven by the agent via terminal commands.
The agent mediates between this script and the user (works on CLI, Telegram, Discord, etc.)

Commands:
  setup.py --check                          # Is auth valid? Exit 0 = yes, 1 = no
  setup.py --client-secret /path/to.json    # Store OAuth client credentials
  setup.py --auth-url                       # Print the OAuth URL for user to visit
  setup.py --auth-code CODE                 # Exchange auth code for token
  setup.py --revoke                         # Revoke and delete stored token
  setup.py --install-deps                   # Install Python dependencies only

Agent workflow:
  1. Run --check. If exit 0, auth is good — skip setup.
  2. Ask user for client_secret.json path. Run --client-secret PATH.
  3. Run --auth-url. Send the printed URL to the user.
  4. User opens URL, authorizes, gets redirected to a page with a code.
  5. User pastes the code. Agent runs --auth-code CODE.
  6. Run --check to verify. Done.
"""

import argparse
import json
import os
import subprocess
import sys
import secrets
import base64
import hashlib
from pathlib import Path
from urllib.parse import urlencode

try:
    from hermes_constants import display_hermes_home, get_hermes_home
except ModuleNotFoundError:
    HERMES_AGENT_ROOT = Path(__file__).resolve().parents[4]
    if HERMES_AGENT_ROOT.exists():
        sys.path.insert(0, str(HERMES_AGENT_ROOT))
    from hermes_constants import display_hermes_home, get_hermes_home

HERMES_HOME = get_hermes_home()
TOKEN_PATH = HERMES_HOME / "square_token.json"
CLIENT_SECRET_PATH = HERMES_HOME / "square_client_secret.json"
PENDING_AUTH_PATH = HERMES_HOME / "square_oauth_pending.json"

# Square OAuth2 endpoints
AUTHORIZE_URL = "https://connect.squareup.com/oauth2/authorize"
TOKEN_URL = "https://connect.squareup.com/oauth2/token"
REVOKE_URL = "https://connect.squareup.com/oauth2/revoke"

# Scopes needed for inventory, catalog, customers, and orders
SCOPES = [
    "ITEMS_READ",
    "ITEMS_WRITE",
    "INVENTORY_READ",
    "INVENTORY_WRITE",
    "MERCHANT_PROFILE_READ",
    "CUSTOMERS_READ",
    "CUSTOMERS_WRITE",
    "ORDERS_READ",
    "ORDERS_WRITE",
    "LOCATION_READ",
]

REQUIRED_PACKAGES = ["squareup"]

REDIRECT_URI = "http://localhost:1"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def install_deps():
    """Install Square SDK if missing. Returns True on success."""
    try:
        import squareup  # noqa: F401
        print("Dependencies already installed.")
        return True
    except ImportError:
        pass

    print("Installing Square SDK...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "--", "squareup"],
            stdout=subprocess.DEVNULL,
        )
        print("Dependencies installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {e}")
        print(f"Try manually: {sys.executable} -m pip install squareup")
        return False


def _ensure_deps():
    """Check deps are available, install if not, exit on failure."""
    try:
        import squareup  # noqa: F401
    except ImportError:
        if not install_deps():
            sys.exit(1)


def check_auth():
    """Check if stored credentials are valid. Prints status, exits 0 or 1."""
    if not TOKEN_PATH.exists():
        print(f"NOT_AUTHENTICATED: No token at {TOKEN_PATH}")
        return False

    _ensure_deps()
    from squareup import Client
    from squareup.oauth2 import OAuth2

    try:
        data = _load_json(TOKEN_PATH)
        access_token = data.get("access_token")
        if not access_token:
            print("TOKEN_INVALID: Missing access_token")
            return False

        # Try to refresh to verify token is still valid
        client_secret = _load_json(CLIENT_SECRET_PATH).get("clientSecret", "")
        client_id = _load_json(CLIENT_SECRET_PATH).get("clientId", "")

        if not client_id or not client_secret:
            print("TOKEN_INVALID: Missing client credentials")
            return False

        # Token status check
        from squareup.http.client import HttpClient
        from squareup.http.api_response import ApiResponse

        http_client = HttpClient()
        response = http_client.request(
            "POST",
            TOKEN_URL,
            headers={"Content-Type": "application/json"},
            body=json.dumps({
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "access_token",
                "access_token": access_token,
            }),
        )
        # Square returns 200 if token is valid
        print(f"AUTHENTICATED: Token valid at {TOKEN_PATH}")
        return True

    except Exception as e:
        # Try refresh token flow
        try:
            data = _load_json(TOKEN_PATH)
            refresh_token = data.get("refresh_token")
            if not refresh_token:
                print(f"TOKEN_INVALID: {e}")
                return False

            client_secret = _load_json(CLIENT_SECRET_PATH).get("clientSecret", "")
            client_id = _load_json(CLIENT_SECRET_PATH).get("clientId", "")

            if not client_id or not client_secret:
                print(f"TOKEN_INVALID: Missing client credentials: {e}")
                return False

            from squareup.http.client import HttpClient
            http_client = HttpClient()
            response = http_client.request(
                "POST",
                TOKEN_URL,
                headers={"Content-Type": "application/json"},
                body=json.dumps({
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                }),
            )

            body = json.loads(response.body)
            if response.status_code == 200:
                # Update token file
                TOKEN_PATH.write_text(json.dumps(body, indent=2))
                print(f"AUTHENTICATED: Token refreshed at {TOKEN_PATH}")
                return True
            else:
                print(f"TOKEN_INVALID: Refresh failed: {body}")
                return False

        except Exception as refresh_error:
            print(f"TOKEN_INVALID: {refresh_error}")
            return False


def store_client_secret(path: str):
    """Copy and validate client_secret.json to Hermes home."""
    src = Path(path).expanduser().resolve()
    if not src.exists():
        print(f"ERROR: File not found: {src}")
        sys.exit(1)

    try:
        data = json.loads(src.read_text())
    except json.JSONDecodeError:
        print("ERROR: File is not valid JSON.")
        sys.exit(1)

    # Validate required fields
    client_id = data.get("clientId") or data.get("client_id")
    client_secret = data.get("clientSecret") or data.get("client_secret")

    if not client_id or not client_secret:
        print("ERROR: File must contain 'clientId' and 'clientSecret' fields.")
        print("Download from: https://developer.squareup.com/apps → Credentials → OAuth")
        sys.exit(1)

    # Normalize to the format we use
    normalized = {"clientId": client_id, "clientSecret": client_secret}
    CLIENT_SECRET_PATH.write_text(json.dumps(normalized, indent=2))
    print(f"OK: Client secret saved to {CLIENT_SECRET_PATH}")


def _generate_pkce_pair():
    """Generate PKCE code verifier and challenge."""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")
    return code_verifier, code_challenge


def _save_pending_auth(*, state: str, code_verifier: str, scopes: list):
    """Persist the OAuth session bits needed for a later token exchange."""
    PENDING_AUTH_PATH.write_text(
        json.dumps(
            {
                "state": state,
                "code_verifier": code_verifier,
                "scopes": scopes,
                "redirect_uri": REDIRECT_URI,
            },
            indent=2,
        )
    )


def _load_pending_auth() -> dict:
    """Load the pending OAuth session created by get_auth_url()."""
    if not PENDING_AUTH_PATH.exists():
        print("ERROR: No pending OAuth session found. Run --auth-url first.")
        sys.exit(1)

    try:
        data = json.loads(PENDING_AUTH_PATH.read_text())
    except Exception as e:
        print(f"ERROR: Could not read pending OAuth session: {e}")
        print("Run --auth-url again to start a fresh OAuth session.")
        sys.exit(1)

    if not data.get("state") or not data.get("code_verifier"):
        print("ERROR: Pending OAuth session is missing PKCE data.")
        print("Run --auth-url again to start a fresh OAuth session.")
        sys.exit(1)

    return data


def get_auth_url():
    """Print the OAuth authorization URL. User visits this in a browser."""
    if not CLIENT_SECRET_PATH.exists():
        print("ERROR: No client secret stored. Run --client-secret first.")
        sys.exit(1)

    client_data = _load_json(CLIENT_SECRET_PATH)
    client_id = client_data.get("clientId")
    if not client_id:
        print("ERROR: clientId not found in client secret file.")
        sys.exit(1)

    code_verifier, code_challenge = _generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": client_id,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    auth_url = f"{AUTHORIZE_URL}?{urlencode(params)}"
    _save_pending_auth(state=state, code_verifier=code_verifier, scopes=SCOPES)
    print(auth_url)


def _extract_code_and_state(code_or_url: str) -> tuple[str, str | None]:
    """Accept either a raw auth code or the full redirect URL pasted by the user."""
    if not code_or_url.startswith("http"):
        return code_or_url, None

    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(code_or_url)
    params = parse_qs(parsed.query)
    if "code" not in params:
        print("ERROR: No 'code' parameter found in URL.")
        sys.exit(1)

    state = params.get("state", [None])[0]
    return params["code"][0], state


def exchange_auth_code(code: str):
    """Exchange the authorization code for a token and save it."""
    if not CLIENT_SECRET_PATH.exists():
        print("ERROR: No client secret stored. Run --client-secret first.")
        sys.exit(1)

    pending_auth = _load_pending_auth()
    code, returned_state = _extract_code_and_state(code)

    if returned_state and returned_state != pending_auth["state"]:
        print("ERROR: OAuth state mismatch. Run --auth-url again to start a fresh session.")
        sys.exit(1)

    _ensure_deps()
    from squareup.http.client import HttpClient

    client_data = _load_json(CLIENT_SECRET_PATH)
    client_id = client_data.get("clientId")
    client_secret = client_data.get("clientSecret")

    http_client = HttpClient()

    try:
        response = http_client.request(
            "POST",
            TOKEN_URL,
            headers={"Content-Type": "application/json"},
            body=json.dumps({
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
                "code_verifier": pending_auth["code_verifier"],
            }),
        )

        body = json.loads(response.body)

        if response.status_code != 200:
            error_msg = body.get("error_description", body.get("error", "Unknown error"))
            print(f"ERROR: Token exchange failed: {error_msg}")
            print("The code may have expired. Run --auth-url to get a fresh URL.")
            sys.exit(1)

        TOKEN_PATH.write_text(json.dumps(body, indent=2))
        PENDING_AUTH_PATH.unlink(missing_ok=True)
        print(f"OK: Authenticated. Token saved to {TOKEN_PATH}")
        print(f"Profile-scoped token location: {display_hermes_home()}/square_token.json")

    except Exception as e:
        print(f"ERROR: Token exchange failed: {e}")
        print("The code may have expired. Run --auth-url to get a fresh URL.")
        sys.exit(1)


def revoke():
    """Revoke stored token and delete it."""
    if not TOKEN_PATH.exists():
        print("No token to revoke.")
        return

    data = _load_json(TOKEN_PATH)
    access_token = data.get("access_token")

    if not access_token:
        TOKEN_PATH.unlink(missing_ok=True)
        PENDING_AUTH_PATH.unlink(missing_ok=True)
        print("No access token to revoke.")
        return

    try:
        client_data = _load_json(CLIENT_SECRET_PATH)
        client_id = client_data.get("clientId")
        client_secret = client_data.get("clientSecret")

        _ensure_deps()
        from squareup.http.client import HttpClient
        http_client = HttpClient()

        http_client.request(
            "POST",
            REVOKE_URL,
            headers={"Content-Type": "application/json"},
            body=json.dumps({
                "client_id": client_id,
                "access_token": access_token,
            }),
        )
        print("Token revoked with Square.")
    except Exception as e:
        print(f"Remote revocation failed (token may already be invalid): {e}")

    TOKEN_PATH.unlink(missing_ok=True)
    PENDING_AUTH_PATH.unlink(missing_ok=True)
    print(f"Deleted {TOKEN_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Square OAuth setup for Hermes")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check if auth is valid (exit 0=yes, 1=no)")
    group.add_argument("--client-secret", metavar="PATH", help="Store OAuth client_secret.json")
    group.add_argument("--auth-url", action="store_true", help="Print OAuth URL for user to visit")
    group.add_argument("--auth-code", metavar="CODE", help="Exchange auth code for token")
    group.add_argument("--revoke", action="store_true", help="Revoke and delete stored token")
    group.add_argument("--install-deps", action="store_true", help="Install Python dependencies")

    args = parser.parse_args()

    if args.check:
        sys.exit(0 if check_auth() else 1)
    elif args.client_secret:
        store_client_secret(args.client_secret)
    elif args.auth_url:
        get_auth_url()
    elif args.auth_code:
        exchange_auth_code(args.auth_code)
    elif args.revoke:
        revoke()
    elif args.install_deps:
        sys.exit(0 if install_deps() else 1)


if __name__ == "__main__":
    main()
