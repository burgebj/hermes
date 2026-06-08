"""SQLite tests for gateway.reaction_store (issue #27438).

Uses ``tmp_path`` to isolate every test from the user's real
``$HERMES_HOME/reactions.db``.  No PTB, no adapters -- only the storage
contract.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

import pytest

from gateway.reaction_store import (
    DEFAULT_REACTION_WEIGHTS,
    ReactionEvent,
    ReactionPolarity,
    ReactionStore,
    default_reactions_db_path,
    get_reaction_store,
    reset_reaction_store_for_tests,
)
from gateway.reactions import ReactionSignal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _event(
    *,
    platform: str = "telegram",
    channel_id: str = "42",
    actor_user_id: str = "user-1",
    target_message_id: str = "msg-1",
    emoji: str = "\U0001F44D",
    added: bool = True,
    timestamp: datetime | None = None,
    platform_data: dict | None = None,
) -> ReactionEvent:
    sig = DEFAULT_REACTION_WEIGHTS[emoji]
    return ReactionEvent(
        platform=platform,
        channel_id=channel_id,
        actor_user_id=actor_user_id,
        target_message_id=target_message_id,
        emoji=emoji,
        signal=sig,
        added=added,
        timestamp=timestamp or datetime.now(timezone.utc),
        platform_data=platform_data or {},
    )


@pytest.fixture
def store(tmp_path: Path) -> Iterator[ReactionStore]:
    db = tmp_path / "reactions.db"
    yield ReactionStore(db_path=db)


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------


class TestSchema:
    def test_db_file_created_on_init(self, tmp_path):
        db = tmp_path / "subdir" / "reactions.db"
        assert not db.exists()
        ReactionStore(db_path=db)
        assert db.exists()
        assert db.parent.is_dir()

    def test_schema_version_seeded(self, tmp_path):
        db = tmp_path / "reactions.db"
        ReactionStore(db_path=db)
        with sqlite3.connect(str(db)) as conn:
            row = conn.execute("SELECT version FROM schema_version").fetchone()
        assert row == (1,)

    def test_expected_tables_present(self, tmp_path):
        db = tmp_path / "reactions.db"
        ReactionStore(db_path=db)
        with sqlite3.connect(str(db)) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            ).fetchall()
        tables = {r[0] for r in rows}
        assert "reaction_events" in tables
        assert "schema_version" in tables

    def test_expected_indexes_present(self, tmp_path):
        db = tmp_path / "reactions.db"
        ReactionStore(db_path=db)
        with sqlite3.connect(str(db)) as conn:
            rows = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        idx_names = {r[0] for r in rows}
        assert "idx_reaction_events_target" in idx_names
        assert "idx_reaction_events_actor" in idx_names
        assert "idx_reaction_events_ts" in idx_names

    def test_reinit_is_idempotent(self, tmp_path):
        # Re-opening the same DB must not duplicate or fail.
        db = tmp_path / "reactions.db"
        ReactionStore(db_path=db)
        ReactionStore(db_path=db)
        ReactionStore(db_path=db)
        with sqlite3.connect(str(db)) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM schema_version").fetchone()
        assert rows == (1,)


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_record_returns_row_id(self, store):
        row_id = store.record(_event())
        assert row_id >= 1
        assert store.count() == 1

    def test_record_persists_all_fields(self, store, tmp_path):
        ts = datetime(2026, 5, 17, 10, 0, tzinfo=timezone.utc)
        store.record(
            _event(
                timestamp=ts,
                platform_data={"chat_type": "private"},
            )
        )
        with sqlite3.connect(str(store.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM reaction_events").fetchone()
        assert row["platform"] == "telegram"
        assert row["channel_id"] == "42"
        assert row["actor_user_id"] == "user-1"
        assert row["target_message_id"] == "msg-1"
        assert row["emoji"] == "\U0001F44D"
        assert row["label"] == "thumbs_up"
        assert row["weight"] == 1.0  # positive thumbs_up
        assert row["polarity"] == "positive"
        assert row["added"] == 1
        assert row["platform_data"] == '{"chat_type":"private"}'

    def test_negative_polarity_persists_negative_weight(self, store):
        store.record(_event(emoji="\U0001F44E"))  # thumbs_down
        with sqlite3.connect(str(store.db_path)) as conn:
            row = conn.execute("SELECT weight FROM reaction_events").fetchone()
        assert row[0] == -1.0

    def test_removal_persists_as_added_zero(self, store):
        store.record(_event(added=False))
        with sqlite3.connect(str(store.db_path)) as conn:
            row = conn.execute("SELECT added FROM reaction_events").fetchone()
        assert row[0] == 0

    def test_record_concurrent_writes_serialise(self, store):
        # Stress: lots of small inserts must not corrupt the table.
        # ReactionStore uses an internal lock; the test just verifies
        # the public contract under repeated calls.
        for _ in range(25):
            store.record(_event())
        assert store.count() == 25


# ---------------------------------------------------------------------------
# aggregate_for_message
# ---------------------------------------------------------------------------


class TestAggregateForMessage:
    def test_empty_returns_zero_summary(self, store):
        summary = store.aggregate_for_message(
            platform="telegram",
            channel_id="missing",
            target_message_id="missing",
        )
        assert summary["net_weight"] == 0.0
        assert summary["positive"] == 0
        assert summary["negative"] == 0
        assert summary["unique_users"] == 0
        assert summary["sample_count"] == 0

    def test_positive_then_negative_sums(self, store):
        store.record(_event(emoji="\u2764\ufe0f"))           # +2
        store.record(_event(emoji="\U0001F44D", actor_user_id="u2"))  # +1
        store.record(_event(emoji="\U0001F44E", actor_user_id="u3"))  # -1
        summary = store.aggregate_for_message(
            platform="telegram",
            channel_id="42",
            target_message_id="msg-1",
        )
        assert summary["net_weight"] == pytest.approx(2.0)
        assert summary["positive"] == 2
        assert summary["negative"] == 1
        assert summary["unique_users"] == 3
        assert summary["sample_count"] == 3

    def test_removal_subtracts_prior_add(self, store):
        # User adds heart (+2), then removes it -- net 0.
        store.record(_event(emoji="\u2764\ufe0f", added=True))
        store.record(_event(emoji="\u2764\ufe0f", added=False))
        summary = store.aggregate_for_message(
            platform="telegram",
            channel_id="42",
            target_message_id="msg-1",
        )
        assert summary["net_weight"] == pytest.approx(0.0)
        # Removal isn't counted as a positive engagement.
        assert summary["positive"] == 1
        assert summary["sample_count"] == 2

    def test_since_filter_excludes_old_events(self, store):
        old = datetime(2026, 1, 1, tzinfo=timezone.utc)
        new = datetime(2026, 5, 17, tzinfo=timezone.utc)
        store.record(_event(emoji="\U0001F44E", timestamp=old))   # -1, old
        store.record(_event(emoji="\u2764\ufe0f", timestamp=new))  # +2, new
        summary = store.aggregate_for_message(
            platform="telegram",
            channel_id="42",
            target_message_id="msg-1",
            since=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        assert summary["net_weight"] == pytest.approx(2.0)
        assert summary["sample_count"] == 1

    def test_scoped_to_target_message(self, store):
        store.record(_event(target_message_id="m1", emoji="\u2764\ufe0f"))
        store.record(_event(target_message_id="m2", emoji="\U0001F4A9"))
        summary = store.aggregate_for_message(
            platform="telegram",
            channel_id="42",
            target_message_id="m1",
        )
        assert summary["net_weight"] == pytest.approx(2.0)
        assert summary["sample_count"] == 1

    def test_scoped_to_platform_and_channel(self, store):
        store.record(_event(platform="telegram", channel_id="42", emoji="\U0001F44D"))
        store.record(_event(platform="discord", channel_id="42", emoji="\U0001F44D"))
        store.record(_event(platform="telegram", channel_id="99", emoji="\U0001F44D"))
        summary = store.aggregate_for_message(
            platform="telegram",
            channel_id="42",
            target_message_id="msg-1",
        )
        assert summary["sample_count"] == 1


# ---------------------------------------------------------------------------
# recent_for_user
# ---------------------------------------------------------------------------


class TestRecentForUser:
    def test_returns_newest_first(self, store):
        old = datetime(2026, 1, 1, tzinfo=timezone.utc)
        new = datetime(2026, 5, 17, tzinfo=timezone.utc)
        store.record(_event(emoji="\U0001F44E", timestamp=old))
        store.record(_event(emoji="\u2764\ufe0f", timestamp=new))
        rows = store.recent_for_user(platform="telegram", actor_user_id="user-1")
        assert len(rows) == 2
        assert rows[0]["emoji"] == "\u2764\ufe0f"
        assert rows[1]["emoji"] == "\U0001F44E"

    def test_limit_caps_result(self, store):
        for _ in range(5):
            store.record(_event())
        rows = store.recent_for_user(
            platform="telegram", actor_user_id="user-1", limit=2
        )
        assert len(rows) == 2

    def test_scoped_to_platform(self, store):
        store.record(_event(platform="telegram"))
        store.record(_event(platform="discord"))
        rows = store.recent_for_user(platform="telegram", actor_user_id="user-1")
        assert len(rows) == 1
        assert rows[0]["platform"] == "telegram"

    def test_scoped_to_user(self, store):
        store.record(_event(actor_user_id="alice"))
        store.record(_event(actor_user_id="bob"))
        rows = store.recent_for_user(platform="telegram", actor_user_id="alice")
        assert len(rows) == 1
        assert rows[0]["actor_user_id"] == "alice"

    def test_since_filter(self, store):
        old = datetime(2026, 1, 1, tzinfo=timezone.utc)
        new = datetime(2026, 5, 17, tzinfo=timezone.utc)
        store.record(_event(emoji="\U0001F44E", timestamp=old))
        store.record(_event(emoji="\u2764\ufe0f", timestamp=new))
        rows = store.recent_for_user(
            platform="telegram",
            actor_user_id="user-1",
            since=datetime(2026, 4, 1, tzinfo=timezone.utc),
        )
        assert len(rows) == 1
        assert rows[0]["emoji"] == "\u2764\ufe0f"


# ---------------------------------------------------------------------------
# prune_older_than
# ---------------------------------------------------------------------------


class TestPruneOlderThan:
    def test_deletes_rows_older_than_cutoff(self, store):
        old = datetime.now(timezone.utc) - timedelta(days=100)
        new = datetime.now(timezone.utc)
        store.record(_event(timestamp=old))
        store.record(_event(timestamp=new))
        deleted = store.prune_older_than(30)
        assert deleted == 1
        assert store.count() == 1

    def test_zero_days_is_noop(self, store):
        store.record(_event())
        deleted = store.prune_older_than(0)
        assert deleted == 0
        assert store.count() == 1

    def test_negative_days_is_noop(self, store):
        store.record(_event())
        assert store.prune_older_than(-5) == 0
        assert store.count() == 1


# ---------------------------------------------------------------------------
# Singleton / get_reaction_store
# ---------------------------------------------------------------------------


class TestGetReactionStore:
    def test_returns_same_instance(self, tmp_path, monkeypatch):
        reset_reaction_store_for_tests()
        db = tmp_path / "reactions.db"
        a = get_reaction_store(db_path=db)
        b = get_reaction_store()
        assert a is b

    def test_passing_db_path_rebinds(self, tmp_path):
        reset_reaction_store_for_tests()
        a = get_reaction_store(db_path=tmp_path / "a.db")
        b = get_reaction_store(db_path=tmp_path / "b.db")
        # Explicit override creates a fresh store.
        assert a is not b
        assert b.db_path.name == "b.db"

    def test_reset_for_tests_drops_singleton(self, tmp_path):
        a = get_reaction_store(db_path=tmp_path / "a.db")
        reset_reaction_store_for_tests()
        b = get_reaction_store(db_path=tmp_path / "a.db")
        assert a is not b


# ---------------------------------------------------------------------------
# default_reactions_db_path
# ---------------------------------------------------------------------------


class TestDefaultReactionsDbPath:
    def test_under_hermes_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        path = default_reactions_db_path()
        assert path == tmp_path / "reactions.db"

    def test_resolved_dynamically_per_call(self, tmp_path, monkeypatch):
        # Profile switches at startup must be reflected on next call.
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "profile-a"))
        a = default_reactions_db_path()
        monkeypatch.setenv("HERMES_HOME", str(tmp_path / "profile-b"))
        b = default_reactions_db_path()
        assert a != b
