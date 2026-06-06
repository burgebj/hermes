#!/usr/bin/env python3
"""
State Persistence — Periodic snapshots of live conversation state for crash recovery.

Saves conversation messages, tool results, and agent state to a recovery
file that can be restored on restart. Designed to survive process crashes.
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home


STATE_DIR = get_hermes_home() / "state"
MAX_SNAPSHOTS = 5


def _ensure_state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def _state_path(session_id: str) -> Path:
    return _ensure_state_dir() / f"session_{session_id}.json"


def save_conversation_state(
    session_id: str,
    messages: List[Dict[str, Any]],
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Save conversation state to disk for crash recovery.

    Args:
        session_id: Current session identifier
        messages: List of conversation messages (OpenAI format)
        metadata: Optional dict with agent state info (provider, model, etc.)

    Returns:
        True if state was saved, False otherwise
    """
    path = _state_path(session_id)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")

    snapshot = {
        "session_id": session_id,
        "saved_at": time.time(),
        "message_count": len(messages),
        "messages": messages,
        "metadata": metadata or {},
    }

    try:
        tmp.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(path)
        _prune_stale_snapshots()
        return True
    except (OSError, TypeError) as e:
        if tmp.exists():
            tmp.unlink()
        return False


def load_conversation_state(session_id: str) -> Optional[Dict[str, Any]]:
    """Load a previously saved conversation state.

    Args:
        session_id: Session identifier to restore

    Returns:
        Dict with 'messages' and 'metadata' keys, or None if not found
    """
    path = _state_path(session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "messages": data.get("messages", []),
            "metadata": data.get("metadata", {}),
            "saved_at": data.get("saved_at", 0),
            "message_count": data.get("message_count", 0),
        }
    except (json.JSONDecodeError, OSError):
        return None


def has_recovery_state(session_id: str) -> bool:
    """Check if a recovery state exists for the given session."""
    return _state_path(session_id).exists()


def discard_recovery_state(session_id: str) -> None:
    """Remove a saved recovery state (call after successful resume)."""
    path = _state_path(session_id)
    if path.exists():
        path.unlink()


def list_recovery_sessions() -> List[str]:
    """List all session IDs that have recovery state available."""
    if not STATE_DIR.exists():
        return []
    sessions = []
    for f in STATE_DIR.iterdir():
        if f.suffix == ".json" and f.name.startswith("session_"):
            sid = f.stem[len("session_"):]
            sessions.append(sid)
    return sessions


def _prune_stale_snapshots() -> None:
    """Remove oldest snapshots when exceeding MAX_SNAPSHOTS."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    snapshots = sorted(
        [f for f in STATE_DIR.iterdir() if f.suffix == ".json" and f.name.startswith("session_")],
        key=lambda f: f.stat().st_mtime,
    )
    while len(snapshots) > MAX_SNAPSHOTS:
        oldest = snapshots.pop(0)
        try:
            oldest.unlink()
        except OSError:
            pass