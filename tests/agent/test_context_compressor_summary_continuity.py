"""Regression tests for iterative context-summary continuity."""

from unittest.mock import MagicMock, patch

from agent.context_compressor import ContextCompressor, SUMMARY_PREFIX


def _compressor() -> ContextCompressor:
    with patch("agent.context_compressor.get_model_context_length", return_value=100000):
        return ContextCompressor(
            model="test/model",
            threshold_percent=0.85,
            protect_first_n=1,
            protect_last_n=1,
            quiet_mode=True,
        )


def _response(content: str):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    return mock_response


def _messages_with_handoff(summary_body: str):
    return [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": f"{SUMMARY_PREFIX}\n{summary_body}"},
        {"role": "assistant", "content": "handoff acknowledged after resume"},
        {"role": "user", "content": "new user turn after resume"},
        {"role": "assistant", "content": "new assistant work after resume"},
        {"role": "user", "content": "more new work after resume"},
        {"role": "assistant", "content": "latest tail response"},
        {"role": "user", "content": "final active request stays in protected tail"},
    ]


def test_existing_previous_summary_is_not_serialized_again_as_new_turn():
    """Same-process iterative compression should not feed the old handoff twice.

    P0-2: the new delta path sends old context as PRIOR CONTEXT (read-only),
    asks the LLM to summarize only the NEW TURNS, and must not include the
    summary text as a serialized [USER] turn in the content.
    """
    compressor = _compressor()
    old_summary = "OLD-SUMMARY-BODY unique continuity facts"
    compressor._previous_summary = old_summary
    # Bootstrap segments so the delta path is active.
    compressor._summary_segments = [{"start": 0, "end": 5, "text": old_summary}]

    with patch("agent.context_compressor.call_llm", return_value=_response("updated summary")) as mock_call:
        compressor.compress(_messages_with_handoff(old_summary))

    prompt = mock_call.call_args.kwargs["messages"][0]["content"]
    # New delta-path labels
    assert "PRIOR CONTEXT" in prompt
    assert "NEW TURNS TO SUMMARIZE" in prompt
    # Old summary text appears exactly once (in the PRIOR CONTEXT block, not as a user turn).
    assert prompt.count(old_summary) == 1
    # The handoff message must never be serialized as [USER]: <prefix> in the prompt.
    assert f"[USER]: {SUMMARY_PREFIX}" not in prompt


def test_resume_rehydrates_previous_summary_from_handoff_message():
    """After restart/resume, the persisted handoff should regain summary identity.

    P0-2: on first re-compaction after resume (no live segments yet), the
    legacy summary is bootstrapped into _summary_segments and the delta path
    uses it as PRIOR CONTEXT so the LLM only summarizes the new turns.
    """
    compressor = _compressor()
    old_summary = "RESUMED-SUMMARY-BODY durable continuity facts"
    assert compressor._previous_summary is None

    with patch("agent.context_compressor.call_llm", return_value=_response("updated summary")) as mock_call:
        compressor.compress(_messages_with_handoff(old_summary))

    prompt = mock_call.call_args.kwargs["messages"][0]["content"]
    # After rehydration the delta path fires — legacy "TURNS TO SUMMARIZE:"
    # (cold-start path) must not appear.
    assert "TURNS TO SUMMARIZE:" not in prompt
    # New delta-path labels
    assert "PRIOR CONTEXT" in prompt
    assert "NEW TURNS TO SUMMARIZE" in prompt
    # Summary body appears exactly once in the PRIOR CONTEXT block.
    assert prompt.count(old_summary) == 1
    assert f"[USER]: {SUMMARY_PREFIX}" not in prompt


def test_handoff_in_protected_head_populates_previous_summary_before_update():
    """A resumed protected-head handoff should restore iterative-summary state."""
    compressor = _compressor()
    old_summary = "PROTECTED-HEAD-SUMMARY durable facts from before restart"
    seen_turns = []

    def fake_generate_summary(turns_to_summarize, focus_topic=None):
        seen_turns.extend(turns_to_summarize)
        return "new summary from resumed turns"

    with patch.object(compressor, "_generate_summary", side_effect=fake_generate_summary):
        compressor.compress(_messages_with_handoff(old_summary))

    assert compressor._previous_summary == old_summary
    assert seen_turns
    assert all(old_summary not in str(msg.get("content", "")) for msg in seen_turns)
