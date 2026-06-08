"""Regression tests for ``determine_api_mode`` hostname handling.

Companion to tests/hermes_cli/test_detect_api_mode_for_url.py — the same
false-positive class (custom URLs containing ``api.openai.com`` /
``api.anthropic.com`` as a path segment or host suffix) must be rejected
by ``determine_api_mode`` as well, since it's the code path used by
custom/unknown providers in ``resolve_custom_provider``.
"""

from __future__ import annotations

from hermes_cli.providers import determine_api_mode


class TestOpenAIHostHardening:
    def test_native_openai_url_is_codex_responses(self):
        assert determine_api_mode("", "https://api.openai.com/v1") == "codex_responses"

    def test_openai_host_suffix_is_not_codex(self):
        assert determine_api_mode("", "https://api.openai.com.example/v1") == "chat_completions"

    def test_openai_path_segment_is_not_codex(self):
        assert determine_api_mode("", "https://proxy.example.test/api.openai.com/v1") == "chat_completions"


class TestAnthropicHostHardening:
    def test_native_anthropic_url_is_anthropic_messages(self):
        assert determine_api_mode("", "https://api.anthropic.com") == "anthropic_messages"

    def test_anthropic_host_suffix_is_not_anthropic(self):
        assert determine_api_mode("", "https://api.anthropic.com.example/v1") == "chat_completions"

    def test_anthropic_path_segment_is_not_anthropic(self):
        # A proxy whose path contains ``api.anthropic.com`` must not be misrouted.
        # Note: the ``/anthropic`` convention for third-party gateways still wins
        # via explicit path-suffix check — see test_anthropic_path_suffix_still_wins.
        assert determine_api_mode("", "https://proxy.example.test/api.anthropic.com/v1") == "chat_completions"

    def test_anthropic_path_suffix_still_wins(self):
        # Third-party Anthropic-compatible gateways (MiniMax, Zhipu GLM, LiteLLM
        # proxies) expose the Anthropic protocol under a ``/anthropic`` suffix.
        # That convention must still resolve to anthropic_messages.
        assert determine_api_mode("", "https://api.minimax.io/anthropic") == "anthropic_messages"


class TestKnownProviderHostHardening:
    """The known-provider branch (``get_provider(provider) is not None``) must
    apply the same hostname hardening as the unknown-provider branch. These
    cases pass a REAL provider ("openai" → openrouter aggregator, transport
    openai_chat) so ``get_provider`` returns non-None and the known-provider
    branch — not the unknown one — decides the wire protocol.
    """

    def test_known_provider_native_openai_is_codex_responses(self):
        assert determine_api_mode("openai", "https://api.openai.com/v1") == "codex_responses"

    def test_known_provider_scheme_less_native_openai_is_codex_responses(self):
        # base_url_hostname normalises scheme-less hosts (urlparse with a //
        # prefix), so a scheme-less native endpoint still routes correctly —
        # i.e. no regression vs the previous substring check for this input.
        assert determine_api_mode("openai", "api.openai.com/v1") == "codex_responses"

    def test_known_provider_openai_path_segment_falls_back_to_transport(self):
        # A proxy whose path merely contains ``api.openai.com`` must not be
        # misrouted to the OpenAI Responses protocol; it resolves to the
        # provider transport default (openai_chat -> chat_completions).
        assert (
            determine_api_mode("openai", "https://gateway.example.test/api.openai.com/v1")
            == "chat_completions"
        )

    def test_known_provider_openai_lookalike_host_falls_back_to_transport(self):
        assert (
            determine_api_mode("openai", "https://api.openai.com.evil.test/v1") == "chat_completions"
        )

    def test_known_provider_anthropic_path_suffix_still_wins(self):
        # The ``/anthropic`` suffix convention must still win for known providers.
        assert (
            determine_api_mode("openai", "https://gateway.example.test/anthropic")
            == "anthropic_messages"
        )
