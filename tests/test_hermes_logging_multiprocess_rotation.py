"""Regression tests for issue #27649.

When multiple Hermes processes share ``~/.hermes/logs/agent.log`` and one
of them rotates the file (renaming it to ``agent.log.1``), the others
keep an open file descriptor pointing at the renamed inode and silently
write to the rotated backup file forever.

The fix in ``hermes_logging._ManagedRotatingFileHandler`` is:
  * compare the open stream's inode against ``baseFilename`` on disk
    every N records (default 16), close + reopen on mismatch;
  * short-circuit ``doRollover`` when an external rotation already
    happened so we never overwrite the newer ``agent.log``.

These tests pin both behaviours and the corner cases (read-only ``st_ino``
of 0 on Windows, missing/closed stream, throttle interval boundaries,
chmod-in-managed-mode still applied after the reopen path).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import pytest

import hermes_logging
from hermes_logging import _ManagedRotatingFileHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_handler(path: Path, **kwargs) -> _ManagedRotatingFileHandler:
    """Construct a handler with sensible defaults for these tests.

    We force ``_REOPEN_CHECK_INTERVAL`` down to 1 by default so every
    emit exercises the inode-check path; individual tests override it
    where the throttle itself is under test.
    """
    handler = _ManagedRotatingFileHandler(
        str(path),
        maxBytes=kwargs.pop("maxBytes", 1024),
        backupCount=kwargs.pop("backupCount", 3),
        encoding="utf-8",
        **kwargs,
    )
    handler._REOPEN_CHECK_INTERVAL = 1
    handler.setFormatter(logging.Formatter("%(message)s"))
    return handler


def _emit(handler: _ManagedRotatingFileHandler, msg: str) -> None:
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1,
        msg=msg, args=None, exc_info=None,
    )
    handler.emit(record)
    handler.flush()


def _inode(path: Path) -> int:
    return os.stat(str(path)).st_ino


# ---------------------------------------------------------------------------
# Core regression: external rotation should not split writes.
# ---------------------------------------------------------------------------


class TestExternalRotationReopen:
    """Pin the #27649 reopen-on-inode-change behaviour."""

    def test_writes_land_in_live_file_after_external_rename(self, tmp_path):
        """The exact bug from the issue: an external rename moves the
        live log to ``.1`` and our open fd should follow ``baseFilename``,
        not the rotated backup."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            _emit(h, "pre-rotation")

            # Simulate another process rotating: rename agent.log -> agent.log.1
            # and create a fresh agent.log.  Our open fd now points at the
            # renamed file (== agent.log.1).
            rotated = tmp_path / "agent.log.1"
            os.rename(str(log), str(rotated))
            log.write_text("")  # fresh active file

            live_inode_before = _inode(log)
            backup_inode = _inode(rotated)
            assert live_inode_before != backup_inode

            # The next emit must detect the mismatch and reopen on
            # ``baseFilename`` -- i.e. write to the new agent.log, not
            # to agent.log.1.
            _emit(h, "post-rotation")

            live_text = log.read_text()
            rotated_text = rotated.read_text()

            assert "post-rotation" in live_text, (
                "writes after external rotation must land in the live log"
            )
            assert "post-rotation" not in rotated_text, (
                "writes after external rotation must NOT land in the backup"
            )
            assert "pre-rotation" in rotated_text, (
                "the pre-rotation record should still be in the backup"
            )
        finally:
            h.close()

    def test_no_reopen_when_inode_unchanged(self, tmp_path):
        """Steady state: ``stat()`` shows the same inode, no reopen happens."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            _emit(h, "a")
            stream_id_before = id(h.stream)
            _emit(h, "b")
            stream_id_after = id(h.stream)
            assert stream_id_before == stream_id_after, (
                "no inode change should not provoke a stream reopen"
            )
        finally:
            h.close()

    def test_reopen_helper_returns_true_only_on_mismatch(self, tmp_path):
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            _emit(h, "warmup")
            assert h._reopen_if_rotated_externally() is False

            rotated = tmp_path / "agent.log.1"
            os.rename(str(log), str(rotated))
            log.write_text("")

            assert h._reopen_if_rotated_externally() is True
            # Second call after the reopen should be a no-op again.
            assert h._reopen_if_rotated_externally() is False
        finally:
            h.close()

    def test_reopen_continues_writing_to_baseFilename(self, tmp_path):
        """After a reopen, baseFilename grows on each subsequent emit."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            _emit(h, "pre")
            os.rename(str(log), str(tmp_path / "agent.log.1"))
            log.write_text("")
            _emit(h, "one")
            _emit(h, "two")
            _emit(h, "three")
            text = log.read_text()
            assert "one" in text and "two" in text and "three" in text
        finally:
            h.close()


# ---------------------------------------------------------------------------
# doRollover short-circuit -- never clobber a newer ``agent.log``.
# ---------------------------------------------------------------------------


class TestDoRolloverShortCircuit:
    def test_dorollover_skips_rename_when_already_rotated_externally(self, tmp_path):
        """If our open fd already points at a rotated backup, our own
        rollover must NOT rename the newer ``agent.log`` -- that would
        overwrite the active log that another process just created."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            _emit(h, "pre")

            # External rotation -- rename our file out from under us.
            rotated = tmp_path / "agent.log.1"
            os.rename(str(log), str(rotated))
            # Another process creates a brand-new active log and writes
            # something we must not clobber.
            log.write_text("sibling-process-content\n")
            sibling_inode = _inode(log)
            sibling_content = log.read_text()

            # Force our own rollover.  Pre-#27649, this would have
            # renamed agent.log -> agent.log.1 (overwriting our pre
            # record) and created a fresh empty agent.log.
            h.doRollover()

            assert log.exists(), "baseFilename must still exist after the short-circuit"
            assert log.read_text() == sibling_content, (
                "the sibling process's content must not be overwritten"
            )
            assert _inode(log) == sibling_inode, (
                "we must not have renamed/recreated the sibling's file"
            )
        finally:
            h.close()

    def test_dorollover_still_rotates_when_no_external_rotation(self, tmp_path):
        """The short-circuit must NOT break ordinary single-process
        rotation -- if no one rotated externally, behaviour is unchanged."""
        log = tmp_path / "agent.log"
        h = _make_handler(log, maxBytes=10, backupCount=2)
        try:
            _emit(h, "a" * 50)
            h.doRollover()
            assert log.exists()
            assert (tmp_path / "agent.log.1").exists()
        finally:
            h.close()


