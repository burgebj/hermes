"""Achievement engine.

The orchestrator calls :func:`evaluate_after_correct` after a correct guess
is recorded, and :func:`evaluate_after_wrong` after a wrong guess. Both
return a list of newly-awarded achievement keys.

Achievements are deliberately additive — once awarded, they stay awarded.
The evaluator is idempotent: multiple correct answers in the same day will
not award a streak achievement twice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from . import state


@dataclass(frozen=True)
class Achievement:
    key: str
    title: str
    description: str


CATALOG: Dict[str, Achievement] = {
    "first_sight": Achievement(
        key="first_sight",
        title="First Sight",
        description="Played your first On-This-Day challenge.",
    ),
    "historian_i": Achievement(
        key="historian_i",
        title="Historian I",
        description="Got 3 correct answers.",
    ),
    "historian_ii": Achievement(
        key="historian_ii",
        title="Historian II",
        description="Got 10 correct answers.",
    ),
    "streak_spark": Achievement(
        key="streak_spark",
        title="Streak Spark",
        description="3 days in a row with a correct answer.",
    ),
    "calendar_beast": Achievement(
        key="calendar_beast",
        title="Calendar Beast",
        description="7 days in a row with a correct answer.",
    ),
    "no_hints_needed": Achievement(
        key="no_hints_needed",
        title="No Hints Needed",
        description="Got it right on the first try with no hints.",
    ),
    "cold_case": Achievement(
        key="cold_case",
        title="Cold Case",
        description="Got it right after at least one wrong guess.",
    ),
    "globe_trotter": Achievement(
        key="globe_trotter",
        title="Globe Trotter",
        description="Correct answers from 5 different countries.",
    ),
    "ancient_mode": Achievement(
        key="ancient_mode",
        title="Ancient Mode",
        description="Solved a pre-1000 CE event.",
    ),
    "modern_memory": Achievement(
        key="modern_memory",
        title="Modern Memory",
        description="Solved a post-2000 event.",
    ),
}


def all_keys() -> Set[str]:
    return set(CATALOG.keys())


def evaluate_after_correct(
    *,
    platform: str,
    user_id: str,
    challenge: Dict,
    user_after: Dict,
    wrong_count: int,
    hints_used: int,
) -> List[str]:
    """Run the rule set; award any new achievements; return newly-awarded keys.

    Args:
        platform: The user's platform.
        user_id:  The user's stable id on that platform.
        challenge: dict-shape result of :func:`state.get_challenge`.
        user_after: dict returned by :func:`state.update_streak_after_correct`.
        wrong_count: number of wrong/close guesses by this user on this challenge.
        hints_used:  number of hints recorded against the challenge.
    """
    awarded: List[str] = []

    def maybe(key: str) -> None:
        if state.award_achievement(platform, user_id, key):
            awarded.append(key)

    maybe("first_sight")

    total_correct = int(user_after.get("total_correct", 0))
    if total_correct >= 3:
        maybe("historian_i")
    if total_correct >= 10:
        maybe("historian_ii")

    streak = int(user_after.get("current_streak", 0))
    if streak >= 3:
        maybe("streak_spark")
    if streak >= 7:
        maybe("calendar_beast")

    if wrong_count == 0 and hints_used == 0:
        maybe("no_hints_needed")
    if wrong_count >= 1:
        maybe("cold_case")

    countries = user_after.get("countries", [])
    if isinstance(countries, list) and len({c for c in countries if c}) >= 5:
        maybe("globe_trotter")

    year = challenge.get("event_year")
    if isinstance(year, int):
        if year < 1000:
            maybe("ancient_mode")
        if year >= 2000:
            maybe("modern_memory")

    return awarded


def evaluate_after_wrong(*, platform: str, user_id: str) -> List[str]:
    """Wrong-only path — currently only awards first_sight."""
    awarded: List[str] = []
    if state.award_achievement(platform, user_id, "first_sight"):
        awarded.append("first_sight")
    return awarded


def render_achievement_line(key: str) -> str:
    """Render a one-line description suitable for chat output."""
    a = CATALOG.get(key)
    if not a:
        return key
    return f"{a.title} — {a.description}"
