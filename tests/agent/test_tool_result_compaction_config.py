"""Config and helper tests for tool result compaction."""

from __future__ import annotations

from pathlib import Path

import yaml

from agent.tool_result_compaction import (
    DEFAULT_MAX_DISK_MB,
    DEFAULT_PREVIEW_CHARS,
    DEFAULT_THRESHOLD_TOKENS,
    _config_bool,
    _config_int,
    _first_last_preview,
    default_raw_result_dir,
    resolve_raw_result_dir,
)


def test_config_bool_accepts_common_true_strings():
    for value in ["1", "true", "TRUE", "yes", "on"]:
        assert _config_bool({"enabled": value}, "enabled", False) is True


def test_config_bool_rejects_common_false_strings():
    for value in ["0", "false", "FALSE", "no", "off", ""]:
        assert _config_bool({"enabled": value}, "enabled", True) is False


def test_config_int_uses_default_for_invalid_values():
    assert _config_int({"threshold_tokens": "not-an-int"}, "threshold_tokens", 5000) == 5000
    assert _config_int({"threshold_tokens": None}, "threshold_tokens", 5000) == 5000


def test_config_int_applies_minimum():
    assert _config_int({"threshold_tokens": -10}, "threshold_tokens", 5000, minimum=1) == 1
    assert _config_int({"threshold_tokens": 0}, "threshold_tokens", 5000, minimum=1) == 1


def test_resolve_raw_result_dir_uses_default_for_empty_config():
    assert resolve_raw_result_dir({}) == default_raw_result_dir()
    assert resolve_raw_result_dir({"raw_result_dir": ""}) == default_raw_result_dir()


def test_resolve_raw_result_dir_expands_user_and_env(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_COMPACTION_TEST_DIR", str(tmp_path))
    expected = Path(tmp_path) / "raw"
    assert resolve_raw_result_dir({"raw_result_dir": "$HERMES_COMPACTION_TEST_DIR/raw"}) == expected


def test_first_last_preview_short_content_returns_original():
    content = "short content"
    assert _first_last_preview(content, DEFAULT_PREVIEW_CHARS) == content


def test_first_last_preview_includes_head_tail_and_omission_marker():
    content = "A" * 20 + "MIDDLE" + "Z" * 20
    preview = _first_last_preview(content, 5)
    assert preview.startswith("A" * 5)
    assert preview.endswith("Z" * 5)
    assert "omitted" in preview


def test_first_last_preview_can_be_disabled():
    assert _first_last_preview("some content", 0) == ""


def test_example_config_matches_runtime_defaults():
    example_path = Path("examples/tool-result-compaction.config.yaml")
    data = yaml.safe_load(example_path.read_text(encoding="utf-8"))
    cfg = data["tool_result_compaction"]

    assert cfg["enabled"] is False
    assert cfg["threshold_tokens"] == DEFAULT_THRESHOLD_TOKENS
    assert cfg["raw_result_dir"] == ""
    assert cfg["max_disk_mb"] == DEFAULT_MAX_DISK_MB
    assert cfg["preview_chars"] == DEFAULT_PREVIEW_CHARS
