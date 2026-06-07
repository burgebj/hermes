"""Regression tests for the interleaved-thinking + tool_use HTTP 400 crash.

Covers two bugs fixed together:

  1. anthropic_adapter.convert_messages_to_anthropic reordered interleaved
     thinking/tool_use blocks to [all-thinking]+text+[all-tool_use], which
     modifies the signed thinking blocks and makes Anthropic reject the turn
     with HTTP 400 "thinking blocks in the latest assistant message cannot be
     modified." The fix replays the captured ordered block list verbatim.

  2. error_classifier did not recognise that 400 string (it only matched
     "signature"+"thinking"), so the existing strip-and-retry recovery never
     fired and the agent hard-aborted. The fix broadens the pattern.
"""

import json

from agent.anthropic_adapter import convert_messages_to_anthropic
from agent.error_classifier import classify_api_error, FailoverReason


class _FakeAPIError(Exception):
    """Mimics an Anthropic SDK 400 with a structured body + status_code."""

    def __init__(self, message: str):
        super().__init__(message)
        self.status_code = 400
        self.body = {
            "type": "error",
            "error": {"type": "invalid_request_error", "message": message},
        }


def _interleaved_assistant_message():
    """An assistant turn exactly like the one that crashed: interleaved
    signed thinking + tool_use blocks captured in anthropic_ordered_content."""
    ordered = [
        {"type": "thinking", "thinking": "First, list processes.", "signature": "SIG_A"},
        {"type": "tool_use", "id": "toolu_01aaa", "name": "mcp_terminal", "input": {"cmd": "ps"}},
        {"type": "thinking", "thinking": "Now check the ports.", "signature": "SIG_B"},
        {"type": "tool_use", "id": "toolu_01bbb", "name": "mcp_terminal", "input": {"cmd": "netstat"}},
        {"type": "thinking", "thinking": "And the config dir.", "signature": "SIG_C"},
        {"type": "tool_use", "id": "toolu_01ccc", "name": "mcp_terminal", "input": {"cmd": "ls ~/.hermes"}},
    ]
    return {
        "role": "assistant",
        "content": "",
        # Flat lists (the lossy representation that caused the reorder).
        "reasoning_details": [b for b in ordered if b["type"] == "thinking"],
        "tool_calls": [
            {
                "id": b["id"],
                "type": "function",
                "function": {"name": b["name"], "arguments": json.dumps(b["input"])},
            }
            for b in ordered
            if b["type"] == "tool_use"
        ],
        # The ordered capture added by the fix.
        "anthropic_ordered_content": ordered,
    }


def test_interleaved_order_preserved_verbatim():
    messages = [
        {"role": "user", "content": "why is hermes broken"},
        _interleaved_assistant_message(),
        {"role": "tool", "tool_call_id": "toolu_01aaa", "content": "proc list"},
        {"role": "tool", "tool_call_id": "toolu_01bbb", "content": "port list"},
        {"role": "tool", "tool_call_id": "toolu_01ccc", "content": "dir list"},
    ]
    _system, result = convert_messages_to_anthropic(
        messages, base_url=None, model="claude-opus-4-8"
    )
    assistant = next(m for m in result if m["role"] == "assistant")
    types_in_order = [b["type"] for b in assistant["content"]]

    # The interleave MUST be preserved exactly — not collapsed to
    # [thinking, thinking, thinking, tool_use, tool_use, tool_use].
    assert types_in_order == [
        "thinking", "tool_use", "thinking", "tool_use", "thinking", "tool_use"
    ], types_in_order

    # Signatures + thinking text round-trip byte-for-byte.
    thinking_blocks = [b for b in assistant["content"] if b["type"] == "thinking"]
    assert [b["signature"] for b in thinking_blocks] == ["SIG_A", "SIG_B", "SIG_C"]
    assert [b["thinking"] for b in thinking_blocks] == [
        "First, list processes.", "Now check the ports.", "And the config dir."
    ]
    # Tool ids round-trip so tool_result blocks still match.
    tool_ids = [b["id"] for b in assistant["content"] if b["type"] == "tool_use"]
    assert tool_ids == ["toolu_01aaa", "toolu_01bbb", "toolu_01ccc"]


def test_classifier_catches_cannot_be_modified_400():
    msg = (
        "messages.1.content.4: `thinking` or `redacted_thinking` blocks in the "
        "latest assistant message cannot be modified. These blocks must remain "
        "as they were in the original response."
    )
    classified = classify_api_error(
        _FakeAPIError(msg), provider="anthropic", model="claude-opus-4-8"
    )
    assert classified.reason == FailoverReason.thinking_signature, classified.reason
    assert classified.retryable is True


def test_classifier_still_catches_signature_400():
    msg = "Invalid signature in thinking block."
    classified = classify_api_error(
        _FakeAPIError(msg), provider="anthropic", model="claude-opus-4-8"
    )
    assert classified.reason == FailoverReason.thinking_signature, classified.reason


class _Block:
    """Minimal stand-in for an Anthropic SDK content block.

    Exposes attribute access (block.type, block.thinking, ...) AND model_dump()
    so _to_plain_data() round-trips it to a plain dict like the real SDK.
    """

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def model_dump(self):
        return dict(self.__dict__)


class _Resp:
    def __init__(self, content, stop_reason="tool_use"):
        self.content = content
        self.stop_reason = stop_reason


def test_normalize_response_captures_ordered_blocks_when_signed():
    from agent.transports.anthropic import AnthropicTransport

    resp = _Resp([
        _Block(type="thinking", thinking="t1", signature="SIG_A"),
        _Block(type="tool_use", id="toolu_01aaa", name="mcp_terminal", input={"cmd": "ps"}),
        _Block(type="thinking", thinking="t2", signature="SIG_B"),
        _Block(type="tool_use", id="toolu_01bbb", name="mcp_terminal", input={"cmd": "netstat"}),
    ])
    normalized = AnthropicTransport().normalize_response(resp)
    ordered = (normalized.provider_data or {}).get("anthropic_ordered_content")
    assert ordered is not None, "ordered content not captured for signed turn"
    assert [b["type"] for b in ordered] == [
        "thinking", "tool_use", "thinking", "tool_use"
    ], [b["type"] for b in ordered]
    assert [b.get("signature") for b in ordered if b["type"] == "thinking"] == ["SIG_A", "SIG_B"]
    # The NormalizedResponse accessor exposes it too.
    assert normalized.anthropic_ordered_content == ordered


def test_normalize_response_skips_ordered_when_unsigned():
    """Kimi/DeepSeek-style unsigned thinking must NOT trigger the ordered path
    (they keep their reasoning_content round-trip)."""
    from agent.transports.anthropic import AnthropicTransport

    resp = _Resp([
        _Block(type="thinking", thinking="t1"),  # no signature
        _Block(type="tool_use", id="toolu_01aaa", name="mcp_terminal", input={"cmd": "ps"}),
    ])
    normalized = AnthropicTransport().normalize_response(resp)
    pd = normalized.provider_data or {}
    assert "anthropic_ordered_content" not in pd, "unsigned turn must not capture ordered blocks"
    # reasoning_details is still captured (existing behaviour).
    assert pd.get("reasoning_details")


if __name__ == "__main__":
    test_interleaved_order_preserved_verbatim()
    test_classifier_catches_cannot_be_modified_400()
    test_classifier_still_catches_signature_400()
    test_normalize_response_captures_ordered_blocks_when_signed()
    test_normalize_response_skips_ordered_when_unsigned()
    print("ALL TESTS PASSED")
