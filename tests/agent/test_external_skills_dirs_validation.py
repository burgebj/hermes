"""Branch coverage for ``get_external_skills_dirs`` input validation.

The mtime-cache happy paths are covered in ``test_external_skills_dirs_cache``.
This module pins the input-validation and entry-normalization branches that
guard malformed config.yaml and exotic ``external_dirs`` entries:

- YAML root is not a mapping
- ``skills:`` is not a mapping
- ``external_dirs`` is a single string (coerced to a one-item list)
- ``external_dirs`` is a non-list / non-string scalar (rejected)
- entries with ``~`` and ``${VAR}`` expansion
- relative entries resolve under ``HERMES_HOME``, not the cwd
- entries pointing to the local ``~/.hermes/skills/`` are silently dropped
- duplicates collapse to a single result
- entries pointing at non-existent paths are silently skipped
- empty / whitespace-only entries are skipped
"""

from __future__ import annotations

from pathlib import Path

import pytest

from agent.skill_utils import (
    _external_dirs_cache_clear,
    get_external_skills_dirs,
)


@pytest.fixture
def isolated_hermes_home(tmp_path, monkeypatch):
    """Empty isolated ``~/.hermes/`` with no config — caller writes config.yaml."""
    home = tmp_path / ".hermes"
    home.mkdir()
    (home / "skills").mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    _external_dirs_cache_clear()
    yield home, tmp_path
    _external_dirs_cache_clear()


def _write_config(home: Path, body: str) -> Path:
    config = home / "config.yaml"
    config.write_text(body, encoding="utf-8")
    return config


def test_yaml_root_not_mapping_returns_empty(isolated_hermes_home):
    home, _ = isolated_hermes_home
    _write_config(home, "- item1\n- item2\n")  # YAML list at root, not a mapping

    assert get_external_skills_dirs() == []


def test_skills_section_not_mapping_returns_empty(isolated_hermes_home):
    home, _ = isolated_hermes_home
    _write_config(home, "skills: just_a_string\n")

    assert get_external_skills_dirs() == []


def test_external_dirs_as_single_string_is_coerced_to_list(isolated_hermes_home):
    home, root = isolated_hermes_home
    target = root / "string_external"
    target.mkdir()

    _write_config(home, f"skills:\n  external_dirs: {target}\n")

    assert get_external_skills_dirs() == [target.resolve()]


def test_external_dirs_as_invalid_type_returns_empty(isolated_hermes_home):
    home, _ = isolated_hermes_home
    _write_config(home, "skills:\n  external_dirs:\n    nested: dict\n")

    assert get_external_skills_dirs() == []


def test_environment_variable_in_entry_is_expanded(isolated_hermes_home, monkeypatch):
    home, root = isolated_hermes_home
    target = root / "env_expanded"
    target.mkdir()
    monkeypatch.setenv("EXT_SKILLS", str(target))

    _write_config(home, "skills:\n  external_dirs:\n    - ${EXT_SKILLS}\n")

    assert get_external_skills_dirs() == [target.resolve()]


def test_tilde_in_entry_is_expanded(isolated_hermes_home):
    home, root = isolated_hermes_home
    # The fixture sets HOME=tmp_path; get_external_skills_dirs() expands `~`
    # via os.path.expanduser(), which on POSIX consults the HOME env var.
    target = root / "tilde_target"
    target.mkdir()

    _write_config(home, "skills:\n  external_dirs:\n    - ~/tilde_target\n")

    assert get_external_skills_dirs() == [target.resolve()]


def test_relative_entry_is_resolved_against_hermes_home(isolated_hermes_home):
    home, _ = isolated_hermes_home
    relative_target = home / "subdir_skills"
    relative_target.mkdir()

    _write_config(home, "skills:\n  external_dirs:\n    - subdir_skills\n")

    assert get_external_skills_dirs() == [relative_target.resolve()]


def test_local_skills_dir_is_silently_dropped(isolated_hermes_home):
    home, root = isolated_hermes_home
    local_skills = home / "skills"
    extra = root / "extra_skills"
    extra.mkdir()

    _write_config(
        home,
        "skills:\n"
        "  external_dirs:\n"
        f"    - {local_skills}\n"
        f"    - {extra}\n",
    )

    result = get_external_skills_dirs()
    assert local_skills.resolve() not in result
    assert extra.resolve() in result


def test_duplicate_entries_collapse(isolated_hermes_home):
    home, root = isolated_hermes_home
    target = root / "dup_skills"
    target.mkdir()

    _write_config(
        home,
        "skills:\n"
        "  external_dirs:\n"
        f"    - {target}\n"
        f"    - {target}\n"
        f"    - {target}\n",
    )

    assert get_external_skills_dirs() == [target.resolve()]


def test_nonexistent_entries_are_skipped(isolated_hermes_home):
    home, root = isolated_hermes_home
    real = root / "real_skills"
    real.mkdir()
    fake = root / "does_not_exist"

    _write_config(
        home,
        "skills:\n"
        "  external_dirs:\n"
        f"    - {fake}\n"
        f"    - {real}\n",
    )

    assert get_external_skills_dirs() == [real.resolve()]


def test_empty_and_whitespace_entries_are_skipped(isolated_hermes_home):
    home, root = isolated_hermes_home
    target = root / "kept_skills"
    target.mkdir()

    _write_config(
        home,
        "skills:\n"
        "  external_dirs:\n"
        "    - ''\n"
        "    - '   '\n"
        f"    - {target}\n",
    )

    assert get_external_skills_dirs() == [target.resolve()]
