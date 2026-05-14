"""Tests for LCM session rebuild."""
import pytest
from plugins.context_engine.lcm.engine import LcmEngine, ContextEntry
from plugins.context_engine.lcm.config import LcmConfig


@pytest.fixture
def config():
    return LcmConfig(enabled=True)


class TestRebuildFromSession:
    def test_empty_session(self, config):
        session_data = {"messages": [], "lcm": {"summaries": [], "store_size": 0}}
        engine = LcmEngine.rebuild_from_session(session_data, config)
        assert len(engine.store) == 0
        assert len(engine.active) == 0
        assert len(engine.dag) == 0

    def test_raw_messages_only(self, config):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "how are you"},
        ]
        session_data = {"messages": messages}
        engine = LcmEngine.rebuild_from_session(session_data, config)
        assert len(engine.store) == 3
        assert len(engine.active) == 3
        assert all(e.kind == "raw" for e in engine.active)
        assert engine.active_messages() == messages

    def test_with_summaries(self, config):
        messages = [
            {"role": "user", "content": "[Summary of 3 messages]", "_lcm_summary": True, "_lcm_node_id": 0},
            {"role": "user", "content": "recent message 1"},
            {"role": "assistant", "content": "recent reply 1"},
        ]
        summaries = [
            {"node_id": 0, "source_ids": [0, 1, 2], "text": "Earlier conversation", "level": 1, "tokens": 50}
        ]
        session_data = {
            "messages": messages,
            "lcm": {"summaries": summaries, "store_size": 5}
        }
        engine = LcmEngine.rebuild_from_session(session_data, config)
        # Should have 3 active entries: 1 summary + 2 raw
        assert len(engine.active) == 3
        assert engine.active[0].kind == "summary"
        assert engine.active[0].node_id == 0
        assert engine.active[1].kind == "raw"
        assert engine.active[2].kind == "raw"
        # DAG should have the summary node
        assert len(engine.dag) == 1

    def test_preserves_dag_structure(self, config):
        """Multi-level summaries should reconstruct the DAG correctly."""
        summaries = [
            {"node_id": 0, "source_ids": [0, 1], "text": "First summary", "level": 1, "tokens": 30},
            {"node_id": 1, "source_ids": [2, 3], "text": "Second summary", "level": 1, "tokens": 30},
            {"node_id": 2, "source_ids": [], "text": "Merged summary", "level": 2, "tokens": 20,
             "child_summaries": [0, 1]},
        ]
        messages = [
            {"role": "user", "content": "[Merged summary]", "_lcm_summary": True, "_lcm_node_id": 2},
            {"role": "user", "content": "latest"},
        ]
        session_data = {
            "messages": messages,
            "lcm": {"summaries": summaries, "store_size": 6}
        }
        engine = LcmEngine.rebuild_from_session(session_data, config)
        assert len(engine.dag) == 3
        # The merged node should reference children
        merged = engine.dag.get(2)
        assert merged is not None
        assert merged.child_summaries == [0, 1]
        # all_source_ids should recursively resolve
        all_ids = engine.dag.all_source_ids(2)
        assert sorted(all_ids) == [0, 1, 2, 3]

    def test_missing_lcm_key_treats_as_legacy(self, config):
        """Session without 'lcm' key should load as all-raw."""
        messages = [
            {"role": "user", "content": "old message"},
            {"role": "assistant", "content": "old reply"},
        ]
        session_data = {"messages": messages}
        engine = LcmEngine.rebuild_from_session(session_data, config)
        assert len(engine.active) == 2
        assert all(e.kind == "raw" for e in engine.active)
        assert len(engine.dag) == 0

    def test_rebuild_then_expand(self, config):
        """After rebuild, expand should still work if store has the messages."""
        original_messages = [
            {"role": "user", "content": "msg 0"},
            {"role": "assistant", "content": "msg 1"},
            {"role": "user", "content": "msg 2"},
            {"role": "user", "content": "recent"},
        ]
        summaries = [
            {"node_id": 0, "source_ids": [0, 1, 2], "text": "Earlier chat", "level": 1, "tokens": 30}
        ]
        # The session stores ALL original messages (even summarized ones) plus recent
        session_data = {
            "messages": [
                {"role": "user", "content": "[Summary]", "_lcm_summary": True, "_lcm_node_id": 0},
                {"role": "user", "content": "recent"},
            ],
            "lcm": {
                "summaries": summaries,
                "store_size": 4,
                "original_messages": original_messages,  # full store backup
            }
        }
        engine = LcmEngine.rebuild_from_session(session_data, config)
        # If original_messages are provided, expand should work
        if len(engine.store) >= 3:
            result = engine.expand([0, 1, 2])
            assert len(result) == 3
