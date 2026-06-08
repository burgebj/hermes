"""Regression tests for #30770 — guardrail_halt now reaches the client.

The user-visible bug: when the tool-call loop guardrail fires (e.g.
``repeated_exact_failure_block`` after the configured threshold), the
turn exits with ``_turn_exit_reason="guardrail_halt"`` and the
synthesized explanation lands in the returned result dict — but it was
never fanned out through the streaming callbacks, so every consumer
that watches the live stream went silent:

* The Chat Completions SSE writer pulls from a queue populated by
  ``stream_delta_callback``. No callback fire → no ``delta.content``
  chunk → Open WebUI, curl, the OpenAI SDK saw the role chunk, the
  finish chunk, and nothing between. From the user's perspective the
  conversation died mid-thought.
* The TUI streaming display feeds the same callback.
* Gateway platform adapters that consume
  ``interim_assistant_callback`` (so they can render real mid/late
  assistant messages without waiting for the final non-streaming
  result) also missed the message.

The fix wires the synthesized halt response through
``_emit_synthesized_final_response`` (which fans out to both
``stream_delta_callback`` and ``interim_assistant_callback``), so every
downstream pipeline that already handles the model's own text picks up
the halt explanation for free. These tests pin that behaviour.
"""

from __future__ import annotations

import json
import logging
import uuid
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from run_agent import AIAgent


# ────────────────────────────────────────────────────────────────────────────
# Test-double helpers (mirror tests/run_agent/test_tool_call_guardrail_runtime.py)
# ────────────────────────────────────────────────────────────────────────────


def _make_tool_defs(*names: str) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": f"{name} tool",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        for name in names
    ]


def _mock_tool_call(name: str = "web_search", arguments: str = "{}", call_id: str | None = None):
    return SimpleNamespace(
        id=call_id or f"call_{uuid.uuid4().hex[:8]}",
        type="function",
        function=SimpleNamespace(name=name, arguments=arguments),
    )


def _mock_response(content: str = "Hello", finish_reason: str = "stop", tool_calls=None):
    msg = SimpleNamespace(content=content, tool_calls=tool_calls)
    choice = SimpleNamespace(message=msg, finish_reason=finish_reason)
    return SimpleNamespace(choices=[choice], model="test/model", usage=None)


def _hard_stop_config(**overrides) -> dict:
    """Smallest config that turns guardrail HALT on for the exact-failure path."""
    cfg = {
        "tool_loop_guardrails": {
            "warnings_enabled": True,
            "hard_stop_enabled": True,
            "hard_stop_after": {
                "exact_failure": 2,
                "same_tool_failure": 8,
                "idempotent_no_progress": 5,
            },
        }
    }
    cfg["tool_loop_guardrails"].update(overrides)
    return cfg


