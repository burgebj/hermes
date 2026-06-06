"""Tests for agent.skill_utils.get_all_skills_dirs — local-first ordering invariant."""
from pathlib import Path

from agent import skill_utils


class TestGetAllSkillsDirsOrdering:
    def test_local_skills_dir_is_first(self, tmp_path, monkeypatch):
        local = tmp_path / "local"
        ext_a = tmp_path / "ext_a"
        ext_b = tmp_path / "ext_b"
        for d in (local, ext_a, ext_b):
            d.mkdir()
        monkeypatch.setattr(skill_utils, "get_skills_dir", lambda: local)
        monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda: [ext_a, ext_b])
        result = skill_utils.get_all_skills_dirs()
        assert result[0] == local
        assert result[1:] == [ext_a, ext_b]

    def test_only_local_when_no_externals(self, tmp_path, monkeypatch):
        local = tmp_path / "local"
        local.mkdir()
        monkeypatch.setattr(skill_utils, "get_skills_dir", lambda: local)
        monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda: [])
        assert skill_utils.get_all_skills_dirs() == [local]

    def test_local_included_even_when_missing_on_disk(self, tmp_path, monkeypatch):
        local = tmp_path / "does_not_exist"
        monkeypatch.setattr(skill_utils, "get_skills_dir", lambda: local)
        monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda: [])
        result = skill_utils.get_all_skills_dirs()
        assert result == [local]
        assert not local.exists()

    def test_preserves_external_dir_order(self, tmp_path, monkeypatch):
        local = tmp_path / "local"
        local.mkdir()
        externals = [tmp_path / f"ext_{i}" for i in range(5)]
        for d in externals:
            d.mkdir()
        monkeypatch.setattr(skill_utils, "get_skills_dir", lambda: local)
        monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda: list(externals))
        result = skill_utils.get_all_skills_dirs()
        assert result == [local, *externals]

    def test_returns_list_type(self, tmp_path, monkeypatch):
        monkeypatch.setattr(skill_utils, "get_skills_dir", lambda: tmp_path)
        monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda: [])
        assert isinstance(skill_utils.get_all_skills_dirs(), list)

    def test_each_entry_is_path_instance(self, tmp_path, monkeypatch):
        local = tmp_path / "local"
        ext = tmp_path / "ext"
        local.mkdir(); ext.mkdir()
        monkeypatch.setattr(skill_utils, "get_skills_dir", lambda: local)
        monkeypatch.setattr(skill_utils, "get_external_skills_dirs", lambda: [ext])
        result = skill_utils.get_all_skills_dirs()
        assert all(isinstance(p, Path) for p in result)
