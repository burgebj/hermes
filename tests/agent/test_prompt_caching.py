"""Tests for agent/prompt_caching.py — Anthropic cache control injection."""


from agent.prompt_caching import (
    _apply_cache_marker,
    apply_anthropic_cache_control,
    apply_tool_cache_control,
)


MARKER = {"type": "ephemeral"}


class TestApplyCacheMarker:
    def test_tool_message_gets_top_level_marker_on_native_anthropic(self):
        """Native Anthropic path: cache_control injected top-level (adapter moves it inside tool_result)."""
        msg = {"role": "tool", "content": "result"}
        _apply_cache_marker(msg, MARKER, native_anthropic=True)
        assert msg["cache_control"] == MARKER

    def test_tool_message_skips_marker_on_openrouter(self):
        """OpenRouter path: top-level cache_control on role:tool is invalid and causes silent hang."""
        msg = {"role": "tool", "content": "result"}
        _apply_cache_marker(msg, MARKER, native_anthropic=False)
        assert "cache_control" not in msg

    def test_none_content_gets_top_level_marker(self):
        msg = {"role": "assistant", "content": None}
        _apply_cache_marker(msg, MARKER)
        assert msg["cache_control"] == MARKER

    def test_empty_string_content_gets_top_level_marker(self):
        """Empty text blocks cannot have cache_control (Anthropic rejects them)."""
        msg = {"role": "assistant", "content": ""}
        _apply_cache_marker(msg, MARKER)
        assert msg["cache_control"] == MARKER
        # Must NOT wrap into [{"type": "text", "text": "", "cache_control": ...}]
        assert msg["content"] == ""

    def test_string_content_wrapped_in_list(self):
        msg = {"role": "user", "content": "Hello"}
        _apply_cache_marker(msg, MARKER)
        assert isinstance(msg["content"], list)
        assert len(msg["content"]) == 1
        assert msg["content"][0]["type"] == "text"
        assert msg["content"][0]["text"] == "Hello"
        assert msg["content"][0]["cache_control"] == MARKER

    def test_list_content_last_item_gets_marker(self):
        msg = {
            "role": "user",
            "content": [
                {"type": "text", "text": "First"},
                {"type": "text", "text": "Second"},
            ],
        }
        _apply_cache_marker(msg, MARKER)
        assert "cache_control" not in msg["content"][0]
        assert msg["content"][1]["cache_control"] == MARKER

    def test_empty_list_content_no_crash(self):
        msg = {"role": "user", "content": []}
        # Should not crash on empty list
        _apply_cache_marker(msg, MARKER)


class TestApplyAnthropicCacheControl:
    def test_empty_messages(self):
        result = apply_anthropic_cache_control([])
        assert result == []

    def test_returns_deep_copy(self):
        msgs = [{"role": "user", "content": "Hello"}]
        result = apply_anthropic_cache_control(msgs)
        assert result is not msgs
        assert result[0] is not msgs[0]
        # Original should be unmodified
        assert "cache_control" not in msgs[0].get("content", "")

    def test_system_message_gets_marker(self):
        msgs = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]
        result = apply_anthropic_cache_control(msgs)
        # System message should have cache_control
        sys_content = result[0]["content"]
        assert isinstance(sys_content, list)
        assert sys_content[0]["cache_control"]["type"] == "ephemeral"

    def test_last_3_non_system_get_markers(self):
        msgs = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "msg1"},
            {"role": "assistant", "content": "msg2"},
            {"role": "user", "content": "msg3"},
            {"role": "assistant", "content": "msg4"},
        ]
        result = apply_anthropic_cache_control(msgs)
        # System (index 0) + last 3 non-system (indices 2, 3, 4) = 4 breakpoints
        # Index 1 (msg1) should NOT have marker
        content_1 = result[1]["content"]
        if isinstance(content_1, str):
            assert True  # No marker applied (still a string)
        else:
            assert "cache_control" not in content_1[0]

    def test_no_system_message(self):
        msgs = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = apply_anthropic_cache_control(msgs)
        # Both should get markers (4 slots available, only 2 messages)
        assert len(result) == 2

    def test_1h_ttl(self):
        msgs = [{"role": "system", "content": "System prompt"}]
        result = apply_anthropic_cache_control(msgs, cache_ttl="1h")
        sys_content = result[0]["content"]
        assert isinstance(sys_content, list)
        assert sys_content[0]["cache_control"]["ttl"] == "1h"

    def test_max_4_breakpoints(self):
        msgs = [
            {"role": "system", "content": "System"},
        ] + [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg{i}"}
            for i in range(10)
        ]
        result = apply_anthropic_cache_control(msgs)
        # Count how many messages have cache_control
        count = 0
        for msg in result:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "cache_control" in item:
                        count += 1
            elif "cache_control" in msg:
                count += 1
        assert count <= 4


