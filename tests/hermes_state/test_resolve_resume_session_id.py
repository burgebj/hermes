"""Regression guards for compression-aware resume target resolution.

``SessionDB.resolve_resume_session_id()`` preserves the legacy #15000 behaviour
for empty non-compression heads, while compressed parents that already have
messages now resolve to the live/latest descendant tip.
"""
import time

import pytest

from hermes_state import SessionDB


@pytest.fixture
def db(tmp_path):
    return SessionDB(tmp_path / "state.db")


def _make_chain(db: SessionDB, ids_with_parent):
    """Create sessions in order, forcing started_at so ordering is deterministic."""
    base = int(time.time()) - 10_000
    for i, (sid, parent) in enumerate(ids_with_parent):
        db.create_session(sid, source="cli", parent_session_id=parent)
        db._conn.execute(
            "UPDATE sessions SET started_at = ? WHERE id = ?",
            (base + i * 100, sid),
        )
    db._conn.commit()

def _mark_ended(db: SessionDB, sid: str, reason: str, ended_at: float | None = None):
    db._conn.execute(
        "UPDATE sessions SET ended_at = ?, end_reason = ? WHERE id = ?",
        (ended_at if ended_at is not None else time.time(), reason, sid),
    )
    db._conn.commit()



def test_redirects_from_empty_head_to_descendant_with_messages(db):
    # Reproducer shape from #15000: 6 sessions, only the 5th holds messages.
    _make_chain(db, [
        ("head",   None),
        ("mid1",   "head"),
        ("mid2",   "mid1"),
        ("mid3",   "mid2"),
        ("bulk",   "mid3"),    # has messages
        ("tail",   "bulk"),    # empty tail after another compression
    ])
    for i in range(5):
        db.append_message("bulk", role="user", content=f"msg {i}")

    assert db.resolve_resume_session_id("head") == "bulk"


def test_compressed_session_with_messages_resolves_to_descendant_tip(db):
    _make_chain(db, [("parent", None), ("child", "parent"), ("tip", "child")])
    db.append_message("parent", role="user", content="parent message")
    _mark_ended(db, "parent", "compression")
    _mark_ended(db, "child", "compression")

    assert db.resolve_resume_session_id("parent") == "tip"


def test_compressed_split_prefers_active_leaf(db):
    _make_chain(
        db,
        [
            ("parent", None),
            ("active_older", "parent"),
            ("ended_newer", "parent"),
        ],
    )
    _mark_ended(db, "parent", "compression")
    _mark_ended(db, "ended_newer", "tui_shutdown")

    assert db.resolve_resume_session_id("parent") == "active_older"


def test_compressed_split_treats_null_end_reason_as_active_leaf(db):
    _make_chain(
        db,
        [
            ("parent", None),
            ("open_older", "parent"),
            ("ended_newer", "parent"),
        ],
    )
    _mark_ended(db, "parent", "compression")
    db._conn.execute(
        "UPDATE sessions SET ended_at = ?, end_reason = NULL WHERE id = ?",
        (time.time(), "open_older"),
    )
    db._conn.commit()
    _mark_ended(db, "ended_newer", "tui_shutdown")

    assert db.resolve_resume_session_id("parent") == "open_older"



def test_compressed_split_falls_back_to_newest_leaf(db):
    _make_chain(
        db,
        [
            ("parent", None),
            ("older_leaf", "parent"),
            ("newer_leaf", "parent"),
        ],
    )
    _mark_ended(db, "parent", "compression")
    _mark_ended(db, "older_leaf", "tui_shutdown")
    _mark_ended(db, "newer_leaf", "tui_shutdown")

    assert db.resolve_resume_session_id("parent") == "newer_leaf"



def test_returns_self_when_session_has_messages(db):
    _make_chain(db, [("root", None), ("child", "root")])
    db.append_message("root", role="user", content="hi")
    assert db.resolve_resume_session_id("root") == "root"


def test_returns_self_when_no_descendant_has_messages(db):
    _make_chain(db, [("root", None), ("child1", "root"), ("child2", "child1")])
    assert db.resolve_resume_session_id("root") == "root"


def test_returns_self_for_isolated_session(db):
    db.create_session("isolated", source="cli")
    assert db.resolve_resume_session_id("isolated") == "isolated"


def test_returns_self_for_nonexistent_session(db):
    assert db.resolve_resume_session_id("does_not_exist") == "does_not_exist"


def test_empty_session_id_passthrough(db):
    assert db.resolve_resume_session_id("") == ""
    assert db.resolve_resume_session_id(None) is None


def test_walks_from_middle_of_chain(db):
    # If the user happens to know an intermediate ID, we still find the msg-bearing descendant.
    _make_chain(db, [("a", None), ("b", "a"), ("c", "b"), ("d", "c")])
    db.append_message("d", role="user", content="x")
    assert db.resolve_resume_session_id("b") == "d"
    assert db.resolve_resume_session_id("c") == "d"


def test_prefers_most_recent_child_when_fork_exists(db):
    # If a session was somehow forked (two children), pick the latest one.
    # In practice, compression only produces single-chain shape, but the helper
    # should degrade gracefully.
    _make_chain(db, [
        ("parent", None),
        ("older_fork", "parent"),
        ("newer_fork", "parent"),
    ])
    db.append_message("newer_fork", role="user", content="x")
    assert db.resolve_resume_session_id("parent") == "newer_fork"
