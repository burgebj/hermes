"""Gateway-side clarify primitive (blocking event-based queue).

The ``clarify`` tool needs to ask the user a question and block the agent
thread until they respond.  In CLI mode this is trivial — ``input()`` is
synchronous.  In gateway mode the agent runs on a worker thread while the
event loop handles the user's reply, so we need a thread-safe primitive
that:

  * stores a pending clarify request (with a generated ``clarify_id``),
  * blocks the agent thread on an ``Event``,
  * resolves the wait when the gateway's button-callback or text-intercept
    fires ``resolve_gateway_clarify(clarify_id, response)``,
  * supports timeouts so a user who never responds does NOT hang the agent
    thread forever (which would also pin the gateway's running-agent guard).

State is module-level (same shape as ``tools.approval``) so platform
adapters can call ``resolve_gateway_clarify`` without holding a back-
reference to the ``GatewayRunner`` instance.

Two delivery paths from the adapter:

  1. **Button UI** — adapters override ``send_clarify`` to render inline
     buttons (e.g. Telegram ``InlineKeyboardMarkup``).  The button
     callback resolves with the chosen string.  A final "Other (type
     answer)" button enters text-capture mode for free-form responses.

  2. **Text fallback** — adapters without rich UI render a numbered list.
     The user replies with a number ("2") or with free text; the gateway's
     ``_handle_message`` intercepts the reply and resolves directly.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =========================================================================
# Module-level state
# =========================================================================

@dataclass
class _ClarifyEntry:
    """One pending clarify request inside a gateway session."""
    clarify_id: str
    session_key: str
    question: str
    choices: Optional[List[str]]
    event: threading.Event = field(default_factory=threading.Event)
    response: Optional[str] = None
    awaiting_text: bool = False  # set when user picked "Other" or clarify is open-ended
    registered_at: float = field(default_factory=time.time)
    # True when this entry was restored from disk after a gateway restart —
    # no agent thread is waiting on ``event``.  The button callback can
    # still record the user's response (so the tap is acknowledged instead
    # of silently dropped — see #32762) but the agent run that originally
    # asked is gone, and the user will need to re-trigger it.
    restored: bool = False

    def signature(self) -> Dict[str, object]:
        return {
            "clarify_id": self.clarify_id,
            "session_key": self.session_key,
            "question": self.question,
            "choices": list(self.choices) if self.choices else None,
        }

    def to_dict(self) -> Dict[str, object]:
        """Serialize the persistable fields (excludes runtime-only Event/response)."""
        return {
            "clarify_id": self.clarify_id,
            "session_key": self.session_key,
            "question": self.question,
            "choices": list(self.choices) if self.choices else None,
            "awaiting_text": self.awaiting_text,
            "registered_at": self.registered_at,
        }


_lock = threading.RLock()
# clarify_id → _ClarifyEntry  (primary lookup for button callbacks)
_entries: Dict[str, _ClarifyEntry] = {}
# session_key → list[clarify_id]  (FIFO; for text-fallback intercept and session cleanup)
_session_index: Dict[str, List[str]] = {}


# =========================================================================
# On-disk persistence (#32762)
# =========================================================================
# In-memory state is lost when the gateway receives SIGTERM (launchd
# watchdog, systemd unit restart, ``hermes gateway restart``, etc).  Any
# button tap that arrives during the window between "agent posted the
# clarify prompt" and "gateway came back up" used to silently fail
# (``resolve_gateway_clarify`` returned False with no user feedback).
#
# We persist a minimal JSON sidecar so the next process can re-hydrate
# pending entries on startup, expire any that aged past the timeout, and
# at least acknowledge late taps to the user.  The agent thread that
# called ``wait_for_response`` is gone after a restart — restored entries
# carry ``restored=True`` so callers can tell the difference and surface
# the right message ("session was restarted; please /retry").
_PERSIST_FILENAME = "clarify_pending.json"
_persist_path_override: Optional[Path] = None


def _persist_path() -> Optional[Path]:
    """Return the JSON sidecar path, honouring tests' override.

    Returns ``None`` if the Hermes home directory can't be located — in
    which case persistence is silently skipped and the module degrades to
    its old in-memory-only behaviour.
    """
    if _persist_path_override is not None:
        return _persist_path_override
    try:
        from hermes_constants import get_hermes_home
        return get_hermes_home() / _PERSIST_FILENAME
    except Exception:
        return None


def set_persist_path(path: Optional[Path]) -> None:
    """Override the persistence path (test seam)."""
    global _persist_path_override
    _persist_path_override = path


def _atomic_write_json(path: Path, payload: object) -> None:
    """Write ``payload`` to ``path`` atomically via a sibling tempfile.

    Never raises — persistence is best-effort; the gateway must keep
    running even if the state dir is read-only or full.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
                fh.flush()
                try:
                    os.fsync(fh.fileno())
                except Exception:
                    pass
            os.replace(tmp, path)
        except Exception:
            try:
                os.unlink(tmp)
            except Exception:
                pass
            raise
    except Exception as exc:  # pragma: no cover - best-effort
        logger.debug("clarify_gateway: persist write failed: %s", exc)


