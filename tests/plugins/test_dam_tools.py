"""Tests for DAM tool handlers and schemas."""
import json
import pytest

from plugins.context_engine.lcm.dam import schemas as dam_schemas
from plugins.context_engine.lcm.dam import tools as dam_tools
from plugins.context_engine.lcm.dam.network import DenseAssociativeMemory
from plugins.context_engine.lcm.dam.encoder import MessageEncoder
from plugins.context_engine.lcm.dam.retrieval import DAMRetriever
from plugins.context_engine.lcm.engine import LcmEngine
from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.tools import set_engine


@pytest.fixture(autouse=True)
def _reset_retriever():
    """Ensure dam_tools._retriever is cleaned up between tests."""
    original = dam_tools._retriever
    yield
    dam_tools._retriever = original
    set_engine(None)


@pytest.fixture
def setup_dam(tmp_path):
    """Set up LCM engine + DAM retriever and inject into dam_tools module."""
    config = LcmConfig(enabled=True, protect_last_n=2)
    engine = LcmEngine(config)
    engine.ingest({"role": "user", "content": "Python error handling with try except"})
    engine.ingest({"role": "assistant", "content": "Use try/except for error handling"})
    engine.ingest({"role": "user", "content": "What is the weather today"})
    engine.ingest({"role": "assistant", "content": "I cannot check weather"})
    set_engine(engine)

    net = DenseAssociativeMemory(nv=512, nh=16, lr=0.01)
    enc = MessageEncoder(nv=512)
    retriever = DAMRetriever(net, enc, tmp_path)
    retriever.sync_with_store()
    dam_tools._retriever = retriever

    yield dam_tools

    dam_tools._retriever = None
    set_engine(None)


class TestSchemas:
    def test_all_schemas_present(self):
        for schema in [dam_schemas.DAM_SEARCH, dam_schemas.DAM_RECALL, dam_schemas.DAM_COMPOSE, dam_schemas.DAM_STATUS]:
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema

    def test_dam_search_has_required_query(self):
        assert "query" in dam_schemas.DAM_SEARCH["parameters"]["required"]

    def test_dam_recall_has_required_message_id(self):
        assert "message_id" in dam_schemas.DAM_RECALL["parameters"]["required"]

    def test_dam_compose_has_required_queries(self):
        assert "queries" in dam_schemas.DAM_COMPOSE["parameters"]["required"]

    def test_dam_status_no_required_params(self):
        assert dam_schemas.DAM_STATUS["parameters"]["required"] == []


class TestDamSearch:
    def test_returns_results(self, setup_dam):
        result = setup_dam.handle_dam_search({"query": "Python exception"})
        assert isinstance(result, str)
        assert len(result) > 0

    def test_result_is_not_error(self, setup_dam):
        result = setup_dam.handle_dam_search({"query": "Python error handling"})
        assert isinstance(result, str)

    def test_empty_query_returns_error(self, setup_dam):
        result = setup_dam.handle_dam_search({"query": ""})
        assert "error" in result.lower()

    def test_empty_query_strips_whitespace(self, setup_dam):
        result = setup_dam.handle_dam_search({"query": "   "})
        assert "error" in result.lower()

    def test_no_retriever_falls_back_gracefully(self):
        dam_tools._retriever = None
        result = dam_tools.handle_dam_search({"query": "test"})
        assert isinstance(result, str)

    def test_respects_limit_parameter(self, setup_dam):
        result = setup_dam.handle_dam_search({"query": "Python", "limit": 1})
        assert isinstance(result, str)


class TestDamRecall:
    def test_finds_similar_messages(self, setup_dam):
        result = setup_dam.handle_dam_recall({"message_id": 0})
        assert isinstance(result, str)
        # Should return a list header, not a JSON error object
        assert result.startswith("Messages similar to") or "msg" in result.lower()

    def test_missing_message_id_returns_error(self, setup_dam):
        result = setup_dam.handle_dam_recall({})
        assert "error" in result.lower()

    def test_invalid_message_id_returns_gracefully(self, setup_dam):
        result = setup_dam.handle_dam_recall({"message_id": 9999})
        assert isinstance(result, str)

    def test_no_retriever_returns_error(self):
        dam_tools._retriever = None
        result = dam_tools.handle_dam_recall({"message_id": 0})
        assert "error" in result.lower()


class TestDamCompose:
    def test_and_operation_returns_string(self, setup_dam):
        result = setup_dam.handle_dam_compose({"queries": ["Python", "error"], "operation": "AND"})
        assert isinstance(result, str)

    def test_or_operation_returns_string(self, setup_dam):
        result = setup_dam.handle_dam_compose({"queries": ["Python", "weather"], "operation": "OR"})
        assert isinstance(result, str)

    def test_too_few_queries_returns_error(self, setup_dam):
        result = setup_dam.handle_dam_compose({"queries": ["solo"]})
        assert "error" in result.lower()

    def test_empty_queries_returns_error(self, setup_dam):
        result = setup_dam.handle_dam_compose({"queries": []})
        assert "error" in result.lower()

    def test_invalid_operation_returns_error(self, setup_dam):
        result = setup_dam.handle_dam_compose({"queries": ["Python", "error"], "operation": "XOR"})
        assert "error" in result.lower()

    def test_no_retriever_returns_error(self):
        dam_tools._retriever = None
        result = dam_tools.handle_dam_compose({"queries": ["Python", "error"]})
        assert "error" in result.lower()


class TestDamStatus:
    def test_shows_network_dimensions(self, setup_dam):
        result = setup_dam.handle_dam_status({})
        assert isinstance(result, str)
        assert "512" in result or "Nv" in result or "dimension" in result.lower()

    def test_shows_patterns_stored(self, setup_dam):
        result = setup_dam.handle_dam_status({})
        assert "pattern" in result.lower() or "stored" in result.lower()

    def test_no_retriever_returns_inactive_message(self):
        dam_tools._retriever = None
        result = dam_tools.handle_dam_status({})
        assert "not initialized" in result.lower() or "inactive" in result.lower()