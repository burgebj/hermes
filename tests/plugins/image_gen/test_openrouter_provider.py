#!/usr/bin/env python3
"""Tests for OpenRouter image generation provider."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch):
    """Ensure OPENROUTER_API_KEY is set for all tests."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-key")


# ---------------------------------------------------------------------------
# Provider class tests
# ---------------------------------------------------------------------------


class TestOpenRouterImageGenProvider:
    def test_name(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        assert provider.name == "openrouter"

    def test_display_name(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        assert provider.display_name == "OpenRouter"

    def test_is_available_with_key(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        assert provider.is_available() is True

    def test_is_available_without_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        assert provider.is_available() is False

    def test_list_models(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        models = provider.list_models()
        assert len(models) == 3
        model_ids = [m["id"] for m in models]
        assert "google/gemini-3.1-flash-image-preview" in model_ids
        assert "openai/gpt-5.4-image-2" in model_ids

    def test_default_model(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        assert provider.default_model() == "google/gemini-3.1-flash-image-preview"

    def test_get_setup_schema(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        schema = provider.get_setup_schema()
        assert schema["name"] == "OpenRouter"
        assert schema["badge"] == "paid"
        assert schema["env_vars"][0]["key"] == "OPENROUTER_API_KEY"


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------


class TestConfig:
    def test_default_model(self):
        from plugins.image_gen.openrouter import _resolve_model

        model_id, meta = _resolve_model()
        assert model_id == "google/gemini-3.1-flash-image-preview"
        assert meta["display"] == "Gemini 3.1 Flash Image"

    def test_env_override_model(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "openai/gpt-5.4-image-2")
        from plugins.image_gen.openrouter import _resolve_model

        model_id, meta = _resolve_model()
        assert model_id == "openai/gpt-5.4-image-2"
        assert meta["display"] == "GPT-5.4 Image 2"

    def test_invalid_env_model_falls_back(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_IMAGE_MODEL", "nonexistent/model")
        from plugins.image_gen.openrouter import _resolve_model

        model_id, _ = _resolve_model()
        assert model_id == "google/gemini-3.1-flash-image-preview"


# ---------------------------------------------------------------------------
# Image extraction tests
# ---------------------------------------------------------------------------


class TestExtractImage:
    def test_gemini_style_images_array(self):
        from plugins.image_gen.openrouter import _extract_image_from_response

        data = {
            "choices": [{
                "message": {
                    "images": [{
                        "type": "image_url",
                        "image_url": {"url": "data:image/jpeg;base64,/9j/test"}
                    }]
                }
            }]
        }
        result = _extract_image_from_response(data)
        assert result == "data:image/jpeg;base64,/9j/test"

    def test_gpt_style_content_parts(self):
        from plugins.image_gen.openrouter import _extract_image_from_response

        data = {
            "choices": [{
                "message": {
                    "content": [{
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,iVBORw0KGgo="}
                    }]
                }
            }]
        }
        result = _extract_image_from_response(data)
        assert result == "data:image/png;base64,iVBORw0KGgo="

    def test_no_choices(self):
        from plugins.image_gen.openrouter import _extract_image_from_response

        result = _extract_image_from_response({"choices": []})
        assert result is None

    def test_no_image_data(self):
        from plugins.image_gen.openrouter import _extract_image_from_response

        data = {
            "choices": [{
                "message": {"content": "Just a text response"}
            }]
        }
        result = _extract_image_from_response(data)
        assert result is None


# ---------------------------------------------------------------------------
# Generate tests
# ---------------------------------------------------------------------------


class TestGenerate:
    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        result = provider.generate(prompt="test")
        assert result["success"] is False
        assert "OPENROUTER_API_KEY" in result["error"]
        assert result["error_type"] == "auth_required"

    def test_empty_prompt(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        provider = OpenRouterImageGenProvider()
        result = provider.generate(prompt="")
        assert result["success"] is False
        assert result["error_type"] == "invalid_argument"

    def test_successful_gemini_generation(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "images": [{
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,dGVzdA=="}
                    }]
                }
            }]
        }

        with patch("plugins.image_gen.openrouter.requests.post", return_value=mock_resp):
            with patch("plugins.image_gen.openrouter.save_b64_image", return_value="/tmp/test.png"):
                provider = OpenRouterImageGenProvider()
                result = provider.generate(prompt="A cat on a router")

        assert result["success"] is True
        assert result["image"] == "/tmp/test.png"
        assert result["provider"] == "openrouter"
        assert result["model"] == "google/gemini-3.1-flash-image-preview"

    def test_api_error_response(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "error": {"message": "Rate limit exceeded", "code": 429}
        }

        with patch("plugins.image_gen.openrouter.requests.post", return_value=mock_resp):
            provider = OpenRouterImageGenProvider()
            result = provider.generate(prompt="test")

        assert result["success"] is False
        assert "Rate limit exceeded" in result["error"]
        assert result["error_type"] == "api_error"

    def test_http_error(self):
        from plugins.image_gen.openrouter import OpenRouterImageGenProvider

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("HTTP 500")

        with patch("plugins.image_gen.openrouter.requests.post", return_value=mock_resp):
            provider = OpenRouterImageGenProvider()
            result = provider.generate(prompt="test")

        assert result["success"] is False
        assert "HTTP 500" in result["error"]
