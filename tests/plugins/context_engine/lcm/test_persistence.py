"""Tests for LCM session persistence."""
import json
import pytest
from plugins.context_engine.lcm.engine import LcmEngine, ContextEntry
from plugins.context_engine.lcm.config import LcmConfig


@pytest.fixture
def config():
    return LcmConfig(enabled=True, protect_last_n=2)


class TestSessionSerialization:
    def test_serialize_lcm_metadata(self, config):
        """Engine state should be serializable to a dict for session JSON."""
        engine = LcmEngine(config)
        for i in range(6):
            engine.ingest({"role": "user" if i % 2 == 0 else "assistant",
                           "content": f"Message {i}"})

        block = engine.find_compactable_block()
        engine.compact("Test summary", level=1, block_start=block[0], block_end=block[1])

        metadata = engine.to_session_metadata()

        assert "summaries" in metadata
        assert "original_messages" in metadata
        assert "store_size" in metadata
        assert "pinned" in metadata
        assert len(metadata["summaries"]) == 1
        assert metadata["store_size"] == 6
        # Should be JSON serializable
        json.dumps(metadata)

    def test_round_trip(self, config):
        """Serialize then rebuild should produce equivalent state."""
        engine = LcmEngine(config)
        for i in range(6):
            engine.ingest({"role": "user" if i % 2 == 0 else "assistant",
                           "content": f"Message {i}"})
        block = engine.find_compactable_block()
        engine.compact("Summary text", level=1, block_start=block[0], block_end=block[1])

        # Serialize
        metadata = engine.to_session_metadata()
        messages = engine.active_messages()

        # Mark summary messages
        for i, entry in enumerate(engine.active):
            if entry.kind == "summary":
                messages[i]["_lcm_summary"] = True
                messages[i]["_lcm_node_id"] = entry.node_id

        # Rebuild
        session_data = {"messages": messages, "lcm": metadata}
        rebuilt = LcmEngine.rebuild_from_session(session_data, config)

        assert len(rebuilt.dag) == len(engine.dag)
        assert len(rebuilt.active) == len(engine.active)
        # Store should have all originals
        assert len(rebuilt.store) >= len(engine.store)

    def test_empty_engine_serializes(self, config):
        """An engine with no messages should serialize cleanly."""
        engine = LcmEngine(config)
        metadata = engine.to_session_metadata()
        assert metadata["summaries"] == []
        assert metadata["store_size"] == 0

    def test_pinned_ids_serialized(self, config):
        """Pinned message IDs should be included in metadata."""
        engine = LcmEngine(config)
        engine.ingest({"role": "user", "content": "important"})
        engine._pinned_ids.add(0)
        metadata = engine.to_session_metadata()
        assert 0 in metadata["pinned"]
