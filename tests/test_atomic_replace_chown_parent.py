"""Regression tests for GitHub #17144 — atomic writes from a root-context
must chown the resulting file to match the parent directory's owner so
the gateway service user can read it.

Containerized hermes deployments (``nousresearch/hermes-agent:latest``)
run PID 1 as root via tini and the gateway as ``hermes`` / UID 10000.
Memory-tool / aux writes that happen to land on the root side of that
boundary land on the persistent volume as ``root:root`` and the gateway
silently can't read them — the agent looks like it persisted the memory
but the next session never sees it.

The fix sticks the parent directory's owner/group onto the new file
inside ``atomic_replace`` so every atomic-write call site benefits and
no per-tool plumbing is needed. These tests pin the gating logic
without requiring real root: ``os.geteuid`` / ``os.stat`` / ``os.chown``
are monkey-patched, and the chown call is observed.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import utils as utils_mod
from utils import atomic_replace


pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX-only")


def _write_tmp(dir_: Path, content: str = "x") -> Path:
    tmp = dir_ / ".src.tmp"
    tmp.write_text(content, encoding="utf-8")
    return tmp


def _fake_parent_stat(uid: int, gid: int) -> SimpleNamespace:
    return SimpleNamespace(st_uid=uid, st_gid=gid)


def test_chown_to_match_parent_runs_when_root_and_parent_is_user(tmp_path):
    """As root, after replace, chown to parent's non-root owner.

    Repro: gateway runs as ``hermes`` (UID 10000), persistent volume
    parent is owned by 10000, but the write happens from a root context.
    The new file should end up owned by 10000:10000.
    """
    target = tmp_path / "MEMORY.md"
    target.write_text("old\n", encoding="utf-8")
    tmp = _write_tmp(tmp_path, "new\n")

    chown_calls: list[tuple[str, int, int]] = []

    def fake_chown(path, uid, gid):
        chown_calls.append((str(path), uid, gid))

    real_stat = os.stat

    def fake_stat(path, *args, **kwargs):
        if str(path) == str(tmp_path):
            return _fake_parent_stat(uid=10000, gid=10000)
        return real_stat(path, *args, **kwargs)

    with patch.object(utils_mod.os, "geteuid", lambda: 0), \
         patch.object(utils_mod.os, "chown", side_effect=fake_chown), \
         patch.object(utils_mod.os, "stat", side_effect=fake_stat):
        atomic_replace(tmp, target)

    assert chown_calls, "expected chown call when root + non-root parent"
    chown_path, chown_uid, chown_gid = chown_calls[-1]
    assert chown_path == str(target)
    assert chown_uid == 10000
    assert chown_gid == 10000


def test_chown_skipped_when_not_root(tmp_path):
    """As non-root, the chown is a no-op (would EPERM anyway)."""
    target = tmp_path / "f.txt"
    target.write_text("old", encoding="utf-8")
    tmp = _write_tmp(tmp_path, "new")

    chown_calls: list = []

    with patch.object(utils_mod.os, "geteuid", lambda: 1000), \
         patch.object(utils_mod.os, "chown", side_effect=lambda *a, **k: chown_calls.append(a)):
        atomic_replace(tmp, target)

    assert chown_calls == [], (
        "chown must not run when the process is not root"
    )


def test_chown_skipped_when_parent_is_also_root(tmp_path):
    """If the parent dir is itself root-owned, there's nothing to fix."""
    target = tmp_path / "f.txt"
    target.write_text("old", encoding="utf-8")
    tmp = _write_tmp(tmp_path, "new")

    chown_calls: list = []
    real_stat = os.stat

    def fake_stat(path, *args, **kwargs):
        if str(path) == str(tmp_path):
            return _fake_parent_stat(uid=0, gid=0)
        return real_stat(path, *args, **kwargs)

    with patch.object(utils_mod.os, "geteuid", lambda: 0), \
         patch.object(utils_mod.os, "chown", side_effect=lambda *a, **k: chown_calls.append(a)), \
         patch.object(utils_mod.os, "stat", side_effect=fake_stat):
        atomic_replace(tmp, target)

    assert chown_calls == [], (
        "chown must not run when both the process and the parent are root"
    )


def test_chown_failure_does_not_break_atomic_replace(tmp_path):
    """The replace must succeed even if the chown is rejected."""
    target = tmp_path / "f.txt"
    target.write_text("old", encoding="utf-8")
    tmp = _write_tmp(tmp_path, "new")

    real_stat = os.stat

    def fake_stat(path, *args, **kwargs):
        if str(path) == str(tmp_path):
            return _fake_parent_stat(uid=10000, gid=10000)
        return real_stat(path, *args, **kwargs)

    def chown_eperm(*_args, **_kwargs):
        raise OSError(1, "Operation not permitted")  # EPERM

    with patch.object(utils_mod.os, "geteuid", lambda: 0), \
         patch.object(utils_mod.os, "chown", side_effect=chown_eperm), \
         patch.object(utils_mod.os, "stat", side_effect=fake_stat):
        # Must not raise.
        atomic_replace(tmp, target)

    assert target.read_text(encoding="utf-8") == "new", (
        "atomic_replace must commit the new content even if chown fails"
    )
