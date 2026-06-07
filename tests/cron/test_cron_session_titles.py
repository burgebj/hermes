"""Regression test for cron session titles.

A finished cron run used to leave its session title NULL, so the desktop /
dashboard fell back to rendering the raw cron prompt (e.g.
"[IMPORTANT: You are ru...") as the title for every run. The scheduler now
stamps a clean "⏰ <job name> · <Mon DD YYYY>" title on completion, retrying
with a more specific (time-stamped) candidate when the same job completes
twice in one day and hits the unique-title constraint.

These tests exercise the title-generation + collision-retry contract directly
against a real SessionDB, which is the integration point the scheduler relies
on (set_session_title raising ValueError on a duplicate title).
"""

import datetime
from pathlib import Path

import pytest

from hermes_state import SessionDB


@pytest.fixture
def db(tmp_path):
    store = SessionDB(tmp_path / "sessions.db")
    yield store
    store.close()


def _candidates(job_name: str, when: datetime.datetime):
    """Mirror the scheduler's candidate ladder for a fixed timestamp."""
    base = f"\u23f0 {job_name} \u00b7 {when.strftime('%b %d %Y')}"[:100]
    return [
        base,
        f"{base[:92]} {when.strftime('%H:%M')}",
        f"{base[:89]} {when.strftime('%H:%M:%S')}",
    ]


def _apply_title(db, session_id, candidates):
    """Mirror the scheduler's set-with-retry loop; return the title that stuck."""
    for candidate in candidates:
        try:
            if db.set_session_title(session_id, candidate):
                return candidate
        except ValueError:
            continue
    return None


def test_cron_title_is_human_readable(db):
    sid = db.create_session("cron-1", "cron")
    when = datetime.datetime(2026, 6, 5, 9, 0, 0)

    title = _apply_title(db, sid, _candidates("Daily Briefing", when))

    assert title == "\u23f0 Daily Briefing \u00b7 Jun 05 2026"
    assert db.get_session_title(sid) == title
    # Never the raw-prompt fallback.
    assert not title.startswith("[")


def test_same_job_same_day_falls_back_to_timestamped_candidate(db):
    when = datetime.datetime(2026, 6, 5, 9, 0, 0)
    sid_a = db.create_session("cron-a", "cron")
    sid_b = db.create_session("cron-b", "cron")

    first = _apply_title(db, sid_a, _candidates("Daily Briefing", when))
    second = _apply_title(db, sid_b, _candidates("Daily Briefing", when))

    # Both got a title, and they differ (the second escalated to include HH:MM).
    assert first and second
    assert first != second
    assert second.endswith("09:00")
    assert db.get_session_title(sid_a) == first
    assert db.get_session_title(sid_b) == second


def test_long_job_name_is_capped_to_max_title_length(db):
    sid = db.create_session("cron-long", "cron")
    when = datetime.datetime(2026, 6, 5, 9, 0, 0)

    title = _apply_title(db, sid, _candidates("X" * 300, when))

    assert title is not None
    assert len(title) <= SessionDB.MAX_TITLE_LENGTH
