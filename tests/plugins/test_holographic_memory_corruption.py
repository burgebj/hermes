import json
import sqlite3

from plugins.memory.holographic import HolographicMemoryProvider
from plugins.memory.holographic.store import MemoryStore


def test_memory_store_quarantines_corrupt_database(tmp_path):
    db_path = tmp_path / "memory_store.db"
    db_path.write_bytes(b"not a sqlite database")

    store = MemoryStore(db_path=db_path)

    assert db_path.exists()
    assert (tmp_path / "memory_store.db.corrupt").read_bytes() == b"not a sqlite database"
    store.add_fact("Hermes remembers the moonlit path")
    assert store.list_facts()[0]["content"] == "Hermes remembers the moonlit path"

    sqlite3.connect(db_path).execute("SELECT COUNT(*) FROM facts").fetchone()
    store.close()


def test_memory_store_does_not_quarantine_transient_database_errors(tmp_path, monkeypatch):
    db_path = tmp_path / "memory_store.db"
    db_path.write_bytes(b"valid user data")

    def raise_locked(self):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(MemoryStore, "_init_db", raise_locked)

    try:
        MemoryStore(db_path=db_path)
    except sqlite3.OperationalError as exc:
        assert "database is locked" in str(exc)
    else:
        raise AssertionError("transient database errors must not be treated as corruption")

    assert db_path.read_bytes() == b"valid user data"
    assert not (tmp_path / "memory_store.db.corrupt").exists()


def test_fact_store_returns_clear_error_when_provider_uninitialized():
    provider = HolographicMemoryProvider(config={})

    result = json.loads(provider.handle_tool_call("fact_store", {"action": "list"}))

    assert "holographic memory is unavailable" in result["error"]
    assert "NoneType" not in result["error"]


def test_fact_feedback_returns_clear_error_when_provider_uninitialized():
    provider = HolographicMemoryProvider(config={})

    result = json.loads(provider.handle_tool_call("fact_feedback", {"action": "helpful", "fact_id": 1}))

    assert "holographic memory is unavailable" in result["error"]
    assert "NoneType" not in result["error"]


def test_system_prompt_reports_unavailable_memory_when_uninitialized():
    provider = HolographicMemoryProvider(config={})
    prompt = provider.system_prompt_block()

    assert "Unavailable" in prompt
    assert "fact storage failed to initialize" in prompt
