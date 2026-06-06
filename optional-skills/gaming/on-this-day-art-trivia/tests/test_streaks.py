"""Streak update tests."""

from __future__ import annotations


def test_first_correct_starts_streak_at_one(tmp_db):
    from scripts import state

    state.upsert_user("telegram", "u1", "alice")
    out = state.update_streak_after_correct("telegram", "u1", "2026-04-28", "United States")
    assert out["current_streak"] == 1
    assert out["longest_streak"] == 1
    assert out["total_correct"] == 1
    assert "United States" in out["countries"]


def test_consecutive_days_extend_streak(tmp_db):
    from scripts import state

    state.upsert_user("telegram", "u1", None)
    state.update_streak_after_correct("telegram", "u1", "2026-04-28", None)
    state.update_streak_after_correct("telegram", "u1", "2026-04-29", None)
    out = state.update_streak_after_correct("telegram", "u1", "2026-04-30", None)
    assert out["current_streak"] == 3
    assert out["longest_streak"] == 3


def test_gap_resets_streak(tmp_db):
    from scripts import state

    state.upsert_user("telegram", "u1", None)
    state.update_streak_after_correct("telegram", "u1", "2026-04-28", None)
    out = state.update_streak_after_correct("telegram", "u1", "2026-05-02", None)
    assert out["current_streak"] == 1
    assert out["longest_streak"] == 1


def test_same_day_repeat_does_not_double_count_streak(tmp_db):
    from scripts import state

    state.upsert_user("telegram", "u1", None)
    state.update_streak_after_correct("telegram", "u1", "2026-04-28", None)
    out = state.update_streak_after_correct("telegram", "u1", "2026-04-28", None)
    assert out["current_streak"] == 1


def test_reset_streak_after_failure(tmp_db):
    from scripts import state

    state.upsert_user("telegram", "u1", None)
    state.update_streak_after_correct("telegram", "u1", "2026-04-28", None)
    state.update_streak_after_correct("telegram", "u1", "2026-04-29", None)
    state.reset_streak("telegram", "u1")
    user = state.get_user("telegram", "u1")
    assert user["current_streak"] == 0
    assert user["longest_streak"] == 2
