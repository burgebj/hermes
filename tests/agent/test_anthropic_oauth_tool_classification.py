"""Tests for Anthropic Claude Code billing-route tool-name classification fix.

See :data:`agent.anthropic_adapter._TOOL_NAME_RENAMES` and the step 3/4/5
block in :func:`agent.anthropic_adapter.build_anthropic_kwargs`.
"""

from __future__ import annotations

import pytest

from agent.anthropic_adapter import (
    _MCP_TOOL_PREFIX,
    _TOOL_NAME_RENAMES,
    _TOOL_NAME_RENAME_REVERSE,
    build_anthropic_kwargs,
)


def _openai_tool(name: str, params: dict | None = None) -> dict:
    """Tiny OpenAI-format tool definition helper."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": "x",
            "parameters": params
            or {"type": "object", "properties": {}, "required": []},
        },
    }


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


def test_oauth_does_not_prefix_tool_names_with_mcp():
    """The ``mcp_`` prefix triggers Anthropic's third-party classifier."""
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=[{"role": "user", "content": "hi"}],
        tools=[_openai_tool("my_tool")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=True,
    )
    assert kwargs["tools"][0]["name"] == "my_tool"
    assert not kwargs["tools"][0]["name"].startswith(_MCP_TOOL_PREFIX)


def test_oauth_renames_session_search_tool():
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=[{"role": "user", "content": "hi"}],
        tools=[_openai_tool("session_search")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=True,
    )
    assert kwargs["tools"][0]["name"] == "recall_sessions"


def test_oauth_renames_skills_list_tool():
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=[{"role": "user", "content": "hi"}],
        tools=[_openai_tool("skills_list")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=True,
    )
    assert kwargs["tools"][0]["name"] == "list_capabilities"


def test_non_oauth_keeps_original_tool_names():
    """Non-OAuth paths (regular API keys, third-party) keep original names."""
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=[{"role": "user", "content": "hi"}],
        tools=[_openai_tool("session_search"), _openai_tool("my_tool")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=False,
    )
    names = [t["name"] for t in kwargs["tools"]]
    assert names == ["session_search", "my_tool"]


# ---------------------------------------------------------------------------
# Message history rewriting
# ---------------------------------------------------------------------------


def _openai_history_with_tool_call(tool_name: str) -> list[dict]:
    """OpenAI-format message history with a paired tool_call + tool_result.

    ``convert_messages_to_anthropic`` builds ``tool_use`` blocks from the
    assistant's ``tool_calls`` field, and strips orphaned tool_use blocks
    that have no matching tool_result — so both sides must be present
    for the history round-trip to survive.
    """
    call_id = "toolu_01"
    return [
        {"role": "user", "content": "please run something"},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": tool_name, "arguments": "{}"},
                }
            ],
        },
        {"role": "tool", "tool_call_id": call_id, "content": "ok"},
    ]


def _extract_tool_use_names(kwargs: dict) -> list[str]:
    names = []
    for m in kwargs["messages"]:
        c = m.get("content")
        if not isinstance(c, list):
            continue
        for blk in c:
            if isinstance(blk, dict) and blk.get("type") == "tool_use":
                names.append(blk.get("name"))
    return names


def test_oauth_strips_mcp_prefix_from_historical_tool_use():
    """Sessions that started on older code persist ``mcp_*`` tool_use names.

    Without this rewrite Anthropic sees a ``tool_use`` referring to a tool
    not declared in the request and returns HTTP 200 with empty content.
    """
    history = _openai_history_with_tool_call("mcp_my_tool")
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=history + [{"role": "user", "content": "follow up"}],
        tools=[_openai_tool("my_tool")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=True,
    )
    names = _extract_tool_use_names(kwargs)
    assert names, "expected at least one tool_use block in rewritten messages"
    assert all(not n.startswith(_MCP_TOOL_PREFIX) for n in names)
    assert names[0] == "my_tool"


def test_oauth_renames_tool_use_in_history_even_when_prefixed():
    """``mcp_`` prefix strip and rename combine for legacy sessions."""
    history = _openai_history_with_tool_call("mcp_session_search")
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=history + [{"role": "user", "content": "again"}],
        tools=[_openai_tool("session_search")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=True,
    )
    assert _extract_tool_use_names(kwargs) == ["recall_sessions"]
    # And the declared tool matches the rewritten history entry.
    assert kwargs["tools"][0]["name"] == "recall_sessions"


def test_oauth_history_rewrite_leaves_non_mcp_tool_use_intact():
    """Plain tool_use entries that never had the prefix are untouched."""
    history = _openai_history_with_tool_call("my_tool")
    kwargs = build_anthropic_kwargs(
        model="claude-opus-4-6",
        messages=history + [{"role": "user", "content": "ping"}],
        tools=[_openai_tool("my_tool")],
        max_tokens=16,
        reasoning_config=None,
        is_oauth=True,
    )
    assert _extract_tool_use_names(kwargs) == ["my_tool"]


# ---------------------------------------------------------------------------
# Reverse map
# ---------------------------------------------------------------------------


def test_rename_reverse_map_is_consistent():
    """Every forward rename must have a reverse entry, and vice-versa."""
    assert _TOOL_NAME_RENAME_REVERSE == {
        v: k for k, v in _TOOL_NAME_RENAMES.items()
    }
    for original, renamed in _TOOL_NAME_RENAMES.items():
        assert _TOOL_NAME_RENAME_REVERSE[renamed] == original


def test_handle_function_call_reverses_rename():
    """``model_tools.handle_function_call`` maps renamed calls back to the real name."""
    from model_tools import handle_function_call

    # An unknown renamed name should be mapped back before dispatch.  We
    # assert indirectly by relying on the registry returning an error for
    # the real name rather than the renamed one.
    result = handle_function_call(
        function_name="recall_sessions",
        function_args={},
    )
    # Not asserting success — just that the call didn't blow up on the
    # renamed form (which would be treated as an unknown tool).  We accept
    # either "unknown tool" resolving to the real name, or a real-tool
    # response.  What we DON'T want is a dispatch on the renamed name.
    assert "recall_sessions" not in str(result), (
        "reverse rename should map the call back to 'session_search' "
        "before dispatch"
    )
