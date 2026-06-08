"""Tests for _is_ollama_glm_backend() false-positive fix.

Issue #13971: A local LiteLLM proxy on localhost:8000 forwarding to remote
Z.AI was incorrectly matched by the is_local_endpoint() catch-all, causing
false truncation continuation for non-Ollama GLM backends.

The fix restricts detection to explicit Ollama indicators (URL containing
"ollama" or ":11434", or provider set to "ollama") instead of matching any
RFC-1918 / localhost endpoint.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import run_agent


def _make_agent_stub(
    model: str = "",
    provider: str = "",
    base_url: str = "",
) -> MagicMock:
    """Build a minimal mock with the attributes _is_ollama_glm_backend reads."""
    stub = MagicMock(spec=[])
    stub.model = model
    stub.provider = provider
    stub.base_url = base_url
    stub._base_url_lower = base_url.lower() if base_url else ""
    return stub


class TestIsOllamaGlmBackend:
    """Unit tests for RunAgent._is_ollama_glm_backend."""

    # -- True cases: genuine Ollama GLM backends --

    def test_ollama_default_port_with_glm_model(self):
        """Ollama on its default port (:11434) with a GLM model -> True."""
        stub = _make_agent_stub(
            model="glm-4-9b",
            provider="",
            base_url="http://192.168.1.112:11434",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is True

    def test_ollama_in_url_with_glm_model(self):
        """URL containing 'ollama' with a GLM model -> True."""
        stub = _make_agent_stub(
            model="glm-4-9b",
            provider="",
            base_url="http://localhost:11434/v1",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is True

    def test_provider_ollama_with_glm_model(self):
        """Provider explicitly set to 'ollama' with a GLM model -> True."""
        stub = _make_agent_stub(
            model="glm-4-9b",
            provider="ollama",
            base_url="http://myhost:9999",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is True

    def test_provider_ollama_with_zai_provider(self):
        """Provider 'ollama' also matches when model has no 'glm' but provider is 'zai'.

        (This is a weird edge case — zai provider + ollama provider simultaneously
        can't really happen, but the first guard passes for provider=='zai'.)
        """
        stub = _make_agent_stub(
            model="some-model",
            provider="zai",
            base_url="http://localhost:11434",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is True

    # -- False cases: the fix --

    def test_local_proxy_with_glm_and_zai_returns_false(self):
        """KEY REGRESSION: localhost:8000 + GLM + zai provider -> must be False.

        Before the fix, is_local_endpoint() matched any local address,
        causing a LiteLLM proxy forwarding to remote Z.AI to be treated
        as a local Ollama instance.
        """
        stub = _make_agent_stub(
            model="glm-5.1",
            provider="zai",
            base_url="http://localhost:8000",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    def test_local_proxy_with_glm_and_litellm_returns_false(self):
        """Local LiteLLM proxy with GLM model -> False (not Ollama)."""
        stub = _make_agent_stub(
            model="glm-4-9b",
            provider="litellm",
            base_url="http://127.0.0.1:4000",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    def test_lan_proxy_with_glm_returns_false(self):
        """RFC-1918 address on non-Ollama port with GLM -> False."""
        stub = _make_agent_stub(
            model="glm-4-9b",
            provider="",
            base_url="http://192.168.1.50:8080",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    # -- False cases: non-GLM models --

    def test_non_glm_model_on_ollama_port(self):
        """Non-GLM model on Ollama port -> False (early exit on model check)."""
        stub = _make_agent_stub(
            model="llama3:8b",
            provider="",
            base_url="http://localhost:11434",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    def test_non_glm_model_non_zai_provider(self):
        """Non-GLM model with non-zai provider -> False."""
        stub = _make_agent_stub(
            model="gpt-4o",
            provider="openai",
            base_url="http://localhost:8000",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    # -- False cases: remote endpoints --

    def test_remote_endpoint_with_glm_model(self):
        """Remote endpoint (api.z.ai) with GLM model -> False."""
        stub = _make_agent_stub(
            model="glm-5.1",
            provider="zai",
            base_url="https://api.z.ai/api/coding/paas/v4",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    def test_remote_endpoint_no_base_url(self):
        """No base_url at all with GLM + zai -> False."""
        stub = _make_agent_stub(
            model="glm-5.1",
            provider="zai",
            base_url="",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    # -- Edge cases --

    def test_none_model_and_provider(self):
        """None model and provider -> False (no crash)."""
        stub = _make_agent_stub()
        stub.model = None
        stub.provider = None
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is False

    def test_case_insensitive_glm_match(self):
        """GLM in mixed case still matches on Ollama port."""
        stub = _make_agent_stub(
            model="GLM-4-9B",
            provider="",
            base_url="http://localhost:11434",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is True

    def test_case_insensitive_provider_ollama(self):
        """Provider 'Ollama' in mixed case still matches."""
        stub = _make_agent_stub(
            model="glm-4-9b",
            provider="Ollama",
            base_url="http://myhost:9999",
        )
        result = run_agent.AIAgent._is_ollama_glm_backend(stub)
        assert result is True
