"""Tests for child agent isolation module."""

import json
import time
import pytest
from unittest.mock import MagicMock


class TestChildIsolation:
    def test_wrap_success(self):
        from tools.child_isolation import wrap_child_execution
        result = wrap_child_execution(0, lambda: {"status": "completed", "summary": "done"}, 30.0)
        assert result.success is True
        assert result.status == "completed"
        assert result.summary == "done"

    def test_wrap_success_no_dict(self):
        from tools.child_isolation import wrap_child_execution
        result = wrap_child_execution(0, lambda: "plain string result", 30.0)
        assert result.success is True
        assert result.status == "completed"

    def test_wrap_timeout(self):
        from tools.child_isolation import wrap_child_execution
        result = wrap_child_execution(0, lambda: time.sleep(10), 0.1)
        assert result.success is False
        assert result.status == "timeout"
        assert result.error_type == "timeout"
        assert "timed out" in result.error.lower()

    def test_wrap_crash_with_runtime_error(self):
        from tools.child_isolation import wrap_child_execution
        def crashing():
            raise RuntimeError("child exploded")
        result = wrap_child_execution(0, crashing, 30.0)
        assert result.success is False
        assert result.status == "error"
        assert result.error_type == "crash"

    def test_wrap_crash_with_value_error(self):
        from tools.child_isolation import wrap_child_execution
        def crashing():
            raise ValueError("invalid input")
        result = wrap_child_execution(0, crashing, 30.0)
        assert result.success is False
        assert result.error_type == "crash"

    def test_child_result_to_dict(self):
        from tools.child_isolation import ChildResult
        r = ChildResult(success=False, task_index=1, status="timeout",
                       error="timed out", error_type="timeout")
        d = r.to_dict()
        assert d["success"] is False
        assert d["status"] == "timeout"
        assert d["error_type"] == "timeout"

    def test_child_result_to_json(self):
        from tools.child_isolation import ChildResult
        r = ChildResult(success=True, task_index=0, summary="done")
        j = r.to_json()
        data = json.loads(j)
        assert data["success"] is True
        assert data["summary"] == "done"

    def test_format_error_timeout(self):
        from tools.child_isolation import ChildResult, format_child_error
        r = ChildResult(success=False, status="timeout", error_type="timeout",
                       duration_seconds=120.0, error="timed out")
        msg = format_child_error(r)
        assert "timed out" in msg.lower() or "120" in msg

    def test_format_error_crash(self):
        from tools.child_isolation import ChildResult, format_child_error
        r = ChildResult(success=False, status="error", error_type="crash",
                       error="Something broke")
        msg = format_child_error(r)
        assert "crashed" in msg.lower()
        assert "parent" in msg.lower()

    def test_format_error_no_error(self):
        from tools.child_isolation import ChildResult, format_child_error
        r = ChildResult(success=True, status="completed")
        msg = format_child_error(r)
        assert msg == ""