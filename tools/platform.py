"""Windows Native Platform Utilities for Hermes Agent.

Central place for OS detection, path conversion (Git Bash ↔ Windows),
and subprocess settings.
"""

import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict

# =============================================================================
# Platform Detection
# =============================================================================
IS_WINDOWS = os.name == "nt"
IS_LINUX = os.name == "posix" and platform.system() == "Linux"
IS_MACOS = platform.system() == "Darwin"


def is_windows() -> bool:
    """Explicit runtime check."""
    return IS_WINDOWS


# =============================================================================
# Path Helpers
# =============================================================================
def to_native_path(path: str | Path) -> str:
    """Convert path to native Windows format (backslashes)."""
    if not IS_WINDOWS:
        return str(path)

    p = Path(path)
    if str(p).startswith(("/c/", "/C/")):
        return str(p).replace("/c/", "C:\\", 1).replace("/C/", "C:\\", 1).replace("/", "\\")
    return str(p).replace("/", "\\")


def to_git_bash_path(path: str | Path) -> str:
    """Convert Windows path to Git Bash style (/c/Users/...)."""
    if not IS_WINDOWS:
        return str(path)

    p = Path(path).resolve()
    if p.drive:
        drive = p.drive.lower().replace(":", "")
        rest = p.as_posix()[2:]
        return f"/{drive}{rest}"
    return str(p).replace("\\", "/")


def to_posix_path(path: str | Path) -> str:
    """Alias for forward-slash paths."""
    return to_git_bash_path(path) if IS_WINDOWS else str(path)


# =============================================================================
# Subprocess Helpers
# =============================================================================
def get_subprocess_kwargs(
    hidden: bool = True,
    detached: bool = True,
) -> Dict[str, Any]:
    """Return best subprocess kwargs for Windows (no console popup)."""
    if not IS_WINDOWS:
        return {"start_new_session": True} if detached else {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 0  # SW_HIDE

    creationflags = 0
    if hidden:
        creationflags |= subprocess.CREATE_NO_WINDOW
    if detached:
        creationflags |= subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP

    return {
        "startupinfo": startupinfo,
        "creationflags": creationflags,
        "start_new_session": False,
    }