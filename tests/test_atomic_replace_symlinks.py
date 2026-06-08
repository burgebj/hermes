"""Regression tests for GitHub #16743 — atomic writes must preserve symlinks.

``os.replace(tmp, target)`` replaces whatever exists at ``target`` — including
symlinks, which it swaps for a regular file.  Managed deployments that
symlink ``~/.hermes/config.yaml`` (and other state files) to a git-tracked
profile package were silently detached on every config write.

The fix: a shared ``atomic_replace`` helper in ``utils.py`` that resolves the
target through ``os.path.realpath`` when it is a symlink, so the real file is
overwritten in-place while the symlink survives.  All atomic-write sites in
the codebase were migrated to the helper; these tests pin that invariant.
"""
from __future__ import annotations

import errno
import json
import os
import sys
from pathlib import Path

import pytest
import yaml

# Ensure the repo root is importable when running via `pytest tests/...`.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from utils import atomic_json_write, atomic_replace, atomic_yaml_write


# ─── Direct helper ────────────────────────────────────────────────────────────


def _write_tmp(dir_: Path, content: str) -> Path:
    tmp = dir_ / ".src.tmp"
    tmp.write_text(content, encoding="utf-8")
    return tmp


def test_atomic_replace_preserves_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.yaml"
    link = tmp_path / "link.yaml"
    real.write_text("original\n", encoding="utf-8")
    link.symlink_to(real)

    tmp = _write_tmp(tmp_path, "updated\n")
    returned = atomic_replace(tmp, link)

    assert link.is_symlink(), "symlink must not be replaced with a regular file"
    assert real.read_text(encoding="utf-8") == "updated\n"
    assert Path(returned) == real
    # Follow the symlink — same content.
    assert link.read_text(encoding="utf-8") == "updated\n"


def test_atomic_replace_regular_file(tmp_path: Path) -> None:
    target = tmp_path / "plain.yaml"
    target.write_text("old\n", encoding="utf-8")

    tmp = _write_tmp(tmp_path, "fresh\n")
    returned = atomic_replace(tmp, target)

    assert Path(returned) == target
    assert target.read_text(encoding="utf-8") == "fresh\n"
    assert not target.is_symlink()


def test_atomic_replace_first_time_create(tmp_path: Path) -> None:
    target = tmp_path / "new.yaml"
    assert not target.exists()

    tmp = _write_tmp(tmp_path, "brand new\n")
    returned = atomic_replace(tmp, target)

    assert Path(returned) == target
    assert target.read_text(encoding="utf-8") == "brand new\n"


def test_atomic_replace_accepts_pathlike_and_str(tmp_path: Path) -> None:
    target = tmp_path / "dual.json"
    target.write_text("{}", encoding="utf-8")

    # str inputs
    tmp1 = _write_tmp(tmp_path, "1")
    atomic_replace(str(tmp1), str(target))
    assert target.read_text(encoding="utf-8") == "1"

    # Path inputs
    tmp2 = _write_tmp(tmp_path, "2")
    atomic_replace(tmp2, target)
    assert target.read_text(encoding="utf-8") == "2"


# ─── atomic_json_write / atomic_yaml_write wiring ──────────────────────────


def test_atomic_json_write_preserves_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.json"
    link = tmp_path / "link.json"
    real.write_text("{}", encoding="utf-8")
    link.symlink_to(real)

    atomic_json_write(link, {"hello": "world"})

    assert link.is_symlink()
    loaded = json.loads(real.read_text(encoding="utf-8"))
    assert loaded == {"hello": "world"}


def test_atomic_yaml_write_preserves_symlink(tmp_path: Path) -> None:
    real = tmp_path / "real.yaml"
    link = tmp_path / "link.yaml"
    real.write_text("placeholder: true\n", encoding="utf-8")
    link.symlink_to(real)

    atomic_yaml_write(link, {"model": {"provider": "openrouter"}})

    assert link.is_symlink()
    data = yaml.safe_load(real.read_text(encoding="utf-8"))
    assert data == {"model": {"provider": "openrouter"}}


def test_atomic_json_write_preserves_symlink_permissions(tmp_path: Path) -> None:
    """Symlinked targets keep the real file's permission bits."""
    if os.name != "posix":
        pytest.skip("POSIX-only")

    real = tmp_path / "real.json"
    link = tmp_path / "link.json"
    real.write_text("{}", encoding="utf-8")
    os.chmod(real, 0o644)
    link.symlink_to(real)

    atomic_json_write(link, {"x": 1})

    import stat as _stat
    mode = _stat.S_IMODE(real.stat().st_mode)
    assert mode == 0o644, f"permissions drifted after symlinked write: {oct(mode)}"


# ─── Broken-symlink edge case ─────────────────────────────────────────────


def test_atomic_replace_broken_symlink_creates_target(tmp_path: Path) -> None:
    """A symlink pointing at a missing file: the write should create the
    real target (resolving via realpath) rather than leaving the dangling
    link in place as a regular file.
    """
    missing = tmp_path / "does_not_exist_yet.yaml"
    link = tmp_path / "link.yaml"
    link.symlink_to(missing)
    assert link.is_symlink()
    assert not missing.exists()

    tmp = _write_tmp(tmp_path, "created-through-link\n")
    atomic_replace(tmp, link)

    assert link.is_symlink(), "symlink must be preserved"
    assert missing.exists(), "real target should now exist"
    assert missing.read_text(encoding="utf-8") == "created-through-link\n"


