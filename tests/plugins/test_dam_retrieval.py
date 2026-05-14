"""Tests for DAM retrieval engine."""
import pytest
import numpy as np

from plugins.context_engine.lcm.dam.network import DenseAssociativeMemory
from plugins.context_engine.lcm.dam.encoder import MessageEncoder
from plugins.context_engine.lcm.dam.retrieval import DAMRetriever
from plugins.context_engine.lcm.engine import LcmEngine
from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.tools import set_engine


@pytest.fixture
def lcm_engine():
    config = LcmConfig(enabled=True, protect_last_n=2)
    engine = LcmEngine(config)
    engine.ingest({"role": "user", "content": "Python error handling with try except blocks"})
    engine.ingest({"role": "assistant", "content": "Use try/except blocks for error handling in Python"})
    engine.ingest({"role": "user", "content": "What is the weather forecast for tomorrow"})
    engine.ingest({"role": "assistant", "content": "I don't have access to weather data"})
    engine.ingest({"role": "user", "content": "Rust ownership and borrowing system"})
    engine.ingest({"role": "assistant", "content": "Rust uses ownership rules to manage memory safely"})
    set_engine(engine)
    yield engine
    set_engine(None)


@pytest.fixture
def retriever(lcm_engine, tmp_path):
    net = DenseAssociativeMemory(nv=512, nh=16, lr=0.01)
    enc = MessageEncoder(nv=512)
    return DAMRetriever(net, enc, tmp_path)


class TestSyncWithStore:
    def test_indexes_new_messages(self, retriever, lcm_engine):
        count = retriever.sync_with_store()
        assert count == 6
        assert len(retriever._pattern_cache) == 6

    def test_incremental_sync(self, retriever, lcm_engine):
        retriever.sync_with_store()
        lcm_engine.ingest({"role": "user", "content": "new message"})
        count = retriever.sync_with_store()
        assert count == 1
        assert len(retriever._pattern_cache) == 7

    def test_no_engine_returns_zero(self, tmp_path):
        set_engine(None)
        net = DenseAssociativeMemory(nv=512, nh=16)
        enc = MessageEncoder(nv=512)
        r = DAMRetriever(net, enc, tmp_path)
        assert r.sync_with_store() == 0


class TestSearch:
    def test_returns_relevant_results(self, retriever):
        retriever.sync_with_store()
        results = retriever.search("exception handling Python")
        assert len(results) > 0
        # Top results should be the Python error handling messages (ids 0 or 1)
        top_ids = [r[0] for r in results[:2]]
        assert 0 in top_ids or 1 in top_ids

    def test_empty_query(self, retriever):
        retriever.sync_with_store()
        results = retriever.search("")
        assert results == []


class TestRecallSimilar:
    def test_finds_related_messages(self, retriever):
        retriever.sync_with_store()
        results = retriever.recall_similar(0, limit=3)  # msg 0 is about Python errors
        assert len(results) > 0
        # msg 1 (assistant reply about error handling) should be most similar
        top_ids = [r[0] for r in results]
        assert 1 in top_ids


class TestCompose:
    def test_and_composition(self, retriever):
        retriever.sync_with_store()
        results = retriever.compose(["Python", "error"], operation="AND", limit=3)
        assert len(results) > 0

    def test_or_composition(self, retriever):
        retriever.sync_with_store()
        results = retriever.compose(["Python", "Rust"], operation="OR", limit=5)
        assert len(results) > 0


class TestStatus:
    def test_returns_stats(self, retriever):
        retriever.sync_with_store()
        status = retriever.get_status()
        assert status["nv"] == 512
        assert status["nh"] == 16
        assert status["patterns_stored"] == 6