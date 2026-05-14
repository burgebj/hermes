"""Regression tests: compaction must never split tool-call / tool-result pairs.

Fix 1: _retreat_from_tool_result must also retreat when the block's last entry
is an assistant message with tool_calls and the first protected-tail entry is
the matching tool result.  Previously only the "block ends with bare tool"
case was handled; the "block ends with assistant+tool_calls whose result is
in the protected zone" case was missed.

Both OpenAI-style (top-level tool_calls) and Anthropic-style (content list with
type=tool_use blocks) assistant messages are exercised.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from plugins.context_engine.lcm.config import LcmConfig
from plugins.context_engine.lcm.engine import LcmEngine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_engine(protect_last_n: int = 3) -> LcmEngine:
    cfg = LcmConfig(enabled=True, protect_last_n=protect_last_n)
    eng = LcmEngine(config=cfg, context_length=10_000)
    eng.summarizer.summarize = MagicMock(return_value="MOCK SUMMARY")
    return eng


def _ingest_all(engine: LcmEngine, messages: list[dict]) -> None:
    for m in messages:
        engine.ingest(m)


def _active_roles(engine: LcmEngine) -> list[str]:
    return [e.message.get("role", "?") for e in engine.active]


def _assert_no_orphan_tool(engine: LcmEngine) -> None:
    """Assert every 'tool' message in active is immediately preceded by assistant+tool_calls."""
    active = engine.active
    for i, entry in enumerate(active):
        if entry.message.get("role") == "tool":
            assert i > 0, "tool message at index 0 has no preceding assistant"
            prev_msg = active[i - 1].message
            assert LcmEngine._has_tool_calls(prev_msg), (
                f"tool message at index {i} is not preceded by assistant+tool_calls; "
                f"preceding role={prev_msg.get('role')!r}"
            )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _openai_style_sequence() -> list[dict]:
    """Returns: [user, assistant+tool_calls(X), tool(X), user]."""
    return [
        {"role": "user", "content": "Please check the weather."},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "call_X", "type": "function", "function": {"name": "get_weather", "arguments": "{}"}}
            ],
        },
        {"role": "tool", "tool_call_id": "call_X", "content": "Sunny, 22C"},
        {"role": "user", "content": "Great, thanks!"},
    ]


def _anthropic_style_sequence() -> list[dict]:
    """Returns: [user, assistant+tool_use(Y), tool(Y), user]."""
    return [
        {"role": "user", "content": "Translate hello."},
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "tool_Y", "name": "translate", "input": {"text": "hello"}},
            ],
        },
        {"role": "tool", "tool_use_id": "tool_Y", "content": "Hola"},
        {"role": "user", "content": "Perfect."},
    ]


# ---------------------------------------------------------------------------
# Tests: find_compactable_block boundary safety
# ---------------------------------------------------------------------------

class TestCompactionBoundaryOpenAI:
    """OpenAI-style tool_calls must not be split from their tool result."""

    def test_block_does_not_end_at_assistant_tool_calls_when_result_in_tail(self):
        """When protect_last_n covers the tool result, the assistant+tool_calls
        must also be excluded from the compactable block."""
        # Sequence: [padding...] + [assistant(tool_calls)] + [tool] + [user]
        # protect_last_n=3 -> tail = [assistant(tool_calls), tool, user]
        # The compactable block candidate ends just before the tail, which is
        # the assistant+tool_calls entry.  The block must retreat further.
        engine = _make_engine(protect_last_n=3)
        padding = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"padding {i}"}
            for i in range(10)
        ]
        tail = _openai_style_sequence()[1:]  # [assistant+tool_calls, tool, user]
        _ingest_all(engine, padding + tail)

        block = engine.find_compactable_block()
        if block is not None:
            start, end = block
            # The block must not include the assistant+tool_calls entry (index 10)
            # because active[10] is the assistant whose result is in the tail.
            for i in range(start, end):
                entry = engine.active[i]
                assert not LcmEngine._has_tool_calls(entry.message), (
                    f"Block [{start}:{end}) includes assistant+tool_calls at index {i}, "
                    "whose tool result is in the protected tail."
                )

    def test_active_list_has_no_orphan_tool_after_compact(self):
        """After auto_compact fires, no 'tool' message should lack a preceding
        assistant+tool_calls in the active list."""
        # Use a tiny context so compaction fires.
        cfg = LcmConfig(enabled=True, tau_hard=0.5, protect_last_n=3)
        engine = LcmEngine(config=cfg, context_length=500)
        engine.summarizer.summarize = MagicMock(return_value="MOCK SUMMARY")

        filler = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "x " * 30}
            for i in range(20)
        ]
        tail = _openai_style_sequence()[1:]  # ends with user
        _ingest_all(engine, filler + tail)

        engine.auto_compact()
        _assert_no_orphan_tool(engine)


class TestCompactionBoundaryAnthropic:
    """Anthropic-style content[{type:tool_use}] must not be split from result."""

    def test_block_does_not_end_at_anthropic_tool_calls_when_result_in_tail(self):
        engine = _make_engine(protect_last_n=3)
        padding = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"padding {i}"}
            for i in range(10)
        ]
        tail = _anthropic_style_sequence()[1:]  # [assistant+tool_use, tool, user]
        _ingest_all(engine, padding + tail)

        block = engine.find_compactable_block()
        if block is not None:
            start, end = block
            for i in range(start, end):
                entry = engine.active[i]
                assert not LcmEngine._has_tool_calls(entry.message), (
                    f"Block [{start}:{end}) includes Anthropic assistant+tool_use at index {i}."
                )

    def test_active_list_has_no_orphan_tool_after_compact_anthropic(self):
        cfg = LcmConfig(enabled=True, tau_hard=0.5, protect_last_n=3)
        engine = LcmEngine(config=cfg, context_length=500)
        engine.summarizer.summarize = MagicMock(return_value="MOCK SUMMARY")

        filler = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": "y " * 30}
            for i in range(20)
        ]
        tail = _anthropic_style_sequence()[1:]
        _ingest_all(engine, filler + tail)

        engine.auto_compact()
        _assert_no_orphan_tool(engine)


class TestHasToolCallsHelper:
    """Unit tests for the _has_tool_calls static helper."""

    def test_openai_style_detected(self):
        msg = {"role": "assistant", "tool_calls": [{"id": "c1"}]}
        assert LcmEngine._has_tool_calls(msg) is True

    def test_anthropic_style_detected(self):
        msg = {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "fn", "input": {}}],
        }
        assert LcmEngine._has_tool_calls(msg) is True

    def test_plain_assistant_not_detected(self):
        msg = {"role": "assistant", "content": "Just text"}
        assert LcmEngine._has_tool_calls(msg) is False

    def test_user_message_not_detected(self):
        msg = {"role": "user", "content": "Hello"}
        assert LcmEngine._has_tool_calls(msg) is False

    def test_content_list_without_tool_use_not_detected(self):
        msg = {
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello"}],
        }
        assert LcmEngine._has_tool_calls(msg) is False
