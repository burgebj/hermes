#!/usr/bin/env python3
"""Tests for Google Imagen + Gemini Flash Image provider."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fake_api_key(monkeypatch):
    """Ensure GEMINI_API_KEY is set for all tests; clear GOOGLE_API_KEY so
    tests that exercise key-fallback behaviour are explicit."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-12345")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def _clear_model_overrides(monkeypatch):
    """Image-gen tests assume default model selection unless overridden."""
    monkeypatch.delenv("GOOGLE_IMAGE_MODEL", raising=False)


# ---------------------------------------------------------------------------
# Provider class — surface
# ---------------------------------------------------------------------------


class TestGoogleImageGenProvider:
    def test_name(self):
        from plugins.image_gen.google import GoogleImageGenProvider

        assert GoogleImageGenProvider().name == "google"

    def test_display_name(self):
        from plugins.image_gen.google import GoogleImageGenProvider

        assert GoogleImageGenProvider().display_name == "Google (Imagen + Gemini)"

    def test_is_available_with_gemini_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "k")
        from plugins.image_gen.google import GoogleImageGenProvider

        assert GoogleImageGenProvider().is_available() is True

    def test_is_available_falls_back_to_google_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.setenv("GOOGLE_API_KEY", "k")
        from plugins.image_gen.google import GoogleImageGenProvider

        assert GoogleImageGenProvider().is_available() is True

    def test_is_available_without_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        from plugins.image_gen.google import GoogleImageGenProvider

        assert GoogleImageGenProvider().is_available() is False

    def test_list_models_includes_imagen_and_gemini(self):
        from plugins.image_gen.google import GoogleImageGenProvider

        ids = {m["id"] for m in GoogleImageGenProvider().list_models()}
        assert "imagen-4.0-fast-generate-001" in ids
        assert "imagen-4.0-ultra-generate-001" in ids
        assert "gemini-2.5-flash-image" in ids

    def test_default_model_is_fast_imagen(self):
        from plugins.image_gen.google import GoogleImageGenProvider

        assert GoogleImageGenProvider().default_model() == "imagen-4.0-fast-generate-001"

    def test_get_setup_schema(self):
        from plugins.image_gen.google import GoogleImageGenProvider

        schema = GoogleImageGenProvider().get_setup_schema()
        assert schema["name"] == "Google (Imagen + Gemini)"
        assert schema["badge"] == "paid"
        assert schema["env_vars"][0]["key"] == "GEMINI_API_KEY"
        assert "aistudio.google.com" in schema["env_vars"][0]["url"]


# ---------------------------------------------------------------------------
# Model resolution
# ---------------------------------------------------------------------------


class TestModelResolution:
    def test_default(self):
        from plugins.image_gen.google import _resolve_model

        model_id, meta = _resolve_model()
        assert model_id == "imagen-4.0-fast-generate-001"
        assert meta["endpoint"] == "predict"

    def test_env_override_to_gemini(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "gemini-2.5-flash-image")
        from plugins.image_gen.google import _resolve_model

        model_id, meta = _resolve_model()
        assert model_id == "gemini-2.5-flash-image"
        assert meta["endpoint"] == "generateContent"

    def test_env_override_unknown_falls_back(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "definitely-not-real")
        from plugins.image_gen.google import _resolve_model

        model_id, _ = _resolve_model()
        assert model_id == "imagen-4.0-fast-generate-001"


# ---------------------------------------------------------------------------
# Imagen (:predict) endpoint dispatch
# ---------------------------------------------------------------------------


class TestImagenEndpoint:
    def test_success_saves_image(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "imagen-4.0-fast-generate-001")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "predictions": [
                {"bytesBase64Encoded": "dGVzdC1pbWFnZS1kYXRh", "mimeType": "image/png"}
            ]
        }

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp) as post:
            with patch(
                "plugins.image_gen.google.save_b64_image", return_value="/tmp/google_img.png"
            ):
                result = GoogleImageGenProvider().generate(
                    prompt="a robot", aspect_ratio="landscape"
                )

        assert result["success"] is True
        assert result["image"] == "/tmp/google_img.png"
        assert result["provider"] == "google"
        assert result["model"] == "imagen-4.0-fast-generate-001"
        assert result["endpoint"] == "predict"
        assert result["aspect_ratio_sent"] == "16:9"

        called_url = post.call_args.args[0]
        assert ":predict" in called_url
        body = post.call_args.kwargs["json"]
        assert body["instances"][0]["prompt"] == "a robot"
        assert body["parameters"]["aspectRatio"] == "16:9"

    def test_aspect_ratio_mapping(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "imagen-4.0-fast-generate-001")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "predictions": [{"bytesBase64Encoded": "eA==", "mimeType": "image/png"}]
        }

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp) as post:
            with patch("plugins.image_gen.google.save_b64_image", return_value="/tmp/x.png"):
                GoogleImageGenProvider().generate(prompt="x", aspect_ratio="portrait")
        assert post.call_args.kwargs["json"]["parameters"]["aspectRatio"] == "9:16"

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp) as post:
            with patch("plugins.image_gen.google.save_b64_image", return_value="/tmp/x.png"):
                GoogleImageGenProvider().generate(prompt="x", aspect_ratio="square")
        assert post.call_args.kwargs["json"]["parameters"]["aspectRatio"] == "1:1"

    def test_api_error_returns_error_response(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "imagen-4.0-fast-generate-001")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = '{"error": {"message": "paid plan required"}}'
        mock_resp.json.return_value = {"error": {"message": "paid plan required"}}

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp):
            result = GoogleImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "api_error"
        assert "paid plan" in result["error"]

    def test_empty_predictions(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "imagen-4.0-fast-generate-001")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"predictions": []}

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp):
            result = GoogleImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "empty_response"

    def test_timeout(self, monkeypatch):
        import requests as req_lib

        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "imagen-4.0-fast-generate-001")
        from plugins.image_gen.google import GoogleImageGenProvider

        with patch("plugins.image_gen.google.requests.post", side_effect=req_lib.Timeout()):
            result = GoogleImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "timeout"


