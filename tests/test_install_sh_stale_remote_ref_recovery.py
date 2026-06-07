"""Regression for #32384: install.sh recovers from stale remote-tracking refs.

When a remote branch is force-pushed or a dependabot/PR ref is rewritten
upstream, ``$INSTALL_DIR/.git/refs/remotes/origin/<branch>`` can be left
pointing at an object that no longer exists. The next ``git fetch origin``
inside install.sh's ``clone_repo`` update path then aborts with::

    fatal: bad object refs/remotes/origin/<branch>
    error: ... did not send all necessary objects

Because install.sh runs under ``set -e``, that single fetch failure tears
the whole installer down — including the ``install.sh`` re-run the user is
typically told to use to recover from a failed ``hermes update``.

install.sh now detects ``bad object refs/remotes/origin/`` in fetch output,
runs ``git remote prune origin`` once, and retries the fetch. This mirrors
the equivalent recovery in ``hermes_cli/main.py::_cmd_update_impl`` (the
``hermes update`` path) so both update surfaces survive a stale-ref
upstream rewrite.
"""

from __future__ import annotations

import os
import re
import stat
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = REPO_ROOT / "scripts" / "install.sh"


def _extract_update_fetch_block() -> str:
    """Return the install.sh block that runs `git fetch origin` and recovers
    from a stale-ref error. Bounded by the autostash setup above and the
    `git checkout "$BRANCH"` line below — both are stable structural anchors.
    """
    text = INSTALL_SH.read_text()
    match = re.search(
        r"(?P<block>local fetch_log.*?git checkout \"\$BRANCH\")",
        text,
        re.DOTALL,
    )
    assert match is not None, (
        "Could not locate the fetch-with-stale-ref-recovery block in "
        "scripts/install.sh (between `local fetch_log` and "
        "`git checkout \"$BRANCH\"`)."
    )
    return match["block"]


def test_install_sh_fetch_block_invokes_prune_on_stale_ref_error() -> None:
    """Static guard: the recovery branch must run `git remote prune origin`
    and a second `git fetch origin` after detecting `bad object
    refs/remotes/origin/`. The two-step prune-then-retry shape is what makes
    the recovery idempotent."""
    block = _extract_update_fetch_block()
    assert "bad object refs/remotes/origin/" in block, (
        "fetch block must grep for the exact stale-ref error string; otherwise "
        "the recovery branch never triggers."
    )
    assert "git remote prune origin" in block, (
        "fetch block must run `git remote prune origin` to clear the stale "
        "remote-tracking refs."
    )
    # Both fetch calls must be present — the initial one (which fails) and the
    # retry after prune.
    assert block.count("git fetch origin") >= 2, (
        "fetch block must retry `git fetch origin` after prune; otherwise the "
        "user still hits the bad-object error."
    )
    assert "${PIPESTATUS[0]}" in block, (
        "fetch block must check ${PIPESTATUS[0]} for git's exit code rather "
        "than the pipeline's overall status — `tee` always succeeds."
    )


