"""Prompt-builder anti-spoiler + safety tests."""

from __future__ import annotations

import pytest


def _ev(**kw):
    from scripts.scoring import CandidateEvent

    base = dict(
        summary="Muhammad Ali refused induction into the U.S. Army in Houston, Texas.",
        canonical_answer="Muhammad Ali refused induction",
        year=1967,
        location="Houston, Texas",
        country="United States",
        category="event",
        source="britannica",
    )
    base.update(kw)
    return CandidateEvent(**base)


def test_prompt_does_not_leak_canonical_answer_proper_nouns():
    from scripts import prompt_builder

    ev = _ev()
    prompt = prompt_builder.build_image_prompt(ev, surface_date="April 28")
    low = prompt.lower()
    assert "muhammad" not in low
    assert "ali" not in low.split() or " ali " not in f" {low} "
    assert "u.s. army" not in low
    assert "induction" not in low


def test_prompt_includes_only_location_and_date_and_safety_constraints():
    from scripts import prompt_builder

    ev = _ev()
    prompt = prompt_builder.build_image_prompt(ev, surface_date="April 28")
    assert "Houston, Texas" in prompt
    assert "April 28" in prompt
    assert "no readable text" in prompt.lower()
    assert "no weapons" in prompt.lower()


def test_prompt_safety_blocklist_is_enforced():
    from scripts import prompt_builder

    assert prompt_builder.prompt_passes_safety("a calm street scene") is True
    assert prompt_builder.prompt_passes_safety("a street with blood and guns") is False


def test_disqualified_event_raises():
    from scripts import prompt_builder

    bad = _ev(summary="The school shooting in town X.",
              canonical_answer="school shooting in X")
    with pytest.raises(ValueError):
        prompt_builder.build_image_prompt(bad, surface_date="April 28")


def test_scrub_spoilers_replaces_proper_nouns():
    from scripts import prompt_builder

    ev = _ev()
    out = prompt_builder.scrub_spoilers("Muhammad Ali refused induction in Houston", ev)
    low = out.lower()
    assert "muhammad" not in low
    assert "ali" not in low or " ali" not in f" {low}"


def test_no_central_protagonist_directive_present():
    from scripts import prompt_builder

    ev = _ev()
    prompt = prompt_builder.build_image_prompt(ev, surface_date="April 28")
    assert "no central protagonist" in prompt.lower()
