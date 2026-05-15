"""Regression tests for silent-empty response detection in ``AIAgent``.

Issue: #18066 — some OpenAI-compatible providers (notably Ollama-hosted
GLM / reasoning models) occasionally return a structurally valid choice
that's logically empty:

  * ``message.content`` is ``None`` or whitespace-only
  * ``message.reasoning_content`` is ``None`` or whitespace-only
  * ``message.tool_calls`` is empty / ``None``
  * ``finish_reason`` is ``"stop"`` (or absent)

The existing ``validate_response`` only checks that ``choices`` is non-empty,
so these silent-empty turns slipped through as blank replies with no retry.

Fix: an additional guard in ``run_agent.py`` after the validation block that
detects "valid choice list, but the first choice has no usable payload" and
sets ``response_invalid = True`` so the existing retry/fallback machinery
kicks in.
"""

import types
import pytest


# ---------------------------------------------------------------------------
# Helpers — lightweight mock objects that mimic the OpenAI response shape
# ---------------------------------------------------------------------------

def _make_message(content=None, reasoning_content=None, reasoning=None,
                  tool_calls=None):
    msg = types.SimpleNamespace()
    msg.content = content
    msg.reasoning_content = reasoning_content
    msg.reasoning = reasoning
    msg.tool_calls = tool_calls
    return msg


def _make_choice(message=None, finish_reason="stop"):
    choice = types.SimpleNamespace()
    choice.message = message or _make_message()
    choice.finish_reason = finish_reason
    return choice


def _make_response(choices):
    resp = types.SimpleNamespace()
    resp.choices = choices
    resp.model = "test-model"
    resp.usage = types.SimpleNamespace(
        prompt_tokens=10, completion_tokens=0, total_tokens=10,
    )
    return resp


# ---------------------------------------------------------------------------
# The guard logic extracted for unit testing (mirrors run_agent.py)
# ---------------------------------------------------------------------------

def _is_silent_empty(response):
    """Return True if the response passes ``validate_response`` but has no
    usable content, reasoning, or tool calls in the first choice."""
    if response is None:
        return False
    if not hasattr(response, "choices") or not response.choices:
        return False

    choice = response.choices[0]
    msg = getattr(choice, "message", None)
    content = getattr(msg, "content", None) if msg else None
    reasoning = (
        getattr(msg, "reasoning_content", None)
        or getattr(msg, "reasoning", None)
    ) if msg else None
    tool_calls = getattr(msg, "tool_calls", None) if msg else None
    fr = getattr(choice, "finish_reason", None)

    content_empty = (
        content is None
        or (isinstance(content, str) and not content.strip())
    )
    return (
        content_empty
        and not reasoning
        and not tool_calls
        and fr in (None, "stop")
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSilentEmptyDetection:
    """Responses that should be flagged as silent-empty."""

    def test_none_content_no_reasoning_no_tools_stop(self):
        """Classic silent-empty: content=None, finish_reason='stop'."""
        msg = _make_message(content=None, tool_calls=None)
        resp = _make_response([_make_choice(message=msg, finish_reason="stop")])
        assert _is_silent_empty(resp) is True

    def test_whitespace_content_no_reasoning_no_tools_stop(self):
        """Whitespace-only content is treated as empty."""
        msg = _make_message(content="   \n\t  ", tool_calls=None)
        resp = _make_response([_make_choice(message=msg, finish_reason="stop")])
        assert _is_silent_empty(resp) is True

    def test_empty_string_content_no_reasoning_no_tools_stop(self):
        """Empty string content."""
        msg = _make_message(content="", tool_calls=None)
        resp = _make_response([_make_choice(message=msg, finish_reason="stop")])
        assert _is_silent_empty(resp) is True

    def test_none_finish_reason(self):
        """finish_reason=None (absent) is also detected."""
        msg = _make_message(content=None, tool_calls=None)
        resp = _make_response([_make_choice(message=msg, finish_reason=None)])
        assert _is_silent_empty(resp) is True

    def test_none_message_object(self):
        """choice.message is None."""
        resp = _make_response([_make_choice(message=None, finish_reason="stop")])
        assert _is_silent_empty(resp) is True


class TestNotSilentEmpty:
    """Responses that should NOT be flagged as silent-empty."""

    def test_valid_content(self):
        """Normal response with text content."""
        msg = _make_message(content="Hello, world!")
        resp = _make_response([_make_choice(message=msg)])
        assert _is_silent_empty(resp) is False

    def test_reasoning_content_present(self):
        """Model returned reasoning but no visible text — not empty."""
        msg = _make_message(
            content=None,
            reasoning_content="Let me think about this...",
        )
        resp = _make_response([_make_choice(message=msg)])
        assert _is_silent_empty(resp) is False

    def test_reasoning_field_present(self):
        """Some providers use 'reasoning' instead of 'reasoning_content'."""
        msg = _make_message(content=None, reasoning="Thinking...")
        resp = _make_response([_make_choice(message=msg)])
        assert _is_silent_empty(resp) is False

    def test_tool_calls_present(self):
        """Tool-call-only response (content=None is normal here)."""
        msg = _make_message(
            content=None,
            tool_calls=[types.SimpleNamespace(id="call_1")],
        )
        resp = _make_response([_make_choice(message=msg)])
        assert _is_silent_empty(resp) is False

    def test_finish_reason_length(self):
        """finish_reason='length' (truncation) is not silent-empty."""
        msg = _make_message(content=None)
        resp = _make_response([_make_choice(message=msg, finish_reason="length")])
        assert _is_silent_empty(resp) is False

    def test_finish_reason_tool_calls(self):
        """finish_reason='tool_calls' is not silent-empty."""
        msg = _make_message(content=None)
        resp = _make_response([_make_choice(message=msg, finish_reason="tool_calls")])
        assert _is_silent_empty(resp) is False

    def test_empty_choices_list(self):
        """No choices at all — handled by existing validation, not this guard."""
        resp = _make_response([])
        assert _is_silent_empty(resp) is False

    def test_none_response(self):
        """None response — handled by existing validation."""
        assert _is_silent_empty(None) is False

    def test_content_with_think_blocks_only(self):
        """Content has only <think> blocks.  The guard does NOT strip think blocks
        (that's the thinking-prefill path's job), so raw content is non-empty."""
        msg = _make_message(content="<think>reasoning here</think>")
        resp = _make_response([_make_choice(message=msg)])
        # Raw content is non-empty (has <think> tags), so guard does not flag it.
        # The separate thinking-prefill retry path handles this case.
        assert _is_silent_empty(resp) is False
