"""Event scoring rubric tests."""

from __future__ import annotations


def _ev(**kw):
    from scripts.scoring import CandidateEvent

    base = dict(
        summary="A signed treaty in Paris",
        canonical_answer="Treaty of Paris",
        year=1783,
        location="Paris",
        country="France",
        category="event",
        source="britannica",
    )
    base.update(kw)
    return CandidateEvent(**base)


def test_treaty_event_passes_floor():
    from scripts import scoring

    ev = _ev()
    breakdown = scoring.score_event(ev)
    assert breakdown.score >= 50


def test_birthday_is_penalised():
    from scripts import scoring

    ev = _ev(category="birth", summary="Jessica Alba was born in Pomona, California.",
             canonical_answer="Jessica Alba", year=1981, location="Pomona", country="United States")
    breakdown = scoring.score_event(ev)
    assert breakdown.components.get("birthday_penalty") == -40


def test_obituary_is_penalised_more_than_birthday():
    from scripts import scoring

    ev = _ev(category="death", summary="A famous person died at home.",
             canonical_answer="death of person", year=1995, location=None, country=None)
    breakdown = scoring.score_event(ev)
    assert breakdown.components.get("death_penalty") == -60


def test_disqualifying_phrase_short_circuits():
    from scripts import scoring

    ev = _ev(summary="A school shooting in Anywhere claimed many lives.",
             canonical_answer="school shooting in Anywhere")
    breakdown = scoring.score_event(ev)
    assert breakdown.score == -1000
    assert breakdown.rejected_reason == "graphic_or_exploitative"


def test_rank_filters_low_scores():
    from scripts import scoring

    good = _ev()
    bad = _ev(summary="x", canonical_answer="y", year=None, location=None, country=None)
    ranked = scoring.rank_candidates([bad, good], min_score=50)
    assert len(ranked) == 1
    assert ranked[0] is good


def test_visual_word_bumps_score():
    from scripts import scoring

    plain = _ev(summary="Something happened.", year=None, location=None, country=None,
                category="event")
    visual = _ev(summary="The treaty was signed during a public ceremony.",
                 year=None, location=None, country=None, category="event")
    assert scoring.score_event(visual).score > scoring.score_event(plain).score
