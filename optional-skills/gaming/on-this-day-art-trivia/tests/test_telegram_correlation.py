"""Tests for Telegram message_id correlation between challenge and inbound reply."""

from __future__ import annotations


def test_attach_message_id_round_trip(tmp_db):
    from scripts import state

    cid = state.create_challenge(
        platform="telegram", chat_id="c1", scope="dm", user_id="u1",
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="Muhammad Ali refused induction",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("Muhammad Ali refused induction", 1)],
    )
    state.attach_telegram_message_id(cid, "555")
    found = state.get_challenge_by_message_id("telegram", "555")
    assert found is not None
    assert found["challenge_id"] == cid


def test_get_active_challenge_is_chat_scoped(tmp_db):
    from scripts import state

    a = state.create_challenge(
        platform="telegram", chat_id="chat-A", scope="dm", user_id="uA",
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="A canon",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("A canon", 1)],
    )
    b = state.create_challenge(
        platform="telegram", chat_id="chat-B", scope="dm", user_id="uB",
        event_date="April 28", event_year=1789,
        location="South Pacific", country=None,
        canonical_answer="B canon",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("B canon", 1)],
    )
    a_active = state.get_active_challenge_for_chat("telegram", "chat-A")
    b_active = state.get_active_challenge_for_chat("telegram", "chat-B")
    assert a_active and a_active["challenge_id"] == a
    assert b_active and b_active["challenge_id"] == b
