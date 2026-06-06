"""Tests for the bundled Lemonade image_gen plugin (local SD inference)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


# 1x1 transparent PNG — valid bytes for save_b64_image().
_PNG_HEX = (
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c6300010000000500010d0a2db40000000049454e44"
    "ae426082"
)


def _b64_png() -> str:
    import base64
    return base64.b64encode(bytes.fromhex(_PNG_HEX)).decode()


def _fake_response(*, b64=None, url=None):
    item = {"b64_json": b64, "url": url}
    return MagicMock(
        status_code=200,
        raise_for_status=MagicMock(),
        json=MagicMock(return_value={"data": [item]}),
    )


# ---------------------------------------------------------------------------
# Provider metadata
# ---------------------------------------------------------------------------


class TestMetadata:
    def test_name(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        assert LemonadeImageGenProvider().name == "lemonade"

    def test_display_name(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        assert LemonadeImageGenProvider().display_name == "Lemonade"

    def test_list_models_has_three_entries(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        ids = [m["id"] for m in LemonadeImageGenProvider().list_models()]
        assert ids == ["SD-Turbo", "Flux-2-Klein-9B-GGUF", "Z-Image-Turbo"]

    def test_catalog_entries_have_required_fields(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        for entry in LemonadeImageGenProvider().list_models():
            assert entry["id"]
            assert entry["display"]
            assert entry["speed"]
            assert entry["strengths"]
            assert entry["price"] == "free (local)"

    def test_default_model(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider, DEFAULT_MODEL
        assert LemonadeImageGenProvider().default_model() == DEFAULT_MODEL
        assert DEFAULT_MODEL == "SD-Turbo"

    def test_get_setup_schema(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        schema = LemonadeImageGenProvider().get_setup_schema()
        assert schema["name"] == "Lemonade (local)"
        assert schema["badge"] == "free"
        # Auth is optional (the default stock lemonade server is unauthenticated),
        # so the picker should not blindly prompt for an API key.
        assert schema["env_vars"] == []


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------


class TestAvailability:
    def test_available_when_requests_importable(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        assert LemonadeImageGenProvider().is_available() is True

    def test_available_even_without_api_key(self, monkeypatch):
        """Auth is optional — provider is selectable even with no env vars set."""
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        monkeypatch.delenv("LEMONADE_API_KEY", raising=False)
        assert LemonadeImageGenProvider().is_available() is True


# ---------------------------------------------------------------------------
# Config resolution
# ---------------------------------------------------------------------------


class TestConfigResolution:
    def test_default_model_when_no_config(self, monkeypatch):
        monkeypatch.delenv("LEMONADE_IMAGE_MODEL", raising=False)
        from plugins.image_gen.lemonade import _resolve_model, DEFAULT_MODEL
        model_id, _ = _resolve_model()
        assert model_id == DEFAULT_MODEL

    def test_env_var_overrides_config(self, monkeypatch):
        monkeypatch.setenv("LEMONADE_IMAGE_MODEL", "Z-Image-Turbo")
        from plugins.image_gen.lemonade import _resolve_model
        model_id, _ = _resolve_model()
        assert model_id == "Z-Image-Turbo"

    def test_env_var_with_unknown_model_falls_through(self, monkeypatch):
        monkeypatch.setenv("LEMONADE_IMAGE_MODEL", "NotARealModel")
        from plugins.image_gen.lemonade import _resolve_model, DEFAULT_MODEL
        model_id, _ = _resolve_model()
        assert model_id == DEFAULT_MODEL

    def test_base_url_default(self, monkeypatch):
        monkeypatch.delenv("LEMONADE_BASE_URL", raising=False)
        from plugins.image_gen.lemonade import _resolve_base_url
        assert _resolve_base_url() == "http://localhost:13305/api/v1"

    def test_base_url_env_override(self, monkeypatch):
        monkeypatch.setenv("LEMONADE_BASE_URL", "http://10.0.0.5:9000/api/v1/")
        from plugins.image_gen.lemonade import _resolve_base_url
        # Trailing slash and whitespace are stripped.
        assert _resolve_base_url() == "http://10.0.0.5:9000/api/v1"


# ---------------------------------------------------------------------------
# generate() — happy path
# ---------------------------------------------------------------------------


class TestGenerateSuccess:
    def test_b64_response_saves_to_cache(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        b64 = _b64_png()
        mock_resp = _fake_response(b64=b64)

        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            with patch(
                "plugins.image_gen.lemonade.save_b64_image",
                return_value=MagicMock(__str__=lambda self: "/tmp/lemonade_test.png"),
            ) as mock_save:
                result = LemonadeImageGenProvider().generate(prompt="a corgi in space")

        assert result["success"] is True
        assert result["image"] == "/tmp/lemonade_test.png"
        assert result["provider"] == "lemonade"
        assert result["model"] == "SD-Turbo"
        assert result["prompt"] == "a corgi in space"
        assert result["aspect_ratio"] == "landscape"
        # save_b64_image was called with the b64 payload and a per-model prefix.
        assert mock_save.call_args.args[0] == b64
        assert mock_save.call_args.kwargs["prefix"].startswith("lemonade_")

    def test_url_response_uses_cache_url_bytes(self):
        """URL fallback must be cached locally, not returned as-is."""
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        mock_resp = _fake_response(url="https://lemonade.local/tmp/abc.png")

        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            with patch(
                "plugins.image_gen.lemonade._cache_url_bytes",
                return_value=MagicMock(__str__=lambda self: "/tmp/cached.png"),
            ) as mock_cache:
                result = LemonadeImageGenProvider().generate(prompt="a corgi in space")

        assert result["success"] is True
        assert result["image"] == "/tmp/cached.png"
        assert mock_cache.call_args.args[0] == "https://lemonade.local/tmp/abc.png"
        assert mock_cache.call_args.kwargs["prefix"].startswith("lemonade_")

    def test_url_response_falls_back_to_bare_url_if_cache_fails(self):
        """If _cache_url_bytes raises, the bare URL is returned (with a warning logged)."""
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        mock_resp = _fake_response(url="https://lemonade.local/tmp/abc.png")

        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            with patch(
                "plugins.image_gen.lemonade._cache_url_bytes",
                side_effect=ValueError("expired"),
            ):
                result = LemonadeImageGenProvider().generate(prompt="x")

        # Falls back to the raw URL rather than failing the call.
        assert result["success"] is True
        assert result["image"] == "https://lemonade.local/tmp/abc.png"

    def test_payload_carries_aspect_size(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        mock_resp = _fake_response(b64=_b64_png())
        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp) as mock_post:
            with patch("plugins.image_gen.lemonade.save_b64_image", return_value="/tmp/x.png"):
                LemonadeImageGenProvider().generate(prompt="x", aspect_ratio="square")

        payload = mock_post.call_args.kwargs["json"]
        assert payload["model"] == "SD-Turbo"
        assert payload["prompt"] == "x"
        # Default bumped to 1024 in this PR.
        assert payload["size"] == "1024x1024"
        assert payload["response_format"] == "b64_json"
        assert payload["steps"] == 4
        assert payload["cfg_scale"] == 1.0

    def test_extra_carries_steps_and_cfg(self):
        """``success_response`` merges the extra dict into the top-level payload."""
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        mock_resp = _fake_response(b64=_b64_png())
        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            with patch("plugins.image_gen.lemonade.save_b64_image", return_value="/tmp/x.png"):
                result = LemonadeImageGenProvider().generate(prompt="x")

        # Default aspect is landscape → 1024x768.
        assert result["size"] == "1024x768"
        assert result["steps"] == 4
        assert result["cfg_scale"] == 1.0


# ---------------------------------------------------------------------------
# generate() — auth (optional, no header by default)
# ---------------------------------------------------------------------------


class TestAuth:
    def test_no_auth_header_when_key_unset(self, monkeypatch):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        monkeypatch.delenv("LEMONADE_API_KEY", raising=False)

        mock_resp = _fake_response(b64=_b64_png())
        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp) as mock_post:
            with patch("plugins.image_gen.lemonade.save_b64_image", return_value="/tmp/x.png"):
                LemonadeImageGenProvider().generate(prompt="x")

        headers = mock_post.call_args.kwargs["headers"]
        assert "Authorization" not in headers

    def test_bearer_header_when_key_set(self, monkeypatch):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        monkeypatch.setenv("LEMONADE_API_KEY", "test-key")

        mock_resp = _fake_response(b64=_b64_png())
        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp) as mock_post:
            with patch("plugins.image_gen.lemonade.save_b64_image", return_value="/tmp/x.png"):
                LemonadeImageGenProvider().generate(prompt="x")

        headers = mock_post.call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer test-key"


# ---------------------------------------------------------------------------
# generate() — error paths
# ---------------------------------------------------------------------------


class TestGenerateErrors:
    def test_empty_prompt_is_invalid_argument(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        result = LemonadeImageGenProvider().generate(prompt="   ")
        assert result["success"] is False
        assert result["error_type"] == "invalid_argument"
        assert result["provider"] == "lemonade"

    def test_no_api_key_still_works(self, monkeypatch):
        """Regression: API key must not be required (stock lemonade has no auth)."""
        from plugins.image_gen.lemonade import LemonadeImageGenProvider
        monkeypatch.delenv("LEMONADE_API_KEY", raising=False)

        mock_resp = _fake_response(b64=_b64_png())
        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            with patch("plugins.image_gen.lemonade.save_b64_image", return_value="/tmp/x.png"):
                result = LemonadeImageGenProvider().generate(prompt="x")

        assert result["success"] is True

    def test_timeout(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        with patch(
            "plugins.image_gen.lemonade.requests.post",
            side_effect=__import__("requests").Timeout,
        ):
            result = LemonadeImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "timeout"
        assert "300s" in result["error"]

    def test_connection_error(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        with patch(
            "plugins.image_gen.lemonade.requests.post",
            side_effect=__import__("requests").ConnectionError("refused"),
        ):
            result = LemonadeImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "connection_error"
        assert "refused" in result["error"]

    def test_http_error_extracts_status_and_message(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        response = MagicMock()
        response.status_code = 422
        response.text = "bad prompt"
        response.json.return_value = {"error": {"message": "prompt too long"}}
        response.raise_for_status.side_effect = __import__("requests").HTTPError(response=response)

        with patch("plugins.image_gen.lemonade.requests.post", return_value=response):
            result = LemonadeImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "api_error"
        assert "422" in result["error"]
        assert "prompt too long" in result["error"]

    def test_empty_data_list(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": []}

        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            result = LemonadeImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "empty_response"

    def test_neither_b64_nor_url(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"data": [{}]}

        with patch("plugins.image_gen.lemonade.requests.post", return_value=mock_resp):
            result = LemonadeImageGenProvider().generate(prompt="x")

        assert result["success"] is False
        assert result["error_type"] == "empty_response"
        assert "neither" in result["error"]


# ---------------------------------------------------------------------------
# Plugin registration
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_register_calls_register_image_gen_provider(self):
        from plugins.image_gen.lemonade import LemonadeImageGenProvider, register

        mock_ctx = MagicMock()
        register(mock_ctx)
        mock_ctx.register_image_gen_provider.assert_called_once()
        provider = mock_ctx.register_image_gen_provider.call_args.args[0]
        assert isinstance(provider, LemonadeImageGenProvider)
        assert provider.name == "lemonade"
