"""Regression tests for None-guard fixes in holographic MemoryStore.

Bug: add_fact() and update_fact() could crash with TypeError on fetchone()
when a concurrent process deletes the row between an UNIQUE violation and
the subsequent SELECT that retrieves the existing id / category.
"""

import sqlite3

import pytest

from plugins.memory.holographic.store import MemoryStore


@pytest.fixture
def store(tmp_path):
    return MemoryStore(db_path=str(tmp_path / "test.db"))


class TestAddFactNullGuard:
    """add_fact() must raise RuntimeError (not TypeError) when IntegrityError
    fires but the row is missing by the time we SELECT it."""

    def test_add_fact_duplicate_returns_existing_id(self, store):
        """Normal duplicate path still works — returns same fact_id."""
        fid1 = store.add_fact("hello world fact")
        fid2 = store.add_fact("hello world fact")
        assert fid1 == fid2

    def test_add_fact_concurrent_delete_raises_runtime_error(self, store):
        """Simulate: INSERT fails (IntegrityError) but SELECT finds no row.

        Patch _conn so the INSERT raises IntegrityError and the subsequent
        SELECT returns a cursor whose fetchone() returns None.
        """
        real_conn = store._conn

        class _SmartConn:
            def execute(self, sql, params=()):
                if "INSERT INTO facts" in sql:
                    raise sqlite3.IntegrityError("UNIQUE constraint failed")
                if "SELECT fact_id FROM facts WHERE content" in sql:
                    class _Empty:
                        def fetchone(self):
                            return None
                    return _Empty()
                return real_conn.execute(sql, params)

            def commit(self):
                real_conn.commit()

            def __getattr__(self, name):
                return getattr(real_conn, name)

        store._conn = _SmartConn()
        try:
            with pytest.raises(RuntimeError, match="concurrent deletion"):
                store.add_fact("race condition fact")
        finally:
            store._conn = real_conn


class TestEditFactNullGuard:
    """update_fact() must not crash when the category re-fetch returns None."""

    def test_update_fact_nonexistent_returns_false(self, store):
        """Editing a non-existent fact_id returns False, no crash."""
        result = store.update_fact(fact_id=99999, content="ghost")
        assert result is False

    def test_update_fact_with_category_skips_refetch(self, store):
        """When category is supplied, no second SELECT is issued."""
        fid = store.add_fact("refetch test", category="alpha")
        result = store.update_fact(fact_id=fid, category="beta")
        assert result is True

    def test_update_fact_concurrent_delete_uses_general_fallback(self, store):
        """If the category re-fetch returns None (row deleted concurrently),
        update_fact falls back to 'general' instead of crashing with TypeError."""
        fid = store.add_fact("concurrent edit fact", category="science")

        real_conn = store._conn

        class _ConcurrentDeleteConn:
            """Lets existence-check SELECT and UPDATE through, but returns None
            for the category-SELECT that follows the UPDATE."""

            def execute(self, sql, params=()):
                if "SELECT fact_id, trust_score FROM facts" in sql:
                    return real_conn.execute(sql, params)
                if "SELECT category FROM facts WHERE fact_id" in sql:
                    class _Empty:
                        def fetchone(self):
                            return None
                    return _Empty()
                return real_conn.execute(sql, params)

            def commit(self):
                real_conn.commit()

            def __getattr__(self, name):
                return getattr(real_conn, name)

        store._conn = _ConcurrentDeleteConn()
        try:
            # Must not raise TypeError — should complete with 'general' fallback
            result = store.update_fact(fact_id=fid, content="updated content")
            assert result is True
        finally:
            store._conn = real_conn


class TestSearchFactsFTS5ErrorGuard:
    """search_facts() must return [] instead of raising OperationalError when
    the FTS5 query expression is syntactically invalid (#holographic-2)."""

    def test_search_facts_valid_query_returns_results(self, store):
        """Sanity check: valid query still works after the guard is in place."""
        store.add_fact("Python is a programming language", category="tech")
        results = store.search_facts("Python")
        assert len(results) >= 1
        assert any("Python" in r["content"] for r in results)

    def test_search_facts_malformed_fts5_returns_empty(self, store):
        """Invalid FTS5 syntax must return [] not raise OperationalError."""
        store.add_fact("some fact to ensure FTS5 table exists")
        # These are all invalid FTS5 expressions that trigger OperationalError
        malformed_queries = [
            '"unclosed phrase',
            "AND",
            "OR",
            "NOT",
            "hello AND OR world",
        ]
        for q in malformed_queries:
            result = store.search_facts(q)
            assert result == [], f"Expected [] for malformed query {q!r}, got {result}"

    def test_search_facts_empty_query_returns_empty(self, store):
        """Empty/whitespace query returns [] (existing guard)."""
        assert store.search_facts("") == []
        assert store.search_facts("   ") == []
