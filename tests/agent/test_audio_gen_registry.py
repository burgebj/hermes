"""Tests for agent/audio_gen_registry.py — provider registration & active lookup."""

from __future__ import annotations

import pytest

from agent import audio_gen_registry
from agent.audio_gen_provider import AudioGenProvider


class _FakeProvider(AudioGenProvider):
    def __init__(self, name: str, available: bool = True):
        self._name = name
        self._available = available

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    def generate(self, prompt, **kw):
        return {"success": True, "audio": f"{self._name}://{prompt}"}


@pytest.fixture(autouse=True)
def _reset_registry():
    audio_gen_registry._reset_for_tests()
    yield
    audio_gen_registry._reset_for_tests()


class TestRegisterProvider:
    def test_register_and_lookup(self):
        provider = _FakeProvider("fake")
        audio_gen_registry.register_provider(provider)
        assert audio_gen_registry.get_provider("fake") is provider

    def test_rejects_non_provider(self):
        with pytest.raises(TypeError):
            audio_gen_registry.register_provider("not a provider")  # type: ignore[arg-type]

    def test_rejects_empty_name(self):
        class Empty(AudioGenProvider):
            @property
            def name(self) -> str:
                return ""

            def generate(self, prompt, **kw):
                return {}

        with pytest.raises(ValueError):
            audio_gen_registry.register_provider(Empty())

    def test_reregister_overwrites(self):
        a = _FakeProvider("same")
        b = _FakeProvider("same")
        audio_gen_registry.register_provider(a)
        audio_gen_registry.register_provider(b)
        assert audio_gen_registry.get_provider("same") is b

    def test_list_is_sorted(self):
        audio_gen_registry.register_provider(_FakeProvider("zeta"))
        audio_gen_registry.register_provider(_FakeProvider("alpha"))
        names = [p.name for p in audio_gen_registry.list_providers()]
        assert names == ["alpha", "zeta"]


class TestGetActiveProvider:
    def test_single_provider_autoresolves(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        audio_gen_registry.register_provider(_FakeProvider("solo"))
        active = audio_gen_registry.get_active_provider()
        assert active is not None and active.name == "solo"

    def test_no_provider_returns_none(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        assert audio_gen_registry.get_active_provider() is None

    def test_multi_without_config_returns_none(self, tmp_path, monkeypatch):
        """Like video_gen, audio_gen has no legacy default — multiple
        providers with no config returns None and the tool surfaces a
        helpful error."""
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        audio_gen_registry.register_provider(_FakeProvider("openrouter"))
        audio_gen_registry.register_provider(_FakeProvider("other"))
        assert audio_gen_registry.get_active_provider() is None

    def test_config_selects_provider(self, tmp_path, monkeypatch):
        import yaml

        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            yaml.safe_dump({"audio_gen": {"provider": "openrouter"}})
        )
        audio_gen_registry.register_provider(_FakeProvider("other"))
        audio_gen_registry.register_provider(_FakeProvider("openrouter"))
        active = audio_gen_registry.get_active_provider()
        assert active is not None and active.name == "openrouter"

    def test_unknown_config_falls_back(self, tmp_path, monkeypatch):
        """If audio_gen.provider names a provider that isn't registered,
        the single-provider fallback still applies."""
        import yaml

        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            yaml.safe_dump({"audio_gen": {"provider": "ghost"}})
        )
        audio_gen_registry.register_provider(_FakeProvider("only"))
        active = audio_gen_registry.get_active_provider()
        assert active is not None and active.name == "only"
