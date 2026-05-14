"""Tests for LCM Engine core."""
import pytest
from plugins.context_engine.lcm.engine import LcmEngine, CompactionAction, ContextEntry
from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.dag import MessageId


@pytest.fixture
def config():
    return LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85, protect_last_n=4)


@pytest.fixture
def engine(config):
    return LcmEngine(config)


@pytest.fixture
def populated_engine(engine):
    """Engine with 20 messages ingested (10 user + 10 assistant)."""
    for i in range(10):
        engine.ingest({"role": "user", "content": f"User message {i} " + "x" * 100})
        engine.ingest({"role": "assistant", "content": f"Assistant reply {i} " + "y" * 100})
    return engine


class TestIngest:
    def test_returns_sequential_ids(self, engine):
        id0 = engine.ingest({"role": "user", "content": "hello"})
        id1 = engine.ingest({"role": "assistant", "content": "hi"})
        assert id0 == 0
        assert id1 == 1

    def test_adds_to_store_and_active(self, engine):
        msg = {"role": "user", "content": "test"}
        engine.ingest(msg)
        assert len(engine.store) == 1
        assert len(engine.active) == 1
        assert engine.active[0].kind == "raw"
        assert engine.active[0].message == msg


class TestActiveMessages:
    def test_returns_message_dicts(self, engine):
        engine.ingest({"role": "user", "content": "hello"})
        engine.ingest({"role": "assistant", "content": "hi"})
        msgs = engine.active_messages()
        assert len(msgs) == 2
        assert msgs[0]["content"] == "hello"
        assert msgs[1]["content"] == "hi"

    def test_empty_engine(self, engine):
        assert engine.active_messages() == []


class TestCheckThresholds:
    def test_none_below_soft(self, engine):
        # Small message, huge budget
        engine.ingest({"role": "user", "content": "hi"})
        assert engine.check_thresholds(100000) == CompactionAction.NONE

    def test_async_between_soft_and_hard(self):
        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85, protect_last_n=2)
        engine = LcmEngine(config)
        # Ingest enough to be > 50% of a small budget
        for i in range(10):
            engine.ingest({"role": "user", "content": "x" * 200})
        # With a budget of ~2000 tokens, 10 msgs of ~50 tokens each = ~500 tokens
        # tau_soft = 0.5 * 2000 = 1000. Need to be above that.
        # Let's use a budget where our content is between soft and hard
        tokens = engine.active_tokens()
        budget = int(tokens / 0.6)  # puts us at 60%, above soft (50%), below hard (85%)
        action = engine.check_thresholds(budget)
        assert action == CompactionAction.ASYNC

    def test_blocking_above_hard(self):
        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85, protect_last_n=2)
        engine = LcmEngine(config)
        for i in range(20):
            engine.ingest({"role": "user", "content": "x" * 200})
        tokens = engine.active_tokens()
        budget = int(tokens / 0.9)  # puts us at 90%, above hard (85%)
        action = engine.check_thresholds(budget)
        assert action == CompactionAction.BLOCKING

    def test_async_not_retriggered_when_pending(self):
        config = LcmConfig(enabled=True, tau_soft=0.5, tau_hard=0.85, protect_last_n=2)
        engine = LcmEngine(config)
        for i in range(10):
            engine.ingest({"role": "user", "content": "x" * 200})
        tokens = engine.active_tokens()
        budget = int(tokens / 0.6)
        assert engine.check_thresholds(budget) == CompactionAction.ASYNC
        # Second call should return NONE (pending flag set)
        assert engine.check_thresholds(budget) == CompactionAction.NONE


