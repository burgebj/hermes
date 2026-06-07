"""Cross-platform path compatibility helpers."""

from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

IS_WINDOWS = sys.platform == "win32"


def msys_to_windows_path(path: str, *, is_windows: bool | None = None) -> str:
    """Translate Git Bash/MSYS paths to native Windows paths.

    ``/c/Users/name`` becomes ``C:\\Users\\name`` and Git Bash ``/tmp`` maps
    to the host temp directory. Non-Windows hosts and non-MSYS paths are left
    untouched.
    """
    windows = IS_WINDOWS if is_windows is None else is_windows
    if not windows or not path:
        return path

    match = re.match(r"^/([a-zA-Z])(/.*)?$", path)
    if match:
        drive = match.group(1).upper()
        tail = (match.group(2) or "").replace("/", "\\")
        return f"{drive}:{tail or chr(92)}"

    if path == "/tmp" or path.startswith("/tmp/"):
        tail = path[5:].replace("/", "\\") if path.startswith("/tmp/") else ""
        return str(Path(tempfile.gettempdir()) / tail) if tail else tempfile.gettempdir()

    return path


def native_path(path: Any, *, is_windows: bool | None = None) -> str:
    """Return a string path suitable for native filesystem APIs."""
    return msys_to_windows_path(os.fspath(path), is_windows=is_windows)
