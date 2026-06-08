"""Regression tests for the Cursor provider auth wiring."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


def _write_auth_store(tmp_path, payload: dict) -> None:
    hermes_home = tmp_path / "hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    (hermes_home / "auth.json").write_text(json.dumps(payload, indent=2))


def test_auth_add_cursor_persists_provider_state_and_pool_entry(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    _write_auth_store(tmp_path, {"version": 1, "providers": {}})

    from hermes_cli.auth_commands import auth_add_command

    monkeypatch.setattr(
        "hermes_cli.auth.login_cursor",
        lambda **_kwargs: {
            "access_token": "cursor-access-token",
            "refresh_token": "cursor-refresh-token",
            "expires_at": 1893456000,
        },
    )

    auth_add_command(
        SimpleNamespace(
            provider="cursor",
            auth_type="oauth",
            api_key=None,
            label="cursor-subscription",
        )
    )

    payload = json.loads((tmp_path / "hermes" / "auth.json").read_text())
    assert payload["active_provider"] == "cursor"

    state = payload["providers"]["cursor"]
    assert state["access_token"] == "cursor-access-token"
    assert state["refresh_token"] == "cursor-refresh-token"
    assert state["expires_at"] == 1893456000
    assert state["auth_mode"] == "oauth_external"
    assert state["base_url"] == "https://api2.cursor.sh"

    entries = payload["credential_pool"]["cursor"]
    entry = next(item for item in entries if item["source"] == "manual:cursor_oauth")
    assert entry["label"] == "cursor-subscription"
    assert entry["auth_type"] == "oauth"
    assert entry["access_token"] == "cursor-access-token"
    assert entry["refresh_token"] == "cursor-refresh-token"
    assert entry["base_url"] == "https://api2.cursor.sh"


def test_get_auth_status_dispatches_cursor_branch(monkeypatch):
    from hermes_cli.auth import get_auth_status

    expected = {
        "logged_in": True,
        "source": "hermes-auth-store",
        "api_key": "cursor-access-token",
    }
    monkeypatch.setattr("hermes_cli.auth.get_cursor_auth_status", lambda: expected)

    assert get_auth_status("cursor") == expected


def test_auth_add_cursor_defaults_to_oauth_branch(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / "hermes"))
    _write_auth_store(tmp_path, {"version": 1, "providers": {}})

    from hermes_cli.auth_commands import _OAUTH_CAPABLE_PROVIDERS, auth_add_command

    assert "cursor" in _OAUTH_CAPABLE_PROVIDERS

    called = {"login_cursor": 0, "prompted_for_api_key": 0}

    monkeypatch.setattr(
        "hermes_cli.auth.login_cursor",
        lambda **_kwargs: called.__setitem__("login_cursor", called["login_cursor"] + 1) or {
            "access_token": "cursor-access-token",
            "refresh_token": "cursor-refresh-token",
            "expires_at": 1893456000,
        },
    )

    def _unexpected_prompt(_prompt: str) -> str:
        called["prompted_for_api_key"] += 1
        return ""

    monkeypatch.setattr("hermes_cli.auth_commands.masked_secret_prompt", _unexpected_prompt)

    auth_add_command(
        SimpleNamespace(
            provider="cursor",
            auth_type=None,
            api_key=None,
            label=None,
        )
    )

    assert called["login_cursor"] == 1
    assert called["prompted_for_api_key"] == 0