# ---------------------------------------------------------------------------
# Throttle / safety / Windows-compat corner cases.
# ---------------------------------------------------------------------------


class TestThrottleAndCorners:
    def test_first_emit_always_checks(self, tmp_path):
        """The first emit on a fresh handler must check immediately --
        otherwise a process that starts AFTER another process has already
        rotated would write to ``.1`` for N records before noticing."""
        log = tmp_path / "agent.log"
        h = _ManagedRotatingFileHandler(
            str(log), maxBytes=10_000, backupCount=2, encoding="utf-8",
        )
        # Default throttle (16) -- but the first emit must still check.
        try:
            # Externally rotate BEFORE the first emit.
            _emit(h, "warmup")  # initial write
            rotated = tmp_path / "agent.log.1"
            os.rename(str(log), str(rotated))
            log.write_text("")

            # Reset the counter so we're at "first emit since check".
            h._emit_count = 0
            _emit(h, "first")

            assert "first" in log.read_text()
            assert "first" not in rotated.read_text()
        finally:
            h.close()

    def test_throttle_bounded_window(self, tmp_path):
        """With ``_REOPEN_CHECK_INTERVAL=N`` writes after rotation may
        land in the backup for at most N-1 records before the next
        check.  This pins the boundedness contract advertised in the
        docstring rather than promising zero lost writes."""
        log = tmp_path / "agent.log"
        h = _ManagedRotatingFileHandler(
            str(log), maxBytes=10_000, backupCount=2, encoding="utf-8",
        )
        h._REOPEN_CHECK_INTERVAL = 4
        h.setFormatter(logging.Formatter("%(message)s"))
        try:
            _emit(h, "warmup")
            os.rename(str(log), str(tmp_path / "agent.log.1"))
            log.write_text("")

            # We want the inode check to run on the *next* emit.  After
            # warmup, _emit_count is 1.  Aligning to N means the next
            # multiple-of-N tick happens at _emit_count == 4 -> we emit
            # three records to get there.
            for i in range(3):
                _emit(h, f"between-{i}")
            # 4th emit is the boundary -> inode check runs here, reopen.
            _emit(h, "after-window")

            assert "after-window" in log.read_text()
        finally:
            h.close()

    def test_stream_inode_returns_none_when_stream_closed(self, tmp_path):
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        h.stream.close()
        h.stream = None
        assert h._stream_inode_key() is None
        # And the reopen helper must be a no-op rather than crashing.
        assert h._reopen_if_rotated_externally() is False
        h.close()

    def test_stream_inode_treats_st_ino_zero_as_unknown(self, tmp_path, monkeypatch):
        """Windows sometimes returns st_ino == 0 for regular files;
        we must treat that as 'unknown' rather than reopening on every
        write."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            class _ZeroInodeStat:
                st_dev = 1
                st_ino = 0
                st_mode = 0
                st_size = 0
                st_atime = 0
                st_mtime = 0
                st_ctime = 0

            monkeypatch.setattr(os, "fstat", lambda _fd: _ZeroInodeStat())
            assert h._stream_inode_key() is None
        finally:
            h.close()

    def test_baseFilename_inode_returns_none_when_missing(self, tmp_path):
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            log.unlink()
            assert h._baseFilename_inode_key() is None
        finally:
            h.close()

    def test_reopen_is_silent_on_oserror(self, tmp_path, monkeypatch):
        """``_reopen_if_rotated_externally`` must never propagate an
        exception -- a broken logging path must not kill the calling
        code path."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            _emit(h, "warmup")
            rotated = tmp_path / "agent.log.1"
            os.rename(str(log), str(rotated))
            log.write_text("")

            # Force the close path to raise; the wrapper must swallow.
            real_close = h.stream.close
            def _explode():
                raise OSError("simulated close failure")
            monkeypatch.setattr(h.stream, "close", _explode)

            # Should not raise.
            assert h._reopen_if_rotated_externally() is True
            # And the stream should be re-pointed at baseFilename.
            assert _inode(Path(h.baseFilename)) == os.fstat(h.stream.fileno()).st_ino

            real_close  # silence unused -- we only kept the ref for clarity
        finally:
            h.close()

    def test_emit_exception_in_check_does_not_drop_record(self, tmp_path, monkeypatch):
        """If the inode check raises unexpectedly, the underlying record
        must still be written (best-effort fail-open)."""
        log = tmp_path / "agent.log"
        h = _make_handler(log)
        try:
            def _explode(*_a, **_kw):
                raise RuntimeError("simulated inode-check failure")
            monkeypatch.setattr(h, "_reopen_if_rotated_externally", _explode)

            _emit(h, "still-written")
            assert "still-written" in log.read_text()
        finally:
            h.close()


