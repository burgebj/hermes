"""Integration-style tests for compacted tool-result message shape."""

from __future__ import annotations

import json

from agent.tool_dispatch_helpers import make_tool_result_message
from agent.tool_result_compaction import compact_tool_content_if_needed


class DummyAgent:
    session_id = "integration/session"


def test_compacted_content_remains_valid_tool_message(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agent.tool_result_compaction.get_config",
        lambda: {
            "enabled": True,
            "threshold_tokens": 1,
            "preview_chars": 12,
            "raw_result_dir": str(tmp_path),
            "max_disk_mb": 500,
        },
    )
    original_content = "alpha\n" + ("middle\n" * 50) + "omega\n"

    compacted_content, info = compact_tool_content_if_needed(
        "terminal",
        "call_integration",
        original_content,
        DummyAgent(),
    )
    message = make_tool_result_message(
        "terminal",
        compacted_content,
        "call_integration",
    )

    assert message["role"] == "tool"
    assert message["name"] == "terminal"
    assert message["tool_name"] == "terminal"
    assert message["tool_call_id"] == "call_integration"
    assert isinstance(message["content"], str)

    payload = json.loads(message["content"])
    assert payload["type"] == "compacted_tool_result"
    assert payload["tool_name"] == "terminal"
    assert payload["tool_call_id"] == "call_integration"
    assert payload["raw_result_path"] == info["raw_result_path"]
    assert "alpha" in payload["compacted_preview"]
    assert "omega" in payload["compacted_preview"]


def test_disabled_compaction_tool_message_is_unchanged(monkeypatch):
    monkeypatch.setattr(
        "agent.tool_result_compaction.get_config",
        lambda: {"enabled": False},
    )
    original_content = "small output"

    content, info = compact_tool_content_if_needed(
        "read_file",
        "call_disabled",
        original_content,
        DummyAgent(),
    )
    message = make_tool_result_message("read_file", content, "call_disabled")

    assert info is None
    assert message["content"] == original_content
    assert message["tool_call_id"] == "call_disabled"
