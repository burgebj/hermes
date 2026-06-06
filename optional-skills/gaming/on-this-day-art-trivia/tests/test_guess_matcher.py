"""Guess matcher tests."""

from __future__ import annotations


def _accept(*aliases):
    from scripts.guess_matcher import Acceptable, normalize

    return [
        Acceptable(alias=a, alias_normalized=normalize(a), precision_tier=tier)
        for a, tier in aliases
    ]


def test_normalize_strips_punctuation_and_diacritics():
    from scripts.guess_matcher import normalize

    assert normalize("Café — Curaçao!") == "cafe curacao"
    assert normalize("U.S. Army") == "u s army"


def test_exact_alias_is_correct():
    from scripts.guess_matcher import match_guess

    acceptable = _accept(("Muhammad Ali refused induction", 1))
    res = match_guess("Muhammad Ali refused induction", acceptable)
    assert res.outcome == "correct"
    assert res.matched_alias is not None


def test_anchor_token_match_returns_close_for_short_guess():
    from scripts.guess_matcher import build_anchor_tokens, match_guess

    canonical = "Mutiny on the Bounty"
    anchors = build_anchor_tokens(canonical)
    res = match_guess(
        "bounty mutiny",
        _accept(("Mutiny on the Bounty", 1)),
        canonical_anchor_tokens=anchors,
    )
    assert res.outcome in ("correct", "close")


def test_unrelated_guess_is_wrong():
    from scripts.guess_matcher import build_anchor_tokens, match_guess

    canonical = "Muhammad Ali refused induction"
    anchors = build_anchor_tokens(canonical)
    res = match_guess(
        "bananas",
        _accept(("Muhammad Ali refused induction", 1)),
        canonical_anchor_tokens=anchors,
    )
    assert res.outcome == "wrong"


def test_substring_alias_in_guess_is_correct():
    from scripts.guess_matcher import match_guess

    res = match_guess(
        "i think it was the mutiny on the bounty in 1789",
        _accept(("Mutiny on the Bounty", 1)),
    )
    assert res.outcome == "correct"


def test_close_path_short_one_word_is_wrong():
    from scripts.guess_matcher import build_anchor_tokens, match_guess

    canonical = "Muhammad Ali refused induction"
    anchors = build_anchor_tokens(canonical)
    res = match_guess(
        "war",
        _accept(("Muhammad Ali refused induction", 1)),
        canonical_anchor_tokens=anchors,
    )
    assert res.outcome == "wrong"
