"""Atomic file write operations to prevent TOCTOU race conditions.

SECURITY FIX (V-015): Implements atomic writes using temp files + rename
to prevent Time-of-Check to Time-of-Use race conditions.

CWE-367: Time-of-check Time-of-use (TOCTOU) Race Condition
"""

import os
import tempfile
from pathlib import Path
from typing import Union


def atomic_write(path: Union[str, Path], content: str, mode: str = "w") -> None:
    """Atomically write content to file using temp file + rename.
    
    This prevents TOCTOU race conditions where the file could be
    modified between checking permissions and writing.
    
    Args:
        path: Target file path
        content: Content to write
        mode: Write mode ("w" for text, "wb" for bytes)
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temp file in same directory (same filesystem for atomic rename)
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".tmp_{path.name}.",
        suffix=".tmp"
    )
    
    try:
        if "b" in mode:
            os.write(fd, content if isinstance(content, bytes) else content.encode())
        else:
            os.write(fd, content.encode() if isinstance(content, str) else content)
        os.fsync(fd)  # Ensure data is written to disk
    finally:
        os.close(fd)
    
    # Atomic rename - this is guaranteed to be atomic on POSIX
    os.replace(temp_path, path)


def safe_read_write(path: Union[str, Path], content: str) -> dict:
    """Safely read and write file with TOCTOU protection.
    
    Returns:
        dict with status and error message if any
    """
    try:
        # SECURITY: Use atomic write to prevent race conditions
        atomic_write(path, content)
        return {"success": True, "error": None}
    except PermissionError as e:
        return {"success": False, "error": f"Permission denied: {e}"}
    except OSError as e:
        return {"success": False, "error": f"OS error: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {e}"}
