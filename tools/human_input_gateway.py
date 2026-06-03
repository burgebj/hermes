"""Gateway-side human-input primitive — shared by clarify and interactive_prompt.

Modeled on ``tools.clarify_gateway`` but extended to support:

  * Per-option modal actions (return vs modal popup)
  * Structured file upload results (attachment metadata + cached paths)
  * Prompt-specific auth policies (session_owner_only, etc.)
  * Platform capability negotiation

The blocking pattern is identical to clarify:

  1. ``register()`` creates a pending entry with a ``threading.Event``
  2. ``wait_for_response()`` blocks the agent thread in 1-second slices
     (heartbeat polling keeps the inactivity watchdog alive)
  3. Adapter callbacks fire ``resolve_choice()`` or ``resolve_modal()``
     to unblock the agent thread
  4. ``clear_session()`` cancels everything on session boundary

State is module-level so platform adapters can resolve without holding a
back-reference to the GatewayRunner.
"""

from __future__ import annotations

import logging
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================================================
# Data types
# =========================================================================

@dataclass
class ModalFieldResult:
    """One field value from a modal submission."""
    key: str
    value: Any = None


@dataclass
class FileResult:
    """Structured result for a file upload field."""
    field_key: str
    attachment_id: str
    filename: str
    content_type: str
    size: int
    cached_path: str


@dataclass
class ActorInfo:
    """Who interacted with the prompt."""
    platform: str
    user_id: str
    display_name: str


@dataclass
class HumanInputResult:
    """Structured result returned to the agent thread."""
    status: str  # "selected" | "submitted" | "timeout" | "cancelled"
    choice: Optional[str] = None
    actor: Optional[ActorInfo] = None
    fields: Optional[Dict[str, Any]] = None
    files: Optional[List[FileResult]] = None
    timed_out: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a JSON-friendly dict."""
        result: Dict[str, Any] = {
            "status": self.status,
            "choice": self.choice,
            "timed_out": self.timed_out,
        }
        if self.actor:
            result["actor"] = {
                "platform": self.actor.platform,
                "user_id": self.actor.user_id,
                "display_name": self.actor.display_name,
            }
        if self.fields:
            result["fields"] = self.fields
        if self.files:
            result["files"] = [
                {
                    "field_key": f.field_key,
                    "attachment_id": f.attachment_id,
                    "filename": f.filename,
                    "content_type": f.content_type,
                    "size": f.size,
                    "cached_path": f.cached_path,
                }
                for f in self.files
            ]
        return result


@dataclass
class _HumanInputEntry:
    """One pending human-input request inside a gateway session."""
    prompt_id: str
    session_key: str
    question: str
    options: List[Dict[str, Any]]
    timeout_seconds: float
    auth_policy: str  # "session_owner_only" | "any_allowed_user" | "any_allowed_role" | "any_allowed_user_or_role"
    origin_user_id: Optional[str] = None
    message_id: Optional[str] = None
    display_type: str = "buttons"  # Currently only "buttons" supported

    # Internal
    event: threading.Event = field(default_factory=threading.Event)
    result: Optional[HumanInputResult] = None
    _resolved: bool = False

    def signature(self) -> Dict[str, object]:
        return {
            "prompt_id": self.prompt_id,
            "session_key": self.session_key,
            "question": self.question,
            "options": self.options,
            "auth_policy": self.auth_policy,
            "origin_user_id": self.origin_user_id,
        }


# =========================================================================
# Module-level state
# =========================================================================

_lock = threading.RLock()
# prompt_id → _HumanInputEntry
_entries: Dict[str, _HumanInputEntry] = {}
# session_key → list[prompt_id]
_session_index: Dict[str, List[str]] = {}

# Per-session notify callbacks (gateway → adapter bridge)
_notify_cbs: Dict[str, Callable[[_HumanInputEntry], None]] = {}


# =========================================================================
# Config helpers
# =========================================================================

def get_interactive_prompt_timeout() -> int:
    """Read the interactive prompt timeout (seconds) from config.

    Defaults to 900 (15 minutes).  Reads
    ``agent.interactive_prompt_timeout`` from config.yaml.
    Falls back to ``agent.clarify_timeout`` if the dedicated key
    is absent, matching the pattern in ``tools.clarify_gateway``.
    """
    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        agent_cfg = cfg.get("agent", {}) or {}
        val = agent_cfg.get("interactive_prompt_timeout")
        if val is not None:
            return int(val)
        return int(agent_cfg.get("clarify_timeout", 900))
    except Exception:
        return 900


# =========================================================================
# ID generation
# =========================================================================

def generate_prompt_id() -> str:
    """Generate an opaque prompt ID for component custom_ids."""
    return uuid.uuid4().hex[:16]


def make_component_custom_id(prompt_id: str, action_id: str) -> str:
    """Build an opaque custom_id for a Discord component."""
    return f"hermes:ip:{prompt_id}:{action_id}"


def make_modal_custom_id(prompt_id: str, action_id: str) -> str:
    """Build an opaque custom_id for a Discord modal."""
    return f"hermes:ip-modal:{prompt_id}:{action_id}"


def parse_custom_id(custom_id: str) -> Optional[tuple]:
    """Parse a custom_id back into (prefix, prompt_id, action_id).

    Returns None if the format doesn't match.
    """
    parts = custom_id.split(":", 3)
    if len(parts) == 4 and parts[0] == "hermes":
        return (parts[1], parts[2], parts[3])
    return None


# =========================================================================
# Public API — agent-thread side
# =========================================================================

def register(
    prompt_id: str,
    session_key: str,
    question: str,
    options: List[Dict[str, Any]],
    timeout_seconds: float,
    auth_policy: str = "session_owner_only",
    origin_user_id: Optional[str] = None,
    display_type: str = "buttons",
) -> _HumanInputEntry:
    """Register a pending human-input request and return the entry."""
    entry = _HumanInputEntry(
        prompt_id=prompt_id,
        session_key=session_key,
        question=question,
        options=list(options),
        timeout_seconds=timeout_seconds,
        auth_policy=auth_policy,
        origin_user_id=origin_user_id,
        display_type=display_type,
    )
    with _lock:
        _entries[prompt_id] = entry
        _session_index.setdefault(session_key, []).append(prompt_id)
    return entry


def wait_for_response(prompt_id: str, timeout: float) -> Optional[HumanInputResult]:
    """Block on the entry's event until resolved or timeout fires.

    Polls in 1-second slices so the agent's inactivity heartbeat keeps
    firing.  Returns a HumanInputResult or None if entry not found.
    """
    with _lock:
        entry = _entries.get(prompt_id)
    if entry is None:
        return None

    try:
        from tools.environments.base import touch_activity_if_due
    except Exception:
        touch_activity_if_due = None

    deadline = time.monotonic() + max(timeout, 0.0)
    activity_state = {"last_touch": time.monotonic(), "start": time.monotonic()}
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        if entry.event.wait(timeout=min(1.0, remaining)):
            break
        if touch_activity_if_due is not None:
            touch_activity_if_due(activity_state, "waiting for user interactive_prompt response")

    with _lock:
        _entries.pop(prompt_id, None)
        ids = _session_index.get(entry.session_key)
        if ids and prompt_id in ids:
            ids.remove(prompt_id)
            if not ids:
                _session_index.pop(entry.session_key, None)

    # If never resolved, produce timeout result
    if entry.result is None:
        entry.result = HumanInputResult(status="timeout", timed_out=True)
    return entry.result


# =========================================================================
# Public API — gateway / adapter side
# =========================================================================

def resolve_choice(
    prompt_id: str,
    choice_value: str,
    actor: Optional[ActorInfo] = None,
) -> bool:
    """Resolve a prompt where the user clicked a 'return' option."""
    with _lock:
        entry = _entries.get(prompt_id)
        if entry is None or entry._resolved:
            return False
        entry._resolved = True
    entry.result = HumanInputResult(
        status="selected",
        choice=choice_value,
        actor=actor,
    )
    entry.event.set()
    return True


def resolve_modal(
    prompt_id: str,
    choice_value: str,
    fields: Optional[Dict[str, Any]] = None,
    files: Optional[List[FileResult]] = None,
    actor: Optional[ActorInfo] = None,
) -> bool:
    """Resolve a prompt where the user submitted a modal."""
    with _lock:
        entry = _entries.get(prompt_id)
        if entry is None or entry._resolved:
            return False
        entry._resolved = True
    entry.result = HumanInputResult(
        status="submitted",
        choice=choice_value,
        actor=actor,
        fields=fields or {},
        files=files or [],
    )
    entry.event.set()
    return True


def get_entry(prompt_id: str) -> Optional[_HumanInputEntry]:
    """Look up a pending entry by prompt_id."""
    with _lock:
        return _entries.get(prompt_id)


def get_option_by_index(prompt_id: str, index: int) -> Optional[Dict[str, Any]]:
    """Look up an option by its index in the entry's options list."""
    with _lock:
        entry = _entries.get(prompt_id)
        if entry is None or index < 0 or index >= len(entry.options):
            return None
        return entry.options[index]


