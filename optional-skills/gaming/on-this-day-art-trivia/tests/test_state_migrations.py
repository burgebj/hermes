"""State / migration tests."""

from __future__ import annotations


def test_migrate_creates_all_tables(tmp_db):
    from scripts import state

    with state.get_readonly_conn() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r[0] for r in rows}
    expected = {
        "achievements",
        "acceptable_answers",
        "challenges",
        "guesses",
        "schema_version",
        "subscriptions",
        "users",
    }
    missing = expected - names
    assert not missing, f"missing tables: {missing}"


def test_migrate_is_idempotent(tmp_db):
    from scripts import state

    v1 = state.migrate()
    v2 = state.migrate()
    assert v1 == v2 == state.CURRENT_SCHEMA_VERSION


def test_create_challenge_marks_prior_active_as_expired(tmp_db):
    from scripts import state

    a = state.create_challenge(
        platform="telegram", chat_id="c1", scope="dm", user_id="u1",
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="Muhammad Ali refused induction",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("Muhammad Ali refused induction", 1)],
    )
    b = state.create_challenge(
        platform="telegram", chat_id="c1", scope="dm", user_id="u1",
        event_date="April 29", event_year=1789,
        location="South Pacific", country=None,
        canonical_answer="Mutiny on the Bounty",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("Mutiny on the Bounty", 1)],
    )
    ca = state.get_challenge(a)
    cb = state.get_challenge(b)
    assert ca["status"] == "expired"
    assert cb["status"] == "active"


def test_record_guess_and_attempts_increment(tmp_db):
    from scripts import state

    cid = state.create_challenge(
        platform="telegram", chat_id="c2", scope="dm", user_id="u1",
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="Muhammad Ali refused induction",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("Muhammad Ali refused induction", 1)],
    )
    state.record_guess(cid, "telegram", "u1", "ali", "wrong")
    n1 = state.increment_attempts(cid)
    n2 = state.increment_attempts(cid)
    assert n1 == 1 and n2 == 2


def test_acceptable_answers_normalized(tmp_db):
    from scripts import state

    cid = state.create_challenge(
        platform="telegram", chat_id="c3", scope="dm", user_id="u1",
        event_date="April 28", event_year=1967,
        location="Houston", country="United States",
        canonical_answer="Muhammad Ali refused induction",
        short_summary=None, full_description=None, source="britannica",
        aliases=[("Muhammad Ali refused induction", 1), ("U.S. Army draft", 2)],
    )
    rows = state.list_acceptable_answers(cid)
    norm = {r["alias_normalized"] for r in rows}
    assert "muhammad ali refused induction" in norm
    assert "u s army draft" in norm
