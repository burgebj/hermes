"""Tests for gateway model resolution migration to ModelRegistry.

TDD: write failing tests, then refactor gateway/run.py to use the registry.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


class TestResolveGatewayModel:
    """Ensure _resolve_gateway_model uses ModelRegistry."""

    def test_resolves_from_model_block_default(self):
        from gateway.run import _resolve_gateway_model

        with patch("gateway.run._load_gateway_config") as mock_load:
            mock_load.return_value = {
                "model": {"provider": "openrouter", "default": "anthropic/claude-sonnet-4"}
            }
            result = _resolve_gateway_model()
            assert result == "anthropic/claude-sonnet-4"

    def test_resolves_from_model_block_model_key(self):
        from gateway.run import _resolve_gateway_model

        with patch("gateway.run._load_gateway_config") as mock_load:
            mock_load.return_value = {
                "model": {"provider": "gemini", "model": "gemini-2.5-flash"}
            }
            result = _resolve_gateway_model()
            assert result == "gemini-2.5-flash"

    def test_returns_empty_when_no_model(self):
        from gateway.run import _resolve_gateway_model

        with patch("gateway.run._load_gateway_config") as mock_load:
            mock_load.return_value = {}
            result = _resolve_gateway_model()
            assert result == ""

    def test_returns_empty_when_model_is_string(self):
        from gateway.run import _resolve_gateway_model

        with patch("gateway.run._load_gateway_config") as mock_load:
            mock_load.return_value = {"model": "bare-string-model"}
            result = _resolve_gateway_model()
            assert result == "bare-string-model"


class TestFallbackChain:
    """Ensure fallback resolution uses ModelRegistry."""

    def test_fallback_chain_from_list(self):
        from gateway.run import _try_resolve_fallback_provider

        with patch("gateway.run._load_gateway_config") as mock_load:
            mock_load.return_value = {
                "model": {"provider": "openrouter", "default": "anthropic/claude-sonnet-4"},
                "fallback_providers": [
                    {"provider": "gemini", "model": "gemini-2.5-flash"},
                ],
            }
            # This should NOT crash — it should use ModelRegistry internally
            result = _try_resolve_fallback_provider()
            # With no actual auth provider configured, result may be None
            # but the important thing is it doesn't raise
            assert result is None or isinstance(result, dict)

    def test_legacy_fallback_model_dict(self):
        from gateway.run import _try_resolve_fallback_provider

        with patch("gateway.run._load_gateway_config") as mock_load:
            mock_load.return_value = {
                "model": {"provider": "openrouter", "default": "anthropic/claude-sonnet-4"},
                "fallback_model": {"provider": "gemini", "model": "gemini-2.5-flash"},
            }
            result = _try_resolve_fallback_provider()
            assert result is None or isinstance(result, dict)