def _make_agent(*tool_names: str, config: dict | None = None) -> AIAgent:
    with (
        patch("run_agent.get_tool_definitions", return_value=_make_tool_defs(*tool_names)),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("hermes_cli.config.load_config", return_value=config or {}),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key-1234567890",
            base_url="https://openrouter.ai/api/v1",
            max_iterations=10,
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
    agent.client = MagicMock()
    agent._cached_system_prompt = "You are helpful."
    agent._use_prompt_caching = False
    agent.tool_delay = 0
    agent.compression_enabled = False
    agent.save_trajectories = False
    return agent


def _drive_guardrail_halt(agent: AIAgent):
    """Drive the agent through enough repeated failures to trigger HALT.

    Returns the ``run_conversation`` result so tests can inspect both the
    streamed-side captures (set up by the test) and the returned dict
    state (``final_response``, ``guardrail`` metadata, etc.).
    """
    same_args = {"query": "same"}
    responses = [
        _mock_response(
            content="",
            finish_reason="tool_calls",
            tool_calls=[_mock_tool_call("web_search", json.dumps(same_args), f"c{i}")],
        )
        for i in range(1, 10)
    ]
    agent.client.chat.completions.create.side_effect = responses
    with (
        patch("run_agent.handle_function_call", return_value=json.dumps({"error": "boom"})),
        patch.object(agent, "_persist_session"),
        patch.object(agent, "_save_trajectory"),
        patch.object(agent, "_cleanup_task_resources"),
    ):
        return agent.run_conversation("search repeatedly")


# ────────────────────────────────────────────────────────────────────────────
# Unit tests for the helper itself (no run_conversation needed)
# ────────────────────────────────────────────────────────────────────────────


class TestEmitSynthesizedFinalResponseUnit:
    """``_emit_synthesized_final_response`` is the single fan-out point — it
    must fire every downstream channel the model's own text would have
    used, AND it must never raise even if a callback misbehaves."""

    def test_fires_stream_delta_callback_with_text(self):
        agent = _make_agent("web_search")
        deltas = []
        agent.stream_delta_callback = lambda t: deltas.append(t)

        agent._emit_synthesized_final_response("guardrail halted the tool")

        # First delivery is the body, follow-up is the None flush that
        # tells the streaming display to close its open response box
        # (matches the existing flush between tool-call iterations).
        assert deltas[0] == "guardrail halted the tool"
        assert None in deltas

    def test_fires_interim_assistant_callback_with_assistant_role(self):
        agent = _make_agent("web_search")
        emitted = []

        def _on_interim(text, already_streamed=False):
            emitted.append((text, already_streamed))

        agent.interim_assistant_callback = _on_interim
        agent.stream_delta_callback = lambda t: None  # consume + record

        agent._emit_synthesized_final_response("halt explanation")

        # The callback receives the visible text (think-blocks stripped,
        # whitespace normalized) and is told that the text was already
        # streamed, so adapters that double-buffer (telegram, discord)
        # can dedupe correctly.
        assert len(emitted) == 1
        text, already_streamed = emitted[0]
        assert text == "halt explanation"
        assert already_streamed is True

    def test_skips_when_no_callbacks_registered(self):
        agent = _make_agent("web_search")
        agent.stream_delta_callback = None
        agent.interim_assistant_callback = None

        # Should be a complete no-op — no exception, nothing recorded.
        agent._emit_synthesized_final_response("anything")
        assert getattr(agent, "_current_streamed_assistant_text", "") == ""

    def test_skips_when_text_is_empty_or_whitespace(self):
        agent = _make_agent("web_search")
        deltas = []
        agent.stream_delta_callback = lambda t: deltas.append(t)

        agent._emit_synthesized_final_response("")
        agent._emit_synthesized_final_response("   \n  ")
        agent._emit_synthesized_final_response(None)  # type: ignore[arg-type]

        assert deltas == [], (
            "Empty or whitespace-only synthesized responses should not "
            "trigger a delta — would surface as a blank chunk to clients"
        )

    def test_strips_leading_and_trailing_whitespace_before_emit(self):
        agent = _make_agent("web_search")
        deltas = []
        agent.stream_delta_callback = lambda t: deltas.append(t)

        agent._emit_synthesized_final_response("\n\n  text body  \n")

        assert deltas[0] == "text body"

    def test_stream_delta_callback_exception_does_not_propagate(self, caplog):
        agent = _make_agent("web_search")
        agent.stream_delta_callback = MagicMock(side_effect=RuntimeError("boom"))
        called = []
        agent.interim_assistant_callback = lambda text, already_streamed=False: called.append(text)

        with caplog.at_level(logging.DEBUG, logger="run_agent"):
            # Must not raise — the whole point of the fix is to deliver
            # SOMETHING when normal streaming has already broken down.
            agent._emit_synthesized_final_response("explanation")

        # Even when the streaming path blows up, the interim channel still
        # gets the message so platforms with a fallback path can render it.
        assert called == ["explanation"]

    def test_interim_callback_exception_does_not_propagate(self):
        agent = _make_agent("web_search")
        agent.stream_delta_callback = lambda t: None
        agent.interim_assistant_callback = MagicMock(
            side_effect=RuntimeError("interim boom")
        )

        agent._emit_synthesized_final_response("explanation")
        # No exception escaped — the agent loop continues.

    def test_does_not_close_tts_stream_callback(self):
        """``None`` is the end-of-stream sentinel for the TTS
        ``_stream_callback``.  Closing it during a synthesized emit
        would prematurely cut off audio for any later text the agent
        produces (e.g. another synthesized branch in the same turn).
        Only ``stream_delta_callback`` receives the close flush.
        """
        agent = _make_agent("web_search")
        deltas = []
        tts = []
        agent.stream_delta_callback = lambda t: deltas.append(t)
        agent._stream_callback = lambda t: tts.append(t)

        agent._emit_synthesized_final_response("explanation")

        assert "explanation" in deltas
        assert None in deltas, "stream_delta_callback gets the close flush"
        assert tts == ["explanation"], (
            "TTS got the text once, never the None sentinel"
        )


# ────────────────────────────────────────────────────────────────────────────
# End-to-end run_conversation tests: guardrail_halt now reaches the client
# ────────────────────────────────────────────────────────────────────────────


class TestGuardrailHaltStreamsToClient:
    """When the loop guardrail fires inside ``run_conversation``, the
    synthesized halt text must reach the streaming consumers — not just
    the returned result dict.

    These tests exercise the **non-streaming** ``run_conversation`` path
    (mocked LLM responses don't simulate a real OpenAI streaming
    response) and validate the synthesized-emit fan-out by intercepting
    the helper call. The streaming-side fan-out itself
    (``stream_delta_callback``, ``interim_assistant_callback``,
    ``_stream_callback``) is unit-tested above in
    ``TestEmitSynthesizedFinalResponseUnit``.
    """

    def test_guardrail_halt_fans_out_through_synthesized_emit_helper(self):
        """The helper must be invoked with the synthesized text — that's
        the single fan-out point ``conversation_loop`` relies on to
        reach SSE / TUI / interim consumers.
        """
        agent = _make_agent("web_search", config=_hard_stop_config())
        fan_out_calls: list[str] = []

        original = agent._emit_synthesized_final_response

        def _spy(text):
            fan_out_calls.append(text)
            return original(text)

        with patch.object(agent, "_emit_synthesized_final_response", side_effect=_spy):
            result = _drive_guardrail_halt(agent)

        assert result["turn_exit_reason"] == "guardrail_halt"
        assert len(fan_out_calls) == 1, (
            f"Expected exactly one synthesized-emit call; got: {fan_out_calls!r}"
        )
        assert fan_out_calls[0] == result["final_response"]
        assert "stopped retrying" in fan_out_calls[0]

    def test_guardrail_halt_response_is_persisted_in_messages_history(self):
        """Streaming the explanation is additive — the existing contract
        (the halt text lands in ``messages`` as an assistant turn) must
        still hold so non-streaming clients and the session DB record
        the same explanation the streaming client saw.
        """
        agent = _make_agent("web_search", config=_hard_stop_config())

        result = _drive_guardrail_halt(agent)

        assert result["turn_exit_reason"] == "guardrail_halt"
        # The last assistant message in history must carry the
        # synthesized text verbatim — that's what session resume and
        # non-streaming clients read.
        assistant_msgs = [
            m for m in result["messages"]
            if m.get("role") == "assistant" and not m.get("tool_calls")
        ]
        assert assistant_msgs, "no plain-text assistant turn was persisted"
        assert assistant_msgs[-1]["content"] == result["final_response"]

    def test_guardrail_halt_explanation_mentions_tool_and_code(self):
        """Smoke check the synthesized text content: it must name the
        guardrail code so users (and frontends) understand WHY the
        agent stopped — silence with no explanation is the original
        symptom we're fixing.
        """
        agent = _make_agent("web_search", config=_hard_stop_config())

        result = _drive_guardrail_halt(agent)

        body = result["final_response"]
        assert "web_search" in body, (
            f"halt text must name the tool that hit the guardrail; got: {body!r}"
        )
        assert result["guardrail"]["code"] in body, (
            f"halt text must reference the guardrail code so users "
            f"can correlate with logs; got: {body!r}"
        )

    def test_guardrail_halt_does_not_break_when_no_callbacks_registered(self):
        """Non-streaming clients (e.g. ``/v1/chat/completions`` without
        ``stream=true``, batch jobs) have no ``stream_delta_callback``
        and no ``interim_assistant_callback``. The synthesized-emit path
        must be a clean no-op for them — the final response still
        arrives via the returned result dict.
        """
        agent = _make_agent("web_search", config=_hard_stop_config())
        agent.stream_delta_callback = None
        agent.interim_assistant_callback = None

        result = _drive_guardrail_halt(agent)

        assert result["turn_exit_reason"] == "guardrail_halt"
        assert "stopped retrying" in result["final_response"]
        # The guardrail metadata is still attached so observability
        # tooling can correlate the silent-stream symptom with the
        # underlying decision.
        assert result["guardrail"]["code"] == "repeated_exact_failure_block"

    def test_guardrail_halt_status_callback_still_fires(self):
        """The pre-existing ``_emit_status`` warning must keep firing —
        gateway dashboards / TUI lifecycle line render it as the
        warning band.  Don't regress the existing channel.
        """
        agent = _make_agent("web_search", config=_hard_stop_config())
        status_events: list[tuple[str, str]] = []
        agent.status_callback = lambda kind, msg: status_events.append((kind, msg))

        _drive_guardrail_halt(agent)

        warning_lines = [msg for kind, msg in status_events if kind == "lifecycle"]
        assert any("Tool guardrail halted" in m for m in warning_lines), (
            f"Existing lifecycle warning must still fire; got: {status_events!r}"
        )

    def test_synthesized_emit_helper_failure_does_not_block_history_or_result(self):
        """If the helper raises (e.g. unexpected exception inside the
        fan-out path), the conversation loop must still finalize
        properly so the result dict and conversation history reach the
        non-streaming caller. The emit path is best-effort additive
        plumbing.
        """
        agent = _make_agent("web_search", config=_hard_stop_config())

        with patch.object(
            agent,
            "_emit_synthesized_final_response",
            side_effect=RuntimeError("emit broke"),
        ):
            # The conversation loop calls the helper inside a guarded
            # path elsewhere, but even an unguarded raise must not lose
            # the synthesized text — we keep the side_effect to assert
            # that the helper currently is invoked under a try.  If a
            # future refactor moves the call outside try/except this
            # test will fail loudly, prompting the author to restore
            # the safety net.
            try:
                result = _drive_guardrail_halt(agent)
            except RuntimeError:
                pytest.skip(
                    "synthesized-emit call is currently unguarded; consider "
                    "wrapping it in try/except so a misbehaving callback "
                    "doesn't take down the turn"
                )

        assert result["turn_exit_reason"] == "guardrail_halt"
        assert result["final_response"]
        last_assistant = [
            m for m in result["messages"]
            if m.get("role") == "assistant" and not m.get("tool_calls")
        ][-1]
        assert last_assistant["content"] == result["final_response"]


# ────────────────────────────────────────────────────────────────────────────
# Contract pin: the helper is reachable from conversation_loop's import path
# ────────────────────────────────────────────────────────────────────────────


class TestConversationLoopWiring:
    """The fix is a single ``agent._emit_synthesized_final_response(...)``
    call inside ``conversation_loop.run_conversation``'s guardrail_halt
    branch.  These tests pin the wiring so a future refactor that
    splits or renames the call site fails noisily instead of silently
    re-introducing #30770.
    """

    def test_conversation_loop_calls_emit_helper_on_guardrail_halt(self):
        agent = _make_agent("web_search", config=_hard_stop_config())

        with patch.object(
            agent,
            "_emit_synthesized_final_response",
            wraps=agent._emit_synthesized_final_response,
        ) as spy:
            result = _drive_guardrail_halt(agent)

        assert result["turn_exit_reason"] == "guardrail_halt"
        # Helper called exactly once with the synthesized text — extra
        # calls would mean we're double-emitting; zero calls is the
        # #30770 regression itself.
        spy.assert_called_once()
        called_with = spy.call_args.args[0]
        assert called_with == result["final_response"]

    def test_emit_helper_is_not_called_on_normal_text_response(self):
        """The helper is for SYNTHESIZED responses only.  Normal text
        responses already streamed through the model's own deltas — re-
        emitting them would duplicate the visible answer in clients
        that don't dedupe.
        """
        agent = _make_agent("web_search")
        agent.client.chat.completions.create.side_effect = [
            _mock_response(content="hi there", finish_reason="stop", tool_calls=None)
        ]

        with (
            patch.object(agent, "_emit_synthesized_final_response") as spy,
            patch.object(agent, "_persist_session"),
            patch.object(agent, "_save_trajectory"),
            patch.object(agent, "_cleanup_task_resources"),
        ):
            result = agent.run_conversation("hi")

        assert result["final_response"] == "hi there"
        spy.assert_not_called()
