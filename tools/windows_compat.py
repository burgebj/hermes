"""Windows subprocess compatibility helpers.
Hermes is developed on Linux / macOS and tested natively on Windows too.

Several common subprocess patterns break silently-or-loudly on Windows:
* ``["npm", "install", ...]`` — on Windows ``npm`` is ``npm.cmd``, a batch
  shim. ``subprocess.Popen(["npm", ...])`` fails with WinError 193
  ("not a valid Win32 application") because CreateProcessW can't run a
  ``.cmd`` file without ``shell=True`` or PATHEXT resolution.
* ``start_new_session=True`` — on POSIX, this maps to ``os.setsid()`` and
  actually detaches the child. On Windows it's silently ignored; the
  Windows equivalent is ``CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS``
  creationflags, which Python only applies when you pass them explicitly.
* Console-window flashes — every ``subprocess.Popen`` of a ``.exe`` on
  Windows spawns a cmd window briefly unless ``CREATE_NO_WINDOW`` is
  passed. Cosmetic but jarring for background daemons.

This module centralizes the platform-branching logic so the rest of the
codebase doesn't sprinkle ``if sys.platform == "win32":`` everywhere.

**All helpers are no-ops on non-Windows** — calling them in Linux/macOS
code paths is safe by design. That's the "do no damage on POSIX"
guarantee.
"""

import os
import shutil
import subprocess
import sys
from typing import Any, Sequence

__all__ = [
    "IS_WINDOWS",
    "resolve_node_command",
    "windows_detach_flags",
    "windows_hide_flags",
    "windows_detach_popen_kwargs",
    "get_subprocess_kwargs",
]

IS_WINDOWS = sys.platform == "win32"


# -----------------------------------------------------------------------------
# Node ecosystem launcher resolution
# -----------------------------------------------------------------------------
def resolve_node_command(name: str, argv: Sequence[str]) -> list[str]:
    """Resolve a Node-ecosystem command name to an absolute-path argv.

    On Windows, commands like ``npm``, ``npx``, ``yarn``, ``pnpm``,
    ``playwright``, ``prettier`` ship as ``.cmd`` files (batch shims).
    ``subprocess.Popen(["npm", "install"])`` fails with WinError 193
    because CreateProcessW doesn't execute batch files directly.

    ``shutil.which(name)`` *does* resolve ``.cmd`` via PATHEXT and returns
    the fully-qualified path — which CreateProcessW accepts because the
    extension tells Windows to route through ``cmd.exe /c``.
    """
    resolved = shutil.which(name)
    if resolved:
        return [resolved, *argv]
    return [name, *argv]


# -----------------------------------------------------------------------------
# Detached / hidden process creation
# -----------------------------------------------------------------------------
# Win32 CreationFlags — defined here rather than imported from subprocess
# because CREATE_NO_WINDOW and DETACHED_PROCESS aren't guaranteed to be
# present on stdlib subprocess on older Pythons or non-Windows builds.
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_DETACHED_PROCESS = 0x00000008
_CREATE_NO_WINDOW = 0x08000000


def windows_detach_flags() -> int:
    """Return Win32 creationflags that detach a child from the parent
    console and process group. 0 on non-Windows.
    """
    if not IS_WINDOWS:
        return 0
    return _CREATE_NEW_PROCESS_GROUP | _DETACHED_PROCESS | _CREATE_NO_WINDOW


def windows_hide_flags() -> int:
    """Return Win32 creationflags that merely hide the child's console
    window without detaching the child. 0 on non-Windows.
    """
    if not IS_WINDOWS:
        return 0
    return _CREATE_NO_WINDOW


def windows_detach_popen_kwargs() -> dict[str, Any]:
    """Return a dict of Popen kwargs that detach a child on Windows and
    fall back to the POSIX equivalent (``start_new_session=True``) on
    Linux/macOS.
    """
    if IS_WINDOWS:
        return {
            "creationflags": windows_detach_flags(),
            "start_new_session": False,
        }
    return {"start_new_session": True}


def get_subprocess_kwargs(
    detach: bool = False,
    hide: bool = False,
    **extra_kwargs,
) -> dict[str, Any]:
    """Convenience helper for common subprocess patterns."""
    if detach:
        return windows_detach_popen_kwargs()
    if hide and IS_WINDOWS:
        return {"creationflags": windows_hide_flags()}
    return extra_kwargs or {}