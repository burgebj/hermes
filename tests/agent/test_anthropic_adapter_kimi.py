"""Tests for Kimi Coding /v1 stripping in anthropic_adapter.

Refs: https://www.kimi.com/code/docs/en/
"""

from unittest.mock import patch

import pytest

from agent.anthropic_adapter import _is_kimi_coding_endpoint, build_anthropic_client


class TestIsKimiCodingEndpoint:
    def test_detects_coding_without_v1(self):
        assert _is_kimi_coding_endpoint("https://api.kimi.com/coding") is True

    def test_detects_coding_with_v1(self):
        assert _is_kimi_coding_endpoint("https://api.kimi.com/coding/v1") is True

    def test_detects_coding_with_trailing_slash(self):
        assert _is_kimi_coding_endpoint("https://api.kimi.com/coding/") is True

    def test_rejects_anthropic_com(self):
        assert _is_kimi_coding_endpoint("https://api.anthropic.com") is False

    def test_rejects_minimax(self):
        assert _is_kimi_coding_endpoint("https://api.minimax.io/anthropic") is False

    def test_rejects_none(self):
        assert _is_kimi_coding_endpoint(None) is False


class TestBuildAnthropicClientKimiStripping:
    def test_strips_v1_for_kimi(self):
        """Kimi Coding URL with /v1 → stripped to /coding."""
        with patch("agent.anthropic_adapter._anthropic_sdk") as mock_sdk:
            build_anthropic_client(
                "sk-kimi-test-key",
                base_url="https://api.kimi.com/coding/v1",
            )
            kwargs = mock_sdk.Anthropic.call_args[1]
            assert kwargs["base_url"] == "https://api.kimi.com/coding"
            assert kwargs["default_headers"]["User-Agent"] == "claude-code/0.1.0"

    def test_without_v1_unchanged(self):
        """Kimi Coding URL without /v1 → preserved as-is."""
        with patch("agent.anthropic_adapter._anthropic_sdk") as mock_sdk:
            build_anthropic_client(
                "sk-kimi-test-key",
                base_url="https://api.kimi.com/coding",
            )
            kwargs = mock_sdk.Anthropic.call_args[1]
            assert kwargs["base_url"] == "https://api.kimi.com/coding"

    def test_preserves_non_kimi_url(self):
        """Non-Kimi endpoints (e.g. Anthropic native) are untouched."""
        with patch("agent.anthropic_adapter._anthropic_sdk") as mock_sdk:
            build_anthropic_client(
                "sk-ant-api03-test",
                base_url="https://api.anthropic.com",
            )
            kwargs = mock_sdk.Anthropic.call_args[1]
            assert kwargs["base_url"] == "https://api.anthropic.com"
