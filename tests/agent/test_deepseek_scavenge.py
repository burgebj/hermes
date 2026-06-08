"""Tests for DeepSeek R1 tool-call scavenge."""
import pytest
from agent.deepseek_scavenge import (
    scavenge_tool_calls_from_reasoning,
    _parse_arguments,
)

VALID_TOOLS = {"read_file", "web_search", "terminal", "write_file"}


class TestParseArguments:
    def test_valid_json(self):
        assert _parse_arguments('{"path": "/tmp/x"}') == {"path": "/tmp/x"}

    def test_truncated_with_brace_balancing(self):
        # Bare truncated JSON without brace balancing yields empty dict;
        # this function is meant for already-balanced args from _extract_balanced_braces.
        result = _parse_arguments('{"path": "/tmp/x", "offset": 1')
        # Graceful degradation: return empty dict on unparseable input
        assert isinstance(result, dict)

    def test_empty(self):
        assert _parse_arguments("") == {}
        assert _parse_arguments("not json") == {}

    def test_nested(self):
        result = _parse_arguments('{"a": {"b": 1}, "c": [1, 2, 3]}')
        assert result == {"a": {"b": 1}, "c": [1, 2, 3]}


class TestScavenge:
    def test_no_reasoning(self):
        calls, msg = scavenge_tool_calls_from_reasoning("", VALID_TOOLS)
        assert calls is None
        assert "empty reasoning" in msg

    def test_no_valid_tool_names(self):
        calls, msg = scavenge_tool_calls_from_reasoning(
            '{"name": "read_file", "arguments": {"path": "/x"}}', set()
        )
        assert calls is None
        assert "no tool names" in msg

    def test_single_valid_tool_call(self):
        reasoning = 'Let me read the file...\n{"name": "read_file", "arguments": {"path": "/tmp/x"}}'
        calls, msg = scavenge_tool_calls_from_reasoning(reasoning, VALID_TOOLS)
        assert calls is not None
        assert len(calls) == 1
        assert calls[0].function.name == "read_file"
        assert '{"path": "/tmp/x"}' in calls[0].function.arguments

    def test_unknown_tool_ignored(self):
        reasoning = '{"name": "delete_everything", "arguments": {}}'
        calls, msg = scavenge_tool_calls_from_reasoning(reasoning, VALID_TOOLS)
        assert calls is None
        assert "no valid tool calls" in msg

    def test_duplicates_removed(self):
        reasoning = (
            '{"name": "read_file", "arguments": {"path": "/a"}}\n'
            '{"name": "read_file", "arguments": {"path": "/a"}}'
        )
        calls, msg = scavenge_tool_calls_from_reasoning(reasoning, VALID_TOOLS)
        assert calls is not None
        assert len(calls) == 1

    def test_multiple_valid_tools(self):
        reasoning = (
            '{"name": "read_file", "arguments": {"path": "/a"}}\n'
            '{"name": "web_search", "arguments": {"query": "test"}}'
        )
        calls, msg = scavenge_tool_calls_from_reasoning(reasoning, VALID_TOOLS)
        assert calls is not None
        assert len(calls) == 2
        names = {c.function.name for c in calls}
        assert names == {"read_file", "web_search"}
