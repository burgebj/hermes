"""Tests for ProviderProfile.cache_strategy_for() and the conversation-loop fallback.

The old ``AIAgent._anthropic_prompt_cache_policy()`` returned ``(should_cache,
use_native_layout)``.  That function is deleted; the same decision is now made
by two co-operating parts:

1. ``ProviderProfile.cache_strategy_for(model)`` — returns a ``PromptCacheStrategy``
   instance for recognised providers.
2. A fallback in ``conversation_loop.py`` that injects a native-layout strategy
   for any unknown provider that speaks the Anthropic wire format with a Claude
   model.

These tests pin the strategy type + layout for every endpoint class so that a
regression (e.g. silently dropping caching on third-party Anthropic gateways,
or applying the native layout on OpenRouter) surfaces loudly.

Old ``(True, True)``  → ``AnthropicInlineCacheStrategy(layout="native")``
Old ``(True, False)`` → ``AnthropicInlineCacheStrategy(layout="envelope")``
Old ``(False, False)`` → ``NoCacheStrategy``
"""

from __future__ import annotations

import pytest

from agent.prompt_cache_strategy import AnthropicInlineCacheStrategy, NoCacheStrategy
from providers import get_provider_profile


# ── helpers ──────────────────────────────────────────────────────────────────


def _strategy(provider_id: str, model: str):
    """Return the cache strategy for a provider/model pair via the profile."""
    profile = get_provider_profile(provider_id)
    assert profile is not None, f"provider '{provider_id}' not found in registry"
    return profile.cache_strategy_for(model)


def _is_native(strategy) -> bool:
    return isinstance(strategy, AnthropicInlineCacheStrategy) and strategy.layout == "native"


def _is_envelope(strategy) -> bool:
    return isinstance(strategy, AnthropicInlineCacheStrategy) and strategy.layout == "envelope"


def _is_no_cache(strategy) -> bool:
    return isinstance(strategy, NoCacheStrategy)


# ── Native Anthropic ──────────────────────────────────────────────────────────


class TestNativeAnthropic:
    def test_claude_on_native_anthropic_caches_with_native_layout(self):
        s = _strategy("anthropic", "claude-sonnet-4-6")
        assert _is_native(s), f"expected native layout, got {s!r}"

    def test_claude_opus_on_anthropic_caches_with_native_layout(self):
        s = _strategy("anthropic", "claude-opus-4.6")
        assert _is_native(s)

    def test_non_claude_on_anthropic_profile_does_not_cache(self):
        # Anthropic profile's strategy is scoped to Claude models.
        s = _strategy("anthropic", "gpt-5.4")
        assert _is_no_cache(s)

    def test_unknown_provider_anthropic_wire_claude_gets_fallback(self):
        """Unknown/custom provider on anthropic_messages transport with Claude
        model is handled by the conversation_loop fallback, not a profile.

        This documents the expected strategy the fallback would inject.
        """
        from agent.prompt_cache_strategy import NoCacheStrategy
        unknown_profile = get_provider_profile("nonexistent_provider_xyz")
        # The profile for an unknown provider is None (or returns NoCacheStrategy).
        # The conversation_loop fallback upgrades NoCacheStrategy to native for
        # api_mode="anthropic_messages" + claude model — that upgrade is tested
        # in tests/agent/test_conversation_loop_caching.py.
        if unknown_profile is not None:
            s = unknown_profile.cache_strategy_for("claude-sonnet-4-6")
            assert _is_no_cache(s), (
                "Unknown providers must return NoCacheStrategy so the "
                "conversation_loop fallback can upgrade it conditionally"
            )


# ── OpenRouter ────────────────────────────────────────────────────────────────


class TestOpenRouter:
    def test_claude_on_openrouter_caches_with_envelope_layout(self):
        s = _strategy("openrouter", "anthropic/claude-sonnet-4.6")
        assert _is_envelope(s), f"expected envelope layout, got {s!r}"

    def test_claude_shortname_on_openrouter_caches(self):
        s = _strategy("openrouter", "claude-sonnet-4-6")
        assert _is_envelope(s)

    def test_non_claude_on_openrouter_does_not_cache(self):
        s = _strategy("openrouter", "openai/gpt-5.4")
        assert _is_no_cache(s)

    def test_qwen_on_openrouter_does_not_cache(self):
        # Qwen via OpenRouter falls through — OpenRouter has its own
        # upstream caching arrangement (provider-dependent).
        s = _strategy("openrouter", "qwen/qwen3-coder")
        assert _is_no_cache(s)


# ── MiniMax (Anthropic-compatible endpoint) ───────────────────────────────────


