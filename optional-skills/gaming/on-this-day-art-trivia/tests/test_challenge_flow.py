"""End-to-end flow tests using the Wikimedia fixture for offline determinism."""

from __future__ import annotations

from pathlib import Path


def _install_fixture(month: int, day: int, payload):
    import json
    from scripts import sources

    sources.FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    target = sources.FIXTURES_DIR / f"{month:02d}-{day:02d}.json"
    target.write_text(json.dumps(payload), encoding="utf-8")
    return target


def _patch_sources(monkeypatch, payload):
    """Force fetch_all_candidates to return our fixture-derived events."""
    from scripts import sources

    monkeypatch.setattr(sources, "fetch_britannica", lambda m, d, html=None: [])
    monkeypatch.setattr(sources, "fetch_onthisday", lambda m, d, html=None: [])
    monkeypatch.setattr(
        sources,
        "fetch_wikimedia",
        lambda m, d, payload=None: sources.parse_wikimedia_payload(payload),
    )

    return None


def test_start_then_correct_guess_resolves(tmp_db, wikimedia_fixture, monkeypatch):
    import datetime as _dt

    from scripts import challenge, sources, state

    monkeypatch.setattr(
        sources, "fetch_all_candidates",
        lambda m, d: sources.parse_wikimedia_payload(wikimedia_fixture),
    )

    res = challenge.start_challenge(
        platform="telegram", chat_id="cfg-1", user_id="u-flow",
        user_display_name="alice", scope="dm",
        on_date=_dt.date(2026, 4, 28),
        image_generator=lambda prompt, out: None,
        deliver_to_telegram=False,
    )
    assert res is not None
    # Caption must include full date with year.
    assert "April 28, 2001" in res.surface_caption
    # Caption must NOT contain the answer.
    cap_low = res.surface_caption.lower()
    assert "dennis" not in cap_low
    assert "tito" not in cap_low

    chal = state.get_challenge(res.challenge_id)
    assert chal["status"] == "active"

    # Now guess correctly — should use the canonical answer of the selected event.
    g = challenge.handle_guess(
        platform="telegram", chat_id="cfg-1", user_id="u-flow",
        user_display_name="alice",
        guess_text=chal["canonical_answer"],
    )
    assert g is not None
    assert g.outcome == "correct"
    chal2 = state.get_challenge(res.challenge_id)
    assert chal2["status"] == "solved"


def test_three_wrong_answers_exhaust_and_reset_streak(tmp_db, wikimedia_fixture, monkeypatch):
    import datetime as _dt

    from scripts import challenge, sources, state

    monkeypatch.setattr(
        sources, "fetch_all_candidates",
        lambda m, d: sources.parse_wikimedia_payload(wikimedia_fixture),
    )

    state.upsert_user("telegram", "u-fail", "x")
    state.update_streak_after_correct("telegram", "u-fail", "2026-04-27", "X")

    res = challenge.start_challenge(
        platform="telegram", chat_id="cfg-2", user_id="u-fail",
        user_display_name=None, scope="dm",
        on_date=_dt.date(2026, 4, 28),
        image_generator=lambda prompt, out: None,
        deliver_to_telegram=False,
    )
    assert res is not None
    for _ in range(3):
        out = challenge.handle_guess(
            platform="telegram", chat_id="cfg-2", user_id="u-fail",
            user_display_name=None, guess_text="completely wrong",
        )
        assert out is not None
    user = state.get_user("telegram", "u-fail")
    assert user["current_streak"] == 0
    chal = state.get_challenge(res.challenge_id)
    assert chal["status"] == "failed"


def test_caption_contains_only_date_and_location(tmp_db, wikimedia_fixture, monkeypatch):
    import datetime as _dt

    from scripts import challenge, sources

    monkeypatch.setattr(
        sources, "fetch_all_candidates",
        lambda m, d: sources.parse_wikimedia_payload(wikimedia_fixture),
    )

    res = challenge.start_challenge(
        platform="telegram", chat_id="cfg-3", user_id="u",
        user_display_name=None, scope="dm",
        on_date=_dt.date(2026, 4, 28),
        image_generator=lambda prompt, out: None,
        deliver_to_telegram=False,
    )
    assert res is not None
    lines = [l for l in res.surface_caption.splitlines() if l.strip()]
    assert len(lines) == 2, f"expected 2 lines, got {lines!r}"
    # Caption must include full date with year: e.g. "April 28, 2026" or "April 28, 1967"
    date_line = lines[0]
    assert ", " in date_line, f"expected comma separator in date line: {date_line!r}"
    year_part = date_line.rsplit(", ", 1)[-1]
    assert year_part.isdigit() and len(year_part) == 4, f"expected 4-digit year in caption date line: {date_line!r}"
    # Caption must NOT contain the answer/event title
    cap_low = res.surface_caption.lower()
    assert "muhammad" not in cap_low
    assert "ali" not in cap_low or " ali " not in f" {cap_low} "
    # Caption must NOT contain source URL
    assert "http" not in cap_low
    assert "wikimedia" not in cap_low
    assert "britannica" not in cap_low


def test_subscribe_unsubscribe_round_trip(tmp_db):
    from scripts import challenge, state

    challenge.subscribe(platform="telegram", user_id="u-sub", chat_id="c-sub", scope="dm")
    subs = state.list_active_subscriptions()
    assert any(s["user_id"] == "u-sub" for s in subs)
    challenge.unsubscribe(platform="telegram", user_id="u-sub", chat_id="c-sub")
    subs = state.list_active_subscriptions()
    assert not any(s["user_id"] == "u-sub" for s in subs)
