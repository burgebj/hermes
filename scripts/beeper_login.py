#!/usr/bin/env python3
"""Mint a Matrix access token for a Beeper account (for the Matrix gateway).

Beeper is a hosted Matrix homeserver (matrix.beeper.com) but it has NO password
login — auth goes through Beeper's own email-code → JWT flow. Hermes' Matrix
adapter authenticates with MATRIX_ACCESS_TOKEN (it calls /whoami), so once this
script hands you a token the existing adapter works against Beeper unchanged.
See website/docs/user-guide/messaging/matrix.md ("Connect via Beeper").

Run this for the *dedicated bot* Beeper account (a second Beeper signup with its
own email). The flow:

  1. start a login          POST api.beeper.com/user/login          -> request id
  2. send a code to email   POST api.beeper.com/user/login/email    -> emails code
  3. exchange the code      POST api.beeper.com/user/login/response -> Beeper JWT
  4. exchange the JWT        POST matrix.beeper.com/_matrix/client/v3/login
                             (type: org.matrix.login.jwt)           -> Matrix token

It prints MATRIX_ACCESS_TOKEN / MATRIX_USER_ID / MATRIX_DEVICE_ID. The
(token, device_id) pair is a unit: reuse the same device_id on every restart
(MATRIX_DEVICE_ID) so the bot keeps a stable E2EE identity.

Usage:
    python3 scripts/beeper_login.py                      # prompts for email + code
    python3 scripts/beeper_login.py --email bot@example.com
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

# Beeper's "private" API bearer. It is a fixed, public constant (it appears in
# Beeper's own clients and every community login script) — it is NOT a secret and
# NOT account-specific; it only gates the unauthenticated login endpoints.
BEEPER_API = "https://api.beeper.com"
BEEPER_BEARER = "BEEPER-PRIVATE-API-PLEASE-DONT-USE"
MATRIX_HOMESERVER = "https://matrix.beeper.com"
DEVICE_DISPLAY_NAME = "Hermes Agent (Beeper gateway)"


def _post(url: str, body: dict, *, bearer: str | None = None) -> dict:
    data = json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"\n[error] {url}\n  HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"\n[error] could not reach {url}: {e.reason}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Mint a Beeper Matrix access token.")
    ap.add_argument("--email", help="bot account email (prompted if omitted)")
    args = ap.parse_args()

    email = args.email or input("Bot account Beeper email: ").strip()
    if not email:
        sys.exit("[error] email is required")

    print("[1/4] starting login...", file=sys.stderr)
    start = _post(f"{BEEPER_API}/user/login", {}, bearer=BEEPER_BEARER)
    request_id = start.get("request")
    if not request_id:
        sys.exit(f"[error] no 'request' in login response: {start}")

    print(f"[2/4] emailing a login code to {email} ...", file=sys.stderr)
    _post(
        f"{BEEPER_API}/user/login/email",
        {"request": request_id, "email": email},
        bearer=BEEPER_BEARER,
    )

    code = input("Enter the 6-digit code from the Beeper email: ").strip()
    if not code:
        sys.exit("[error] code is required")

    print("[3/4] exchanging code for a Beeper JWT...", file=sys.stderr)
    resp = _post(
        f"{BEEPER_API}/user/login/response",
        {"request": request_id, "response": code},
        bearer=BEEPER_BEARER,
    )
    jwt = resp.get("token")
    if not jwt:
        sys.exit(f"[error] no 'token' (JWT) in response: {resp}")

    print("[4/4] exchanging JWT for a Matrix access token...", file=sys.stderr)
    login = _post(
        f"{MATRIX_HOMESERVER}/_matrix/client/v3/login",
        {
            "type": "org.matrix.login.jwt",
            "token": jwt,
            "initial_device_display_name": DEVICE_DISPLAY_NAME,
        },
    )

    access_token = login.get("access_token")
    user_id = login.get("user_id")
    device_id = login.get("device_id")
    if not (access_token and user_id and device_id):
        sys.exit(f"[error] unexpected Matrix login response: {login}")

    print("\n" + "=" * 70, file=sys.stderr)
    print("SUCCESS — set these for the Hermes Matrix gateway:", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    print(f"MATRIX_HOMESERVER={MATRIX_HOMESERVER}")
    print(f"MATRIX_ACCESS_TOKEN={access_token}")
    print(f"MATRIX_USER_ID={user_id}")
    print(f"MATRIX_DEVICE_ID={device_id}")
    print(
        "\nBeeper rooms are encrypted, so also set MATRIX_ENCRYPTION=true and\n"
        "MATRIX_RECOVERY_KEY (the bot account's Beeper recovery key, from Beeper\n"
        "Settings -> Encryption). Keep MATRIX_ACCESS_TOKEN + MATRIX_DEVICE_ID\n"
        "together — the device_id is tied to this token and the bot's E2EE identity.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
