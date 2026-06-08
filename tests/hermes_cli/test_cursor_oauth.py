from __future__ import annotations

import base64
import hashlib
import json
import time
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from hermes_cli.cursor_oauth import (
    CURSOR_LOGIN_URL,
    generate_cursor_auth_params,
    get_token_expiry,
    is_cursor_token_expiring_soon,
    poll_cursor_auth,
)


def _jwt_with_exp(exp: int) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode("utf-8")).decode("ascii").rstrip("=")
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode("utf-8")).decode("ascii").rstrip("=")
    return f"{header}.{payload}."


def test_generate_cursor_auth_params_builds_pkce_login_url():
    params = generate_cursor_auth_params()

    verifier = params["verifier"]
    challenge = params["challenge"]
    auth_uuid = params["uuid"]
    login_url = params["login_url"]

    assert len(verifier) >= 43
    assert isinstance(auth_uuid, str) and auth_uuid

    expected_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest())
        .decode("ascii")
        .rstrip("=")
    )
    assert challenge == expected_challenge

    parsed = urlparse(login_url)
    query = parse_qs(parsed.query)
    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == CURSOR_LOGIN_URL
    assert query["challenge"] == [challenge]
    assert query["uuid"] == [auth_uuid]
    assert query["mode"] == ["login"]
    assert query["redirectTarget"] == ["cli"]


def test_get_token_expiry_reads_jwt_exp():
    exp = int(time.time()) + 3600
    token = _jwt_with_exp(exp)
    assert get_token_expiry(token) == exp


def test_is_cursor_token_expiring_soon_respects_five_minute_buffer():
    soon = _jwt_with_exp(int(time.time()) + 60)
    later = _jwt_with_exp(int(time.time()) + 3600)

    assert is_cursor_token_expiring_soon(soon) is True
    assert is_cursor_token_expiring_soon(later) is False


def test_poll_cursor_auth_retries_404_then_returns_tokens(monkeypatch):
    responses = [
        httpx.Response(404, text="pending"),
        httpx.Response(200, json={"accessToken": "cursor-access", "refreshToken": "cursor-refresh"}),
    ]
    calls: list[dict] = []

    def _fake_get(url, *, params=None, timeout=None, **kwargs):
        calls.append({"url": url, "params": params, "timeout": timeout, "kwargs": kwargs})
        return responses.pop(0)

    monkeypatch.setattr("hermes_cli.cursor_oauth.httpx.get", _fake_get)
    monkeypatch.setattr("hermes_cli.cursor_oauth.time.sleep", lambda *_args, **_kwargs: None)

    tokens = poll_cursor_auth("uuid-123", "verifier-abc")

    assert tokens == {
        "access_token": "cursor-access",
        "refresh_token": "cursor-refresh",
    }
    assert len(calls) == 2
    assert calls[0]["params"] == {"uuid": "uuid-123", "verifier": "verifier-abc"}
