import json

from plugins.memory.holographic import HolographicMemoryProvider
from plugins.memory.holographic.retrieval import FactRetriever
from plugins.memory.holographic.store import MemoryStore


def test_store_search_facts_sanitizes_slash_query(tmp_path):
    store = MemoryStore(db_path=tmp_path / "memory_store.db")
    try:
        store.add_fact(
            "Claude/Codex handoff lives in the gateway/WebUI notes.",
            category="general",
        )

        results = store.search_facts("Claude/Codex", limit=5)

        assert len(results) == 1
        assert results[0]["content"] == "Claude/Codex handoff lives in the gateway/WebUI notes."
    finally:
        store.close()


def test_retriever_search_uses_or_fallback_for_sanitized_slash_query(tmp_path):
    store = MemoryStore(db_path=tmp_path / "memory_store.db")
    try:
        store.add_fact("Gateway restart SOP for Claude agents.", category="general")
        retriever = FactRetriever(store)

        results = retriever.search("gateway/WebUI restart SOP", limit=5)

        assert len(results) == 1
        assert results[0]["content"] == "Gateway restart SOP for Claude agents."
    finally:
        store.close()


def test_fact_store_search_handles_slash_queries_end_to_end(tmp_path):
    provider = HolographicMemoryProvider(
        {
            "db_path": str(tmp_path / "memory_store.db"),
            "default_trust": 0.5,
            "min_trust_threshold": 0.3,
        }
    )
    provider.initialize("session-1")
    try:
        provider.handle_tool_call(
            "fact_store",
            {
                "action": "add",
                "content": "gateway restart SOP for Claude agents",
                "category": "general",
            },
        )

        raw = provider.handle_tool_call(
            "fact_store",
            {
                "action": "search",
                "query": "gateway/WebUI restart SOP",
                "limit": 5,
            },
        )

        payload = json.loads(raw)
        assert payload["count"] == 1
        assert payload["results"][0]["content"] == "gateway restart SOP for Claude agents"
    finally:
        provider.shutdown()
