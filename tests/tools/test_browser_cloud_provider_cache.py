"""Tests for ``_get_cloud_provider`` cache-only-on-success semantics.

A transient credential gap at process startup (e.g. a managed Nous Portal
access token mid-refresh, or a config-read raising) must not pin the
process to local mode for its entire lifetime. Subsequent calls should
re-resolve and pick up the cloud provider once credentials are available.

Conversely, an explicit ``cloud_provider: local`` choice and a successful
cloud-provider resolution should both cache permanently.
"""
import pytest

import tools.browser_tool as browser_tool


def _reset_resolver(monkeypatch):
    """Clear the resolver cache so each test starts fresh."""
    monkeypatch.setattr(browser_tool, "_cached_cloud_provider", None)
    monkeypatch.setattr(browser_tool, "_cloud_provider_resolved", False)


class TestCloudProviderCacheSemantics:
    """Cache-only-on-success: None results re-resolve on next call."""

    def test_explicit_local_caches_permanently(self, monkeypatch):
        """``cloud_provider: local`` must be cached so we don't re-read every call."""
        _reset_resolver(monkeypatch)

        calls = {"n": 0}

        def fake_read():
            calls["n"] += 1
            return {"browser": {"cloud_provider": "local"}}

        monkeypatch.setattr(
            "hermes_cli.config.read_raw_config", fake_read,
        )

        assert browser_tool._get_cloud_provider() is None
        assert browser_tool._get_cloud_provider() is None
        assert browser_tool._get_cloud_provider() is None
        # Resolved on first call, cached after.
        assert calls["n"] == 1
        assert browser_tool._cloud_provider_resolved is True

    def test_successful_cloud_resolution_caches_permanently(self, monkeypatch):
        """A successful provider lookup pins the cache."""
        _reset_resolver(monkeypatch)

        calls = {"n": 0}

        class FakeProvider:
            def is_configured(self):
                return True

        monkeypatch.setitem(browser_tool._PROVIDER_REGISTRY, "fake", FakeProvider)

        def fake_read():
            calls["n"] += 1
            return {"browser": {"cloud_provider": "fake"}}

        monkeypatch.setattr(
            "hermes_cli.config.read_raw_config", fake_read,
        )

        first = browser_tool._get_cloud_provider()
        second = browser_tool._get_cloud_provider()
        assert isinstance(first, FakeProvider)
        # Same cached instance — no re-instantiation.
        assert first is second
        assert calls["n"] == 1
        assert browser_tool._cloud_provider_resolved is True

    def test_no_credentials_yet_does_not_cache_none(self, monkeypatch):
        """Auto-detect with no creds returns None but does NOT pin the cache.

        This is the primary regression test for the startup-race bug: a
        transient credential gap must not pin the process to local mode
        forever.
        """
        _reset_resolver(monkeypatch)

        # No explicit cloud_provider; both auto-detect candidates unconfigured
        # at first, then Browser Use becomes available.
        bu_state = {"configured": False}

        class FakeBrowserUseUnconfigured:
            def is_configured(self):
                return bu_state["configured"]

        class FakeBrowserbaseUnconfigured:
            def is_configured(self):
                return False

        monkeypatch.setattr(
            browser_tool, "BrowserUseProvider", FakeBrowserUseUnconfigured,
        )
        monkeypatch.setattr(
            browser_tool, "BrowserbaseProvider", FakeBrowserbaseUnconfigured,
        )
        monkeypatch.setattr(
            "hermes_cli.config.read_raw_config",
            lambda: {"browser": {}},
        )

        # First call: no creds yet → None, not cached.
        assert browser_tool._get_cloud_provider() is None
        assert browser_tool._cloud_provider_resolved is False

        # Token refresh / creds now available.
        bu_state["configured"] = True
        result = browser_tool._get_cloud_provider()
        assert isinstance(result, FakeBrowserUseUnconfigured)
        assert browser_tool._cloud_provider_resolved is True

    def test_config_read_failure_does_not_cache_none(self, monkeypatch):
        """A raising config read must not pin local mode for the rest of life."""
        _reset_resolver(monkeypatch)

        attempts = {"n": 0}

        def flaky_read():
            attempts["n"] += 1
            if attempts["n"] == 1:
                raise OSError("config not yet readable")
            return {"browser": {"cloud_provider": "local"}}

        monkeypatch.setattr(
            "hermes_cli.config.read_raw_config", flaky_read,
        )

        # First call: config read raises → None returned, NOT cached.
        assert browser_tool._get_cloud_provider() is None
        assert browser_tool._cloud_provider_resolved is False
        assert attempts["n"] == 1

        # Second call: config now readable, explicit local — caches.
        assert browser_tool._get_cloud_provider() is None
        assert browser_tool._cloud_provider_resolved is True
        assert attempts["n"] == 2

    def test_explicit_provider_instantiation_failure_does_not_cache(
        self, monkeypatch, caplog,
    ):
        """If an explicit provider's __init__ raises, retry on next call."""
        import logging
        _reset_resolver(monkeypatch)

        attempts = {"n": 0}

        class FlakyProvider:
            def __init__(self):
                attempts["n"] += 1
                if attempts["n"] == 1:
                    raise RuntimeError("transient init failure")

            def is_configured(self):
                return True

        monkeypatch.setitem(browser_tool._PROVIDER_REGISTRY, "flaky", FlakyProvider)
        monkeypatch.setattr(
            "hermes_cli.config.read_raw_config",
            lambda: {"browser": {"cloud_provider": "flaky"}},
        )

        with caplog.at_level(logging.WARNING, logger=browser_tool.logger.name):
            assert browser_tool._get_cloud_provider() is None
        assert browser_tool._cloud_provider_resolved is False
        assert any(
            "Failed to instantiate explicit cloud_provider" in r.message
            for r in caplog.records
        )

        # Second call succeeds and caches.
        result = browser_tool._get_cloud_provider()
        assert isinstance(result, FlakyProvider)
        assert browser_tool._cloud_provider_resolved is True
