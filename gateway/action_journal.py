"""Durable gateway action journal for restart recovery.

The session transcript tells the model what was said. This journal tells a
restarting gateway what the agent was *doing* when the process stopped: the
turn that was in flight, tool calls that started, and tool calls that finished.
It is intentionally append-only JSONL so it can be written before side effects
without requiring a SQLite migration.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Iterable, Optional

from hermes_constants import get_hermes_home

logger = logging.getLogger(__name__)

_JOURNAL_LOCK = threading.Lock()
_DEFAULT_MAX_TEXT = 500
_DEFAULT_MAX_EVENTS = 5000


def _sanitize_obj(value: Any) -> Any:
    sensitive = {
        "access_token", "refresh_token", "id_token", "token", "api_key",
        "apikey", "client_secret", "password", "auth", "jwt", "secret",
        "private_key", "authorization", "key",
    }
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            key = str(k)
            if key.lower() in sensitive:
                result[key] = "[REDACTED]"
            else:
                result[key] = _sanitize_obj(v)
        return result
    if isinstance(value, list):
        return [_sanitize_obj(v) for v in value]
    return value


def _redact_text(value: Any, *, max_chars: int = _DEFAULT_MAX_TEXT) -> str:
    if value is None:
        return ""
    try:
        if not isinstance(value, str):
            value = json.dumps(_sanitize_obj(value), ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        value = str(value)
    try:
        from agent.redact import redact_sensitive_text
        value = redact_sensitive_text(value)
    except Exception:
        pass
    value = value.replace("\x00", "")
    if len(value) > max_chars:
        return value[: max_chars - 1] + "…"
    return value


def _utc_ts() -> float:
    return time.time()


class ActionJournal:
    """Append-only JSONL journal scoped to the active Hermes profile."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (get_hermes_home() / "action_journal.jsonl")

    def record(self, event: str, **fields: Any) -> None:
        payload = {
            "ts": _utc_ts(),
            "event": event,
        }
        payload.update({k: v for k, v in fields.items() if v is not None})
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            line = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
            with _JOURNAL_LOCK:
                with self.path.open("a", encoding="utf-8") as fh:
                    fh.write(line + "\n")
        except Exception as exc:
            logger.debug("action journal write failed: %s", exc)

    def record_turn_started(
        self,
        *,
        session_id: str,
        session_key: str,
        platform: str = "",
        chat_id: str = "",
        thread_id: str = "",
        user_text: Any = "",
    ) -> None:
        self.record(
            "turn.started",
            session_id=session_id,
            session_key=session_key,
            platform=platform,
            chat_id=str(chat_id or ""),
            thread_id=str(thread_id or ""),
            user_preview=_redact_text(user_text),
        )

    def record_turn_finished(
        self,
        *,
        session_id: str,
        session_key: str,
        status: str,
        error: Any = None,
    ) -> None:
        self.record(
            "turn.finished",
            session_id=session_id,
            session_key=session_key,
            status=status,
            error_preview=_redact_text(error, max_chars=300) if error else None,
        )

    def record_tool_started(
        self,
        *,
        session_id: str,
        session_key: str,
        tool_call_id: str,
        tool_name: str,
        args: Any,
    ) -> None:
        self.record(
            "tool.started",
            session_id=session_id,
            session_key=session_key,
            tool_call_id=str(tool_call_id or ""),
            tool_name=str(tool_name or ""),
            args_preview=_redact_text(args),
        )

    def record_tool_finished(
        self,
        *,
        session_id: str,
        session_key: str,
        tool_call_id: str,
        tool_name: str,
        status: str,
        result: Any = None,
    ) -> None:
        self.record(
            "tool.finished",
            session_id=session_id,
            session_key=session_key,
            tool_call_id=str(tool_call_id or ""),
            tool_name=str(tool_name or ""),
            status=status,
            result_preview=_redact_text(result, max_chars=300) if result is not None else None,
        )

    def recent_events(
        self,
        *,
        session_id: Optional[str] = None,
        session_key: Optional[str] = None,
        limit: int = _DEFAULT_MAX_EVENTS,
    ) -> list[dict[str, Any]]:
        try:
            if not self.path.exists():
                return []
            lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception as exc:
            logger.debug("action journal read failed: %s", exc)
            return []

        events: list[dict[str, Any]] = []
        for line in lines[-max(limit, 1):]:
            try:
                event = json.loads(line)
            except Exception:
                continue
            if session_id and event.get("session_id") != session_id:
                continue
            if session_key and event.get("session_key") != session_key:
                continue
            events.append(event)
        return events


def _latest_turn_slice(events: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items = list(events)
    start_idx = None
    for idx in range(len(items) - 1, -1, -1):
        if items[idx].get("event") == "turn.started":
            start_idx = idx
            break
    if start_idx is None:
        return items[-20:]
    return items[start_idx:]


def format_recovery_context(
    *,
    session_id: str,
    session_key: Optional[str] = None,
    journal: Optional[ActionJournal] = None,
) -> str:
    """Return a compact recovery preflight note for a resume-pending turn."""

    j = journal or ActionJournal()
    events = j.recent_events(session_id=session_id, session_key=session_key)
    if not events and session_key:
        events = j.recent_events(session_key=session_key)
    if not events:
        return ""

    turn_events = _latest_turn_slice(events)
    latest_turn = next((e for e in turn_events if e.get("event") == "turn.started"), None)
    finished = any(e.get("event") == "turn.finished" for e in turn_events)

    started: dict[str, dict[str, Any]] = {}
    completed: list[dict[str, Any]] = []
    for event in turn_events:
        if event.get("event") == "tool.started":
            key = event.get("tool_call_id") or f"{event.get('tool_name')}:{event.get('ts')}"
            started[str(key)] = event
        elif event.get("event") == "tool.finished":
            key = str(event.get("tool_call_id") or "")
            if key and key in started:
                completed.append(event)
                started.pop(key, None)
            else:
                completed.append(event)

    lines = [
        "[Restart recovery preflight — durable action journal context:",
    ]
    if latest_turn and latest_turn.get("user_preview"):
        lines.append(f"- Last user text preview: {latest_turn['user_preview']}")
    if completed:
        rendered = ", ".join(
            f"{e.get('tool_name', 'tool')}={e.get('status', 'finished')}"
            for e in completed[-5:]
        )
        lines.append(f"- Tool/action(s) completed before interruption: {rendered}")
    if started:
        rendered = ", ".join(
            f"{e.get('tool_name', 'tool')} started"
            for e in list(started.values())[-5:]
        )
        lines.append(f"- Tool/action(s) still unresolved at restart: {rendered}")
    elif not finished:
        lines.append("- No unfinished tool start was found, but the turn had not recorded a normal finish.")
    if finished:
        lines.append("- The latest journaled turn recorded a finish; verify transcript/logs before claiming pending work.")
    lines.append(
        "Use this journal plus the transcript/tool results to summarize what was actually accomplished; do not claim nothing was in progress unless this context and transcript both support that.]"
    )
    return "\n".join(lines)