# ---------------------------------------------------------------------------
# Managed-mode permissions are still applied after the reopen path.
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="POSIX file modes only"
)
class TestManagedModeChmodAfterReopen:
    def test_chmod_660_applied_after_external_rotation(self, tmp_path, monkeypatch):
        """When managed mode is on, the chmod-after-open contract must
        survive the reopen path -- otherwise a sibling-rotated log
        ends up with the process umask (0644) and the gateway can't
        share the file with interactive users."""
        log = tmp_path / "agent.log"
        # Pretend we're in managed mode.
        h = _ManagedRotatingFileHandler(
            str(log), maxBytes=10_000, backupCount=2, encoding="utf-8",
        )
        h._managed = True  # bypass NixOS check
        h._REOPEN_CHECK_INTERVAL = 1
        h.setFormatter(logging.Formatter("%(message)s"))
        try:
            _emit(h, "warmup")

            os.rename(str(log), str(tmp_path / "agent.log.1"))
            log.write_text("")
            os.chmod(str(log), 0o644)  # sibling created with default umask

            _emit(h, "post")

            # After our reopen, the chmod path must have run.
            mode = os.stat(str(log)).st_mode & 0o777
            assert mode == 0o660, f"expected 0o660 after reopen, got {oct(mode)}"
        finally:
            h.close()


# ---------------------------------------------------------------------------
# Sanity: the handler integrates cleanly with the rest of hermes_logging.
# ---------------------------------------------------------------------------


class TestIntegrationWithSetupLogging:
    def test_setup_logging_uses_managed_handler(self, tmp_path, monkeypatch):
        """``setup_logging()`` must still wire ``_ManagedRotatingFileHandler``
        rather than the bare stdlib class -- otherwise the #27649 fix
        wouldn't be picked up on real installs."""
        hermes_home = tmp_path / ".hermes"
        hermes_home.mkdir()
        monkeypatch.setattr(hermes_logging, "get_hermes_home", lambda: hermes_home)
        monkeypatch.setattr(
            hermes_logging, "get_config_path", lambda: hermes_home / "config.yaml",
        )
        hermes_logging._logging_initialized = False
        root = logging.getLogger()
        previous_handlers = list(root.handlers)
        try:
            hermes_logging.setup_logging(force=True)
            rotating = [
                h for h in root.handlers
                if isinstance(h, _ManagedRotatingFileHandler)
            ]
            assert len(rotating) >= 1, (
                "setup_logging must attach the inode-aware managed handler"
            )
        finally:
            for h in list(root.handlers):
                if h not in previous_handlers:
                    root.removeHandler(h)
                    h.close()
            hermes_logging._logging_initialized = False
