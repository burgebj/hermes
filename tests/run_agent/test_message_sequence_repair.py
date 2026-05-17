"""Tests for pre-API-call message-sequence repair.

Covers ``_repair_message_sequence`` and the extended
``_drop_trailing_empty_response_scaffolding`` behavior that rewinds past
orphan tool-result tails. Together these prevent the self-reinforcing empty-
response loop observed in session 20260507_044111_fa7e65, where a tool-result
followed directly by a user message produced silent empty responses from
providers (violating role alternation), which retriggered the empty-retry
recovery every turn.
"""

from run_agent import AIAgent


def _bare_agent():
    return AIAgent.__new__(AIAgent)


# ── _drop_trailing_empty_response_scaffolding ──────────────────────────────

def test_drop_scaffolding_rewinds_orphan_tool_tail():
    """When scaffolding is stripped, also rewind the orphan assistant+tool pair."""
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "t1", "type": "function",
                         "function": {"name": "f", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "out"},
        {"role": "assistant", "content": "(empty)",
         "_empty_terminal_sentinel": True},
    ]

    AIAgent._drop_trailing_empty_response_scaffolding(agent, messages)

    assert messages == [{"role": "user", "content": "task"}]


def test_drop_scaffolding_keeps_tail_when_no_scaffolding():
    """Mid-iteration tool results must NOT be rewound — only if scaffolding fires."""
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "t1", "type": "function",
                         "function": {"name": "f", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "out"},
    ]
    original = [dict(m) for m in messages]

    AIAgent._drop_trailing_empty_response_scaffolding(agent, messages)

    assert messages == original


def test_drop_scaffolding_handles_multiple_parallel_tool_results():
    """Parallel tool calls (one assistant → many tool results) all rewound together."""
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "task"},
        {"role": "assistant", "content": "",
         "tool_calls": [
             {"id": "t1", "type": "function",
              "function": {"name": "f", "arguments": "{}"}},
             {"id": "t2", "type": "function",
              "function": {"name": "g", "arguments": "{}"}},
         ]},
        {"role": "tool", "tool_call_id": "t1", "content": "out1"},
        {"role": "tool", "tool_call_id": "t2", "content": "out2"},
        {"role": "assistant", "content": "(empty)",
         "_empty_terminal_sentinel": True},
    ]

    AIAgent._drop_trailing_empty_response_scaffolding(agent, messages)

    assert messages == [{"role": "user", "content": "task"}]


# ── _repair_message_sequence ───────────────────────────────────────────────

def test_repair_merges_consecutive_user_messages():
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "first"},
        {"role": "user", "content": "second"},
    ]

    repairs = AIAgent._repair_message_sequence(agent, messages)

    assert repairs == 1
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "first\n\nsecond"
    assert agent._session_db_needs_rewrite is True


def test_repaired_shorter_history_rewrites_session_db_current_turn(tmp_path):
    """If repair shortens history, persistence must not skip the current turn."""
    from hermes_state import SessionDB

    db = SessionDB(db_path=tmp_path / "state.db")
    session_id = "repair-current-turn"
    db.create_session(session_id=session_id, source="test")
    db.append_message(session_id, role="assistant", content="prior answer")
    db.append_message(session_id, role="user", content="stale user tail")

    agent = _bare_agent()
    agent.session_id = session_id
    agent._session_db = db
    agent._session_db_created = True
    agent._last_flushed_db_idx = 0
    agent._persist_user_message_idx = None
    agent._persist_user_message_override = None
    agent._ensure_db_session = lambda: None

    conversation_history = [
        {"role": "assistant", "content": "prior answer"},
        {"role": "user", "content": "stale user tail"},
    ]
    messages = list(conversation_history) + [
        {"role": "user", "content": "CURRENT TURN SHOULD PERSIST"},
    ]

    repairs = AIAgent._repair_message_sequence(agent, messages)
    AIAgent._flush_messages_to_session_db(agent, messages, conversation_history)

    rows = db.get_messages(session_id)
    assert repairs == 1
    assert len(messages) == len(conversation_history)
    assert len(rows) == 2
    assert rows[1]["role"] == "user"
    assert rows[1]["content"] == "stale user tail\n\nCURRENT TURN SHOULD PERSIST"
    assert agent._last_flushed_db_idx == 2
    assert agent._session_db_needs_rewrite is False


def test_repair_preserves_user_content_when_one_side_empty():
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": ""},
        {"role": "user", "content": "real message"},
    ]

    AIAgent._repair_message_sequence(agent, messages)

    assert messages == [{"role": "user", "content": "real message"}]


def test_repair_does_not_rewind_ongoing_dialog_tool_pair():
    """assistant(tool_calls) + tool + user is a VALID pattern (user redirect
    before the model gets its continuation turn). Repair must not touch it —
    only the flag-gated scaffolding strip rewinds, and only when the
    empty-recovery scaffolding was actually present.
    """
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "t1", "type": "function",
                         "function": {"name": "f", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "out"},
        {"role": "user", "content": "Q2"},
    ]
    original = [dict(m) for m in messages]

    repairs = AIAgent._repair_message_sequence(agent, messages)

    assert repairs == 0
    assert messages == original


def test_repair_drops_stray_tool_with_unknown_tool_call_id():
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
        {"role": "tool", "tool_call_id": "orphan", "content": "stray"},
        {"role": "user", "content": "real"},
    ]

    repairs = AIAgent._repair_message_sequence(agent, messages)

    assert repairs >= 1
    assert all(m.get("role") != "tool" for m in messages)


def test_repair_leaves_valid_conversation_unchanged():
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": "list files"},
        {"role": "assistant", "content": "",
         "tool_calls": [{"id": "t1", "type": "function",
                         "function": {"name": "ls", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "t1", "content": "a.txt b.txt"},
        {"role": "assistant", "content": "Found 2 files"},
        {"role": "user", "content": "more"},
    ]
    original = [dict(m) for m in messages]

    repairs = AIAgent._repair_message_sequence(agent, messages)

    assert repairs == 0
    assert messages == original


def test_repair_preserves_multimodal_user_content():
    """Multimodal (list) content must NOT be merged — risks mangling attachments."""
    agent = _bare_agent()
    messages = [
        {"role": "user", "content": [{"type": "text", "text": "hi"},
                                     {"type": "image_url", "image_url": {"url": "..."}}]},
        {"role": "user", "content": "follow-up"},
    ]

    AIAgent._repair_message_sequence(agent, messages)

    # The multimodal user message stays as a distinct message — no merge
    assert len(messages) == 2
    assert isinstance(messages[0]["content"], list)


def test_repair_empty_messages_returns_zero():
    agent = _bare_agent()
    messages = []

    repairs = AIAgent._repair_message_sequence(agent, messages)

    assert repairs == 0
    assert messages == []


def test_repair_preserves_system_messages():
    agent = _bare_agent()
    messages = [
        {"role": "system", "content": "You are..."},
        {"role": "user", "content": "hi"},
    ]
    original = [dict(m) for m in messages]

    AIAgent._repair_message_sequence(agent, messages)

    assert messages == original
