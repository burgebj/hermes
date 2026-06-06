"""Tests for Kimi Coding provider /v1 stripping in runtime_provider.

Refs: https://www.kimi.com/code/docs/en/
"""

import pytest

from hermes_cli import runtime_provider as rp


def test_kimi_coding_anthropic_strips_trailing_v1(monkeypatch):
    """kimi-coding with /coding/v1 → anthropic_messages, /v1 stripped."""
    monkeypatch.setattr(rp, "resolve_provider", lambda *a, **k: "kimi-coding")
    monkeypatch.setattr(rp, "_get_model_config", lambda: {})
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
    monkeypatch.setenv("KIMI_BASE_URL", "https://api.kimi.com/coding/v1")

    resolved = rp.resolve_runtime_provider(requested="kimi-coding")

    assert resolved["provider"] == "kimi-coding"
    assert resolved["api_mode"] == "anthropic_messages"
    # Trailing /v1 stripped — Anthropic SDK appends /v1/messages itself.
    assert resolved["base_url"] == "https://api.kimi.com/coding"


def test_kimi_coding_anthropic_without_v1_unchanged(monkeypatch):
    """kimi-coding with /coding/ (no /v1) → base_url preserved."""
    monkeypatch.setattr(rp, "resolve_provider", lambda *a, **k: "kimi-coding")
    monkeypatch.setattr(rp, "_get_model_config", lambda: {})
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")
    monkeypatch.setenv("KIMI_BASE_URL", "https://api.kimi.com/coding/")

    resolved = rp.resolve_runtime_provider(requested="kimi-coding")

    assert resolved["base_url"] == "https://api.kimi.com/coding"


def test_kimi_coding_chat_completions_keeps_v1(monkeypatch):
    """When api_mode is chat_completions (OpenAI), /v1 must NOT be stripped."""
    monkeypatch.setattr(rp, "resolve_provider", lambda *a, **k: "kimi-coding")
    monkeypatch.setattr(
        rp,
        "_get_model_config",
        lambda: {
            "provider": "kimi-coding",
            "base_url": "https://api.kimi.com/coding/v1",
            "api_mode": "chat_completions",
        },
    )
    monkeypatch.setenv("KIMI_API_KEY", "test-kimi-key")

    resolved = rp.resolve_runtime_provider(requested="kimi-coding")

    assert resolved["api_mode"] == "chat_completions"
    # OpenAI endpoint keeps /v1 — the OpenAI SDK uses it as-is.
    assert resolved["base_url"] == "https://api.kimi.com/coding/v1"


def test_kimi_coding_cn_anthropic_strips_trailing_v1(monkeypatch):
    """kimi-coding-cn also strips /v1 for anthropic_messages mode."""
    monkeypatch.setattr(rp, "resolve_provider", lambda *a, **k: "kimi-coding-cn")
    monkeypatch.setattr(rp, "_get_model_config", lambda: {})
    monkeypatch.setenv("KIMI_CN_API_KEY", "test-kimi-cn-key")

    # kimi-coding-cn has no base_url_env_var, so pass base_url explicitly
    resolved = rp.resolve_runtime_provider(
        requested="kimi-coding-cn",
        explicit_base_url="https://api.kimi.com/coding/v1",
    )

    assert resolved["provider"] == "kimi-coding-cn"
    assert resolved["api_mode"] == "anthropic_messages"
    assert resolved["base_url"] == "https://api.kimi.com/coding"