# ─── Cross-filesystem (EXDEV) fallback — GitHub #36653 ─────────────────────
#
# When ``target`` is a symlink whose real file lives on a *different*
# filesystem, the temp file (created next to the symlink) and the resolved
# real path straddle a mount point.  ``os.replace`` can't rename across
# devices, so it raises ``OSError(EXDEV)``.  ``atomic_replace`` must fall back
# to staging the bytes on the target's filesystem and replacing there, so the
# write still lands atomically instead of blowing up.


def _patch_exdev_once(monkeypatch) -> dict:
    """Make ``os.replace`` raise EXDEV on its first call, then delegate to the
    real implementation.  Simulates a cross-device symlink target without
    needing two real mounts in the test environment.
    """
    real_replace = os.replace
    state = {"calls": 0}

    def fake_replace(src, dst):
        state["calls"] += 1
        if state["calls"] == 1:
            raise OSError(errno.EXDEV, "Invalid cross-device link")
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", fake_replace)
    return state


def test_atomic_replace_exdev_fallback_preserves_symlink(
    tmp_path: Path, monkeypatch
) -> None:
    real = tmp_path / "real.yaml"
    link = tmp_path / "link.yaml"
    real.write_text("original\n", encoding="utf-8")
    link.symlink_to(real)

    state = _patch_exdev_once(monkeypatch)
    tmp = _write_tmp(tmp_path, "updated\n")
    returned = atomic_replace(tmp, link)

    assert state["calls"] >= 2, "EXDEV must trigger a retry on the target filesystem"
    assert link.is_symlink(), "symlink must survive the cross-device fallback"
    assert real.read_text(encoding="utf-8") == "updated\n"
    assert Path(returned) == real
    assert not Path(tmp).exists(), "the original cross-device temp must be cleaned up"


def test_atomic_json_write_survives_cross_device_symlink(
    tmp_path: Path, monkeypatch
) -> None:
    real = tmp_path / "real.json"
    link = tmp_path / "link.json"
    real.write_text("{}", encoding="utf-8")
    link.symlink_to(real)

    _patch_exdev_once(monkeypatch)
    atomic_json_write(link, {"hello": "world"})

    assert link.is_symlink()
    assert json.loads(real.read_text(encoding="utf-8")) == {"hello": "world"}


def test_atomic_replace_exdev_stages_on_target_filesystem(
    tmp_path: Path, monkeypatch
) -> None:
    """The fallback must stage its temp in the *real target's* directory, not
    next to the symlink — staging next to the symlink would just hit EXDEV
    again.  Spy on mkstemp to pin where the staged file is created."""
    import tempfile

    real = tmp_path / "real.yaml"
    link = tmp_path / "link.yaml"
    real.write_text("original\n", encoding="utf-8")
    link.symlink_to(real)

    _patch_exdev_once(monkeypatch)
    real_mkstemp = tempfile.mkstemp
    seen: dict = {}

    def spy_mkstemp(*args, **kwargs):
        seen["dir"] = kwargs.get("dir")
        return real_mkstemp(*args, **kwargs)

    monkeypatch.setattr(tempfile, "mkstemp", spy_mkstemp)
    tmp = _write_tmp(tmp_path, "updated\n")
    atomic_replace(tmp, link)

    assert seen["dir"] == os.path.dirname(str(real)), "staged temp must land on the target fs"
    assert real.read_text(encoding="utf-8") == "updated\n"


def test_atomic_replace_exdev_copy_failure_leaves_target_intact(
    tmp_path: Path, monkeypatch
) -> None:
    """If the cross-device copy fails mid-way, the target must be untouched and
    no staged temp may leak."""
    import shutil

    real = tmp_path / "real.yaml"
    link = tmp_path / "link.yaml"
    real.write_text("original\n", encoding="utf-8")
    link.symlink_to(real)

    _patch_exdev_once(monkeypatch)

    def boom(src, dst, *args, **kwargs):
        raise RuntimeError("disk full")

    monkeypatch.setattr(shutil, "copyfileobj", boom)
    tmp = _write_tmp(tmp_path, "updated\n")
    with pytest.raises(RuntimeError, match="disk full"):
        atomic_replace(tmp, link)

    assert real.read_text(encoding="utf-8") == "original\n", "target must be untouched"
    assert not list(tmp_path.glob(".atomic_xdev_*")), "staged temp must not leak"
    assert not Path(tmp).exists(), "cross-device temp must still be cleaned up"


def test_atomic_replace_reraises_non_exdev_oserror(tmp_path: Path, monkeypatch) -> None:
    """Only EXDEV gets the fallback; other OSErrors must propagate unchanged
    and leave the target untouched."""
    target = tmp_path / "plain.yaml"
    target.write_text("old\n", encoding="utf-8")

    def boom(src, dst):
        raise OSError(errno.EACCES, "Permission denied")

    monkeypatch.setattr(os, "replace", boom)
    tmp = _write_tmp(tmp_path, "fresh\n")
    with pytest.raises(OSError) as exc_info:
        atomic_replace(tmp, target)

    assert exc_info.value.errno == errno.EACCES
    assert target.read_text(encoding="utf-8") == "old\n", "target must be untouched"
