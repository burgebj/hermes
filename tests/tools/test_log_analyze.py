"""Tests for Log analyze tool."""

import json
import os
import pytest
import tempfile

from tools.log_analyze import log_analyze, check_log_analyze_requirements, LOG_ANALYZE_SCHEMA


class TestLogAnalyze:
    @pytest.fixture
    def temp_log(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("2024-01-01 10:00:00 INFO Starting\n")
            f.write("2024-01-01 10:01:00 DEBUG Debug message\n")
            f.write("2024-01-01 10:02:00 WARNING Warning test\n")
            f.write("2024-01-01 10:03:00 ERROR Error occurred\n")
            f.write("2024-01-01 10:04:00 INFO Running fine\n")
            f.write("2024-01-01 10:05:00 ERROR Another error\n")
            f.write("2024-01-01 10:06:00 CRITICAL Critical issue\n")
        yield f.name
        os.remove(f.name)

    def test_check_requirements(self):
        assert check_log_analyze_requirements() is True

    def test_read_log(self, temp_log):
        result = json.loads(log_analyze(temp_log))
        assert result["success"] is True
        assert result["total_lines"] == 7
        assert result["returned_count"] <= 100

    def test_filter_by_level_info(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="INFO"))
        assert result["success"] is True
        assert result["filtered_count"] == 2

    def test_filter_by_level_error(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="ERROR"))
        assert result["success"] is True
        assert result["filtered_count"] == 2

    def test_filter_by_level_warning(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="WARN"))
        assert result["success"] is True
        assert result["filtered_count"] == 1

    def test_filter_by_level_debug(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="DEBUG"))
        assert result["success"] is True
        assert result["filtered_count"] == 1

    def test_filter_by_level_critical(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="CRITICAL"))
        assert result["success"] is True
        assert result["filtered_count"] == 1

    def test_filter_by_level_case_insensitive(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="error"))
        assert result["success"] is True
        assert result["filtered_count"] == 2

    def test_search_pattern_simple(self, temp_log):
        result = json.loads(log_analyze(temp_log, search_pattern="Starting"))
        assert result["success"] is True
        assert result["filtered_count"] == 1

    def test_search_pattern_regex(self, temp_log):
        result = json.loads(log_analyze(temp_log, search_pattern=r"error\d"))
        assert result["success"] is True

    def test_search_pattern_case_insensitive(self, temp_log):
        result = json.loads(log_analyze(temp_log, search_pattern="ERROR"))
        assert result["success"] is True
        assert result["filtered_count"] == 2

    def test_invalid_regex(self, temp_log):
        result = json.loads(log_analyze(temp_log, search_pattern="[invalid"))
        assert result["success"] is False
        assert "Invalid regex" in result["error"]

    def test_statistics(self, temp_log):
        result = json.loads(log_analyze(temp_log, statistics=True))
        assert result["success"] is True
        assert "statistics" in result
        stats = result["statistics"]
        assert stats["total"] == 7
        assert "INFO" in stats["by_level"]
        assert stats["by_level"]["INFO"] == 2

    def test_limit(self, temp_log):
        result = json.loads(log_analyze(temp_log, limit=2))
        assert result["success"] is True
        assert result["returned_count"] == 2

    def test_file_not_found(self):
        result = json.loads(log_analyze("/nonexistent.log"))
        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_not_a_file(self, temp_log):
        result = json.loads(log_analyze(os.path.dirname(temp_log)))
        assert result["success"] is False
        assert "not a file" in result["error"].lower()

    def test_file_too_large(self, temp_log):
        with patch("os.path.getsize") as mock_size:
            mock_size.return_value = 100 * 1024 * 1024  # 100MB
            result = json.loads(log_analyze(temp_log))
            assert result["success"] is False
            assert "too large" in result["error"].lower()

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            pass
        try:
            result = json.loads(log_analyze(f.name))
            assert result["success"] is True
            assert result["total_lines"] == 0
        finally:
            os.remove(f.name)

    def test_file_with_no_matching_level(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="FATAL"))
        assert result["success"] is True
        assert result["filtered_count"] == 0

    def test_level_all_returns_all(self, temp_log):
        result = json.loads(log_analyze(temp_log, level="ALL"))
        assert result["success"] is True
        assert result["filtered_count"] == 7


class TestLogAnalyzeSchema:
    def test_schema_has_required_fields(self):
        assert LOG_ANALYZE_SCHEMA["name"] == "log_analyze"
        assert "parameters" in LOG_ANALYZE_SCHEMA
        props = LOG_ANALYZE_SCHEMA["parameters"]["properties"]
        assert "file_path" in props
        assert "level" in props
        assert "task_id" in props

    def test_schema_level_enum(self):
        props = LOG_ANALYZE_SCHEMA["parameters"]["properties"]
        assert props["level"]["enum"] == ["DEBUG", "INFO", "WARN", "ERROR", "ALL"]


from unittest.mock import patch


class TestLogAnalyzeSecurity:
    def test_path_traversal_blocked(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            f.write("test log\n")
            temp_path = f.name
        try:
            result = json.loads(log_analyze(temp_path + "/../test.log"))
            assert result["success"] is False
        finally:
            os.remove(temp_path)