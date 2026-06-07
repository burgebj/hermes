"""Tests for the holographic MemoryStore non-destructive supersede feature.

See ~/.hermes/plans/dag-memory-extend-holographic.md for the design.
"""

import sqlite3

import pytest

from plugins.memory.holographic.retrieval import FactRetriever
from plugins.memory.holographic.store import MemoryStore


# Pre-supersede facts schema: the columns that existed before this feature,
# i.e. the current schema minus `superseded_at`. Used to build an "old" DB
# and prove the additive migration upgrades it in place.
_OLD_FACTS_DDL = """
CREATE TABLE facts (
    fact_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    content         TEXT NOT NULL UNIQUE,
    category        TEXT DEFAULT 'general',
    tags            TEXT DEFAULT '',
    trust_score     REAL DEFAULT 0.5,
    retrieval_count INTEGER DEFAULT 0,
    helpful_count   INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hrr_vector      BLOB
);
"""


def _make_old_db(path: str) -> None:
    """Create a pre-supersede database with one existing fact row."""
    conn = sqlite3.connect(path)
    conn.executescript(_OLD_FACTS_DDL)
    conn.execute(
        "INSERT INTO facts (content, category) VALUES (?, ?)",
        ("legacy fact from before the migration", "general"),
    )
    conn.commit()
    conn.close()


