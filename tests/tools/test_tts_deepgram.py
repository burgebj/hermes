import json
from unittest.mock import MagicMock, patch


def test_deepgram_is_builtin_with_max_length():
    from tools.tts_tool import BUILTIN_TTS_PROVIDERS, PROVIDER_MAX_TEXT_LENGTH

    assert "deepgram" in BUILTIN_TTS_PROVIDERS
    assert PROVIDER_MAX_TEXT_LENGTH["deepgram"] > 0


def test_generate_deepgram_tts_writes_mp3(tmp_path, monkeypatch):
    from tools import tts_tool

    monkeypatch.setenv("DEEPGRAM_API_KEY", "dg-test")
    output_path = str(tmp_path / "out.mp3")

    response = MagicMock()
    response.status_code = 200
    response.content = b"mp3-audio"

    captured: dict = {}

    def fake_post(url, **kwargs):
        captured["url"] = url
        captured.update(kwargs)
        return response

    with patch("requests.post", side_effect=fake_post):
        result = tts_tool._generate_deepgram_tts("Hello", output_path, {})

    assert result == output_path
    assert (tmp_path / "out.mp3").read_bytes() == b"mp3-audio"
    assert captured["url"] == "https://api.deepgram.com/v1/speak"
    assert captured["headers"]["Authorization"] == "Token dg-test"
    assert captured["headers"]["Content-Type"] == "application/json"
    assert captured["params"]["model"] == "aura-2-thalia-en"
    assert captured["json"] == {"text": "Hello"}
    assert "encoding" not in captured["params"]


def test_generate_deepgram_tts_requests_ogg_opus(tmp_path, monkeypatch):
    from tools import tts_tool

    monkeypatch.setenv("DEEPGRAM_API_KEY", "dg-test")
    output_path = str(tmp_path / "voice.ogg")

    response = MagicMock()
    response.status_code = 200
    response.content = b"ogg-opus-audio"

    captured: dict = {}

    def fake_post(url, **kwargs):
        captured.update(kwargs)
        return response

    config = {"deepgram": {"model": "aura-2-apollo-en"}}
    with patch("requests.post", side_effect=fake_post):
        tts_tool._generate_deepgram_tts("Hello", output_path, config)

    assert (tmp_path / "voice.ogg").read_bytes() == b"ogg-opus-audio"
    assert captured["params"] == {
        "model": "aura-2-apollo-en",
        "encoding": "opus",
        "container": "ogg",
    }


def test_generate_deepgram_tts_surfaces_api_error(tmp_path, monkeypatch):
    from tools import tts_tool

    monkeypatch.setenv("DEEPGRAM_API_KEY", "dg-test")
    response = MagicMock()
    response.status_code = 400
    response.text = "bad request"
    response.json.return_value = {"err_msg": "invalid voice"}

    with patch("requests.post", return_value=response):
        try:
            tts_tool._generate_deepgram_tts("Hello", str(tmp_path / "out.mp3"), {})
        except RuntimeError as exc:
            assert "invalid voice" in str(exc)
        else:
            raise AssertionError("expected RuntimeError")


def test_text_to_speech_tool_dispatches_to_deepgram(tmp_path, monkeypatch):
    from tools import tts_tool

    output_path = str(tmp_path / "out.mp3")

    def fake_generate(text, path, config):
        assert text == "Hello"
        assert path == output_path
        assert config["provider"] == "deepgram"
        with open(path, "wb") as fh:
            fh.write(b"audio")
        return path

    monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: {"provider": "deepgram"})
    monkeypatch.setattr(tts_tool, "_generate_deepgram_tts", fake_generate)

    result = json.loads(tts_tool.text_to_speech_tool("Hello", output_path=output_path))

    assert result["success"] is True
    assert result["provider"] == "deepgram"
    assert result["voice_compatible"] is False


def test_deepgram_tts_telegram_uses_native_voice_opus(tmp_path, monkeypatch):
    from tools import tts_tool

    def fake_generate(_text, path, _config):
        with open(path, "wb") as fh:
            fh.write(b"ogg")
        return path

    monkeypatch.setattr(tts_tool, "_load_tts_config", lambda: {"provider": "deepgram"})
    monkeypatch.setattr(tts_tool, "_generate_deepgram_tts", fake_generate)

    with patch("gateway.session_context.get_session_env", return_value="telegram"):
        result = json.loads(tts_tool.text_to_speech_tool("Hello"))

    assert result["success"] is True
    assert result["provider"] == "deepgram"
    assert result["file_path"].endswith(".ogg")
    assert result["voice_compatible"] is True
    assert result["media_tag"].startswith("[[audio_as_voice]]")


def test_check_tts_requirements_sees_deepgram_key(monkeypatch):
    from tools import tts_tool

    monkeypatch.setenv("DEEPGRAM_API_KEY", "dg-test")
    with patch.object(tts_tool, "_has_any_command_tts_provider", return_value=False), \
         patch.object(tts_tool, "_import_edge_tts", side_effect=ImportError), \
         patch.object(tts_tool, "_import_elevenlabs", side_effect=ImportError), \
         patch.object(tts_tool, "_import_openai_client", side_effect=ImportError), \
         patch.object(tts_tool, "_check_neutts_available", return_value=False), \
         patch.object(tts_tool, "_check_kittentts_available", return_value=False), \
         patch.object(tts_tool, "_check_piper_available", return_value=False), \
         patch.object(tts_tool, "resolve_managed_tool_gateway", return_value=None), \
         patch.object(tts_tool, "resolve_openai_audio_api_key", return_value=None), \
         patch.object(tts_tool, "resolve_xai_http_credentials", create=True, return_value={}):
        assert tts_tool.check_tts_requirements() is True
