"""Contain the bundled-TUI ``libopentui.so`` ``/tmp`` leak (issue #32283).

The Ink TUI's bundled native helper extracts a ~4.5 MB ``libopentui.so``
to ``os.tmpdir()`` on every render cycle and never reaps prior copies.
On Linux installs where ``/tmp`` lives on the root partition (the
common case), this fills the root disk in ~3 days — ~360-600 new
``.so`` copies per hour, ~38 GB/day — and the agent then errors out
with "no disk space" on every operation.

Until the bundled extractor is patched to cache the file at a stable
path, the Python launcher contains the leak at the *spawner* layer:

1. Point ``TMPDIR`` at a profile-scoped directory under ``HERMES_HOME``
   so the leak can never exhaust the root partition (the scoped dir is
   on whichever filesystem the user already accepted for Hermes state).
2. Sweep stale leak files (``.<hex>-<digits>.so``) from both ``/tmp``
   and the scoped directory before spawning the TUI, so a long-running
   user doesn't carry yesterday's leak forward.

The sweep is *only* against the leak-specific filename pattern — it
never touches well-formed shared objects, lockfiles, or anything else
that legitimately lives in ``/tmp``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

# Leak filenames look like ``/tmp/.f9f3dfe75bcf4fff-00000000.so`` —
# a leading dot, lowercase-hex digest (16 chars in the wild but other
# extractor builds use 8–32), a dash, a decimal counter, ``.so``.
# This is deliberately tight so we never sweep an unrelated ``.so``.
_LEAK_RE = re.compile(r"^\.[0-9a-f]{8,32}-\d{1,12}\.so$")


def is_leak_filename(name: str) -> bool:
    """True for ``.<hex>-<digits>.so`` filenames produced by the leak."""
    return bool(_LEAK_RE.match(name))


def sweep_libopentui_leaks(roots: Iterable[Path]) -> int:
    """Unlink stale leak files in each root; return the number removed.

    Missing roots, non-directory roots, and per-file ``unlink`` errors
    are swallowed — sweeping is best-effort and must never block the
    TUI from launching.
    """
    freed = 0
    for root in roots:
        try:
            entries = list(root.iterdir())
        except (FileNotFoundError, NotADirectoryError, PermissionError, OSError):
            continue
        for entry in entries:
            if not is_leak_filename(entry.name):
                continue
            try:
                entry.unlink()
            except OSError:
                continue
            freed += 1
    return freed


def prepare_tui_tmpdir(env: dict, hermes_home: Path) -> Path:
    """Point ``TMPDIR`` at a profile-scoped path and sweep prior leaks.

    If the caller already set ``TMPDIR`` in ``env`` we honour it (the
    user/operator may have a deliberate redirect, e.g. tmpfs mount) and
    only sweep that location plus ``/tmp``.

    Returns the scoped tmpdir path.
    """
    existing = (env.get("TMPDIR") or "").strip()
    if existing:
        scoped = Path(existing)
    else:
        scoped = hermes_home / "run" / "tui-tmp"
        env["TMPDIR"] = str(scoped)

    try:
        scoped.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

    roots = [scoped]
    # ``/tmp`` only exists on POSIX-like systems; the bug is Linux-only
    # in practice (Windows has no ``/tmp`` and macOS ``$TMPDIR`` already
    # points at a per-user dir under ``/var/folders``).
    if os.name == "posix":
        roots.append(Path("/tmp"))

    sweep_libopentui_leaks(roots)
    return scoped