def _flush_persist_locked() -> None:
    """Write the current ``_entries`` snapshot to disk.  Caller holds _lock."""
    path = _persist_path()
    if path is None:
        return
    payload = {
        "version": 1,
        "entries": [e.to_dict() for e in _entries.values()],
    }
    _atomic_write_json(path, payload)


def _load_persist_payload() -> Optional[Dict[str, object]]:
    path = _persist_path()
    if path is None or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("clarify_gateway: persist read failed: %s", exc)
        return None


def restore_pending(
    timeout_seconds: Optional[float] = None,
    now: Optional[float] = None,
) -> List[_ClarifyEntry]:
    """Re-hydrate pending clarify entries from disk.

    Called by the gateway on startup so a button tap that arrives after a
    restart can still be acknowledged (#32762).  Entries whose age exceeds
    ``timeout_seconds`` are dropped — the agent that asked has long given
    up.  Returns the list of restored entries (caller can log a count).

    Restored entries carry ``restored=True`` and have no thread waiting on
    their ``event``; ``resolve_gateway_clarify`` still records the
    response so the user-visible tap acknowledgement works.
    """
    payload = _load_persist_payload()
    if not payload:
        return []

    if timeout_seconds is None:
        timeout_seconds = float(get_clarify_timeout())
    if now is None:
        now = time.time()

    restored: List[_ClarifyEntry] = []
    expired = 0
    with _lock:
        for raw in payload.get("entries", []) or []:
            try:
                clarify_id = str(raw["clarify_id"])
                session_key = str(raw["session_key"])
                question = str(raw.get("question") or "")
                choices_raw = raw.get("choices")
                choices = (
                    [str(c) for c in choices_raw]
                    if isinstance(choices_raw, list) and choices_raw
                    else None
                )
                registered_at = float(raw.get("registered_at") or now)
                awaiting_text = bool(raw.get("awaiting_text"))
            except Exception:
                continue

            # Drop entries already older than the timeout — the agent
            # that asked is gone and re-delivering would be confusing.
            age = max(now - registered_at, 0.0)
            if age >= timeout_seconds:
                expired += 1
                continue

            # Don't clobber a live in-memory entry (e.g. duplicate restore).
            if clarify_id in _entries:
                continue

            entry = _ClarifyEntry(
                clarify_id=clarify_id,
                session_key=session_key,
                question=question,
                choices=choices,
                awaiting_text=awaiting_text,
                registered_at=registered_at,
                restored=True,
            )
            _entries[clarify_id] = entry
            _session_index.setdefault(session_key, []).append(clarify_id)
            restored.append(entry)

        if restored or expired:
            _flush_persist_locked()

    if restored:
        logger.info(
            "clarify_gateway: restored %d pending clarify entr%s from disk "
            "(%d expired)",
            len(restored), "y" if len(restored) == 1 else "ies", expired,
        )
    elif expired:
        logger.info(
            "clarify_gateway: dropped %d expired clarify entr%s from disk",
            expired, "y" if expired == 1 else "ies",
        )
    return restored