# ---------------------------------------------------------------------------
# Gemini (:generateContent) endpoint dispatch
# ---------------------------------------------------------------------------


class TestGeminiImageEndpoint:
    def test_success_inline_data(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "gemini-2.5-flash-image")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "(reasoning trace)"},
                            {"inlineData": {"mimeType": "image/png", "data": "Zm9v"}},
                        ]
                    }
                }
            ]
        }

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp) as post:
            with patch("plugins.image_gen.google.save_b64_image", return_value="/tmp/gem.png"):
                result = GoogleImageGenProvider().generate(prompt="a robot")

        assert result["success"] is True
        assert result["image"] == "/tmp/gem.png"
        assert result["model"] == "gemini-2.5-flash-image"
        assert result["endpoint"] == "generateContent"

        called_url = post.call_args.args[0]
        assert ":generateContent" in called_url
        body = post.call_args.kwargs["json"]
        assert body["contents"][0]["parts"][0]["text"] == "a robot"
        assert body["generationConfig"]["responseModalities"] == ["IMAGE"]

    def test_snake_case_inline_data_accepted(self, monkeypatch):
        """Some Gemini API revisions return ``inline_data`` instead of ``inlineData``."""
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "gemini-2.5-flash-image")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"inline_data": {"mimeType": "image/png", "data": "Zm9v"}}
                        ]
                    }
                }
            ]
        }

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp):
            with patch("plugins.image_gen.google.save_b64_image", return_value="/tmp/gem.png"):
                result = GoogleImageGenProvider().generate(prompt="x")
        assert result["success"] is True

    def test_no_image_part(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "gemini-2.5-flash-image")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "no image generated"}]}}]
        }

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp):
            result = GoogleImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "empty_response"

    def test_api_error(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "gemini-2.5-flash-image")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = '{"error": {"message": "quota exceeded"}}'
        mock_resp.json.return_value = {"error": {"message": "quota exceeded"}}

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp):
            result = GoogleImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "api_error"
        assert "quota" in result["error"]


# ---------------------------------------------------------------------------
# Auth + arg validation
# ---------------------------------------------------------------------------


class TestAuthAndValidation:
    def test_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        from plugins.image_gen.google import GoogleImageGenProvider

        result = GoogleImageGenProvider().generate(prompt="x")
        assert result["success"] is False
        assert result["error_type"] == "auth_required"
        assert "GEMINI_API_KEY" in result["error"]

    def test_empty_prompt(self):
        from plugins.image_gen.google import GoogleImageGenProvider

        result = GoogleImageGenProvider().generate(prompt="")
        assert result["success"] is False
        assert result["error_type"] == "invalid_argument"

    def test_api_key_passed_in_query_param(self, monkeypatch):
        """The plugin must pass the key via ``params={'key': ...}``, not in the URL or a header."""
        monkeypatch.setenv("GOOGLE_IMAGE_MODEL", "imagen-4.0-fast-generate-001")
        from plugins.image_gen.google import GoogleImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "predictions": [{"bytesBase64Encoded": "eA==", "mimeType": "image/png"}]
        }

        with patch("plugins.image_gen.google.requests.post", return_value=mock_resp) as post:
            with patch("plugins.image_gen.google.save_b64_image", return_value="/tmp/x.png"):
                GoogleImageGenProvider().generate(prompt="x")

        assert post.call_args.kwargs["params"] == {"key": "test-key-12345"}
        url = post.call_args.args[0]
        assert "key=" not in url, "API key should not be in the URL"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register(self):
        from plugins.image_gen.google import GoogleImageGenProvider, register

        ctx = MagicMock()
        register(ctx)
        ctx.register_image_gen_provider.assert_called_once()
        provider = ctx.register_image_gen_provider.call_args[0][0]
        assert isinstance(provider, GoogleImageGenProvider)
        assert provider.name == "google"
