"""Tests for Opus/Anthropic thinking-only terminal response handling.

Covers issue #39234: Opus models fail with "no final response" when they
produce reasoning-only turns at end_turn (finish_reason="stop").

When the Anthropic Messages API returns finish_reason "stop" with ONLY
thinking blocks and no text content, the model has genuinely completed
its turn.  The agent loop must treat the reasoning text as the final
answer rather than attempting prefill retries that would loop forever and
ultimately return "no final response".
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.transports.types import NormalizedResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _tool_defs(*names):
    return [
        {
            "type": "function",
            "function": {
                "name": n,
                "description": f"{n} tool",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        for n in names
    ]


def _make_agent(api_mode: str = "chat_completions"):
    """Build a minimal AIAgent with a mocked client."""
    with (
        patch("run_agent.get_tool_definitions", return_value=_tool_defs("web_search")),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        from run_agent import AIAgent

        agent = AIAgent(
            api_key="sk-ant-api03-test",
            base_url="https://api.anthropic.com",
            model="claude-opus-4-20250514",
            provider="anthropic",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
        agent.api_mode = api_mode
        agent.client = MagicMock()
        agent._cached_system_prompt = "You are helpful."
        agent._use_prompt_caching = False
        agent.tool_delay = 0
        agent.compression_enabled = False
        agent.save_trajectories = False
        return agent


def _make_thinking_only_nr(
    thinking_text: str = "Let me reason carefully.",
    finish_reason: str = "stop",
) -> NormalizedResponse:
    """NormalizedResponse mimicking Anthropic returning only a thinking block."""
    return NormalizedResponse(
        content=None,
        tool_calls=None,
        finish_reason=finish_reason,
        reasoning=thinking_text,
        provider_data={
            "reasoning_details": [{"type": "thinking", "thinking": thinking_text}]
        },
    )


def _make_text_nr(text: str = "Here is my answer.") -> NormalizedResponse:
    """NormalizedResponse with plain text content."""
    return NormalizedResponse(
        content=text,
        tool_calls=None,
        finish_reason="stop",
    )


def _make_thinking_plus_text_nr(
    thinking_text: str = "My reasoning.",
    text: str = "My answer.",
) -> NormalizedResponse:
    """NormalizedResponse with both thinking and text blocks."""
    return NormalizedResponse(
        content=text,
        tool_calls=None,
        finish_reason="stop",
        reasoning=thinking_text,
        provider_data={"reasoning_details": [{"type": "thinking", "thinking": thinking_text}]},
    )


def _run_conv(agent, responses: list, *, api_mode: str = "anthropic_messages") -> dict:
    """Run agent.run_conversation with a sequence of NormalizedResponse objects.

    Patches the transport so that normalize_response returns the next item
    in *responses* on each call.  The raw response fed to normalize_response
    is a dummy SimpleNamespace — it is never inspected by the test since
    normalize_response is fully mocked.
    """
    agent.api_mode = api_mode

    call_idx = {"n": 0}

    def fake_normalize(raw, **kw):
        idx = call_idx["n"]
        call_idx["n"] += 1
        if idx < len(responses):
            return responses[idx]
        # If more calls than expected, return the last response
        return responses[-1]

    mock_transport = MagicMock()
    mock_transport.normalize_response.side_effect = fake_normalize
    mock_transport.map_finish_reason.side_effect = lambda r: r
    mock_transport.validate_response.return_value = True

    # Dummy raw response — never really consumed since normalize is mocked
    _dummy_raw = SimpleNamespace(
        content=[SimpleNamespace(type="thinking", thinking="stub")],
        stop_reason="end_turn",
        usage=SimpleNamespace(input_tokens=10, output_tokens=20),
        model="claude-opus-4-20250514",
        id="msg_test",
    )

    with (
        patch.object(agent, "_get_transport", return_value=mock_transport),
        patch.object(
            agent, "_interruptible_streaming_api_call", return_value=_dummy_raw
        ),
        patch.object(
            agent, "_interruptible_api_call", return_value=_dummy_raw
        ),
        patch.object(agent, "_persist_session"),
        patch.object(agent, "_save_trajectory"),
        patch.object(agent, "_cleanup_task_resources"),
    ):
        return agent.run_conversation("What is the meaning of life?")


# ---------------------------------------------------------------------------
# NormalizedResponse shape contract
# ---------------------------------------------------------------------------


class TestNormalizedResponseThinkingOnlyShape:
    """Verify that a thinking-only Anthropic response has the expected fields."""

    def test_thinking_only_has_none_content(self):
        nr = _make_thinking_only_nr()
        assert nr.content is None

    def test_thinking_only_has_reasoning(self):
        nr = _make_thinking_only_nr("deep reasoning")
        assert nr.reasoning == "deep reasoning"

    def test_thinking_only_has_stop_finish_reason(self):
        nr = _make_thinking_only_nr()
        assert nr.finish_reason == "stop"

    def test_thinking_only_no_tool_calls(self):
        nr = _make_thinking_only_nr()
        assert nr.tool_calls is None

    def test_thinking_plus_text_has_content(self):
        nr = _make_thinking_plus_text_nr()
        assert nr.content == "My answer."
        assert nr.reasoning == "My reasoning."


# ---------------------------------------------------------------------------
# Agent loop: thinking-only terminal response detection
# ---------------------------------------------------------------------------


class TestOpusThinkingOnlyTerminalResponse:
    """run_conversation must detect a thinking-only end_turn and return
    reasoning text as the final response, not trigger prefill retries."""

    def test_thinking_only_stop_returns_reasoning_as_final_response(self):
        """Core regression: thinking-only end_turn must not return empty."""
        agent = _make_agent()
        nr = _make_thinking_only_nr(
            "The meaning of life is to seek understanding."
        )
        result = _run_conv(agent, [nr])

        final = result.get("final_response", "")
        assert final, (
            "final_response must not be empty for a thinking-only Opus turn"
        )
        # The reasoning content should surface as the response
        assert "meaning of life" in final or "understanding" in final

    def test_thinking_only_does_not_trigger_prefill_retry(self):
        """Loop must NOT call the API a second time for a completed turn."""
        agent = _make_agent()
        nr = _make_thinking_only_nr()
        result = _run_conv(agent, [nr])

        assert result.get("api_calls", 0) == 1, (
            f"Expected 1 API call for thinking-only end_turn, "
            f"got {result.get('api_calls')}"
        )

    def test_thinking_only_uses_reasoning_text_stripped(self):
        """The reasoning text must be the final response (stripped)."""
        agent = _make_agent()
        thinking = "  Detailed analysis of the universe.  "
        nr = _make_thinking_only_nr(thinking_text=thinking)
        result = _run_conv(agent, [nr])

        final = result.get("final_response", "")
        assert "Detailed analysis of the universe" in final

    def test_thinking_only_turn_exit_reason(self):
        """The turn_exit_reason must reflect the Opus-specific path."""
        agent = _make_agent()
        nr = _make_thinking_only_nr()
        result = _run_conv(agent, [nr])

        assert result.get("turn_exit_reason") == "opus_thinking_only_terminal"

    def test_thinking_only_guard_is_anthropic_messages_specific(self):
        """The Opus thinking-only shortcut fires ONLY for api_mode
        'anthropic_messages'.  Other modes must not hit the same path."""
        agent = _make_agent()
        nr = _make_thinking_only_nr()
        # In anthropic_messages mode the guard triggers and exits on call 1.
        result_ant = _run_conv(agent, [nr], api_mode="anthropic_messages")
        assert result_ant.get("turn_exit_reason") == "opus_thinking_only_terminal"

        agent2 = _make_agent()
        # In chat_completions mode the guard must NOT trigger — the
        # turn_exit_reason should be different.
        # Provide a second text response so the loop can complete.
        # chat_completions calls normalize_response twice per turn (finish_reason
        # probe + main normalize), so supply two items for turn 1 and one for turn 2.
        nr_text = _make_text_nr("Here is my answer.")
        result_cc = _run_conv(
            agent2, [nr, nr, nr_text], api_mode="chat_completions"
        )
        assert result_cc.get("turn_exit_reason") != "opus_thinking_only_terminal"

    def test_thinking_plus_text_returns_text_content(self):
        """When Opus returns BOTH thinking and text, the text is the response.
        The Opus thinking-only shortcut must not swallow the text."""
        agent = _make_agent()
        nr = _make_thinking_plus_text_nr(
            thinking_text="internal reasoning",
            text="This is the visible answer.",
        )
        result = _run_conv(agent, [nr])

        final = result.get("final_response", "")
        assert "visible answer" in final

    def test_thinking_only_not_triggered_for_length_finish_reason(self):
        """If finish_reason is 'length' (truncated), the shortcut must NOT
        activate — that is a different code path (continuation retry)."""
        agent = _make_agent()
        # length finish_reason = truncated, should NOT treat as terminal
        nr = _make_thinking_only_nr(finish_reason="length")
        # Provide a follow-up text response so the loop can terminate
        nr_text = _make_text_nr("Continued answer.")
        result = _run_conv(agent, [nr, nr_text])

        # Should NOT have turn_exit_reason = opus_thinking_only_terminal
        assert result.get("turn_exit_reason") != "opus_thinking_only_terminal"

    def test_thinking_only_reasoning_content_field_also_triggers(self):
        """reasoning_content (alternative field name) must also trigger the fix."""
        agent = _make_agent()
        # Use reasoning_content instead of reasoning
        nr = NormalizedResponse(
            content=None,
            tool_calls=None,
            finish_reason="stop",
            reasoning=None,
            provider_data={"reasoning_content": "Thinking via alt field."},
        )
        # Manually set reasoning_content so the check picks it up
        nr.reasoning = None  # ensure reasoning is None
        # Directly set provider_data reasoning_content
        # The loop checks: getattr(assistant_message, "reasoning_content", None)
        # NormalizedResponse.reasoning_content is a property from provider_data
        result = _run_conv(agent, [nr])
        # With reasoning_content set, the shortcut should fire
        final = result.get("final_response", "")
        assert final  # should not be empty


# ---------------------------------------------------------------------------
# AnthropicTransport.normalize_response: thinking-only shape
# ---------------------------------------------------------------------------


class TestAnthropicTransportThinkingOnly:
    """Verify the transport produces the correct NormalizedResponse shape
    for a thinking-only Anthropic API response."""

    def _make_anthropic_response(self, content_blocks, stop_reason="end_turn"):
        resp = SimpleNamespace()
        resp.content = content_blocks
        resp.stop_reason = stop_reason
        resp.usage = SimpleNamespace(input_tokens=50, output_tokens=200)
        return resp

    def test_thinking_only_block_produces_none_content(self):
        from agent.transports import get_transport

        thinking_block = SimpleNamespace(
            type="thinking",
            thinking="Extended reasoning without a text response.",
        )
        raw_resp = self._make_anthropic_response([thinking_block], "end_turn")
        nr = get_transport("anthropic_messages").normalize_response(raw_resp)

        assert nr.content is None, (
            "A thinking-only Anthropic response must have content=None"
        )
        assert nr.reasoning == "Extended reasoning without a text response."
        assert nr.finish_reason == "stop"
        assert nr.tool_calls is None

    def test_thinking_only_reasoning_details_populated(self):
        from agent.transports import get_transport

        thinking_block = SimpleNamespace(
            type="thinking",
            thinking="Step 1: assess. Step 2: conclude.",
        )
        raw_resp = self._make_anthropic_response([thinking_block])
        nr = get_transport("anthropic_messages").normalize_response(raw_resp)

        assert nr.reasoning_details is not None
        assert len(nr.reasoning_details) == 1
        assert nr.reasoning_details[0]["type"] == "thinking"

    def test_thinking_block_with_signature_preserved(self):
        from agent.transports import get_transport

        thinking_block = SimpleNamespace(
            type="thinking",
            thinking="Reasoning with crypto signature.",
            signature="opaque_sig_xyz",
        )
        raw_resp = self._make_anthropic_response([thinking_block])
        nr = get_transport("anthropic_messages").normalize_response(raw_resp)

        assert nr.content is None
        assert nr.reasoning == "Reasoning with crypto signature."
        details = nr.reasoning_details
        assert details[0].get("signature") == "opaque_sig_xyz"
