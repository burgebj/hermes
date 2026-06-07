from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreResult:
    impact: int
    visibility: int
    effort: int
    safety: int
    risk_penalty: int
    priority_score: int


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, int(value)))


def score_opportunity(*, impact: int, visibility: int, effort: int, safety: int, risk_penalty: int) -> ScoreResult:
    impact = _clamp(impact, 0, 5)
    visibility = _clamp(visibility, 0, 5)
    effort = _clamp(effort, 1, 5)
    safety = _clamp(safety, 1, 5)
    risk_penalty = _clamp(risk_penalty, 0, 10)
    return ScoreResult(
        impact=impact,
        visibility=visibility,
        effort=effort,
        safety=safety,
        risk_penalty=risk_penalty,
        priority_score=(impact * 3) + (visibility * 2) + effort + safety - risk_penalty,
    )
