"""Tests for Kimi/Moonshot prompt cache inclusion (issue #25970)."""
import pytest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _call_cache_policy(model: str, base_url: str, provider: str = "",
                       api_mode: str = "chat_completions"):
    """Call _anthropic_prompt_cache_policy without full AIAgent init."""
    # Import the standalone helper used by the policy
    from run_agent import AIAgent

    # Create a shell object to call the method on
    agent = object.__new__(AIAgent)
    # Set only the attributes the method reads
    agent.provider = provider
    agent.base_url = base_url
    agent.api_mode = api_mode
    agent.model = model
    return agent._anthropic_prompt_cache_policy()


class TestKimiPrefixCache:
    def test_kimi_k26_openrouter(self):
        result = _call_cache_policy(
            model="moonshotai/kimi-k2.6",
            base_url="https://openrouter.ai/api/v1",
        )
        assert result == (True, False)

    def test_kimi_k2_openrouter(self):
        result = _call_cache_policy(
            model="kimi-k2",
            base_url="https://openrouter.ai/api/v1",
        )
        assert result == (True, False)

    def test_moonshot_v1_openrouter(self):
        result = _call_cache_policy(
            model="moonshotai/moonshot-v1-8k",
            base_url="https://openrouter.ai/api/v1",
        )
        assert result == (True, False)

    def test_kimi_non_openrouter_no_caching(self):
        result = _call_cache_policy(
            model="moonshotai/kimi-k2.6",
            base_url="https://api.example.com/v1",
        )
        assert result == (False, False)

    def test_claude_openrouter_regression(self):
        result = _call_cache_policy(
            model="anthropic/claude-sonnet-4",
            base_url="https://openrouter.ai/api/v1",
        )
        assert result == (True, False)

    def test_kimi_nous_portal(self):
        result = _call_cache_policy(
            model="moonshotai/kimi-k2.6",
            base_url="https://nousresearch.com/api/v1",
        )
        assert result == (True, False)

    def test_random_model_no_caching(self):
        result = _call_cache_policy(
            model="some-random-model",
            base_url="https://api.example.com/v1",
        )
        assert result == (False, False)