class TestFindCompactableBlock:
    def test_returns_none_when_too_few_messages(self, engine):
        engine.ingest({"role": "user", "content": "hi"})
        engine.ingest({"role": "assistant", "content": "hello"})
        assert engine.find_compactable_block() is None

    def test_protects_last_n(self, populated_engine):
        result = populated_engine.find_compactable_block()
        assert result is not None
        start, end = result
        # Should not include the last protect_last_n (4) entries
        assert end <= len(populated_engine.active) - populated_engine.config.protect_last_n

    def test_returns_oldest_raw_block(self, populated_engine):
        result = populated_engine.find_compactable_block()
        assert result is not None
        start, end = result
        assert start == 0  # oldest messages first

    def test_does_not_split_tool_call_result_pair(self, engine):
        """Tool call and its result must stay together."""
        engine.ingest({"role": "user", "content": "read file"})
        engine.ingest({"role": "assistant", "content": "", "tool_calls": [{"id": "tc1", "function": {"name": "read", "arguments": "{}"}}]})
        engine.ingest({"role": "tool", "content": "file contents", "tool_call_id": "tc1"})
        engine.ingest({"role": "assistant", "content": "Here's the file"})
        engine.ingest({"role": "user", "content": "thanks"})
        engine.ingest({"role": "assistant", "content": "welcome"})
        engine.ingest({"role": "user", "content": "next q"})
        engine.ingest({"role": "assistant", "content": "sure"})
        # With protect_last_n=4, compactable block is messages 0-3
        # The tool_call (msg 1) and tool result (msg 2) must be together
        result = engine.find_compactable_block()
        if result:
            start, end = result
            block_entries = engine.active[start:end]
            # Check no tool result is orphaned from its tool call
            for i, entry in enumerate(block_entries):
                if entry.message.get("role") == "tool":
                    # The preceding entry should be an assistant with tool_calls
                    assert i > 0
                    prev = block_entries[i - 1]
                    assert prev.message.get("tool_calls") is not None

    def test_skips_existing_summaries(self, engine):
        """Block should start after any existing summary entries."""
        # Ingest some messages
        for i in range(8):
            engine.ingest({"role": "user", "content": f"msg {i}"})
        # Manually insert a summary at position 0-1 (simulating prior compaction)
        summary_msg = {"role": "user", "content": "[Summary of messages 0-3]"}
        node = engine.dag.create_node(source_ids=[0, 1, 2, 3], text="summary", level=1, tokens=10)
        engine.active[0] = ContextEntry.summary(node.id, summary_msg)
        # Remove entries 1-3 (they're now covered by the summary)
        del engine.active[1:4]

        result = engine.find_compactable_block()
        if result:
            start, end = result
            # Should not try to compact the summary entry
            for entry in engine.active[start:end]:
                assert entry.kind == "raw"


class TestCompact:
    def test_replaces_block_with_summary(self, populated_engine):
        block = populated_engine.find_compactable_block()
        assert block is not None
        start, end = block
        original_len = len(populated_engine.active)
        block_size = end - start

        node = populated_engine.compact("This is a summary", level=1, block_start=start, block_end=end)

        # Active should shrink: removed block_size entries, added 1 summary
        assert len(populated_engine.active) == original_len - block_size + 1
        # The entry at start should now be a summary
        assert populated_engine.active[start].kind == "summary"
        assert populated_engine.active[start].node_id == node.id

    def test_updates_dag(self, populated_engine):
        block = populated_engine.find_compactable_block()
        start, end = block
        assert len(populated_engine.dag) == 0

        node = populated_engine.compact("Summary text", level=1, block_start=start, block_end=end)

        assert len(populated_engine.dag) == 1
        assert node.text == "Summary text"
        assert node.level == 1
        assert len(node.source_ids) == end - start

    def test_preserves_tail(self, populated_engine):
        block = populated_engine.find_compactable_block()
        start, end = block
        tail_before = [e.message for e in populated_engine.active[-4:]]

        populated_engine.compact("Summary", level=1, block_start=start, block_end=end)

        tail_after = [e.message for e in populated_engine.active[-4:]]
        assert tail_before == tail_after

    def test_clears_async_pending_flag(self, populated_engine):
        populated_engine._async_compaction_pending = True
        block = populated_engine.find_compactable_block()
        populated_engine.compact("Summary", level=1, block_start=block[0], block_end=block[1])
        assert populated_engine._async_compaction_pending is False


class TestExpand:
    def test_returns_originals(self, populated_engine):
        result = populated_engine.expand([0, 1, 2])
        assert len(result) == 3
        assert result[0][0] == 0
        assert result[0][1]["role"] == "user"
        assert result[1][0] == 1
        assert result[1][1]["role"] == "assistant"

    def test_expand_summary_recursive(self, populated_engine):
        # Create a compacted summary
        block = populated_engine.find_compactable_block()
        node = populated_engine.compact("Summary", level=1, block_start=block[0], block_end=block[1])

        # Expand should return all original messages
        result = populated_engine.expand_summary(node.id)
        assert len(result) == len(node.source_ids)

    def test_expand_nonexistent_ids(self, engine):
        result = engine.expand([99, 100])
        assert result == []


class TestFormatExpanded:
    def test_formats_with_role_and_id(self, populated_engine):
        result = populated_engine.format_expanded([0, 1])
        assert "[msg 0]" in result
        assert "[msg 1]" in result
        assert "user:" in result.lower() or "User" in result
        assert "assistant:" in result.lower() or "Assistant" in result