class TestMiniMaxAnthropicWire:
    """MiniMax's own model family and Claude on its Anthropic-compatible endpoint.

    Both minimax and minimax-cn always use api_mode='anthropic_messages'.
    cache_control support: 0.1× read pricing, 5-minute TTL.
    Docs: https://platform.minimax.io/docs/api-reference/anthropic-api-compatible-cache
    """

    def test_minimax_m27_on_provider_minimax_caches_native_layout(self):
        s = _strategy("minimax", "minimax-m2.7")
        assert _is_native(s)

    def test_minimax_m25_on_provider_minimax_cn_caches_native_layout(self):
        s = _strategy("minimax-cn", "minimax-m2.5")
        assert _is_native(s)

    def test_claude_on_minimax_caches_native_layout(self):
        s = _strategy("minimax", "claude-sonnet-4-6")
        assert _is_native(s)

    def test_unrecognised_model_on_minimax_does_not_cache(self):
        s = _strategy("minimax", "gpt-5.4")
        assert _is_no_cache(s)


# ── Nous Portal ───────────────────────────────────────────────────────────────


class TestNousPortal:
    def test_claude_on_nous_caches_with_envelope_layout(self):
        s = _strategy("nous", "anthropic/claude-sonnet-4.6")
        assert _is_envelope(s)

    def test_qwen_on_nous_portal_caches_with_envelope_layout(self):
        s = _strategy("nous", "qwen3.6-plus")
        assert _is_envelope(s)

    def test_qwen_vendored_slug_on_nous_portal_caches(self):
        s = _strategy("nous", "qwen/qwen3.6-plus")
        assert _is_envelope(s)

    def test_non_qwen_non_claude_on_nous_portal_does_not_cache(self):
        s = _strategy("nous", "openai/gpt-5.4")
        assert _is_no_cache(s)


# ── Qwen / Alibaba family ─────────────────────────────────────────────────────


class TestQwenAlibabaFamily:
    """Qwen on OpenCode/OpenCode-Go/Alibaba — needs cache_control even on OpenAI-wire.

    Upstream pi-mono #3392 / #3393 documented that these providers serve
    zero cache hits without Anthropic-style markers. Envelope layout, not
    native, because the wire format is OpenAI chat.completions.
    """

    def test_qwen_on_opencode_go_caches_with_envelope_layout(self):
        s = _strategy("opencode-go", "qwen3.6-plus")
        assert _is_envelope(s), f"expected envelope layout, got {s!r}"

    def test_qwen35_plus_on_opencode_go(self):
        s = _strategy("opencode-go", "qwen3.5-plus")
        assert _is_envelope(s)

    def test_qwen_on_opencode_zen_caches(self):
        s = _strategy("opencode", "qwen3-coder-plus")
        assert _is_envelope(s)

    def test_qwen_on_direct_alibaba_caches(self):
        s = _strategy("alibaba", "qwen3-coder")
        assert _is_envelope(s)

    def test_non_qwen_on_opencode_go_does_not_cache(self):
        s = _strategy("opencode-go", "glm-5")
        assert _is_no_cache(s)

    def test_kimi_on_opencode_go_does_not_cache(self):
        s = _strategy("opencode-go", "kimi-k2.5")
        assert _is_no_cache(s)


# ── Custom / unknown providers ────────────────────────────────────────────────


class TestCustomOpenAIWireProvider:
    """A custom provider using chat_completions (OpenAI wire) has no profile entry,
    so cache_strategy_for defaults to NoCacheStrategy from ProviderProfile base.

    Sending cache_control fields in OpenAI-wire JSON can trip strict providers
    that reject unknown keys (#9621). The profile default stays off unless the
    provider is explicitly registered with a cache strategy.
    """

    def test_unknown_custom_provider_returns_none_profile(self):
        profile = get_provider_profile("completely_unknown_custom")
        assert profile is None


# ── Strategy contract (smoke-test apply() callable) ──────────────────────────


class TestStrategiesAreCallable:
    """Smoke-tests that the returned strategies are actually callable."""

    @pytest.fixture
    def sample_messages(self):
        return [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]

    def test_anthropic_native_strategy_apply_returns_messages(self, sample_messages):
        from agent.prompt_cache_strategy import PromptCacheIntent
        s = _strategy("anthropic", "claude-sonnet-4-6")
        result = s.apply(sample_messages, PromptCacheIntent())
        assert isinstance(result, list)

    def test_openrouter_envelope_strategy_apply_returns_messages(self, sample_messages):
        from agent.prompt_cache_strategy import PromptCacheIntent
        s = _strategy("openrouter", "anthropic/claude-sonnet-4.6")
        result = s.apply(sample_messages, PromptCacheIntent())
        assert isinstance(result, list)

    def test_no_cache_strategy_apply_is_identity(self, sample_messages):
        from agent.prompt_cache_strategy import PromptCacheIntent
        s = _strategy("openrouter", "openai/gpt-5.4")  # returns NoCacheStrategy
        result = s.apply(sample_messages, PromptCacheIntent())
        assert result == sample_messages
