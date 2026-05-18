"""Tests for cron job pre-execution condition scripts."""

from unittest.mock import MagicMock, patch

import pytest


class TestEvaluateCondition:
    """Tests for _evaluate_condition() in cron/scheduler.py."""

    def test_no_condition_returns_true(self):
        """When a job has no condition script, it should proceed."""
        from cron.scheduler import _evaluate_condition

        job = {"id": "test-job"}
        logger = MagicMock()

        result = _evaluate_condition(job, logger)

        assert result is True
        logger.info.assert_not_called()

    @patch("cron.scheduler._run_job_script", return_value=(True, "ok"))
    def test_condition_exit_zero_proceeds(self, mock_run):
        """When condition script exits 0, job should proceed."""
        from cron.scheduler import _evaluate_condition

        job = {"id": "test-job", "condition": "workday-check.sh"}
        logger = MagicMock()

        result = _evaluate_condition(job, logger)

        assert result is True
        mock_run.assert_called_once_with("workday-check.sh")

    @patch("cron.scheduler._run_job_script", return_value=(False, "weekend"))
    @patch("cron.scheduler.mark_job_run")
    def test_condition_exit_nonzero_skips(self, mock_mark, mock_run):
        """When condition script exits non-zero, job should be skipped."""
        from cron.scheduler import _evaluate_condition

        job = {"id": "test-job", "condition": "workday-check.sh"}
        logger = MagicMock()

        result = _evaluate_condition(job, logger)

        assert result is False
        mock_mark.assert_called_once_with("test-job", False, "condition_skipped")

    @patch("cron.scheduler._run_job_script", side_effect=FileNotFoundError("no script"))
    @patch("cron.scheduler.mark_job_run")
    def test_condition_exception_skips(self, mock_mark, mock_run):
        """When condition script raises an exception, job should be skipped (not crash)."""
        from cron.scheduler import _evaluate_condition

        job = {"id": "test-job", "condition": "/nonexistent/script.sh"}
        logger = MagicMock()

        result = _evaluate_condition(job, logger)

        assert result is False
        # mark_job_run should be called with an error status
        call_args = mock_mark.call_args[0]
        assert call_args[0] == "test-job"
        assert call_args[1] is False
        assert "condition_error" in call_args[2]

