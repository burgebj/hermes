"""Achievement-engine tests."""

from __future__ import annotations


def test_first_sight_awarded_on_first_correct(tmp_db):
    from scripts import achievements, state

    state.upsert_user("telegram", "u1", None)
    challenge = {"event_year": 1967, "country": "United States"}
    user_after = {"current_streak": 1, "longest_streak": 1, "total_correct": 1, "countries": ["United States"]}
    awarded = achievements.evaluate_after_correct(
        platform="telegram", user_id="u1",
        challenge=challenge, user_after=user_after,
        wrong_count=0, hints_used=0,
    )
    assert "first_sight" in awarded
    assert "no_hints_needed" in awarded


def test_historian_thresholds(tmp_db):
    from scripts import achievements

    awarded3 = achievements.evaluate_after_correct(
        platform="telegram", user_id="u2",
        challenge={"event_year": 1900, "country": "X"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 3, "countries": ["X"]},
        wrong_count=0, hints_used=0,
    )
    assert "historian_i" in awarded3

    awarded10 = achievements.evaluate_after_correct(
        platform="telegram", user_id="u3",
        challenge={"event_year": 1900, "country": "X"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 10, "countries": ["X"]},
        wrong_count=0, hints_used=0,
    )
    assert "historian_ii" in awarded10


def test_streak_achievements(tmp_db):
    from scripts import achievements

    awarded3 = achievements.evaluate_after_correct(
        platform="telegram", user_id="u4",
        challenge={"event_year": 1900, "country": "X"},
        user_after={"current_streak": 3, "longest_streak": 3, "total_correct": 3, "countries": ["X"]},
        wrong_count=0, hints_used=0,
    )
    assert "streak_spark" in awarded3

    awarded7 = achievements.evaluate_after_correct(
        platform="telegram", user_id="u5",
        challenge={"event_year": 1900, "country": "X"},
        user_after={"current_streak": 7, "longest_streak": 7, "total_correct": 7, "countries": ["X"]},
        wrong_count=0, hints_used=0,
    )
    assert "calendar_beast" in awarded7


def test_cold_case_only_when_wrong_attempts(tmp_db):
    from scripts import achievements

    none_awarded = achievements.evaluate_after_correct(
        platform="telegram", user_id="u6",
        challenge={"event_year": 1900, "country": "X"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 1, "countries": ["X"]},
        wrong_count=0, hints_used=0,
    )
    assert "cold_case" not in none_awarded

    cold = achievements.evaluate_after_correct(
        platform="telegram", user_id="u7",
        challenge={"event_year": 1900, "country": "X"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 1, "countries": ["X"]},
        wrong_count=1, hints_used=0,
    )
    assert "cold_case" in cold


def test_globe_trotter_at_five_countries(tmp_db):
    from scripts import achievements

    awarded = achievements.evaluate_after_correct(
        platform="telegram", user_id="u8",
        challenge={"event_year": 1900, "country": "E"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 5,
                    "countries": ["A", "B", "C", "D", "E"]},
        wrong_count=0, hints_used=0,
    )
    assert "globe_trotter" in awarded


def test_ancient_and_modern_modes(tmp_db):
    from scripts import achievements

    ancient = achievements.evaluate_after_correct(
        platform="telegram", user_id="u9",
        challenge={"event_year": 800, "country": "Z"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 1, "countries": ["Z"]},
        wrong_count=0, hints_used=0,
    )
    assert "ancient_mode" in ancient

    modern = achievements.evaluate_after_correct(
        platform="telegram", user_id="u10",
        challenge={"event_year": 2010, "country": "Z"},
        user_after={"current_streak": 1, "longest_streak": 1, "total_correct": 1, "countries": ["Z"]},
        wrong_count=0, hints_used=0,
    )
    assert "modern_memory" in modern


def test_award_idempotent(tmp_db):
    from scripts import state

    assert state.award_achievement("telegram", "u11", "first_sight") is True
    assert state.award_achievement("telegram", "u11", "first_sight") is False
