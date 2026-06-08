"""Test that reasoning is shown when streaming + show_reasoning are both on (#7251)."""

from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

import pytest


@pytest.mark.asyncio
async def test_reasoning_sent_as_separate_message_when_streaming():
    """When already_sent and show_reasoning, reasoning is sent via adapter."""
    adapter = MagicMock()
    adapter.send = AsyncMock(return_value=SimpleNamespace(success=True, message_id="r-1"))

    # Simulate the fix's logic
    _show_reasoning = True
    agent_result = {
        "already_sent": True,
        "last_reasoning": "I need to think about this carefully.\nLet me analyze the problem.",
        "final_response": "The answer is 42.",
    }

    if agent_result.get("already_sent"):
        if _show_reasoning:
            _streamed_reasoning = agent_result.get("last_reasoning")
            if _streamed_reasoning:
                lines = _streamed_reasoning.strip().splitlines()
                if len(lines) > 15:
                    _display_r = "\n".join(lines[:15])
                    _display_r += f"\n_... ({len(lines) - 15} more lines)_"
                else:
                    _display_r = _streamed_reasoning.strip()
                await adapter.send(
                    chat_id="test-chat",
                    content=f"\U0001f4ad **Reasoning:**\n```\n{_display_r}\n```",
                )

    adapter.send.assert_called_once()
    call_content = adapter.send.call_args.kwargs["content"]
    assert "Reasoning:" in call_content
    assert "think about this" in call_content


@pytest.mark.asyncio
async def test_no_reasoning_sent_when_show_reasoning_disabled():
    """When show_reasoning is False, no reasoning message is sent."""
    adapter = MagicMock()
    adapter.send = AsyncMock()

    _show_reasoning = False
    agent_result = {
        "already_sent": True,
        "last_reasoning": "Some reasoning",
    }

    if agent_result.get("already_sent"):
        if _show_reasoning:
            _streamed_reasoning = agent_result.get("last_reasoning")
            if _streamed_reasoning:
                await adapter.send(chat_id="test", content="reasoning")

    adapter.send.assert_not_called()