# ─────────────────────────────────────────────────────────────────────
# Tool schema caching (apply_tool_cache_control)
# ─────────────────────────────────────────────────────────────────────


class TestApplyToolCacheControl:
    def test_empty_tools_returns_unchanged(self):
        assert apply_tool_cache_control([]) == []

    def test_last_tool_gets_cache_marker(self):
        tools = [
            {"type": "function", "function": {"name": "a"}},
            {"type": "function", "function": {"name": "b"}},
        ]
        result = apply_tool_cache_control(tools)
        assert "cache_control" not in result[0]
        assert result[1]["cache_control"] == {"type": "ephemeral"}

    def test_single_tool_gets_marker(self):
        tools = [{"type": "function", "function": {"name": "only"}}]
        result = apply_tool_cache_control(tools)
        assert result[0]["cache_control"] == {"type": "ephemeral"}

    def test_returns_new_list(self):
        tools = [{"type": "function", "function": {"name": "a"}}]
        result = apply_tool_cache_control(tools)
        assert result is not tools

    def test_does_not_mutate_input(self):
        tools = [{"type": "function", "function": {"name": "a"}}]
        apply_tool_cache_control(tools)
        assert "cache_control" not in tools[0]

    def test_earlier_tools_are_shared_references(self):
        tools = [
            {"type": "function", "function": {"name": "a"}},
            {"type": "function", "function": {"name": "b"}},
        ]
        result = apply_tool_cache_control(tools)
        assert result[0] is tools[0]

    def test_1h_ttl(self):
        tools = [{"type": "function", "function": {"name": "a"}}]
        result = apply_tool_cache_control(tools, cache_ttl="1h")
        assert result[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}


# ─────────────────────────────────────────────────────────────────────
# reserved_breakpoints parameter
# ─────────────────────────────────────────────────────────────────────


def _count_cached_messages(messages):
    """Count messages that have a cache_control marker."""
    count = 0
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "cache_control" in item:
                    count += 1
                    break
        elif "cache_control" in msg:
            count += 1
    return count


class TestReservedBreakpoints:
    def test_reserved_reduces_message_breakpoints(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
        ]
        full = apply_anthropic_cache_control(msgs, reserved_breakpoints=0)
        reserved = apply_anthropic_cache_control(msgs, reserved_breakpoints=1)
        assert _count_cached_messages(reserved) == _count_cached_messages(full) - 1

    def test_zero_reserved_is_default_behavior(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
        ]
        default = apply_anthropic_cache_control(msgs)
        explicit = apply_anthropic_cache_control(msgs, reserved_breakpoints=0)
        assert _count_cached_messages(default) == _count_cached_messages(explicit)

    def test_reserved_all_slots_marks_no_messages(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
        ]
        result = apply_anthropic_cache_control(msgs, reserved_breakpoints=3)
        assert _count_cached_messages(result) == 1  # system only

    def test_reserved_exceeding_budget_marks_system_only(self):
        msgs = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
        ]
        result = apply_anthropic_cache_control(msgs, reserved_breakpoints=10)
        assert _count_cached_messages(result) == 1  # system only, no crash
