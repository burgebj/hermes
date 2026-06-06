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


@pytest.mark.asyncio
async def test_handle_401_tracks_inflight_task_to_prevent_gc(tmp_path, monkeypatch):
    """The 401 handler task must be strongly referenced by the manager.

    ``asyncio.create_task`` returns a task the event loop only weakly
    references. If the manager discards its handle, the background coroutine
    can be garbage-collected mid-run and every concurrent waiter stuck on
    ``await pending`` hangs forever. See the design note on
    ``MCPOAuthManager._inflight_tasks``.
    """
    import asyncio

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from tools.mcp_oauth_manager import MCPOAuthManager, _ProviderEntry

    class _TrackedSet(set):
        """set subclass that records every element ever inserted."""

        def __init__(self):
            super().__init__()
            self.ever_added: list = []

        def add(self, item):  # noqa: A003
            self.ever_added.append(item)
            super().add(item)

    mgr = MCPOAuthManager()
    mgr._inflight_tasks = _TrackedSet()

    class _DummyProvider:
        context = None  # forces the can_refresh=False branch

    mgr._entries["srv"] = _ProviderEntry(
        server_url="https://example.com/mcp",
        oauth_config=None,
        provider=_DummyProvider(),
    )

    result = await mgr.handle_401("srv", failed_access_token="TOK")

    # Exactly one handler task was created and tracked.
    assert len(mgr._inflight_tasks.ever_added) == 1
    tracked_task = mgr._inflight_tasks.ever_added[0]
    assert isinstance(tracked_task, asyncio.Task)
    # done_callback must have removed the finished task from the live set,
    # otherwise the set would grow unbounded across repeated 401s.
    assert tracked_task not in mgr._inflight_tasks
    assert len(mgr._inflight_tasks) == 0
    assert tracked_task.done()
    # With provider.context=None, there's nothing to refresh — result False.
    assert result is False


@pytest.mark.asyncio
async def test_handle_401_dedup_survives_even_if_task_reference_dropped(tmp_path, monkeypatch):
    """Concurrent 401s share one handler task and all callers resolve.

    Regression guard: if the manager ever stops holding a strong reference
    to the `_do_handle` task, this test can intermittently hang when the
    task is GC'd between the ``await`` checkpoints inside ``_do_handle``.
    Running it in CI with ``gc.collect()`` mid-flight (below) exercises
    that window.
    """
    import asyncio
    import gc

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    from tools.mcp_oauth_manager import MCPOAuthManager, _ProviderEntry

    mgr = MCPOAuthManager()

    class _DummyProvider:
        context = None

    mgr._entries["srv"] = _ProviderEntry(
        server_url="https://example.com/mcp",
        oauth_config=None,
        provider=_DummyProvider(),
    )

    # Fan out N concurrent callers sharing the same failed token so all
    # collapse onto a single deduped handler future.
    async def _caller():
        return await mgr.handle_401("srv", failed_access_token="TOK")

    tasks = [asyncio.create_task(_caller()) for _ in range(8)]
    # Give the event loop one tick to schedule _do_handle, then force GC.
    await asyncio.sleep(0)
    gc.collect()

    results = await asyncio.wait_for(asyncio.gather(*tasks), timeout=5.0)
    assert results == [False] * 8
    assert len(mgr._inflight_tasks) == 0


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

