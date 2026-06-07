"""Edge-case tests for tool result compaction."""

from __future__ import annotations

import json
from pathlib import Path

from agent.tool_result_compaction import compact_tool_content_if_needed, token_estimate


class AgentWithoutSessionId:
    pass


class AgentWithUnsafeSessionId:
    session_id = "../unsafe/session:id"


def test_equal_threshold_compacts(monkeypatch, tmp_path):
    content = "x" * 40
    threshold = token_estimate(content)
    monkeypatch.setattr(
        "agent.tool_result_compaction.get_config",
        lambda: {
            "enabled": True,
            "threshold_tokens": threshold,
            "preview_chars": 5,
            "raw_result_dir": str(tmp_path),
            "max_disk_mb": 500,
        },
    )

    result, info = compact_tool_content_if_needed(
        "terminal",
        "call_equal_threshold",
        content,
        AgentWithoutSessionId(),
    )

    assert info is not None
    assert json.loads(result)["type"] == "compacted_tool_result"


def test_missing_agent_session_id_uses_session_fallback(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agent.tool_result_compaction.get_config",
        lambda: {
            "enabled": True,
            "threshold_tokens": 1,
            "raw_result_dir": str(tmp_path),
            "max_disk_mb": 500,
        },
    )

    _, info = compact_tool_content_if_needed(
        "terminal",
        "call_no_session",
        "x" * 100,
        AgentWithoutSessionId(),
    )

    assert info is not None
    assert Path(info["raw_result_path"]).parent.name == "session"


def test_unsafe_session_id_is_sanitized(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "agent.tool_result_compaction.get_config",
        lambda: {
            "enabled": True,
            "threshold_tokens": 1,
            "raw_result_dir": str(tmp_path),
            "max_disk_mb": 500,
        },
    )

    _, info = compact_tool_content_if_needed(
        "terminal",
        "call_unsafe_session",
        "x" * 100,
        AgentWithUnsafeSessionId(),
    )

    assert info is not None
    raw_path = Path(info["raw_result_path"])
    assert raw_path.parent.parent == tmp_path
    assert raw_path.parent.name == "unsafe_session_id"


def test_compaction_fail_open_when_config_helper_raises(monkeypatch):
    def boom():
        raise RuntimeError("config unavailable")

    monkeypatch.setattr("agent.tool_result_compaction.get_config", boom)
    content = "x" * 100

    result, info = compact_tool_content_if_needed(
        "terminal",
        "call_config_error",
        content,
        AgentWithoutSessionId(),
    )

    assert result == content
    assert info is None
