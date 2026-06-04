"""Tests for gateway runtime-footer account-usage cache."""
from __future__ import annotations

from gateway import run as gateway_run


def test_footer_account_usage_cache_reuses_snapshot_within_ttl(monkeypatch):
    calls = []

    def fake_fetch(provider, *, base_url=None, api_key=None):
        calls.append((provider, base_url, api_key))
        return {"call": len(calls)}

    monkeypatch.setattr(gateway_run, "fetch_account_usage", fake_fetch)
    gateway_run._FOOTER_ACCOUNT_USAGE_CACHE.clear()

    first = gateway_run._fetch_footer_account_usage_cached(
        "openai-codex", base_url="https://example.test/", api_key="secret", ttl_seconds=60
    )
    second = gateway_run._fetch_footer_account_usage_cached(
        "openai-codex", base_url="https://example.test", api_key="secret", ttl_seconds=60
    )

    assert first == {"call": 1}
    assert second is first
    assert calls == [("openai-codex", "https://example.test/", "secret")]


def test_footer_account_usage_cache_separates_same_token_by_account_label(monkeypatch):
    calls = []

    def fake_fetch(provider, *, base_url=None, api_key=None):
        calls.append((provider, base_url, api_key))
        return {"call": len(calls)}

    monkeypatch.setattr(gateway_run, "fetch_account_usage", fake_fetch)
    gateway_run._FOOTER_ACCOUNT_USAGE_CACHE.clear()

    first = gateway_run._fetch_footer_account_usage_cached(
        "openai-codex", api_key="same-token", account_label="oauth1"
    )
    second = gateway_run._fetch_footer_account_usage_cached(
        "openai-codex", api_key="same-token", account_label="oauth2"
    )

    assert first == {"call": 1}
    assert second == {"call": 2}
    assert len(calls) == 2


def test_footer_account_usage_cache_refreshes_after_ttl(monkeypatch):
    now = [100.0]
    calls = []

    def fake_monotonic():
        return now[0]

    def fake_fetch(provider, *, base_url=None, api_key=None):
        calls.append(provider)
        return {"call": len(calls)}

    monkeypatch.setattr(gateway_run.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(gateway_run, "fetch_account_usage", fake_fetch)
    gateway_run._FOOTER_ACCOUNT_USAGE_CACHE.clear()

    first = gateway_run._fetch_footer_account_usage_cached("anthropic", ttl_seconds=10)
    now[0] = 105.0
    second = gateway_run._fetch_footer_account_usage_cached("anthropic", ttl_seconds=10)
    now[0] = 111.0
    third = gateway_run._fetch_footer_account_usage_cached("anthropic", ttl_seconds=10)

    assert first == {"call": 1}
    assert second is first
    assert third == {"call": 2}
    assert calls == ["anthropic", "anthropic"]
