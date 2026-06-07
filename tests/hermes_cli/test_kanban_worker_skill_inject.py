"""PR2 — _kanban_worker_skill_available counts distinct resolvable candidates.

The dispatcher injects ``--skills kanban-worker`` into every worker, gated on
``_kanban_worker_skill_available(HERMES_HOME)``. The worker resolves the skill
*by name* via ``skill_view``, which collects all candidate ``SKILL.md`` files
across the profile skills dir + the profile's ``skills.external_dirs`` and fails
the worker at startup (``ValueError: Unknown skill(s): kanban-worker``) in two
ways: zero candidates (not found) and two-or-more (ambiguous). The old guard
tested mere file *existence*, so it returned True in the ambiguous case and the
worker's resolver then refused the skill — the exact crash it was meant to
prevent. The fix counts *distinct* resolved files and injects only when exactly
one resolves.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

from hermes_cli import kanban_db as kb


def _write_kanban_worker_skill(skills_root: Path) -> Path:
    """Create ``<skills_root>/devops/kanban-worker/SKILL.md`` and return it."""
    skill_dir = skills_root / "devops" / "kanban-worker"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    skill_md.write_text(
        "---\nname: kanban-worker\ndescription: Kanban worker patterns.\n---\n"
        "# Kanban Worker\n",
        encoding="utf-8",
    )
    return skill_md


def _write_config_external_dirs(home: Path, external_dirs: list[str]) -> None:
    """Write ``<home>/config.yaml`` with ``skills.external_dirs``."""
    (home / "config.yaml").write_text(
        yaml.safe_dump({"skills": {"external_dirs": external_dirs}}),
        encoding="utf-8",
    )


def test_skill_guard_true_when_single(tmp_path):
    """Exactly one resolvable kanban-worker/SKILL.md (in the profile skills dir,
    no external_dirs) → the worker's by-name lookup succeeds → inject."""
    home = tmp_path / "home"
    (home / "skills").mkdir(parents=True)
    _write_kanban_worker_skill(home / "skills")

    assert kb._kanban_worker_skill_available(str(home)) is True


def test_skill_guard_false_when_missing(tmp_path):
    """Zero candidates: profile skills dir lacks the skill and no external_dirs
    supplies it → worker would fail 'not found' → omit the flag."""
    home = tmp_path / "home"
    (home / "skills").mkdir(parents=True)
    # No kanban-worker skill anywhere.

    assert kb._kanban_worker_skill_available(str(home)) is False


def test_skill_guard_false_when_no_skills_dir(tmp_path):
    """Home without a skills/ dir at all → zero candidates → False."""
    home = tmp_path / "home"
    home.mkdir()

    assert kb._kanban_worker_skill_available(str(home)) is False


def test_skill_guard_false_when_ambiguous(tmp_path):
    """Core regression: the skill resolves to TWO distinct files — one in the
    profile's own ``skills/devops/kanban-worker`` AND one in a directory listed
    in ``skills.external_dirs``. The worker's resolver refuses to guess
    ('Ambiguous skill name') and aborts, so the existence-only guard's True was
    the exact bug. The fixed guard counts distinct candidates and returns
    False."""
    home = tmp_path / "home"
    (home / "skills").mkdir(parents=True)
    _write_kanban_worker_skill(home / "skills")  # candidate #1 (profile-local)

    external = tmp_path / "shared-skills"
    external.mkdir()
    _write_kanban_worker_skill(external)  # candidate #2 (distinct file)

    _write_config_external_dirs(home, [str(external)])

    assert kb._kanban_worker_skill_available(str(home)) is False


def test_skill_guard_true_when_only_in_external_dir(tmp_path):
    """Single candidate supplied solely via external_dirs (profile skills dir
    has no copy) → exactly one distinct file resolves → inject."""
    home = tmp_path / "home"
    (home / "skills").mkdir(parents=True)  # empty, no kanban-worker

    external = tmp_path / "shared-skills"
    external.mkdir()
    _write_kanban_worker_skill(external)

    _write_config_external_dirs(home, [str(external)])

    assert kb._kanban_worker_skill_available(str(home)) is True


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Symlinks require elevated privileges on Windows",
)
def test_skill_guard_dedups_symlinked_external_dir(tmp_path):
    """An external_dirs entry that symlinks back at the profile skills dir must
    not be double-counted — both paths resolve to the same file, so it stays a
    single distinct candidate and the guard returns True (matches skill_view's
    resolved-path dedup)."""
    home = tmp_path / "home"
    (home / "skills").mkdir(parents=True)
    _write_kanban_worker_skill(home / "skills")

    link = tmp_path / "skills-link"
    link.symlink_to(home / "skills", target_is_directory=True)
    _write_config_external_dirs(home, [str(link)])

    assert kb._kanban_worker_skill_available(str(home)) is True


def test_skill_guard_handles_missing_config(tmp_path):
    """No config.yaml → external_dirs helper degrades to [] and the guard falls
    back to the local skills dir only (single candidate → True)."""
    home = tmp_path / "home"
    (home / "skills").mkdir(parents=True)
    _write_kanban_worker_skill(home / "skills")
    assert not (home / "config.yaml").exists()

    assert kb._kanban_worker_skill_available(str(home)) is True


def test_external_skill_dirs_reads_config(tmp_path):
    """The new helper returns existing external_dirs entries as absolute Paths
    and drops non-existent / malformed ones."""
    home = tmp_path / "home"
    home.mkdir()
    real = tmp_path / "real-ext"
    real.mkdir()
    missing = tmp_path / "does-not-exist"

    _write_config_external_dirs(home, [str(real), str(missing)])

    dirs = kb._kanban_worker_external_skill_dirs(home)
    resolved = {Path(d).resolve() for d in dirs}

    assert real.resolve() in resolved
    assert missing.resolve() not in resolved


def test_external_skill_dirs_empty_when_no_config(tmp_path):
    """Missing config.yaml → empty list (best-effort, no raise)."""
    home = tmp_path / "home"
    home.mkdir()

    assert kb._kanban_worker_external_skill_dirs(home) == []
