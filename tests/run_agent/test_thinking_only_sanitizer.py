"""Tests for the thinking-only assistant message sanitizer.

Covers _is_thinking_only_assistant() + _drop_thinking_only_and_merge_users()
in run_agent.py. The sanitizer runs on the per-call api_messages copy and
drops assistant turns that contain only reasoning (no visible content, no
tool_calls). Adjacent user messages left behind are merged so role
alternation is preserved for the provider.

Claude Code uses this exact pattern (filterOrphanedThinkingOnlyMessages +
mergeAdjacentUserMessages in src/utils/messages.ts). See #16823 for the
backstory on why the alternative — fabricating "." stub text — was rejected.
"""

from run_agent import AIAgent


# ---------------------------------------------------------------------------
# _is_thinking_only_assistant — detection
# ---------------------------------------------------------------------------


class TestIsThinkingOnlyAssistant:

    def test_plain_assistant_reply_is_not_thinking_only(self):
        msg = {"role": "assistant", "content": "Hello there"}
        assert not AIAgent._is_thinking_only_assistant(msg)

    def test_assistant_with_tool_calls_is_not_thinking_only(self):
        msg = {
            "role": "assistant",
            "content": "",
            "reasoning": "let me use a tool",
            "tool_calls": [{"id": "c1", "function": {"name": "terminal", "arguments": "{}"}}],
        }
        assert not AIAgent._is_thinking_only_assistant(msg)

    def test_empty_content_plus_reasoning_is_thinking_only(self):
        msg = {"role": "assistant", "content": "", "reasoning": "thinking..."}
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_none_content_plus_reasoning_content_is_thinking_only(self):
        msg = {"role": "assistant", "content": None, "reasoning_content": "thinking..."}
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_whitespace_only_content_plus_reasoning_is_thinking_only(self):
        msg = {"role": "assistant", "content": "   \n\n  ", "reasoning": "r"}
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_empty_content_no_reasoning_is_not_thinking_only(self):
        # If there's no reasoning either, this is just an empty turn — let
        # other sanitizers handle it (orphan-tool-pair, etc.). We only care
        # about the specific thinking-only case.
        msg = {"role": "assistant", "content": ""}
        assert not AIAgent._is_thinking_only_assistant(msg)

    def test_list_content_all_thinking_blocks_is_thinking_only(self):
        # Anthropic-native shape
        msg = {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "...", "signature": "sig"},
            ],
            "reasoning": "...",
        }
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_list_content_with_real_text_is_not_thinking_only(self):
        msg = {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "..."},
                {"type": "text", "text": "Hi there"},
            ],
            "reasoning": "...",
        }
        assert not AIAgent._is_thinking_only_assistant(msg)

    def test_list_content_with_tool_use_block_is_not_thinking_only(self):
        msg = {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "..."},
                {"type": "tool_use", "id": "tu1", "name": "terminal", "input": {}},
            ],
        }
        assert not AIAgent._is_thinking_only_assistant(msg)

    def test_list_content_thinking_plus_whitespace_text_is_thinking_only(self):
        msg = {
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "..."},
                {"type": "text", "text": "   "},
            ],
            "reasoning": "...",
        }
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_reasoning_details_list_form_detected(self):
        msg = {
            "role": "assistant",
            "content": "",
            "reasoning_details": [{"type": "thinking", "text": "..."}],
        }
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_codex_reasoning_items_only_is_thinking_only_for_non_codex_target(self):
        # Codex Responses returns no visible content but encrypted reasoning
        # state. On a non-codex target (e.g. an Anthropic fallback) such turns
        # would survive into the request as "(empty)" assistant text →
        # trailing assistant prefill. See #29205.
        msg = {
            "role": "assistant",
            "content": "",
            "finish_reason": "incomplete",
            "codex_reasoning_items": [
                {"type": "reasoning", "encrypted_content": "..."}
            ],
        }
        assert AIAgent._is_thinking_only_assistant(msg, "anthropic_messages")
        # Default (unknown) target also drops — safe for Anthropic-family.
        assert AIAgent._is_thinking_only_assistant(msg)

    def test_codex_reasoning_items_kept_for_codex_responses_target(self):
        # When the target IS codex_responses the encrypted reasoning items are
        # legitimate replay state and must not be dropped.
        msg = {
            "role": "assistant",
            "content": "",
            "finish_reason": "incomplete",
            "codex_reasoning_items": [
                {"type": "reasoning", "encrypted_content": "..."}
            ],
        }
        assert not AIAgent._is_thinking_only_assistant(msg, "codex_responses")

    def test_codex_reasoning_items_with_tool_calls_is_not_thinking_only(self):
        msg = {
            "role": "assistant",
            "content": "",
            "codex_reasoning_items": [{"type": "reasoning", "encrypted_content": "..."}],
            "tool_calls": [{"id": "c1", "function": {"name": "terminal", "arguments": "{}"}}],
        }
        assert not AIAgent._is_thinking_only_assistant(msg, "anthropic_messages")

    def test_empty_codex_reasoning_items_is_not_thinking_only(self):
        msg = {"role": "assistant", "content": "", "codex_reasoning_items": []}
        assert not AIAgent._is_thinking_only_assistant(msg, "anthropic_messages")

    def test_drops_codex_reasoning_only_turns_and_merges_for_anthropic(self):
        # Two consecutive Codex reasoning-only empty turns before an Anthropic
        # fallback would otherwise merge into a trailing assistant "(empty)"
        # block, which Anthropic rejects as assistant prefill.
        msgs = [
            {"role": "user", "content": "u1"},
            {
                "role": "assistant",
                "content": "",
                "codex_reasoning_items": [{"encrypted_content": "a"}],
            },
            {
                "role": "assistant",
                "content": "",
                "codex_reasoning_items": [{"encrypted_content": "b"}],
            },
            {"role": "user", "content": "u2"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs, "anthropic_messages")
        assert len(out) == 1
        assert out[0]["role"] == "user"
        assert out[0]["content"] == "u1\n\nu2"

    def test_keeps_codex_reasoning_only_turns_for_codex_responses(self):
        msgs = [
            {"role": "user", "content": "u1"},
            {
                "role": "assistant",
                "content": "",
                "codex_reasoning_items": [{"encrypted_content": "a"}],
            },
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs, "codex_responses")
        # No drop → identity return.
        assert out is msgs

    def test_user_message_never_thinking_only(self):
        assert not AIAgent._is_thinking_only_assistant({"role": "user", "content": ""})

    def test_tool_message_never_thinking_only(self):
        assert not AIAgent._is_thinking_only_assistant(
            {"role": "tool", "content": "", "tool_call_id": "x"}
        )

    def test_non_dict_returns_false(self):
        assert not AIAgent._is_thinking_only_assistant(None)
        assert not AIAgent._is_thinking_only_assistant("hello")


# ---------------------------------------------------------------------------
# _drop_thinking_only_and_merge_users — the full pass
# ---------------------------------------------------------------------------


class TestDropThinkingOnlyAndMergeUsers:

    def test_empty_list_passthrough(self):
        assert AIAgent._drop_thinking_only_and_merge_users([]) == []

    def test_no_thinking_only_messages_is_noop_identity(self):
        msgs = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        # Should return the original list untouched (identity) when no changes.
        assert out is msgs

    def test_drops_thinking_only_between_user_messages_and_merges(self):
        msgs = [
            {"role": "user", "content": "help me with X"},
            {"role": "assistant", "content": "", "reasoning": "let me think"},
            {"role": "user", "content": "ok continue"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert len(out) == 1
        assert out[0]["role"] == "user"
        assert out[0]["content"] == "help me with X\n\nok continue"

    def test_preserves_alternation_after_drop(self):
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "", "reasoning": "..."},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "real reply"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        roles = [m["role"] for m in out]
        assert roles == ["user", "assistant"]
        assert out[0]["content"] == "u1\n\nu2"
        assert out[1]["content"] == "real reply"

    def test_does_not_merge_when_drop_leaves_non_adjacent_users(self):
        # Thinking-only at end of conversation — no trailing user to merge
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "", "reasoning": "..."},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert [m["role"] for m in out] == ["user", "assistant", "user"]

    def test_multiple_thinking_only_in_sequence_collapses(self):
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "", "reasoning": "r1"},
            {"role": "assistant", "content": "", "reasoning": "r2"},
            {"role": "user", "content": "u2"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert len(out) == 1
        assert out[0]["content"] == "u1\n\nu2"

    def test_does_not_touch_stored_messages_original_list_unmutated(self):
        original_first_user = {"role": "user", "content": "u1"}
        original_assistant = {"role": "assistant", "content": "", "reasoning": "..."}
        original_second_user = {"role": "user", "content": "u2"}
        msgs = [original_first_user, original_assistant, original_second_user]
        AIAgent._drop_thinking_only_and_merge_users(msgs)
        # Caller passes in a per-call copy already, but the sanitizer itself
        # must not rewrite the dicts it was handed on the drop path.
        # (It CAN mutate merged dicts — those come from the caller's copy.)
        assert original_first_user["content"] == "u1"
        assert original_second_user["content"] == "u2"

    def test_tool_result_between_user_and_thinking_preserved(self):
        # Tool results shouldn't block a drop — but they do block the merge
        # (user/tool are different roles). This scenario shouldn't happen in
        # practice because a thinking-only turn won't have tool_calls, but if
        # it did somehow, the surrounding tool result stays put.
        msgs = [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "tool_calls": [{"id": "c1", "function": {"name": "t", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "c1", "content": "ok"},
            {"role": "assistant", "content": "", "reasoning": "..."},
            {"role": "user", "content": "u2"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert [m["role"] for m in out] == ["user", "assistant", "tool", "user"]

    def test_merge_concatenates_list_content_user_messages(self):
        msgs = [
            {"role": "user", "content": [{"type": "text", "text": "first"}]},
            {"role": "assistant", "content": "", "reasoning": "..."},
            {"role": "user", "content": [{"type": "text", "text": "second"}]},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert len(out) == 1
        assert out[0]["content"] == [
            {"type": "text", "text": "first"},
            {"type": "text", "text": "second"},
        ]

    def test_merge_mixed_string_and_list_content(self):
        msgs = [
            {"role": "user", "content": "plain text"},
            {"role": "assistant", "content": "", "reasoning": "..."},
            {"role": "user", "content": [{"type": "text", "text": "block text"}]},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert len(out) == 1
        assert out[0]["content"] == [
            {"type": "text", "text": "plain text"},
            {"type": "text", "text": "block text"},
        ]

    def test_system_messages_ignored_by_pass(self):
        msgs = [
            {"role": "system", "content": "sys prompt"},
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "", "reasoning": "..."},
            {"role": "user", "content": "u2"},
        ]
        out = AIAgent._drop_thinking_only_and_merge_users(msgs)
        assert len(out) == 2
        assert out[0]["role"] == "system"
        assert out[1]["role"] == "user"
        assert out[1]["content"] == "u1\n\nu2"