# =========================================================================
# Public API — agent-thread side
# =========================================================================

def register(
    clarify_id: str,
    session_key: str,
    question: str,
    choices: Optional[List[str]],
) -> _ClarifyEntry:
    """Register a pending clarify request and return the entry.

    The caller (gateway clarify_callback) will then send the prompt to the
    user and block on ``wait_for_response(clarify_id, timeout)``.
    """
    entry = _ClarifyEntry(
        clarify_id=clarify_id,
        session_key=session_key,
        question=question,
        choices=list(choices) if choices else None,
        # Open-ended (no choices) → next message IS the response, no buttons needed.
        awaiting_text=not bool(choices),
    )
    with _lock:
        _entries[clarify_id] = entry
        _session_index.setdefault(session_key, []).append(clarify_id)
        _flush_persist_locked()
    return entry


def wait_for_response(clarify_id: str, timeout: float) -> Optional[str]:
    """Block on the entry's event until resolved or timeout fires.

    Polls in 1-second slices so the agent's inactivity heartbeat keeps
    firing — without this, ``Event.wait(timeout=600)`` blocks the thread
    for 10 minutes with zero activity touches and the gateway's inactivity
    watchdog kills the agent while the user is still typing.

    Returns the resolved response string, or ``None`` on timeout.
    """
    with _lock:
        entry = _entries.get(clarify_id)
    if entry is None:
        return None

    try:
        from tools.environments.base import touch_activity_if_due
    except Exception:  # pragma: no cover - optional
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
            touch_activity_if_due(activity_state, "waiting for user clarify response")

    with _lock:
        # Remove from indices regardless of resolution outcome.
        _entries.pop(clarify_id, None)
        ids = _session_index.get(entry.session_key)
        if ids and clarify_id in ids:
            ids.remove(clarify_id)
            if not ids:
                _session_index.pop(entry.session_key, None)
        _flush_persist_locked()

    return entry.response


# =========================================================================
# Public API — gateway / adapter side
# =========================================================================

def resolve_gateway_clarify(clarify_id: str, response: str) -> bool:
    """Unblock the agent thread waiting on ``clarify_id``.

    Returns True if an entry was found and resolved, False otherwise
    (already resolved, expired, or never existed).

    For entries restored from disk after a gateway restart (#32762), no
    agent thread is waiting — setting ``event`` is a no-op — but we still
    return True so the platform callback can acknowledge the tap to the
    user instead of silently dropping it.  Restored entries are also
    cleaned out of the persistence sidecar immediately, since there's no
    ``wait_for_response`` thread to do it on the way out.
    """
    with _lock:
        entry = _entries.get(clarify_id)
        if entry is None:
            return False
    entry.response = str(response) if response is not None else ""
    entry.event.set()
    if entry.restored:
        # No waiter to clean up after itself — drop it now so the next
        # restart doesn't replay an already-answered entry.
        with _lock:
            _entries.pop(clarify_id, None)
            ids = _session_index.get(entry.session_key)
            if ids and clarify_id in ids:
                ids.remove(clarify_id)
                if not ids:
                    _session_index.pop(entry.session_key, None)
            _flush_persist_locked()
    return True


def was_restored(clarify_id: str) -> bool:
    """Return True if this clarify entry was re-hydrated from disk.

    Lets adapters distinguish "we resolved an active agent's clarify" from
    "we acknowledged a late tap whose agent was lost to a restart" so they
    can tailor the user-visible message (see #32762).
    """
    with _lock:
        entry = _entries.get(clarify_id)
        return bool(entry and entry.restored)


