"""Tests for strict gateway auto-continue resume-marker behavior.

A trailing tool result alone is not sufficient to auto-continue gateway work.
Only sessions explicitly marked ``resume_pending`` by gateway restart/shutdown
recovery should receive the restart-resume system note.
"""

from datetime import datetime

from gateway.run import _is_fresh_gateway_interruption
from gateway.session import SessionEntry


def _simulate_strict_auto_continue(
    *,
    resume_entry: SessionEntry | None,
    user_message: str,
    window_secs: float = 3600,
) -> str:
    """Reproduce the strict resume-marker predicate from gateway/run.py."""
    has_resume_pending = bool(
        resume_entry is not None
        and getattr(resume_entry, "resume_pending", False)
    )
    marker_is_fresh = (
        _is_fresh_gateway_interruption(
            getattr(resume_entry, "last_resume_marked_at", None),
            window_secs=window_secs,
        )
        if has_resume_pending
        else False
    )
    if has_resume_pending and marker_is_fresh:
        return (
            "[System note: Your previous turn in this session was interrupted "
            "by a gateway restart. The conversation history below is intact. "
            "If it contains unfinished tool result(s), process them first and "
            "summarize what was accomplished, then address the user's new "
            "message below.]\n\n"
            + user_message
        )
    return user_message


def _pending_entry(*, marked_at=None) -> SessionEntry:
    now = datetime.now()
    return SessionEntry(
        session_key="agent:main:telegram:dm:1",
        session_id="sid",
        created_at=now,
        updated_at=now,
        resume_pending=True,
        resume_reason="restart_timeout",
        last_resume_marked_at=marked_at if marked_at is not None else now,
    )


class TestStrictResumeMarker:
    def test_trailing_tool_result_without_marker_does_not_trigger_note(self):
        result = _simulate_strict_auto_continue(
            resume_entry=None,
            user_message="what happened?",
        )
        assert result == "what happened?"

    def test_explicit_resume_marker_triggers_note(self):
        result = _simulate_strict_auto_continue(
            resume_entry=_pending_entry(),
            user_message="what happened?",
        )
        assert "[System note:" in result
        assert "gateway restart" in result
        assert result.endswith("what happened?")

    def test_pending_entry_without_marker_timestamp_fails_closed(self):
        entry = _pending_entry()
        entry.last_resume_marked_at = None
        result = _simulate_strict_auto_continue(
            resume_entry=entry,
            user_message="start new work",
        )
        assert result == "start new work"

    def test_empty_history_no_note_without_marker(self):
        result = _simulate_strict_auto_continue(
            resume_entry=None,
            user_message="hello",
        )
        assert result == "hello"
