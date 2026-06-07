from __future__ import annotations

import json
from pathlib import Path

from agent import chat_completion_helpers as helper


def test_split_concatenated_tool_call_arguments_returns_complete_dict_json_objects():
    result = helper._split_concatenated_tool_call_arguments(
        '{"path":"README.md"}{"query":"tool calls"}'
    )
    assert result == ['{"path":"README.md"}', '{"query":"tool calls"}']
    assert [json.loads(item) for item in result] == [
        {"path": "README.md"},
        {"query": "tool calls"},
    ]


def test_split_concatenated_tool_call_arguments_rejects_single_partial_or_non_dict_payloads():
    assert helper._split_concatenated_tool_call_arguments('{"path":"README.md"}') is None
    assert helper._split_concatenated_tool_call_arguments('{"path":"README.md"}{"query":') is None
    assert helper._split_concatenated_tool_call_arguments('[1,2]{"path":"README.md"}') is None
    assert helper._split_concatenated_tool_call_arguments('') is None


def test_streaming_reconstruction_wires_concatenated_argument_splitter():
    source = Path(helper.__file__).read_text(encoding="utf-8")
    assert "split_arguments = _split_concatenated_tool_call_arguments(arguments)" in source
    assert "mock_tool_calls.append(SimpleNamespace(" in source
    assert "split_idx" in source
    assert "continue" in source
