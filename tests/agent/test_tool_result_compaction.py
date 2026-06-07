"""Tests for tool_result_compaction.

No real config, no writes outside pytest tmp dirs — all tests use monkeypatch to isolate.
"""

from __future__ import annotations

import json
import stat

import pytest

from agent.tool_result_compaction import (
    DEFAULT_ENABLED,
    DEFAULT_MAX_DISK_MB,
    DEFAULT_PREVIEW_CHARS,
    DEFAULT_RAW_RESULT_DIR,
    DEFAULT_THRESHOLD_TOKENS,
    compact_tool_content_if_needed,
    get_config,
    is_enabled,
    sanitize_path_component,
    token_estimate,
)


class DummyAgent:
    session_id = "session/test:abc"


class TestConfigDefaults:
    """Default values — no config file read, pure constants."""

    def test_default_enabled_is_false(self):
        assert DEFAULT_ENABLED is False

    def test_default_threshold_tokens(self):
        assert DEFAULT_THRESHOLD_TOKENS == 5000

    def test_default_preview_chars(self):
        assert DEFAULT_PREVIEW_CHARS == 1000

    def test_default_max_disk_mb(self):
        assert DEFAULT_MAX_DISK_MB == 500

    def test_default_raw_result_dir_is_empty(self):
        assert DEFAULT_RAW_RESULT_DIR == ""


class TestConfigMonkeypatch:
    """get_config() and is_enabled() must be monkeypatchable.

    These tests do NOT read the real ~/.hermes/config.yaml.
    """

    def test_is_enabled_default(self, monkeypatch):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {},
        )
        assert is_enabled() is False

    def test_is_enabled_true_when_enabled(self, monkeypatch):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": True},
        )
        assert is_enabled() is True

    def test_get_config_empty_by_default(self, monkeypatch):
        monkeypatch.setattr(
            "hermes_cli.config.read_raw_config",
            lambda: {},
        )
        cfg = get_config()
        assert cfg == {}


class TestHelpers:
    def test_token_estimate_empty(self):
        assert token_estimate("") == 0

    def test_token_estimate_non_empty_minimum_one(self):
        assert token_estimate("abc") == 1

    def test_sanitize_path_component(self):
        assert sanitize_path_component("session/test:abc") == "session_test_abc"

    def test_sanitize_path_component_fallback(self):
        assert sanitize_path_component("///", fallback="fallback") == "fallback"


class TestDisabledPassthrough:
    """compact_tool_content_if_needed passes through when disabled."""

    def test_returns_original_content_when_disabled(self, monkeypatch):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": False},
        )
        content = "some large tool output here"
        result, info = compact_tool_content_if_needed(
            "read_file", "call_abc", content, None,
        )
        assert result == content
        assert info is None

    def test_passthrough_with_large_content_when_disabled(self, monkeypatch):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": False},
        )
        content = "x" * 100_000
        result, info = compact_tool_content_if_needed(
            "terminal", "call_def", content, None,
        )
        assert result == content
        assert info is None

    def test_passthrough_with_empty_string_when_disabled(self, monkeypatch):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": False},
        )
        result, info = compact_tool_content_if_needed(
            "read_file", "call_empty", "", None,
        )
        assert result == ""
        assert info is None

    def test_passthrough_with_special_characters_when_disabled(self, monkeypatch):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": False},
        )
        content = "line1\nline2\n\t\ud83d\ude00  # emoji + tab"
        result, info = compact_tool_content_if_needed(
            "search_files", "call_special", content, None,
        )
        assert result == content
        assert info is None

    def test_passthrough_with_none_agent_when_disabled(self, monkeypatch):
        """agent=None is valid when disabled — no access needed."""
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": False},
        )
        result, info = compact_tool_content_if_needed(
            "web_search", "call_none", "some data", None,
        )
        assert result == "some data"
        assert info is None

    @pytest.mark.parametrize("tool_name", [
        "read_file",
        "terminal",
        "search_files",
        "web_search",
        "vision_analyze",
        "execute_code",
    ])
    def test_passthrough_for_all_tool_names_when_disabled(self, monkeypatch, tool_name):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {"enabled": False},
        )
        result, info = compact_tool_content_if_needed(
            tool_name, "call_param", "content", None,
        )
        assert result == "content"
        assert info is None


class TestCompactionCore:
    def test_below_threshold_passes_through_when_enabled(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {
                "enabled": True,
                "threshold_tokens": 1000,
                "raw_result_dir": str(tmp_path),
            },
        )
        result, info = compact_tool_content_if_needed(
            "read_file", "call_small", "small content", DummyAgent(),
        )
        assert result == "small content"
        assert info is None
        assert list(tmp_path.rglob("*.json")) == []

    def test_large_content_compacts_and_writes_raw_result(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {
                "enabled": True,
                "threshold_tokens": 10,
                "preview_chars": 8,
                "raw_result_dir": str(tmp_path),
            },
        )
        content = "A" * 100 + "MIDDLE" + "Z" * 100
        result, info = compact_tool_content_if_needed(
            "read/file", "call:large", content, DummyAgent(),
        )

        compacted = json.loads(result)
        assert compacted["type"] == "compacted_tool_result"
        assert compacted["tool_name"] == "read/file"
        assert compacted["tool_call_id"] == "call:large"
        assert compacted["original_char_count"] == len(content)
        assert compacted["original_token_estimate"] == token_estimate(content)
        assert "omitted" in compacted["compacted_preview"]
        assert compacted["compacted_preview"].startswith("A" * 8)
        assert compacted["compacted_preview"].endswith("Z" * 8)
        assert info is not None
        assert info["original_chars"] == len(content)

        raw_path = tmp_path / "session_test_abc" / next((tmp_path / "session_test_abc").iterdir()).name
        assert raw_path.exists()
        raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
        assert raw_payload["content"] == content
        assert raw_payload["tool_name"] == "read/file"
        assert raw_payload["tool_call_id"] == "call:large"

    def test_raw_result_file_permissions_are_private(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {
                "enabled": True,
                "threshold_tokens": 1,
                "raw_result_dir": str(tmp_path),
            },
        )
        _, info = compact_tool_content_if_needed(
            "terminal", "call_perm", "x" * 100, DummyAgent(),
        )
        assert info is not None
        raw_path = tmp_path / "session_test_abc" / next((tmp_path / "session_test_abc").iterdir()).name
        assert stat.S_IMODE(raw_path.stat().st_mode) == 0o600
        assert stat.S_IMODE(raw_path.parent.stat().st_mode) == 0o700

    def test_fail_open_on_write_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr(
            "agent.tool_result_compaction.get_config",
            lambda: {
                "enabled": True,
                "threshold_tokens": 1,
                "raw_result_dir": str(tmp_path),
            },
        )

        def boom(*args, **kwargs):
            raise OSError("disk unavailable")

        monkeypatch.setattr("agent.tool_result_compaction._write_raw_result", boom)
        content = "x" * 100
        result, info = compact_tool_content_if_needed(
            "terminal", "call_fail", content, DummyAgent(),
        )
        assert result == content
        assert info is None
