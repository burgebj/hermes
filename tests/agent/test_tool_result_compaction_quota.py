"""Disk quota tests for tool result compaction."""

from __future__ import annotations

import os

from agent.tool_result_compaction import _enforce_disk_quota


def test_quota_cleanup_deletes_oldest_files(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    files = []
    for idx in range(3):
        path = session_dir / f"file_{idx}.json"
        path.write_bytes(b"x" * 500_000)
        os.utime(path, (100 + idx, 100 + idx))
        files.append(path)

    _enforce_disk_quota(tmp_path, max_disk_mb=1)

    assert not files[0].exists()
    assert not files[1].exists()
    assert files[2].exists()


def test_quota_cleanup_preserves_protected_path(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()

    old_path = session_dir / "old.json"
    old_path.write_bytes(b"x" * 500_000)
    os.utime(old_path, (100, 100))

    protected_path = session_dir / "protected.json"
    protected_path.write_bytes(b"x" * 500_000)
    os.utime(protected_path, (101, 101))

    newer_path = session_dir / "newer.json"
    newer_path.write_bytes(b"x" * 500_000)
    os.utime(newer_path, (102, 102))

    _enforce_disk_quota(tmp_path, max_disk_mb=1, protected_path=protected_path)

    assert not old_path.exists()
    assert protected_path.exists()
    assert not newer_path.exists()


def test_quota_cleanup_disabled_when_max_disk_mb_non_positive(tmp_path):
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    path = session_dir / "file.json"
    path.write_bytes(b"x" * 1_500_000)

    _enforce_disk_quota(tmp_path, max_disk_mb=0)

    assert path.exists()
