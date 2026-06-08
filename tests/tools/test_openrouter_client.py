"""Regression tests for tools/openrouter_client.py.

Covers the TOCTOU race in get_async_client() fixed in Issue #24731:
two threads simultaneously seeing _client=None could each call
resolve_provider_client() and create duplicate async HTTP clients.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

import pytest


def _reset_module():
    """Reset the openrouter_client module singleton so each test starts fresh."""
    import tools.openrouter_client as mod
    mod._client = None


class TestGetAsyncClientToctouRace:
    """50-thread barrier tests for get_async_client() double-checked locking."""

    def test_concurrent_calls_return_same_instance(self, monkeypatch):
        """All 50 concurrent callers must receive the exact same client object."""
        _reset_module()

        fake_client = MagicMock(name="fake_async_client")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        import tools.openrouter_client as mod

        with patch("agent.auxiliary_client.resolve_provider_client", return_value=(fake_client, "some-model")):
            barrier = threading.Barrier(50)
            results: list = []
            lock = threading.Lock()

            def call():
                barrier.wait()
                client = mod.get_async_client()
                with lock:
                    results.append(client)

            with ThreadPoolExecutor(max_workers=50) as pool:
                futures = [pool.submit(call) for _ in range(50)]
                for f in futures:
                    f.result()

        assert len(results) == 50
        first = results[0]
        assert all(r is first for r in results), (
            f"Expected 1 unique client, got {len(set(id(r) for r in results))}"
        )

    def test_only_one_client_created(self, monkeypatch):
        """resolve_provider_client must be called exactly once regardless of concurrency."""
        _reset_module()

        call_count = 0
        call_lock = threading.Lock()
        fake_client = MagicMock(name="fake_async_client")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

        import tools.openrouter_client as mod

        def counting_resolver(provider, *, async_mode=False):
            nonlocal call_count
            with call_lock:
                call_count += 1
            return fake_client, "some-model"

        with patch("agent.auxiliary_client.resolve_provider_client", side_effect=counting_resolver):
            barrier = threading.Barrier(50)

            def call():
                barrier.wait()
                mod.get_async_client()

            with ThreadPoolExecutor(max_workers=50) as pool:
                futures = [pool.submit(call) for _ in range(50)]
                for f in futures:
                    f.result()

        assert call_count == 1, f"resolve_provider_client called {call_count} times (expected 1)"


class TestCheckApiKey:
    def test_returns_true_when_key_set(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-test")
        import tools.openrouter_client as mod
        assert mod.check_api_key() is True

    def test_returns_false_when_key_absent(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        import tools.openrouter_client as mod
        assert mod.check_api_key() is False
