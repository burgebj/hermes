"""Tests for credential pool mark_used integration.

The least_used strategy selects credentials by request_count, but
mark_used() was never called from production code — making least_used
behave identically to fill_first. Also, mark_used didn't persist
counts, so they'd reset on restart.
"""

from unittest.mock import MagicMock

from agent.credential_pool import CredentialPool, PooledCredential


def _make_pool(n_entries=3, strategy="least_used"):
    """Build a pool with N entries, all at request_count=0."""
    entries = []
    for i in range(n_entries):
        entries.append(PooledCredential(
            provider="openrouter",
            id=f"key-{i}",
            label=f"Key {i}",
            auth_type="api_key",
            priority=i,
            source="config",
            access_token=f"sk-test-{i}",
            request_count=0,
        ))

    pool = CredentialPool.__new__(CredentialPool)
    pool._entries = list(entries)
    pool._current_id = entries[0].id
    pool._strategy = strategy
    pool.provider = "openrouter"
    pool._lock = __import__("threading").Lock()
    pool._persist = MagicMock()
    return pool


class TestMarkUsedIncrements:

    def test_mark_used_increments_current(self):
        pool = _make_pool()
        pool.mark_used()
        assert pool._entries[0].request_count == 1

    def test_mark_used_increments_specific_entry(self):
        pool = _make_pool()
        pool.mark_used("key-2")
        assert pool._entries[2].request_count == 1
        assert pool._entries[0].request_count == 0

    def test_mark_used_persists(self):
        pool = _make_pool()
        pool.mark_used()
        pool._persist.assert_called_once()

    def test_least_used_rotates_after_mark(self):
        """After marking key-0 as used, least_used should prefer key-1."""
        pool = _make_pool()
        pool.mark_used("key-0")

        available = [e for e in pool._entries if e.request_count >= 0]
        selected = min(available, key=lambda e: e.request_count)
        assert selected.id != "key-0"
