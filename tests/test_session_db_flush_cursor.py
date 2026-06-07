from unittest.mock import MagicMock

from hermes_state import SessionDB
from run_agent import AIAgent


def _agent(db: SessionDB, session_id: str = "s1") -> AIAgent:
    agent = AIAgent.__new__(AIAgent)
    agent._session_db = db
    agent.session_id = session_id
    agent.platform = "cli"
    agent.model = "test-model"
    agent._last_flushed_db_idx = 0
    agent._persist_user_message_idx = None
    agent._persist_user_message_override = None
    return agent


def test_flush_does_not_skip_non_persisted_messages_when_history_cursor_is_ahead(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    agent = _agent(db)

    messages = [
        {"role": "user", "content": "why is this thread empty?"},
        {"role": "assistant", "content": "debugging"},
    ]

    # Reproducer for compressed/resumed sessions: the API-call history cursor
    # can point past the full message list even though the new SessionDB row is
    # still empty.  The DB flush must be anchored to persisted rows, not just
    # the volatile conversation_history length.
    agent._flush_messages_to_session_db(messages, conversation_history=list(messages))

    persisted = db.get_messages("s1")
    assert [m["content"] for m in persisted] == [
        "why is this thread empty?",
        "debugging",
    ]


def test_flush_continues_from_persisted_prefix_when_history_cursor_is_ahead(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    agent = _agent(db)
    db.ensure_session("s1", source="cli", model="test-model")
    db.append_message("s1", "user", "one")
    db.append_message("s1", "assistant", "two")

    messages = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
        {"role": "user", "content": "three"},
    ]

    agent._flush_messages_to_session_db(messages, conversation_history=list(messages))

    persisted = db.get_messages("s1")
    assert [m["content"] for m in persisted] == ["one", "two", "three"]


def test_flush_still_uses_in_memory_cursor_to_avoid_duplicate_writes(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    agent = _agent(db)

    messages = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
    ]

    agent._flush_messages_to_session_db(messages, conversation_history=[])
    agent._flush_messages_to_session_db(messages, conversation_history=[])

    persisted = db.get_messages("s1")
    assert [m["content"] for m in persisted] == ["one", "two"]


def test_flush_ignores_non_integer_mocked_message_count():
    db = MagicMock()
    agent = _agent(db)

    messages = [
        {"role": "user", "content": "one"},
        {"role": "assistant", "content": "two"},
    ]

    agent._flush_messages_to_session_db(messages, conversation_history=[])

    assert db.append_message.call_count == 2
