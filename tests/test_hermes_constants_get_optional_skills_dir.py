"""Tests for hermes_constants.get_optional_skills_dir() — optional-skills resolution."""
from pathlib import Path

from hermes_constants import get_optional_skills_dir


class TestGetOptionalSkillsDir:
    def test_uses_env_override_when_set(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_OPTIONAL_SKILLS", str(tmp_path / "custom"))
        assert get_optional_skills_dir() == tmp_path / "custom"

    def test_env_override_strips_whitespace(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_OPTIONAL_SKILLS", f"  {tmp_path / 'custom'}  ")
        assert get_optional_skills_dir() == tmp_path / "custom"

    def test_blank_env_falls_back_to_default_arg(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_OPTIONAL_SKILLS", "   ")
        default = tmp_path / "fallback"
        assert get_optional_skills_dir(default=default) == default

    def test_uses_default_arg_when_env_unset(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HERMES_OPTIONAL_SKILLS", raising=False)
        default = tmp_path / "given"
        assert get_optional_skills_dir(default=default) == default

    def test_falls_back_to_hermes_home_optional_skills(self, tmp_path, monkeypatch):
        monkeypatch.delenv("HERMES_OPTIONAL_SKILLS", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        assert get_optional_skills_dir() == tmp_path / "optional-skills"

    def test_env_override_wins_over_default_arg(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_OPTIONAL_SKILLS", str(tmp_path / "envwin"))
        default = tmp_path / "ignored"
        assert get_optional_skills_dir(default=default) == tmp_path / "envwin"

    def test_returns_a_path_object(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_OPTIONAL_SKILLS", str(tmp_path))
        assert isinstance(get_optional_skills_dir(), Path)