def _columns(store: MemoryStore, table: str) -> set:
    return {row[1] for row in store._conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _tables(store: MemoryStore) -> set:
    rows = store._conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {row[0] for row in rows}


class TestSupersedeMigration:
    def test_adds_superseded_at_column(self, tmp_path):
        db = str(tmp_path / "old.db")
        _make_old_db(db)
        store = MemoryStore(db_path=db)
        assert "superseded_at" in _columns(store, "facts")

    def test_creates_fact_supersedes_table(self, tmp_path):
        db = str(tmp_path / "old.db")
        _make_old_db(db)
        store = MemoryStore(db_path=db)
        assert "fact_supersedes" in _tables(store)

    def test_preserves_existing_rows(self, tmp_path):
        db = str(tmp_path / "old.db")
        _make_old_db(db)
        store = MemoryStore(db_path=db)
        row = store._conn.execute(
            "SELECT content, superseded_at FROM facts WHERE fact_id = 1"
        ).fetchone()
        assert row["content"] == "legacy fact from before the migration"
        # Existing rows are live: superseded_at defaults to NULL.
        assert row["superseded_at"] is None


class TestRemoveFactLineageCleanup:
    """remove_fact must not leave dangling fact_supersedes rows."""

    def _seed_lineage(self, store, new_id, old_id):
        store._conn.execute(
            "INSERT INTO fact_supersedes (new_id, old_id) VALUES (?, ?)",
            (new_id, old_id),
        )
        store._conn.commit()

    def test_removing_new_id_clears_lineage(self, tmp_path):
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        old_id = store.add_fact("old version of the fact")
        new_id = store.add_fact("new version of the fact")
        self._seed_lineage(store, new_id, old_id)

        store.remove_fact(new_id)

        dangling = store._conn.execute(
            "SELECT COUNT(*) FROM fact_supersedes WHERE new_id = ? OR old_id = ?",
            (new_id, new_id),
        ).fetchone()[0]
        assert dangling == 0

    def test_removing_old_id_clears_lineage(self, tmp_path):
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        old_id = store.add_fact("old version of the fact")
        new_id = store.add_fact("new version of the fact")
        self._seed_lineage(store, new_id, old_id)

        store.remove_fact(old_id)

        dangling = store._conn.execute(
            "SELECT COUNT(*) FROM fact_supersedes WHERE new_id = ? OR old_id = ?",
            (old_id, old_id),
        ).fetchone()[0]
        assert dangling == 0


class TestSupersededRecallFilter:
    """A fact marked superseded must vanish from every default recall path
    and from its category HRR bank, while live versions still surface."""

    def _two_versions(self, tmp_path):
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        old_id = store.add_fact("Project Hermes runs on the old server alpha")
        new_id = store.add_fact("Project Hermes runs on the new server beta")
        return store, old_id, new_id

    def _mark_superseded(self, store, fact_id):
        store._conn.execute(
            "UPDATE facts SET superseded_at = CURRENT_TIMESTAMP WHERE fact_id = ?",
            (fact_id,),
        )
        store._conn.commit()
        cat = store._conn.execute(
            "SELECT category FROM facts WHERE fact_id = ?", (fact_id,)
        ).fetchone()["category"]
        store._rebuild_bank(cat)

    def test_search_facts_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        ids = [f["fact_id"] for f in store.search_facts("Project Hermes server")]
        assert old_id not in ids
        assert new_id in ids

    def test_list_facts_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        ids = [f["fact_id"] for f in store.list_facts()]
        assert old_id not in ids
        assert new_id in ids

    def test_retriever_search_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        ids = [f["fact_id"] for f in FactRetriever(store).search("Project Hermes server")]
        assert old_id not in ids
        assert new_id in ids

    def test_probe_direct_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        # No category -> hits the direct-SQL path in probe.
        ids = [f["fact_id"] for f in FactRetriever(store).probe("Project Hermes")]
        assert old_id not in ids

    def test_probe_bank_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        # Category -> hits the bank path through _score_facts_by_vector.
        ids = [f["fact_id"]
               for f in FactRetriever(store).probe("Project Hermes", category="general")]
        assert old_id not in ids

    def test_related_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        ids = [f["fact_id"] for f in FactRetriever(store).related("Hermes")]
        assert old_id not in ids

    def test_reason_excludes_superseded(self, tmp_path):
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        ids = [f["fact_id"] for f in FactRetriever(store).reason(["Hermes"])]
        assert old_id not in ids

    def test_rebuild_bank_excludes_superseded(self, tmp_path):
        # Banks only exist when numpy/HRR is available; skip otherwise.
        pytest.importorskip("numpy")
        store, old_id, new_id = self._two_versions(tmp_path)
        self._mark_superseded(store, old_id)
        row = store._conn.execute(
            "SELECT fact_count FROM memory_banks WHERE bank_name = ?", ("cat:general",)
        ).fetchone()
        # Only the live fact contributes to the bundle.
        assert row["fact_count"] == 1


class TestSupersede:
    """supersede() inserts a corrected fact, retires the old one, and records
    lineage, without destroying the old wording."""

    def _store(self, tmp_path):
        return MemoryStore(db_path=str(tmp_path / "m.db"))

    def test_returns_new_live_fact(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays", category="project")
        new_id = store.supersede(old_id, "Deploy runs on Fridays")
        assert new_id != old_id
        # New fact is live, old fact is retired.
        new_row = store._conn.execute(
            "SELECT superseded_at FROM facts WHERE fact_id = ?", (new_id,)
        ).fetchone()
        old_row = store._conn.execute(
            "SELECT superseded_at FROM facts WHERE fact_id = ?", (old_id,)
        ).fetchone()
        assert new_row["superseded_at"] is None
        assert old_row["superseded_at"] is not None

    def test_records_lineage(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        new_id = store.supersede(old_id, "Deploy runs on Fridays")
        row = store._conn.execute(
            "SELECT new_id, old_id FROM fact_supersedes WHERE new_id = ? AND old_id = ?",
            (new_id, old_id),
        ).fetchone()
        assert row is not None

    def test_old_content_preserved(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        store.supersede(old_id, "Deploy runs on Fridays")
        # Original wording survives in the row, just retired.
        row = store._conn.execute(
            "SELECT content FROM facts WHERE fact_id = ?", (old_id,)
        ).fetchone()
        assert row["content"] == "Deploy runs on Mondays"

    def test_old_vanishes_from_search_new_surfaces(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        new_id = store.supersede(old_id, "Deploy runs on Fridays")
        ids = [f["fact_id"] for f in store.search_facts("Deploy runs")]
        assert old_id not in ids
        assert new_id in ids

    def test_inherits_old_category_by_default(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays", category="project")
        new_id = store.supersede(old_id, "Deploy runs on Fridays")
        row = store._conn.execute(
            "SELECT category FROM facts WHERE fact_id = ?", (new_id,)
        ).fetchone()
        assert row["category"] == "project"

    def test_category_override(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays", category="project")
        new_id = store.supersede(old_id, "Deploy runs on Fridays", category="tool")
        row = store._conn.execute(
            "SELECT category FROM facts WHERE fact_id = ?", (new_id,)
        ).fetchone()
        assert row["category"] == "tool"

    def test_rejects_identical_content(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        with pytest.raises(ValueError):
            store.supersede(old_id, "Deploy runs on Mondays")

    def test_rejects_identical_content_after_strip(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        with pytest.raises(ValueError):
            store.supersede(old_id, "  Deploy runs on Mondays  ")

    def test_rejects_empty_content(self, tmp_path):
        store = self._store(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        with pytest.raises(ValueError):
            store.supersede(old_id, "   ")

    def test_missing_old_raises(self, tmp_path):
        store = self._store(tmp_path)
        with pytest.raises(KeyError):
            store.supersede(9999, "Deploy runs on Fridays")


class TestSupersedeAction:
    """The fact_store tool exposes supersede via the 'supersede' action."""

    def _provider(self, tmp_path):
        from plugins.memory.holographic import HolographicMemoryProvider

        provider = HolographicMemoryProvider(config={})
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        provider._store = store
        provider._retriever = FactRetriever(store)
        return provider, store

    def test_supersede_action_records_lineage(self, tmp_path):
        import json

        provider, store = self._provider(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        out = json.loads(
            provider._handle_fact_store(
                {"action": "supersede", "fact_id": old_id, "content": "Deploy runs on Fridays"}
            )
        )
        new_id = out["fact_id"]
        assert new_id != old_id
        row = store._conn.execute(
            "SELECT 1 FROM fact_supersedes WHERE new_id = ? AND old_id = ?",
            (new_id, old_id),
        ).fetchone()
        assert row is not None

    def test_supersede_action_rejects_identical(self, tmp_path):
        import json

        provider, store = self._provider(tmp_path)
        old_id = store.add_fact("Deploy runs on Mondays")
        out = json.loads(
            provider._handle_fact_store(
                {"action": "supersede", "fact_id": old_id, "content": "Deploy runs on Mondays"}
            )
        )
        assert "error" in out

    def test_trace_action_returns_chain(self, tmp_path):
        import json

        provider, store = self._provider(tmp_path)
        f1 = store.add_fact("Deploy runs on Mondays")
        f2 = store.supersede(f1, "Deploy runs on Wednesdays")
        f3 = store.supersede(f2, "Deploy runs on Fridays")
        out = json.loads(
            provider._handle_fact_store({"action": "trace", "fact_id": f3})
        )
        ids = [c["fact_id"] for c in out["chain"]]
        assert ids == [f3, f2, f1]
        assert out["count"] == 3


class TestTrace:
    """trace() walks fact_supersedes backward from a fact, returning the full
    version chain including retired versions, bounded by depth."""

    def _chain(self, tmp_path):
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        f1 = store.add_fact("Deploy runs on Mondays", category="project")
        f2 = store.supersede(f1, "Deploy runs on Wednesdays")
        f3 = store.supersede(f2, "Deploy runs on Fridays")
        return FactRetriever(store), f1, f2, f3

    def test_walks_back_to_original(self, tmp_path):
        retriever, f1, f2, f3 = self._chain(tmp_path)
        chain = retriever.trace(f3)
        assert [c["fact_id"] for c in chain] == [f3, f2, f1]
        assert [c["depth"] for c in chain] == [0, 1, 2]

    def test_includes_superseded_content(self, tmp_path):
        retriever, f1, f2, f3 = self._chain(tmp_path)
        contents = [c["content"] for c in retriever.trace(f3)]
        # The retired wordings, invisible to search, are recoverable here.
        assert "Deploy runs on Mondays" in contents
        assert "Deploy runs on Wednesdays" in contents

    def test_single_fact_chain(self, tmp_path):
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        fid = store.add_fact("Standalone fact")
        chain = FactRetriever(store).trace(fid)
        assert [c["fact_id"] for c in chain] == [fid]

    def test_depth_bound_truncates(self, tmp_path):
        retriever, f1, f2, f3 = self._chain(tmp_path)
        # depth=1 -> entry node plus one predecessor only.
        chain = retriever.trace(f3, depth=1)
        assert [c["fact_id"] for c in chain] == [f3, f2]

    def test_missing_fact_returns_empty(self, tmp_path):
        store = MemoryStore(db_path=str(tmp_path / "m.db"))
        assert FactRetriever(store).trace(9999) == []
