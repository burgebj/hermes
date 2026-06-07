"""Tests for Cloudflare Workers AI Aura TTS in tools/tts_tool.py."""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in (
        "CLOUDFLARE_API_TOKEN",
        "CLOUDFLARE_ACCOUNT_ID",
        "HERMES_SESSION_PLATFORM",
    ):
        monkeypatch.delenv(key, raising=False)


class TestGenerateCloudflareTts:
    def test_missing_credentials_raises_value_error(self, tmp_path):
        from tools.tts_tool import _generate_cloudflare_tts

        with pytest.raises(ValueError, match="CLOUDFLARE_API_TOKEN.*CLOUDFLARE_ACCOUNT_ID"):
            _generate_cloudflare_tts("Hello", str(tmp_path / "out.mp3"), {})

    def test_posts_to_aura_endpoint_and_writes_audio(self, tmp_path, monkeypatch):
        from tools.tts_tool import (
            DEFAULT_CLOUDFLARE_TTS_MODEL,
            DEFAULT_CLOUDFLARE_TTS_VOICE,
            _generate_cloudflare_tts,
        )

        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-token")
        monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct-123")
        response = MagicMock()
        response.content = b"mp3-bytes"
        response.raise_for_status = MagicMock()

        output_path = str(tmp_path / "out.mp3")
        with patch("requests.post", return_value=response) as mock_post:
            result = _generate_cloudflare_tts("Hello", output_path, {})

        assert result == output_path
        assert (tmp_path / "out.mp3").read_bytes() == b"mp3-bytes"
        endpoint = mock_post.call_args[0][0]
        assert endpoint == (
            "https://api.cloudflare.com/client/v4/accounts/"
            f"acct-123/ai/run/{DEFAULT_CLOUDFLARE_TTS_MODEL}"
        )
        kwargs = mock_post.call_args[1]
        assert kwargs["headers"]["Authorization"] == "Bearer cf-token"
        assert kwargs["headers"]["Content-Type"] == "application/json"
        assert kwargs["json"] == {
            "text": "Hello",
            "speaker": DEFAULT_CLOUDFLARE_TTS_VOICE,
            "encoding": "mp3",
        }

    def test_custom_model_voice_format_and_base_url(self, tmp_path, monkeypatch):
        from tools.tts_tool import _generate_cloudflare_tts

        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "cf-token")
        monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct-123")
        response = MagicMock()
        response.content = b"audio"
        response.raise_for_status = MagicMock()
        config = {
            "cloudflare": {
                "model": "@cf/deepgram/aura-2-en",
                "voice": "zeus",
                "encoding": "linear16",
                "container": "wav",
                "sample_rate": 24000,
                "bit_rate": 128000,
                "base_url": "https://cf.example/client/v4/accounts",
            }
        }

        with patch("requests.post", return_value=response) as mock_post:
            _generate_cloudflare_tts("Hi", str(tmp_path / "out.wav"), config)

        assert mock_post.call_args[0][0] == (
            "https://cf.example/client/v4/accounts/acct-123/ai/run/@cf/deepgram/aura-2-en"
        )
        assert mock_post.call_args[1]["json"] == {
            "text": "Hi",
            "speaker": "zeus",
            "encoding": "linear16",
            "container": "wav",
            "sample_rate": 24000,
            "bit_rate": 128000,
        }


class TestCloudflareInTextToSpeechTool:
    def test_cloudflare_provider_dispatches(self, tmp_path, monkeypatch):
        from tools import tts_tool

        captured = {}

        def fake_cloudflare(text, output_path, config):
            captured["text"] = text
            captured["output_path"] = output_path
            captured["config"] = config
            with open(output_path, "wb") as f:
                f.write(b"audio")
            return output_path

        monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: {"provider": "cloudflare"})
        monkeypatch.setattr(tts_tool, "_generate_cloudflare_tts", fake_cloudflare)

        result = json.loads(tts_tool.text_to_speech_tool("Hello", str(tmp_path / "out.mp3")))

        assert result["success"] is True
        assert result["provider"] == "cloudflare"
        assert captured["text"] == "Hello"


class TestCloudflareConfigWiring:
    def test_cloudflare_credentials_satisfy_tts_requirements(self, monkeypatch):
        from tools.tts_tool import check_tts_requirements

        monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "token")
        monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "acct")

        with patch("tools.tts_tool._has_any_command_tts_provider", return_value=False), \
             patch("tools.tts_tool._import_edge_tts", side_effect=ImportError), \
             patch("tools.tts_tool._import_elevenlabs", side_effect=ImportError), \
             patch("tools.tts_tool._import_openai_client", side_effect=ImportError), \
             patch("tools.tts_tool._import_mistral_client", side_effect=ImportError), \
             patch("tools.tts_tool._check_neutts_available", return_value=False), \
             patch("tools.tts_tool._check_kittentts_available", return_value=False), \
             patch("tools.tts_tool._check_piper_available", return_value=False):
            assert check_tts_requirements() is True

    def test_default_config_documents_cloudflare_provider(self):
        from hermes_cli.config import DEFAULT_CONFIG, OPTIONAL_ENV_VARS

        assert DEFAULT_CONFIG["tts"]["cloudflare"] == {
            "model": "@cf/deepgram/aura-2-en",
            "voice": "asteria",
            "encoding": "mp3",
        }
        assert OPTIONAL_ENV_VARS["CLOUDFLARE_API_TOKEN"]["password"] is True
        assert OPTIONAL_ENV_VARS["CLOUDFLARE_ACCOUNT_ID"]["password"] is False
