"""Tests for save_config_value() in cli.py — atomic write behavior."""

from pathlib import Path
from unittest.mock import MagicMock

import yaml

import pytest


class TestSaveConfigValueAtomic:
    """save_config_value() must use atomic round-trip YAML updates."""

    @pytest.fixture
    def config_env(self, tmp_path, monkeypatch):
        """Isolated config environment with a writable config.yaml."""
        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        config_path = hermes_home / "config.yaml"
        config_path.write_text(yaml.dump({
            "model": {"default": "test-model", "provider": "openrouter"},
            "display": {"skin": "default"},
        }))
        monkeypatch.setattr("cli._hermes_home", hermes_home)
        return config_path

    def test_calls_roundtrip_yaml_update(self, config_env, monkeypatch):
        """save_config_value must preserve user-edited YAML structure."""
        mock_update = MagicMock()
        monkeypatch.setattr("utils.atomic_roundtrip_yaml_update", mock_update)

        from cli import save_config_value
        save_config_value("display.skin", "mono")

        mock_update.assert_called_once_with(config_env, "display.skin", "mono")

    def test_preserves_existing_keys(self, config_env):
        """Writing a new key must not clobber existing config entries."""
        from cli import save_config_value
        save_config_value("agent.max_turns", 50)

        result = yaml.safe_load(config_env.read_text())
        assert result["model"]["default"] == "test-model"
        assert result["model"]["provider"] == "openrouter"
        assert result["display"]["skin"] == "default"
        assert result["agent"]["max_turns"] == 50

    def test_creates_nested_keys(self, config_env):
        """Dot-separated paths create intermediate dicts as needed."""
        from cli import save_config_value
        save_config_value("auxiliary.compression.model", "google/gemini-3-flash-preview")

        result = yaml.safe_load(config_env.read_text())
        assert result["auxiliary"]["compression"]["model"] == "google/gemini-3-flash-preview"

    def test_overwrites_existing_value(self, config_env):
        """Updating an existing key replaces the value."""
        from cli import save_config_value
        save_config_value("display.skin", "ares")

        result = yaml.safe_load(config_env.read_text())
        assert result["display"]["skin"] == "ares"

    def test_preserves_env_ref_templates_in_unrelated_fields(self, config_env):
        """The /model --global persistence path must not inline env-backed secrets."""
        config_env.write_text(yaml.dump({
            "custom_providers": [{
                "name": "tuzi",
                "api_key": "${TU_ZI_API_KEY}",
                "model": "claude-opus-4-6",
            }],
            "model": {"default": "test-model", "provider": "openrouter"},
        }))

        from cli import save_config_value
        save_config_value("model.default", "doubao-pro")

        result = yaml.safe_load(config_env.read_text())
        assert result["model"]["default"] == "doubao-pro"
        assert result["custom_providers"][0]["api_key"] == "${TU_ZI_API_KEY}"

    def test_preserves_comments_after_config_mutation(self, config_env):
        """CLI config writes should not strip existing user comments."""
        config_env.write_text(
            "# user selected model\n"
            "model:\n"
            "  # keep this provider note\n"
            "  provider: openrouter\n"
            "display:\n"
            "  skin: default  # inline skin note\n",
            encoding="utf-8",
        )

        from cli import save_config_value
        save_config_value("display.skin", "mono")

        text = config_env.read_text(encoding="utf-8")
        result = yaml.safe_load(text)
        assert result["display"]["skin"] == "mono"
        assert "# user selected model" in text
        assert "# keep this provider note" in text
        assert "# inline skin note" in text

    def test_preserves_readable_unicode_after_config_mutation(self, config_env):
        """Non-ASCII prompts should remain readable instead of \\u-escaped."""
        config_env.write_text(
            "agent:\n"
            "  system_prompt: 你好，保持中文输出\n"
            "display:\n"
            "  skin: default\n",
            encoding="utf-8",
        )

        from cli import save_config_value
        save_config_value("display.skin", "mono")

        text = config_env.read_text(encoding="utf-8")
        result = yaml.safe_load(text)
        assert result["agent"]["system_prompt"] == "你好，保持中文输出"
        assert "你好，保持中文输出" in text
        assert "\\u4f60" not in text

    def test_file_not_truncated_on_error(self, config_env, monkeypatch):
        """If atomic_yaml_write raises, the original file is untouched."""
        original_content = config_env.read_text()

        def exploding_write(*args, **kwargs):
            raise OSError("disk full")

        monkeypatch.setattr("utils.atomic_roundtrip_yaml_update", exploding_write)

        from cli import save_config_value
        result = save_config_value("display.skin", "broken")

        assert result is False
        assert config_env.read_text() == original_content


class TestSaveConfigValueWriteTarget:
    """save_config_value() must always write to user config, never repo config."""

    def test_writes_to_user_config_when_it_does_not_exist(self, tmp_path, monkeypatch):
        """When ~/.hermes/config.yaml doesn't exist yet, create it there
        instead of falling back to the repo's cli-config.yaml (#14714)."""
        hermes_home = tmp_path / ".hermes"
        # Do NOT create hermes_home or config.yaml — simulate first run
        monkeypatch.setattr("cli._hermes_home", hermes_home)

        from cli import save_config_value
        result = save_config_value("model.default", "gpt-5")

        assert result is True
        user_config = hermes_home / "config.yaml"
        assert user_config.exists(), "config.yaml must be created in ~/.hermes/"
        saved = yaml.safe_load(user_config.read_text())
        assert saved["model"]["default"] == "gpt-5"

    def test_does_not_write_to_repo_config(self, tmp_path, monkeypatch):
        """Repo cli-config.yaml must never be modified by save_config_value."""
        hermes_home = tmp_path / ".hermes"
        # No user config — triggers the old bug path
        monkeypatch.setattr("cli._hermes_home", hermes_home)

        repo_config = Path(__file__).resolve().parent.parent.parent / "cli-config.yaml"
        if repo_config.exists():
            original_content = repo_config.read_text()
        else:
            original_content = None

        from cli import save_config_value
        save_config_value("test_sentinel.value", "should-not-appear-in-repo")

        if original_content is not None:
            assert repo_config.read_text() == original_content, \
                "repo cli-config.yaml was modified by save_config_value"
        # If repo config didn't exist, it still shouldn't
        # (but we only check if it was present to begin with)

    def test_value_round_trips_through_fresh_user_config(self, tmp_path, monkeypatch):
        """Value written to a new user config can be read back."""
        hermes_home = tmp_path / ".hermes"
        monkeypatch.setattr("cli._hermes_home", hermes_home)

        from cli import save_config_value
        save_config_value("agent.system_prompt", "Be helpful")
        save_config_value("display.skin", "moonsong")

        config = yaml.safe_load((hermes_home / "config.yaml").read_text())
        assert config["agent"]["system_prompt"] == "Be helpful"
        assert config["display"]["skin"] == "moonsong"