def has_pending(session_key: str) -> bool:
    """Return True when this session has at least one pending entry."""
    with _lock:
        ids = _session_index.get(session_key) or []
        return any(_entries.get(cid) is not None for cid in ids)


def clear_session(session_key: str) -> int:
    """Cancel every pending entry for a session.

    Returns the number of entries cancelled.
    """
    with _lock:
        ids = list(_session_index.pop(session_key, []) or [])
        entries = [_entries.pop(cid, None) for cid in ids]
    cancelled = 0
    for entry in entries:
        if entry is None:
            continue
        entry.result = HumanInputResult(status="cancelled")
        entry.event.set()
        cancelled += 1
    return cancelled


def clear_all() -> int:
    """Cancel every pending entry across all sessions.

    Called during gateway shutdown so in-flight interactive prompts
    resolve immediately instead of hanging until their timeout.
    Returns the total number of entries cancelled.
    """
    with _lock:
        all_ids = list(_entries.keys())
        _session_index.clear()
        entries = [_entries.pop(cid, None) for cid in all_ids]
    cancelled = 0
    for entry in entries:
        if entry is None:
            continue
        entry.result = HumanInputResult(status="cancelled")
        entry.event.set()
        cancelled += 1
    return cancelled


# =========================================================================
# Per-session notify hook (gateway → adapter bridge)
# =========================================================================

def register_notify(session_key: str, cb: Callable[[_HumanInputEntry], None]) -> None:
    """Register a per-session notify callback."""
    with _lock:
        _notify_cbs[session_key] = cb


def unregister_notify(session_key: str) -> None:
    """Drop the notify callback and cancel pending entries."""
    with _lock:
        _notify_cbs.pop(session_key, None)
    clear_session(session_key)


def get_notify(session_key: str) -> Optional[Callable[[_HumanInputEntry], None]]:
    with _lock:
        return _notify_cbs.get(session_key)


# ---------------------------------------------------------------------------
# Testing helpers (not public API)
# ---------------------------------------------------------------------------

def _reset_for_testing() -> None:
    """Clear all module state.  For test use only."""
    with _lock:
        _entries.clear()
        _session_index.clear()
        _notify_cbs.clear()
