"""E2E tests for tool_use / tool_result adjacency repair in the Anthropic adapter.

Anthropic's Messages API requires every ``tool_use`` block in an assistant
message to be immediately followed by a user message containing the matching
``tool_result`` block.  Context compression / session truncation can leave a
``tool_use`` and its ``tool_result`` both present but *non-adjacent* — a state
that the absent-side strippers (set-membership) and the alternation enforcer
both miss, producing an HTTP 400:

    messages.N: `tool_use` ids were found without `tool_result` blocks
    immediately after

These tests exercise ``convert_messages_to_anthropic`` end-to-end (OpenAI
format in, Anthropic format out) and assert the adjacency invariant holds.

Route B (B0): the defect is in ``convert_messages_to_anthropic``, not in
``compress()``.  The fix is a new adjacency-repair post-pass that runs after
the alternation enforcer.
"""

from agent.anthropic_adapter import convert_messages_to_anthropic


def _orphan_tool_uses(result):
    """Return [(index, tool_use_id), ...] for every tool_use NOT immediately
    followed by a user message containing its matching tool_result."""
    orphans = []
    for i, m in enumerate(result):
        if m["role"] != "assistant" or not isinstance(m["content"], list):
            continue
        for block in m["content"]:
            if block.get("type") != "tool_use":
                continue
            uid = block.get("id")
            adjacent = (
                i + 1 < len(result)
                and result[i + 1]["role"] == "user"
                and isinstance(result[i + 1]["content"], list)
                and any(
                    b.get("type") == "tool_result"
                    and b.get("tool_use_id") == uid
                    for b in result[i + 1]["content"]
                )
            )
            if not adjacent:
                orphans.append((i, uid))
    return orphans


