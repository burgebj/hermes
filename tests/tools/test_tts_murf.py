"""Tests for Murf TTS provider behavior in tools/tts_tool.py."""

from __future__ import annotations

import base64
from enum import Enum
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import types
import sys

import pytest


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for key in ("MURF_API_KEY", "MURF_REGION", "HERMES_SESSION_PLATFORM"):
        monkeypatch.delenv(key, raising=False)


class _MurfRegion(Enum):
    DEFAULT = "default"
    GLOBAL = "global"


class _FakeTextToSpeech:
    def __init__(self, audio_bytes: bytes):
        self.audio_bytes = audio_bytes
        self.generate_calls = []
        self.stream_calls = []

    def generate(self, **kwargs):
        self.generate_calls.append(kwargs)
        return SimpleNamespace(encoded_audio=base64.b64encode(self.audio_bytes).decode(), audio_file=None)

    def stream(self, **kwargs):
        self.stream_calls.append(kwargs)
        return [self.audio_bytes]


class _FakeMurf:
    instances: list["_FakeMurf"] = []

    def __init__(self, api_key: str, region):
        self.api_key = api_key
        self.region = region
        self.text_to_speech = _FakeTextToSpeech(audio_bytes=b"murf-audio")
        _FakeMurf.instances.append(self)


def test_validate_murf_audio_url_accepts_https_subdomains():
    from tools.tts_tool import _validate_murf_audio_url

    assert _validate_murf_audio_url("https://global.api.murf.ai/audio.mp3") == "https://global.api.murf.ai/audio.mp3"
    assert _validate_murf_audio_url("https://murf.ai/audio.mp3") == "https://murf.ai/audio.mp3"


def test_validate_murf_audio_url_rejects_non_https():
    from tools.tts_tool import _validate_murf_audio_url

    with pytest.raises(RuntimeError, match="only https"):
        _validate_murf_audio_url("http://api.murf.ai/audio.mp3")


def test_validate_murf_audio_url_rejects_untrusted_hosts():
    from tools.tts_tool import _validate_murf_audio_url

    with pytest.raises(RuntimeError, match="untrusted host"):
        _validate_murf_audio_url("https://example.com/audio.mp3")


def test_gen2_forces_default_region_and_writes_audio(tmp_path, monkeypatch):
    from tools.tts_tool import _generate_murf_tts

    monkeypatch.setenv("MURF_API_KEY", "murf-key")
    _FakeMurf.instances = []
    monkeypatch.setattr("tools.tts_tool._import_murf_sdk", lambda: (_FakeMurf, _MurfRegion))

    out = str(tmp_path / "out.mp3")
    cfg = {"murf": {"model": "GEN2", "region": "GLOBAL", "voice_id": "en-US-natalie"}}
    result = _generate_murf_tts("hello", out, cfg)

    assert result == out
    assert (tmp_path / "out.mp3").read_bytes() == b"murf-audio"
    assert _FakeMurf.instances[0].region == _MurfRegion.DEFAULT
    call = _FakeMurf.instances[0].text_to_speech.generate_calls[0]
    assert call["model_version"] == "GEN2"


def test_falcon_keeps_selected_region(tmp_path, monkeypatch):
    from tools.tts_tool import _generate_murf_tts

    monkeypatch.setenv("MURF_API_KEY", "murf-key")
    _FakeMurf.instances = []
    monkeypatch.setattr("tools.tts_tool._import_murf_sdk", lambda: (_FakeMurf, _MurfRegion))

    out = str(tmp_path / "out.mp3")
    cfg = {"murf": {"model": "FALCON", "region": "GLOBAL", "voice_id": "en-US-natalie"}}
    _generate_murf_tts("hello", out, cfg)

    assert _FakeMurf.instances[0].region == _MurfRegion.GLOBAL
    stream_call = _FakeMurf.instances[0].text_to_speech.stream_calls[0]
    assert stream_call["model"] == "FALCON"


def test_speaking_rate_and_sample_rate_forwarded_to_sdk(tmp_path, monkeypatch):
    from tools.tts_tool import _generate_murf_tts

    monkeypatch.setenv("MURF_API_KEY", "murf-key")
    _FakeMurf.instances = []
    monkeypatch.setattr("tools.tts_tool._import_murf_sdk", lambda: (_FakeMurf, _MurfRegion))

    out = str(tmp_path / "out.mp3")
    cfg = {"murf": {"model": "GEN2", "voice_id": "en-US-natalie", "speaking_rate": 5, "sampleRate": 24000}}
    _generate_murf_tts("hello", out, cfg)

    call = _FakeMurf.instances[0].text_to_speech.generate_calls[0]
    assert call["rate"] == 5
    assert call["sample_rate"] == 24000


def test_legacy_rate_alias_still_forwarded_to_sdk(tmp_path, monkeypatch):
    from tools.tts_tool import _generate_murf_tts

    monkeypatch.setenv("MURF_API_KEY", "murf-key")
    _FakeMurf.instances = []
    monkeypatch.setattr("tools.tts_tool._import_murf_sdk", lambda: (_FakeMurf, _MurfRegion))

    out = str(tmp_path / "out.mp3")
    cfg = {"murf": {"model": "GEN2", "voice_id": "en-US-natalie", "rate": -7}}
    _generate_murf_tts("hello", out, cfg)

    call = _FakeMurf.instances[0].text_to_speech.generate_calls[0]
    assert call["rate"] == -7


def test_fallback_audio_url_uses_validator(tmp_path, monkeypatch):
    from tools.tts_tool import _generate_murf_tts

    monkeypatch.setenv("MURF_API_KEY", "murf-key")

    class _UrlTextToSpeech:
        def generate(self, **kwargs):
            return SimpleNamespace(encoded_audio=None, audio_file="https://api.murf.ai/audio.mp3")

        def stream(self, **kwargs):
            return []

    class _UrlMurf:
        def __init__(self, api_key: str, region):
            self.text_to_speech = _UrlTextToSpeech()

    monkeypatch.setattr("tools.tts_tool._import_murf_sdk", lambda: (_UrlMurf, _MurfRegion))
    mock_resp = MagicMock()
    mock_resp.content = b"url-audio"
    mock_resp.raise_for_status = MagicMock()

    out = str(tmp_path / "out.mp3")
    with patch("requests.get", return_value=mock_resp) as mock_get:
        _generate_murf_tts("hello", out, {"murf": {"model": "GEN2", "voice_id": "en-US-natalie"}})

    assert (tmp_path / "out.mp3").read_bytes() == b"url-audio"
    mock_get.assert_called_once_with("https://api.murf.ai/audio.mp3", timeout=60)


def test_import_murf_sdk_uses_lazy_deps(monkeypatch):
    from tools import tts_tool

    calls = []
    monkeypatch.setattr("tools.lazy_deps.ensure", lambda name, prompt=False: calls.append((name, prompt)))

    fake_murf_mod = types.ModuleType("murf")
    fake_region_mod = types.ModuleType("murf.region")

    class _DummyMurf:
        pass

    class _DummyRegion:
        DEFAULT = "default"

    fake_murf_mod.Murf = _DummyMurf
    fake_region_mod.MurfRegion = _DummyRegion

    monkeypatch.setitem(sys.modules, "murf", fake_murf_mod)
    monkeypatch.setitem(sys.modules, "murf.region", fake_region_mod)

    Murf, MurfRegion = tts_tool._import_murf_sdk()
    assert Murf is _DummyMurf
    assert MurfRegion is _DummyRegion
    assert calls == [("tts.murf", False)]