def test_install_sh_recovers_from_stale_remote_ref(tmp_path: Path) -> None:
    """Behavioral repro: drive the extracted fetch block with a fake `git`
    that fails the first fetch with the canonical stale-ref error, then
    succeeds after `git remote prune origin`. The block must:

      * detect the stale-ref error,
      * invoke `git remote prune origin` exactly once,
      * retry `git fetch origin` exactly once,
      * exit 0.
    """
    calls = tmp_path / "calls"
    state = tmp_path / "fetch_count"
    state.write_text("0")

    fake_git = tmp_path / "git"
    fake_git.write_text(
        textwrap.dedent(
            f"""\
            #!/bin/bash
            # Log every invocation (one args-line per call) so the test can
            # assert ordering.
            echo "$*" >> {calls!s}
            case "$1" in
                fetch)
                    if [ "$2" = "origin" ]; then
                        count=$(cat {state!s})
                        if [ "$count" = "0" ]; then
                            echo "1" > {state!s}
                            echo "fatal: bad object refs/remotes/origin/bb/tui-ctrlj-newline" >&2
                            exit 128
                        fi
                        exit 0
                    fi
                    exit 0
                    ;;
                remote)
                    # `git remote prune origin` — succeed silently.
                    exit 0
                    ;;
                *)
                    exit 0
                    ;;
            esac
            """
        )
    )
    fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    block = _extract_update_fetch_block()

    # Minimal harness that defines the log_* helpers and a stripped-down
    # variable shape (BRANCH, etc.) used by the block. The block uses
    # `local`, so it must run inside a function — wrap it in `_run_block()`
    # to match install.sh's `clone_repo()` context. The fake `git` is
    # exposed via PATH.
    harness = textwrap.dedent(
        """\
        set -e
        log_info()    { echo "[info] $1"; }
        log_warn()    { echo "[warn] $1"; }
        log_error()   { echo "[error] $1"; }
        log_success() { echo "[ok] $1"; }
        BRANCH=main
        _run_block() {
        """
    ) + block + "\n}\n_run_block\n"

    env = {
        **os.environ,
        "PATH": f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    result = subprocess.run(
        ["bash", "-c", harness],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    assert result.returncode == 0, (
        f"install.sh fetch block exited {result.returncode} — recovery did not "
        f"complete.\nstdout={result.stdout}\nstderr={result.stderr}"
    )

    call_lines = calls.read_text().splitlines()
    fetch_calls = [c for c in call_lines if c.startswith("fetch origin")]
    prune_calls = [c for c in call_lines if c.startswith("remote prune origin")]

    assert len(fetch_calls) == 2, (
        f"expected exactly 2 `git fetch origin` calls (initial + retry); "
        f"got {len(fetch_calls)}. calls={call_lines}"
    )
    assert len(prune_calls) == 1, (
        f"expected exactly 1 `git remote prune origin` call; got "
        f"{len(prune_calls)}. calls={call_lines}"
    )
    # Order: fetch (fail) → prune → fetch (retry).
    fetch_idxs = [i for i, c in enumerate(call_lines) if c.startswith("fetch origin")]
    prune_idx = next(
        i for i, c in enumerate(call_lines) if c.startswith("remote prune origin")
    )
    assert fetch_idxs[0] < prune_idx < fetch_idxs[1], (
        f"call order must be fetch → prune → fetch; got {call_lines}"
    )
    assert "Stale refs cleaned up" in result.stdout, (
        f"recovery success message missing — user would not see that "
        f"install.sh recovered transparently. stdout={result.stdout}"
    )


def test_install_sh_unrelated_fetch_error_still_aborts(tmp_path: Path) -> None:
    """Negative test: a non-stale-ref fetch failure (e.g. network) must still
    cause install.sh to abort with exit 1, not silently retry. Otherwise the
    recovery branch over-applies and masks real errors."""
    calls = tmp_path / "calls"
    fake_git = tmp_path / "git"
    fake_git.write_text(
        textwrap.dedent(
            f"""\
            #!/bin/bash
            echo "$*" >> {calls!s}
            if [ "$1 $2" = "fetch origin" ]; then
                echo "fatal: unable to access 'https://github.com/...': Could not resolve host: github.com" >&2
                exit 128
            fi
            exit 0
            """
        )
    )
    fake_git.chmod(fake_git.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

    block = _extract_update_fetch_block()
    harness = textwrap.dedent(
        """\
        set -e
        log_info()    { echo "[info] $1"; }
        log_warn()    { echo "[warn] $1"; }
        log_error()   { echo "[error] $1"; }
        log_success() { echo "[ok] $1"; }
        BRANCH=main
        _run_block() {
        """
    ) + block + "\n}\n_run_block\n"

    env = {
        **os.environ,
        "PATH": f"{tmp_path}{os.pathsep}{os.environ.get('PATH', '')}",
    }
    result = subprocess.run(
        ["bash", "-c", harness],
        capture_output=True,
        text=True,
        env=env,
        cwd=tmp_path,
    )

    assert result.returncode != 0, (
        "block must abort on non-stale-ref fetch errors — otherwise it masks "
        "real network/auth failures.\n"
        f"stdout={result.stdout}\nstderr={result.stderr}"
    )
    call_lines = calls.read_text().splitlines()
    fetch_calls = [c for c in call_lines if c.startswith("fetch origin")]
    prune_calls = [c for c in call_lines if c.startswith("remote prune origin")]
    assert len(fetch_calls) == 1, (
        f"network errors must NOT trigger a retry; got {len(fetch_calls)} "
        f"fetch calls. calls={call_lines}"
    )
    assert len(prune_calls) == 0, (
        f"network errors must NOT run `git remote prune origin`; got "
        f"{len(prune_calls)} prune calls. calls={call_lines}"
    )
