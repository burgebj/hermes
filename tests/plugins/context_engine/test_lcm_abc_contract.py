"""ABC contract tests for LcmContextEngine.

Verifies that LCM correctly implements the ContextEngine ABC interface
and integrates with the plugin discovery system.
"""

import pytest
from unittest.mock import patch

from agent.context_engine import ContextEngine
from plugins.context_engine.lcm import LcmContextEngine
from plugins.context_engine.lcm.engine import CompactionAction


# ---------------------------------------------------------------------------
# ABC contract
# ---------------------------------------------------------------------------

class TestAbcCompliance:
    """Verify LcmContextEngine fulfills every abstract method."""

    def test_is_subclass(self):
        assert issubclass(LcmContextEngine, ContextEngine)

    def test_instantiation(self):
        engine = LcmContextEngine()
        assert engine is not None

    def test_name_property(self):
        engine = LcmContextEngine()
        assert engine.name == "lcm"
        assert isinstance(engine.name, str)

    def test_update_from_response(self):
        engine = LcmContextEngine()
        engine.update_from_response({
            "prompt_tokens": 100,
            "completion_tokens": 50,
        })
        assert engine.last_prompt_tokens == 100
        assert engine.last_completion_tokens == 50
        assert engine.last_total_tokens == 150

    def test_should_compress_returns_bool(self):
        engine = LcmContextEngine()
        result = engine.should_compress(prompt_tokens=10)
        assert isinstance(result, bool)

    def test_compress_returns_list(self):
        engine = LcmContextEngine()
        msgs = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        result = engine.compress(msgs)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_should_compress_preflight_returns_bool(self):
        engine = LcmContextEngine()
        result = engine.should_compress_preflight([])
        assert isinstance(result, bool)

    def test_on_session_start_noop(self):
        engine = LcmContextEngine()
        engine.on_session_start("test-session")

    def test_on_session_end_noop(self):
        engine = LcmContextEngine()
        engine.on_session_end("test-session", [])

    def test_on_session_reset(self):
        engine = LcmContextEngine()
        engine.compression_count = 5
        engine.on_session_reset()
        assert engine.compression_count == 0

    def test_get_tool_schemas(self):
        engine = LcmContextEngine()
        schemas = engine.get_tool_schemas()
        assert isinstance(schemas, list)
        names = {s["name"] for s in schemas}
        assert {
            "lcm_expand", "lcm_pin", "lcm_forget",
            "lcm_search", "lcm_budget", "lcm_toc", "lcm_focus",
        }.issubset(names)
        assert any(n.startswith("memory_") for n in names)

    def test_handle_tool_call_valid(self):
        engine = LcmContextEngine()
        result = engine.handle_tool_call("lcm_toc", {})
        assert isinstance(result, str)
        assert "empty" in result.lower() or "Timeline" in result

    def test_handle_tool_call_unknown(self):
        engine = LcmContextEngine()
        result = engine.handle_tool_call("nonexistent_tool", {})
        assert "error" in result.lower()

    def test_get_status(self):
        engine = LcmContextEngine()
        status = engine.get_status()
        assert isinstance(status, dict)
        assert "last_prompt_tokens" in status
        assert "context_length" in status
        assert "compression_count" in status
        # LCM-specific fields
        assert "store_count" in status
        assert "tau_soft" in status

    def test_update_model(self):
        engine = LcmContextEngine()
        engine.update_model("new-model", 64000, base_url="http://test")
        assert engine.context_length == 64000
        assert engine.threshold_tokens > 0


# ---------------------------------------------------------------------------
# Plugin discovery integration
# ---------------------------------------------------------------------------

class TestPluginDiscovery:

    def test_discover_finds_lcm(self):
        from plugins.context_engine import discover_context_engines
        engines = discover_context_engines()
        names = [name for name, _, _ in engines]
        assert "lcm" in names

    def test_load_lcm_engine(self):
        from plugins.context_engine import load_context_engine
        engine = load_context_engine("lcm")
        assert engine is not None
        assert engine.name == "lcm"

    def test_load_nonexistent_returns_none(self):
        from plugins.context_engine import load_context_engine
        engine = load_context_engine("nonexistent")
        assert engine is None

    def test_is_available(self):
        assert LcmContextEngine.is_available() is True


# ---------------------------------------------------------------------------
# Compress/ingest flow
# ---------------------------------------------------------------------------

class TestCompressFlow:

    def test_ingest_on_compress(self):
        """Messages are ingested when compress is called."""
        engine = LcmContextEngine()
        msgs = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
        ]
        engine.compress(msgs)
        assert engine._ingested_count == 2
        assert len(engine._engine.store) == 2

    def test_incremental_ingest(self):
        """Only new messages are ingested on subsequent compress calls."""
        engine = LcmContextEngine()
        msgs_1 = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
        ]
        engine.compress(msgs_1)
        assert engine._ingested_count == 2

        msgs_2 = msgs_1 + [
            {"role": "user", "content": "third"},
            {"role": "assistant", "content": "fourth"},
        ]
        engine.compress(msgs_2)
        assert engine._ingested_count == 4
        assert len(engine._engine.store) == 4

    def test_compress_returns_valid_messages(self):
        """Compressed messages are valid OpenAI-format dicts."""
        engine = LcmContextEngine()
        msgs = [{"role": "user", "content": f"message {i}"} for i in range(10)]
        result = engine.compress(msgs)
        for msg in result:
            assert "role" in msg
            assert "content" in msg


# ---------------------------------------------------------------------------
# Tool dispatch
# ---------------------------------------------------------------------------

class TestToolDispatch:

    def _make_engine_with_messages(self):
        engine = LcmContextEngine()
        msgs = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "2+2 equals 4."},
            {"role": "user", "content": "And 3+3?"},
            {"role": "assistant", "content": "3+3 equals 6."},
        ]
        engine.compress(msgs)
        return engine

    def test_toc(self):
        engine = self._make_engine_with_messages()
        result = engine.handle_tool_call("lcm_toc", {})
        assert "Timeline" in result
        assert "msg 0" in result

    def test_budget(self):
        engine = self._make_engine_with_messages()
        result = engine.handle_tool_call("lcm_budget", {})
        assert "Active entries" in result
        assert "Store total" in result

    def test_search(self):
        engine = self._make_engine_with_messages()
        result = engine.handle_tool_call("lcm_search", {"query": "equals"})
        assert "msg" in result

    def test_pin(self):
        engine = self._make_engine_with_messages()
        result = engine.handle_tool_call("lcm_pin", {"message_ids": "0"})
        assert "Pinned" in result

    def test_expand(self):
        engine = self._make_engine_with_messages()
        result = engine.handle_tool_call("lcm_expand", {"message_ids": "0"})
        assert "user" in result or "msg 0" in result

    def test_forget(self):
        engine = self._make_engine_with_messages()
        result = engine.handle_tool_call("lcm_forget", {"message_ids": "0", "reason": "test"})
        assert "Compacted" in result
