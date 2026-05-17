from agent.resume_history import sanitize_resumed_conversation_history


def test_sanitize_resumed_history_strips_tool_and_reasoning_payloads():
    out = sanitize_resumed_conversation_history(
        [
            {"role": "system", "content": "private system"},
            {"role": "user", "content": "open the skill"},
            {
                "role": "assistant",
                "content": "",
                "reasoning": "private debugging context",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "skill_view",
                            "arguments": '{"name":"x"}',
                        },
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": "x" * 43691,
            },
            {"role": "assistant", "content": "Done."},
        ]
    )

    assert out == [
        {"role": "user", "content": "open the skill"},
        {"role": "assistant", "content": "Done."},
    ]
    serialized = repr(out)
    assert "skill_view" not in serialized
    assert "tool_call_id" not in serialized
    assert "private debugging" not in serialized
    assert "x" * 100 not in serialized


def test_sanitize_resumed_history_keeps_visible_dialogue_only():
    out = sanitize_resumed_conversation_history(
        [
            {"role": "user", "content": "question"},
            {
                "role": "assistant",
                "content": "I will check.",
                "tool_calls": [{"id": "call_1", "function": {"name": "terminal"}}],
                "reasoning_content": "hidden",
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "secret"},
        ]
    )

    assert out == [
        {"role": "user", "content": "question"},
        {"role": "assistant", "content": "I will check."},
    ]
