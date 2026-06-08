"""Tests for profile-scoped xAI HTTP credential resolution.

Regression for the #18594 follow-up: xAI credential probes (the gates behind
x_search, video_gen, and web-search) resolved the auth store from the *root*
``HERMES_HOME`` and missed a named profile's credential — gating those tools
out at boot whenever the gateway ran a named profile with ``HERMES_HOME``
pointed at the root (the Docker multi-profile layout, the multi-profile
dashboard, and lazy tool-gate re-checks).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def _xai_pool_store(access_token: str = "xai-oat-token") -> dict:
    return {
        "version": 1,
        "credential_pool": {
            "xai-oauth": [
                {
                    "id": "x1",
                    "label": "xai",
                    "auth_type": "oauth",
                    "priority": 0,
                    "source": "manual",
                    "access_token": access_token,
                }
            ]
        },
    }


def _xai_singleton_store(access_token: str = "xai-oat-token") -> dict:
    return {
        "version": 1,
        "providers": {"xai-oauth": {"tokens": {"access_token": access_token}}},
    }


@pytest.fixture()
def root_home_with_profile(tmp_path, monkeypatch):
    """Docker-like layout: ``HERMES_HOME`` at the ROOT, named profile active.

    * ``Path.home()`` -> ``tmp_path``
    * root            -> ``tmp_path/.hermes``  (``HERMES_HOME`` points HERE)
    * profile         -> ``tmp_path/.hermes/profiles/coder``  (active)

    Pointing ``HERMES_HOME`` at the root while a named profile is active is the
    exact condition that triggered the bug.
    """
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    root = tmp_path / ".hermes"
    profile = root / "profiles" / "coder"
    profile.mkdir(parents=True)
    (root / "active_profile").write_text("coder\n")
    monkeypatch.setenv("HERMES_HOME", str(root))
    return {"root": root, "profile": profile}


def test_has_xai_credentials_resolves_active_profile_pool(root_home_with_profile):
    """Pool-only credential in the active profile is found despite root HERMES_HOME."""
    from tools.xai_http import has_xai_credentials

    _write(root_home_with_profile["profile"] / "auth.json", _xai_pool_store())
    _write(root_home_with_profile["root"] / "auth.json", {"version": 1, "credential_pool": {}})
    assert has_xai_credentials() is True


def test_has_xai_credentials_resolves_active_profile_singleton(root_home_with_profile):
    """providers.xai-oauth.tokens singleton in the active profile is found too."""
    from tools.xai_http import has_xai_credentials

    _write(root_home_with_profile["profile"] / "auth.json", _xai_singleton_store())
    _write(root_home_with_profile["root"] / "auth.json", {"version": 1, "providers": {}})
    assert has_xai_credentials() is True


def test_has_xai_credentials_false_without_profile_credential(root_home_with_profile):
    """No xAI credential anywhere -> False (guards against over-broad scoping)."""
    from tools.xai_http import has_xai_credentials

    _write(root_home_with_profile["profile"] / "auth.json", {"version": 1, "credential_pool": {}})
    _write(root_home_with_profile["root"] / "auth.json", {"version": 1, "credential_pool": {}})
    assert has_xai_credentials() is False


def test_has_xai_credentials_classic_home_unchanged(tmp_path, monkeypatch):
    """Standard single-home layout (no named profile) is unaffected."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    from tools.xai_http import has_xai_credentials

    _write(home / "auth.json", _xai_singleton_store())
    assert has_xai_credentials() is True


def test_has_xai_credentials_xai_api_key_env(monkeypatch):
    """Explicit XAI_API_KEY short-circuits to True."""
    monkeypatch.setenv("XAI_API_KEY", "sk-xai-explicit")
    from tools.xai_http import has_xai_credentials

    assert has_xai_credentials() is True


def test_resolve_xai_http_credentials_scopes_to_active_profile(root_home_with_profile, monkeypatch):
    """The public resolver applies the active-profile home scope before delegating."""
    import tools.xai_http as xai_http
    from hermes_constants import get_hermes_home

    captured: dict = {}

    def fake_inner(*, force_refresh: bool = False):
        captured["home"] = str(get_hermes_home())
        return {"provider": "xai-oauth", "api_key": "tok", "base_url": "https://api.x.ai/v1"}

    monkeypatch.setattr(xai_http, "_resolve_xai_http_credentials", fake_inner)
    xai_http.resolve_xai_http_credentials()
    assert captured["home"] == str(root_home_with_profile["profile"])
