"""Tests for LCM agent tools."""
import pytest
from plugins.context_engine.lcm.engine import LcmEngine, ContextEntry
from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.tools import (
    handle_lcm_expand, handle_lcm_pin, handle_lcm_forget,
    handle_lcm_search, handle_lcm_budget, handle_lcm_toc,
    handle_lcm_focus, set_engine, LCM_TOOL_SCHEMAS,
)


@pytest.fixture
def engine():
    config = LcmConfig(enabled=True, protect_last_n=2)
    e = LcmEngine(config)
    # Populate with some messages
    e.ingest({"role": "user", "content": "Tell me about Python async patterns"})
    e.ingest({"role": "assistant", "content": "Python async uses coroutines with async/await"})
    e.ingest({"role": "user", "content": "What about error handling in Rust?"})
    e.ingest({"role": "assistant", "content": "Rust uses Result and Option types for error handling"})
    e.ingest({"role": "user", "content": "Compare Python and Rust concurrency"})
    e.ingest({"role": "assistant", "content": "Python has GIL limitations while Rust uses ownership"})
    set_engine(e)
    return e


class TestToolSchemas:
    def test_all_schemas_present(self):
        expected = {"lcm_expand", "lcm_pin", "lcm_forget", "lcm_search", "lcm_budget", "lcm_toc", "lcm_focus"}
        assert set(LCM_TOOL_SCHEMAS.keys()) == expected

    def test_schemas_have_required_fields(self):
        for name, schema in LCM_TOOL_SCHEMAS.items():
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema


class TestExpand:
    def test_returns_original_messages(self, engine):
        result = handle_lcm_expand({"message_ids": "0,1"})
        assert "[msg 0]" in result
        assert "[msg 1]" in result
        assert "Python async" in result

    def test_invalid_ids(self, engine):
        result = handle_lcm_expand({"message_ids": "abc"})
        assert "error" in result.lower() or "invalid" in result.lower()

    def test_no_engine(self):
        set_engine(None)
        result = handle_lcm_expand({"message_ids": "0"})
        assert "not active" in result.lower() or "error" in result.lower()


class TestPin:
    def test_pins_messages(self, engine):
        result = handle_lcm_pin({"message_ids": "0,1"})
        assert "pinned" in result.lower()
        assert 0 in engine._pinned_ids
        assert 1 in engine._pinned_ids

    def test_pinned_survives_find_compactable(self, engine):
        handle_lcm_pin({"message_ids": "0"})
        block = engine.find_compactable_block()
        if block:
            start, end = block
            block_msg_ids = [e.msg_id for e in engine.active[start:end] if e.msg_id is not None]
            assert 0 not in block_msg_ids


class TestForget:
    def test_forgets_messages(self, engine):
        original_len = len(engine.active)
        result = handle_lcm_forget({"message_ids": "0,1", "reason": "debug session done"})
        assert "compacted" in result.lower() or "forgot" in result.lower()
        assert len(engine.active) < original_len


class TestSearch:
    def test_finds_matching_messages(self, engine):
        result = handle_lcm_search({"query": "Rust"})
        assert "Rust" in result
        assert "msg" in result.lower()

    def test_no_matches(self, engine):
        result = handle_lcm_search({"query": "JavaScript"})
        assert "no match" in result.lower() or len(result.strip()) == 0 or "0 results" in result.lower()

    def test_respects_limit(self, engine):
        result = handle_lcm_search({"query": "Python", "limit": 1})
        # Should return at most 1 result
        lines = [l for l in result.strip().split("\n") if l.startswith("[msg")]
        assert len(lines) <= 1


class TestBudget:
    def test_shows_usage(self, engine):
        result = handle_lcm_budget({})
        assert "token" in result.lower() or "message" in result.lower()
        assert "raw" in result.lower() or "active" in result.lower()

    def test_shows_summary_count(self, engine):
        # Compact first to create a summary
        block = engine.find_compactable_block()
        if block:
            engine.compact("Test summary", level=1, block_start=block[0], block_end=block[1])
        result = handle_lcm_budget({})
        assert "summar" in result.lower()


class TestToc:
    def test_shows_conversation_map(self, engine):
        result = handle_lcm_toc({})
        assert len(result) > 0
        # Should reference messages
        assert "msg" in result.lower() or "message" in result.lower()


class TestFocus:
    def test_expands_summary_into_active(self, engine):
        # Create a summary first
        block = engine.find_compactable_block()
        if block:
            node = engine.compact("Summary of early messages", level=1, block_start=block[0], block_end=block[1])
            active_before = len(engine.active)
            result = handle_lcm_focus({"node_id": node.id})
            # Should expand the summary (more entries now)
            assert len(engine.active) > active_before or "expanded" in result.lower() or "focus" in result.lower()


class TestFocusRecompact:
    def test_focus_clears_async_pending(self, engine):
        """After focus expands a summary, async compaction should be re-enabled."""
        block = engine.find_compactable_block()
        if block:
            engine.compact("Summary", level=1, block_start=block[0], block_end=block[1])
            engine._async_compaction_pending = True  # Simulate pending state
            handle_lcm_focus({"node_id": 0})
            assert engine._async_compaction_pending is False


class TestPinCap:
    def test_pin_respects_cap(self, engine):
        """Pinning beyond max_pinned should be rejected."""
        engine.config.max_pinned = 3
        handle_lcm_pin({"message_ids": "0,1,2"})
        result = handle_lcm_pin({"message_ids": "3"})
        assert "limit" in result.lower() or "exceed" in result.lower() or "cannot" in result.lower()

    def test_pin_within_cap_succeeds(self, engine):
        """Pinning within max_pinned should succeed."""
        engine.config.max_pinned = 5
        result = handle_lcm_pin({"message_ids": "0,1,2"})
        assert "pinned" in result.lower()
        assert 0 in engine._pinned_ids
        assert 1 in engine._pinned_ids
        assert 2 in engine._pinned_ids

    def test_pin_exactly_at_cap_succeeds(self, engine):
        """Pinning exactly up to the cap (but not over) should succeed."""
        engine.config.max_pinned = 3
        result = handle_lcm_pin({"message_ids": "0,1,2"})
        assert "pinned" in result.lower()
        assert len(engine._pinned_ids) == 3

    def test_pin_default_cap_is_20(self, engine):
        """Default max_pinned should be 20."""
        assert engine.config.max_pinned == 20
