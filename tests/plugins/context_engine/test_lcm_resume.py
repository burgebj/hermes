"""Regression test for LCM session resume via on_session_start.

Bug: on_session_start called self._engine.rebuild_from_session(hermes_home, session_id)
with wrong arguments (positional hermes_home/session_id instead of session_data dict)
and discarded the returned engine. The exception was swallowed silently.

Fix: load session_data from disk, call LcmEngine.rebuild_from_session(session_data, ...)
and assign the returned engine to self._engine.
"""
import json
import pytest
from pathlib import Path

from plugins.context_engine.lcm import LcmContextEngine
from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.engine import LcmEngine


@pytest.fixture
def session_dir(tmp_path):
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    return tmp_path


def _make_session_json(session_dir: Path, session_id: str, messages, lcm_meta: dict) -> Path:
    """Write a fake session JSON file as run_agent.py would."""
    session_file = session_dir / "sessions" / f"session_{session_id}.json"
    data = {
        "session_id": session_id,
        "model": "test-model",
        "messages": messages,
        "lcm": lcm_meta,
        "message_count": len(messages),
    }
    session_file.write_text(json.dumps(data), encoding="utf-8")
    return session_file


class TestLcmSessionResume:
    def test_rebuild_restores_store_and_active(self, session_dir):
        """After on_session_start with a valid session file, the engine
        should have the same active entries as the original session."""
        # Build an engine with some messages
        config = LcmConfig(enabled=True, protect_last_n=2)
        engine = LcmEngine(config)
        messages_raw = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "Fine, thanks!"},
        ]
        for msg in messages_raw:
            engine.ingest(msg)

        # Serialize engine state
        lcm_meta = engine.to_session_metadata()
        active_msgs = engine.active_messages()

        session_id = "test-session-001"
        _make_session_json(session_dir, session_id, active_msgs, lcm_meta)

        # Create a fresh plugin and trigger resume
        plugin = LcmContextEngine(lcm_config=config)
        plugin.on_session_start(
            session_id=session_id,
            hermes_home=str(session_dir),
        )

        # The rebuilt engine should have the same number of active entries
        assert len(plugin._engine.active) == len(engine.active)
        # Store should be populated
        assert len(plugin._engine.store) == len(engine.store)

    def test_missing_session_file_starts_fresh(self, session_dir):
        """If no session file exists, engine starts fresh without raising."""
        plugin = LcmContextEngine()
        # Should not raise; should log a warning and continue with fresh state
        plugin.on_session_start(
            session_id="nonexistent-session",
            hermes_home=str(session_dir),
        )
        assert len(plugin._engine.active) == 0

    def test_rebuild_with_summaries(self, session_dir):
        """Session with summaries (compacted entries) is restored correctly."""
        config = LcmConfig(enabled=True, protect_last_n=2)
        engine = LcmEngine(config)
        for i in range(6):
            engine.ingest({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i}",
            })

        block = engine.find_compactable_block()
        if block:
            engine.compact("Test summary", level=1, block_start=block[0], block_end=block[1])

        lcm_meta = engine.to_session_metadata()
        active_msgs = engine.active_messages()
        # Mark summary entries
        for i, entry in enumerate(engine.active):
            if entry.kind == "summary":
                active_msgs[i]["_lcm_summary"] = True
                active_msgs[i]["_lcm_node_id"] = entry.node_id

        session_id = "test-session-summaries"
        _make_session_json(session_dir, session_id, active_msgs, lcm_meta)

        plugin = LcmContextEngine(lcm_config=config)
        plugin.on_session_start(
            session_id=session_id,
            hermes_home=str(session_dir),
        )

        assert len(plugin._engine.active) == len(engine.active)
        assert len(plugin._engine.dag.nodes) == len(engine.dag.nodes)