class TestToolAdjacencyRepair:
    def test_non_adjacent_tool_result_is_relocated(self):
        """B0's minimal reproduction: tool_use and its tool_result are both
        present but separated by an intervening user/assistant pair.

        Before the fix this leaves an orphaned tool_use at messages[0] →
        Anthropic 400.  After the fix the tool_result is relocated to a user
        message immediately after the assistant.
        """
        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "toolu_X",
                        "type": "function",
                        "function": {"name": "f", "arguments": "{}"},
                    }
                ],
            },
            {"role": "user", "content": "wait"},
            {"role": "assistant", "content": "ok"},
            {"role": "tool", "tool_call_id": "toolu_X", "content": "result"},
        ]

        _, result = convert_messages_to_anthropic(messages)

        # No tool_use anywhere is left orphaned.
        assert _orphan_tool_uses(result) == [], (
            f"orphaned tool_use(s) remain: {_orphan_tool_uses(result)}"
        )

        # The assistant carrying tool_use toolu_X is immediately followed by a
        # user message containing tool_result toolu_X.
        tu_idx = next(
            i
            for i, m in enumerate(result)
            if m["role"] == "assistant"
            and isinstance(m["content"], list)
            and any(
                b.get("type") == "tool_use" and b.get("id") == "toolu_X"
                for b in m["content"]
            )
        )
        follower = result[tu_idx + 1]
        assert follower["role"] == "user"
        assert isinstance(follower["content"], list)
        assert any(
            b.get("type") == "tool_result" and b.get("tool_use_id") == "toolu_X"
            for b in follower["content"]
        )

    def test_adjacent_pair_not_disturbed(self):
        """A clean, already-adjacent tool_use/tool_result pair must pass
        through untouched."""
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "toolu_X", "function": {"name": "f", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "toolu_X", "content": "result"},
        ]

        _, result = convert_messages_to_anthropic(messages)

        assert _orphan_tool_uses(result) == []
        assert len(result) == 2
        assert result[0]["role"] == "assistant"
        assert any(
            b.get("type") == "tool_use" and b.get("id") == "toolu_X"
            for b in result[0]["content"]
        )
        assert result[1]["role"] == "user"
        assert result[1]["content"] == [
            {"type": "tool_result", "tool_use_id": "toolu_X", "content": "result"}
        ]

    def test_multi_tool_call_all_relocated(self):
        """An assistant message with two tool_use blocks whose results are both
        non-adjacent: both results must end up in a user message immediately
        after the assistant."""
        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "T1", "function": {"name": "a", "arguments": "{}"}},
                    {"id": "T2", "function": {"name": "b", "arguments": "{}"}},
                ],
            },
            {"role": "user", "content": "mid"},
            {"role": "assistant", "content": "resp"},
            {"role": "tool", "tool_call_id": "T1", "content": "r1"},
            {"role": "tool", "tool_call_id": "T2", "content": "r2"},
        ]

        _, result = convert_messages_to_anthropic(messages)

        assert _orphan_tool_uses(result) == [], (
            f"orphaned tool_use(s) remain: {_orphan_tool_uses(result)}"
        )

        tu_idx = next(
            i
            for i, m in enumerate(result)
            if m["role"] == "assistant"
            and isinstance(m["content"], list)
            and any(b.get("type") == "tool_use" for b in m["content"])
        )
        follower = result[tu_idx + 1]
        assert follower["role"] == "user"
        result_ids = {
            b.get("tool_use_id")
            for b in follower["content"]
            if b.get("type") == "tool_result"
        }
        assert {"T1", "T2"} <= result_ids

    def test_idempotency(self):
        """The adjacency pass must be idempotent: running the converter twice
        leaves the orphan count at zero and never duplicates a tool_result.

        The plan's idempotency contract is "running twice on already-fixed
        output changes nothing".  We assert it two ways:

        1. Re-feeding the fixed non-adjacent case keeps orphan count zero.
        2. The already-adjacent case yields exactly one tool_result for the id
           on every call (the pass finds nothing to relocate, so it cannot
           duplicate).
        """
        non_adjacent = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "toolu_X", "function": {"name": "f", "arguments": "{}"}},
                ],
            },
            {"role": "user", "content": "wait"},
            {"role": "assistant", "content": "ok"},
            {"role": "tool", "tool_call_id": "toolu_X", "content": "result"},
        ]
        _, first = convert_messages_to_anthropic(non_adjacent)
        assert _orphan_tool_uses(first) == []
        # Re-process the fixed Anthropic-format output: orphan count stays zero.
        _, second = convert_messages_to_anthropic(first)
        assert _orphan_tool_uses(second) == []

        # On already-adjacent input the pass relocates nothing and therefore
        # never duplicates the tool_result — exactly one per call, every call.
        adjacent = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"id": "toolu_Y", "function": {"name": "f", "arguments": "{}"}},
                ],
            },
            {"role": "tool", "tool_call_id": "toolu_Y", "content": "result"},
        ]
        for _ in range(2):
            _, out = convert_messages_to_anthropic(adjacent)
            assert _orphan_tool_uses(out) == []
            tool_result_count = sum(
                1
                for m in out
                if m["role"] == "user" and isinstance(m["content"], list)
                for b in m["content"]
                if b.get("type") == "tool_result"
                and b.get("tool_use_id") == "toolu_Y"
            )
            assert tool_result_count == 1, (
                f"expected exactly 1 tool_result for toolu_Y, got {tool_result_count}"
            )

    def test_strippers_still_work(self):
        """A genuinely absent tool_result (no tool result anywhere) must still
        be handled by the absent-side stripper — the tool_use block is removed
        and replaced with the '(tool call removed)' placeholder.

        Confirms the new adjacency pass does not shadow the existing strippers
        (B1 characterization-style check for the adapter side).
        """
        messages = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {"id": "toolu_X", "function": {"name": "x", "arguments": "{}"}},
                ],
            },
            {"role": "user", "content": "never mind"},
        ]

        _, result = convert_messages_to_anthropic(messages)

        assert _orphan_tool_uses(result) == []
        assistant_blocks = result[0]["content"]
        assert all(b.get("type") != "tool_use" for b in assistant_blocks)
        assert assistant_blocks == [{"type": "text", "text": "(tool call removed)"}]

    def test_relocated_tool_result_preserves_screenshot(self):
        """Relocating a tool_result that carries a computer_use screenshot must
        keep adjacency AND leave the image intact (it is well under the
        image-eviction keep-N cap).

        Guards the B0 caveat: relocation changes a tool_result's position in
        the backward image-eviction walk.  A relocated single screenshot must
        not be evicted.
        """
        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "toolu_X",
                        "function": {"name": "screenshot", "arguments": "{}"},
                    }
                ],
            },
            {"role": "user", "content": "wait"},
            {"role": "assistant", "content": "ok"},
            {
                "role": "tool",
                "tool_call_id": "toolu_X",
                "content": [
                    {"type": "text", "text": "shot"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,AAAA"},
                    },
                ],
            },
        ]

        _, result = convert_messages_to_anthropic(messages)

        assert _orphan_tool_uses(result) == []
        follower = result[1]
        assert follower["role"] == "user"
        tool_result = next(
            b
            for b in follower["content"]
            if b.get("type") == "tool_result" and b.get("tool_use_id") == "toolu_X"
        )
        inner_types = [b.get("type") for b in tool_result["content"]]
        assert "image" in inner_types, (
            "relocated screenshot must survive image eviction (under keep-N cap)"
        )
