from __future__ import annotations

from types import SimpleNamespace

from hermes_cli.setup import _setup_tts_provider


def test_setup_murf_fallback_to_edge_does_not_reimport_sdk(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    calls = {"count": 0}

    class _FakeMurf:
        def __init__(self, api_key: str):
            self.text_to_speech = SimpleNamespace(get_voices=lambda model: [])

    class _FakeRegion:
        DEFAULT = "default"

    def fake_import_murf_sdk():
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeMurf, _FakeRegion
        raise ImportError("second import should not happen after edge fallback")

    monkeypatch.setattr("tools.tts_tool._import_murf_sdk", fake_import_murf_sdk)
    monkeypatch.setattr("hermes_cli.setup.get_env_value", lambda _key: "")
    monkeypatch.setattr("hermes_cli.setup.save_env_value", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("hermes_cli.setup.save_config", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        "hermes_cli.setup.get_nous_subscription_features",
        lambda _cfg: SimpleNamespace(nous_auth_present=False),
    )

    def fake_prompt(question: str, default: str = "", password: bool = False):
        if question == "Murf API key for TTS":
            return ""  # force fallback
        return default

    def fake_choice(question: str, choices: list[str], default: int = 0, description=None):
        if question == "Select TTS provider:":
            return next(i for i, c in enumerate(choices) if c.startswith("Murf TTS"))
        return default

    monkeypatch.setattr("hermes_cli.setup.prompt", fake_prompt)
    monkeypatch.setattr("hermes_cli.setup.prompt_choice", fake_choice)

    config = {"tts": {"provider": "edge", "murf": {}}}
    _setup_tts_provider(config)

    assert config["tts"]["provider"] == "edge"
    assert calls["count"] == 1
