"""Tests for the MCP OAuth manager (tools/mcp_oauth_manager.py).

The manager consolidates the eight scattered MCP-OAuth call sites into a
single object with disk-mtime watch, dedup'd 401 handling, and a provider
cache. See `tools/mcp_oauth_manager.py` for design rationale.
"""
import json
import os
import time

import pytest

pytest.importorskip(
    "mcp.client.auth.oauth2",
    reason="MCP SDK 1.26.0+ required for OAuth support",
)


def test_manager_is_singleton():
    """get_manager() returns the same instance across calls."""
    from tools.mcp_oauth_manager import get_manager, reset_manager_for_tests
    reset_manager_for_tests()
    m1 = get_manager()
    m2 = get_manager()
    assert m1 is m2


def test_manager_get_or_build_provider_caches(tmp_path, monkeypatch):
    """Calling get_or_build_provider twice with same name returns same provider."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from tools.mcp_oauth_manager import MCPOAuthManager

    mgr = MCPOAuthManager()
    p1 = mgr.get_or_build_provider("srv", "https://example.com/mcp", None)
    p2 = mgr.get_or_build_provider("srv", "https://example.com/mcp", None)
    assert p1 is p2


def test_manager_get_or_build_rebuilds_on_url_change(tmp_path, monkeypatch):
    """Changing the URL discards the cached provider."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from tools.mcp_oauth_manager import MCPOAuthManager

    mgr = MCPOAuthManager()
    p1 = mgr.get_or_build_provider("srv", "https://a.example.com/mcp", None)
    p2 = mgr.get_or_build_provider("srv", "https://b.example.com/mcp", None)
    assert p1 is not p2


def test_manager_remove_evicts_cache(tmp_path, monkeypatch):
    """remove(name) evicts the provider from cache AND deletes disk files."""
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from tools.mcp_oauth_manager import MCPOAuthManager

    # Pre-seed tokens on disk
    token_dir = tmp_path / "mcp-tokens"
    token_dir.mkdir(parents=True)
    (token_dir / "srv.json").write_text(json.dumps({
        "access_token": "TOK",
        "token_type": "Bearer",
    }))

    mgr = MCPOAuthManager()
    p1 = mgr.get_or_build_provider("srv", "https://example.com/mcp", None)
    assert p1 is not None
    assert (token_dir / "srv.json").exists()

    mgr.remove("srv")

    assert not (token_dir / "srv.json").exists()
    p2 = mgr.get_or_build_provider("srv", "https://example.com/mcp", None)
    assert p1 is not p2


def test_hermes_provider_subclass_exists():
    """HermesMCPOAuthProvider is defined and subclasses OAuthClientProvider."""
    from tools.mcp_oauth_manager import _HERMES_PROVIDER_CLS
    from mcp.client.auth.oauth2 import OAuthClientProvider

    assert _HERMES_PROVIDER_CLS is not None
    assert issubclass(_HERMES_PROVIDER_CLS, OAuthClientProvider)


@pytest.mark.asyncio
async def test_disk_watch_invalidates_on_mtime_change(tmp_path, monkeypatch):
    """When the tokens file mtime changes, provider._initialized flips False.

    This is the behaviour Claude Code ships as
    invalidateOAuthCacheIfDiskChanged (CC-1096 / GH#24317) and is the core
    fix for Cthulhu's external-cron refresh workflow.
    """
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from tools.mcp_oauth_manager import MCPOAuthManager, reset_manager_for_tests

    reset_manager_for_tests()

    token_dir = tmp_path / "mcp-tokens"
    token_dir.mkdir(parents=True)
    tokens_file = token_dir / "srv.json"
    tokens_file.write_text(json.dumps({
        "access_token": "OLD",
        "token_type": "Bearer",
    }))

    mgr = MCPOAuthManager()
    provider = mgr.get_or_build_provider("srv", "https://example.com/mcp", None)
    assert provider is not None

    # First call: records mtime (zero -> real) -> returns True
    changed1 = await mgr.invalidate_if_disk_changed("srv")
    assert changed1 is True

    # No file change -> False
    changed2 = await mgr.invalidate_if_disk_changed("srv")
    assert changed2 is False

    # Touch file with a newer mtime
    future_mtime = time.time() + 10
    os.utime(tokens_file, (future_mtime, future_mtime))

    changed3 = await mgr.invalidate_if_disk_changed("srv")
    assert changed3 is True
    # _initialized flipped — next async_auth_flow will re-read from disk
    assert provider._initialized is False


def test_manager_builds_hermes_provider_subclass(tmp_path, monkeypatch):
    """get_or_build_provider returns HermesMCPOAuthProvider, not plain OAuthClientProvider."""
    from tools.mcp_oauth_manager import (
        MCPOAuthManager, _HERMES_PROVIDER_CLS, reset_manager_for_tests,
    )
    reset_manager_for_tests()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    mgr = MCPOAuthManager()
    provider = mgr.get_or_build_provider("srv", "https://example.com/mcp", None)

    assert _HERMES_PROVIDER_CLS is not None
    assert isinstance(provider, _HERMES_PROVIDER_CLS)
    assert provider._hermes_server_name == "srv"


@pytest.mark.asyncio
async def test_manager_provider_token_exchange_includes_dcr_secret(tmp_path, monkeypatch):
    """The manager provider path applies the same Supabase DCR secret fix."""
    from urllib.parse import parse_qs

    from mcp.shared.auth import OAuthClientInformationFull
    from tools.mcp_oauth_manager import MCPOAuthManager, reset_manager_for_tests

    reset_manager_for_tests()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    mgr = MCPOAuthManager()
    provider = mgr.get_or_build_provider("supabase", "https://mcp.supabase.com/mcp", None)
    provider.context.client_info = OAuthClientInformationFull.model_validate({
        "client_id": "client-id",
        "client_secret": "secret",
        "redirect_uris": [str(provider.context.client_metadata.redirect_uris[0])],
        "token_endpoint_auth_method": "none",
    })

    request = await provider._exchange_token_authorization_code("auth-code", "verifier")
    body = parse_qs(request.content.decode())

    assert body["client_secret"] == ["secret"]
    assert provider.context.client_info.token_endpoint_auth_method == "client_secret_post"


def test_manager_reuses_cached_dcr_redirect_port(tmp_path, monkeypatch):
    """Manager provider path must reuse the redirect_uri registered by DCR."""
    from tools.mcp_oauth_manager import MCPOAuthManager, reset_manager_for_tests

    reset_manager_for_tests()
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    token_dir = tmp_path / "mcp-tokens"
    token_dir.mkdir(parents=True)
    (token_dir / "supabase.client.json").write_text(json.dumps({
        "client_id": "client-id",
        "client_secret": "secret",
        "redirect_uris": ["http://127.0.0.1:53902/callback"],
        "token_endpoint_auth_method": "client_secret_post",
    }))

    mgr = MCPOAuthManager()
    provider = mgr.get_or_build_provider("supabase", "https://mcp.supabase.com/mcp", None)

    assert str(provider.context.client_metadata.redirect_uris[0]) == (
        "http://127.0.0.1:53902/callback"
    )