def get_pending_for_session(session_key: str) -> Optional[_ClarifyEntry]:
    """Return the OLDEST pending clarify entry for a session, or None.

    Used by the text-fallback intercept in ``_handle_message`` — when a
    clarify is awaiting a free-form text response, the next user message
    in that session is captured as the answer.
    """
    with _lock:
        ids = _session_index.get(session_key) or []
        for cid in ids:
            entry = _entries.get(cid)
            if entry is None:
                continue
            if entry.awaiting_text:
                return entry
        return None


def mark_awaiting_text(clarify_id: str) -> bool:
    """Flip an entry into text-capture mode (user picked the 'Other' button).

    Returns True if the entry exists and was flipped, False otherwise.
    """
    with _lock:
        entry = _entries.get(clarify_id)
        if entry is None:
            return False
        entry.awaiting_text = True
        _flush_persist_locked()
        return True


def has_pending(session_key: str) -> bool:
    """Return True when this session has at least one pending clarify entry."""
    with _lock:
        ids = _session_index.get(session_key) or []
        return any(_entries.get(cid) is not None for cid in ids)


def clear_session(session_key: str) -> int:
    """Resolve and drop every pending clarify for a session.

    Used by session-boundary cleanup (e.g. ``/new``, gateway shutdown,
    cached-agent eviction) so blocked agent threads don't hang past the
    end of their session.  Returns the number of entries cancelled.
    """
    with _lock:
        ids = list(_session_index.pop(session_key, []) or [])
        entries = [_entries.pop(cid, None) for cid in ids]
        _flush_persist_locked()
    cancelled = 0
    for entry in entries:
        if entry is None:
            continue
        # Empty string sentinel — agent code can distinguish from a real
        # response by inspecting the wait_for_response return value
        # alongside its own timeout deadline.  Most callers just treat any
        # falsy result as "user did not respond".
        entry.response = ""
        entry.event.set()
        cancelled += 1
    return cancelled


# =========================================================================
# Config
# =========================================================================

def get_clarify_timeout() -> int:
    """Read the clarify response timeout (seconds) from config.

    Defaults to 600 (10 minutes) — long enough for the user to type a
    thoughtful response, short enough that an abandoned prompt eventually
    unblocks the agent thread instead of pinning the running-agent guard
    forever.

    Reads ``agent.clarify_timeout`` from config.yaml.
    """
    try:
        from hermes_cli.config import load_config
        cfg = load_config() or {}
        agent_cfg = cfg.get("agent", {}) or {}
        return int(agent_cfg.get("clarify_timeout", 600))
    except Exception:
        return 600


# =========================================================================
# Per-session notify hook (gateway → adapter bridge)
# =========================================================================
# Mirrors tools.approval's _gateway_notify_cbs: the gateway registers a
# per-session callback that sends the clarify prompt to the user.  The
# callback bridges sync→async (runs on the agent thread; schedules the
# adapter ``send_clarify`` call on the event loop).

_notify_cbs: Dict[str, Callable[[_ClarifyEntry], None]] = {}


def register_notify(session_key: str, cb: Callable[[_ClarifyEntry], None]) -> None:
    """Register a per-session notify callback used by ``clarify_callback``."""
    with _lock:
        _notify_cbs[session_key] = cb


def unregister_notify(session_key: str) -> None:
    """Drop the per-session notify callback and cancel any pending clarify entries."""
    with _lock:
        _notify_cbs.pop(session_key, None)
    # Cancel any pending entries so blocked threads unwind when the run
    # ends (interrupt, completion, gateway shutdown).
    clear_session(session_key)


def get_notify(session_key: str) -> Optional[Callable[[_ClarifyEntry], None]]:
    with _lock:
        return _notify_cbs.get(session_key)
