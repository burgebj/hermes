"""Realistic-shape regression tests for ProviderTransport.extract_usage().

Production-shaped fixtures (not minimal hand-crafted mocks) for each
transport's canonical usage extraction. Locks down the numeric values
the field reads produce — the method renamed from `extract_cache_stats`
to `extract_usage` and the return type changed from a dict to `Usage`
in the refactor, but the numbers it reports must match across the rename.
"""

import pytest
from types import SimpleNamespace

from agent.transports import get_transport


# ── Anthropic transport ─────────────────────────────────────────────────


@pytest.fixture
def anthropic_transport():
    import agent.transports.anthropic  # noqa: F401 — register on import
    return get_transport("anthropic_messages")


class TestAnthropicRealisticShapes:
    """Anthropic's `Usage` shape: `input_tokens`, `output_tokens`,
    `cache_read_input_tokens`, `cache_creation_input_tokens`."""

    def test_realistic_message_with_cache_hit(self, anthropic_transport):
        """Sustained-session shape: most input came from cache."""
        usage = SimpleNamespace(
            input_tokens=200,                  # net new tokens this turn
            output_tokens=150,
            cache_read_input_tokens=14_500,    # bulk of system + history
            cache_creation_input_tokens=0,
        )
        result = anthropic_transport.extract_usage(usage)
        assert result.cache_read_tokens == 14_500
        assert result.cache_write_tokens == 0
        assert result.prompt_tokens == 200       # Anthropic input_tokens is net
        assert result.completion_tokens == 150

    def test_realistic_first_turn_creates_cache(self, anthropic_transport):
        """First turn of session: cache is written, no reads yet."""
        usage = SimpleNamespace(
            input_tokens=200,
            output_tokens=300,
            cache_read_input_tokens=0,
            cache_creation_input_tokens=12_000,
        )
        result = anthropic_transport.extract_usage(usage)
        assert result.cache_read_tokens == 0
        assert result.cache_write_tokens == 12_000
        assert result.prompt_tokens == 200
        assert result.completion_tokens == 300

    def test_no_cache_fields_present_returns_zero_usage(self, anthropic_transport):
        """Some proxies omit cache fields entirely. Must coerce to 0, not raise."""
        usage = SimpleNamespace(input_tokens=500, output_tokens=200)
        result = anthropic_transport.extract_usage(usage)
        assert result.prompt_tokens == 500
        assert result.cache_read_tokens == 0
        assert result.cache_write_tokens == 0

    def test_explicit_none_cache_values_treated_as_zero(self, anthropic_transport):
        """Field exists but is None (some proxies do this). Must coerce to 0."""
        usage = SimpleNamespace(
            input_tokens=500,
            output_tokens=200,
            cache_read_input_tokens=None,
            cache_creation_input_tokens=None,
        )
        result = anthropic_transport.extract_usage(usage)
        assert result.cache_read_tokens == 0
        assert result.cache_write_tokens == 0


# ── Chat-completions transport ──────────────────────────────────────────


@pytest.fixture
def chat_transport():
    import agent.transports.chat_completions  # noqa: F401
    return get_transport("chat_completions")


class TestChatCompletionsRealisticShapes:
    """OpenAI-wire `Usage` shape: `prompt_tokens`, `completion_tokens`,
    `total_tokens`, with cache fields nested in `prompt_tokens_details`."""

    def test_openai_native_cache_hit(self, chat_transport):
        """OpenAI auto-cache: `prompt_tokens_details.cached_tokens` populated."""
        usage = SimpleNamespace(
            prompt_tokens=5_000,
            completion_tokens=200,
            total_tokens=5_200,
            prompt_tokens_details=SimpleNamespace(cached_tokens=3_500),
        )
        result = chat_transport.extract_usage(usage)
        # cache_write stays 0 — OpenAI auto-cache has no write event.
        assert result.cache_read_tokens == 3_500
        assert result.cache_write_tokens == 0
        # Gross prompt 5000 minus cache 3500 = 1500 net.
        assert result.prompt_tokens == 1_500
        assert result.completion_tokens == 200

    def test_openai_no_cache_returns_zero(self, chat_transport):
        """Plain OpenAI call with no cache hit."""
        usage = SimpleNamespace(
            prompt_tokens=1_000,
            completion_tokens=200,
            prompt_tokens_details=SimpleNamespace(cached_tokens=0),
        )
        result = chat_transport.extract_usage(usage)
        assert result.cache_read_tokens == 0
        assert result.prompt_tokens == 1_000

    def test_response_with_no_prompt_tokens_details_returns_zero(self, chat_transport):
        """Some proxies don't include prompt_tokens_details at all."""
        usage = SimpleNamespace(
            prompt_tokens=1_000,
            completion_tokens=200,
            total_tokens=1_200,
        )
        result = chat_transport.extract_usage(usage)
        assert result.cache_read_tokens == 0
        assert result.prompt_tokens == 1_000

    def test_response_with_cache_write_populated(self, chat_transport):
        """Some proxies surface cache_write_tokens on details (mirroring
        Anthropic's cache_creation_input_tokens). Must read both."""
        usage = SimpleNamespace(
            prompt_tokens=1_000,
            completion_tokens=200,
            prompt_tokens_details=SimpleNamespace(
                cached_tokens=600,
                cache_write_tokens=150,
            ),
        )
        result = chat_transport.extract_usage(usage)
        assert result.cache_read_tokens == 600
        assert result.cache_write_tokens == 150
        # Gross 1000 minus 600 minus 150 = 250.
        assert result.prompt_tokens == 250


# ── Codex Responses-API transport ───────────────────────────────────────
#
# The Codex transport currently has NO extract_cache_stats() override —
# it inherits the base class no-op. That's a real coverage gap: every
# Codex Responses session reports $0 cache hits to telemetry.
#
# This class documents the expected behavior. Today every test here will
# return None because the base class no-op fires. PR-1 adds the impl on
# the Codex transport, and these tests will then pass with real values.


@pytest.fixture
def codex_transport():
    import agent.transports.codex  # noqa: F401
    return get_transport("codex_responses")


class TestCodexResponsesRealisticShapes:
    """Codex Responses API shape: `input_tokens`, `output_tokens`,
    `input_tokens_details.cached_tokens` + `cache_creation_tokens`.

    The transport had no extract override before this refactor; the new
    extract_usage() reads the input_tokens_details fields and subtracts
    them from gross input_tokens for the net prompt count.
    """

    def test_codex_cache_hit_with_creation(self, codex_transport):
        usage = SimpleNamespace(
            input_tokens=2_500,                  # gross total per Responses API contract
            output_tokens=300,
            input_tokens_details=SimpleNamespace(
                cached_tokens=1_500,
                cache_creation_tokens=200,
            ),
        )
        result = codex_transport.extract_usage(usage)
        assert result.cache_read_tokens == 1_500
        assert result.cache_write_tokens == 200
        # Gross 2500 minus 1500 minus 200 = 800 net input.
        assert result.prompt_tokens == 800
        assert result.completion_tokens == 300

    def test_codex_no_cache_details_returns_zero(self, codex_transport):
        usage = SimpleNamespace(input_tokens=1_000, output_tokens=200)
        result = codex_transport.extract_usage(usage)
        assert result.cache_read_tokens == 0
        assert result.cache_write_tokens == 0
        # No details → all input is net.
        assert result.prompt_tokens == 1_000
