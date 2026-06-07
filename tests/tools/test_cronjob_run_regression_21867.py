"""
Regression tests for cronjob action='run' immediate execution (issue #21867).

The cronjob tool's action='run' previously only set next_run_at to the current
time, but did not actually execute the job. Users expected immediate execution.
"""

import json
from unittest.mock import patch, MagicMock

import pytest

from tools.cronjob_tools import cronjob


class TestCronjobRunImmediateExecution:
    """Tests that action='run' executes the job immediately."""

    @patch("tools.cronjob_tools.trigger_job")
    @patch("tools.cronjob_tools.get_job")
    @patch("tools.cronjob_tools._run_cron_job")
    @patch("tools.cronjob_tools._save_cron_output")
    @patch("tools.cronjob_tools.mark_job_run")
    def test_run_executes_job_immediately(
        self,
        mock_mark_run,
        mock_save_output,
        mock_run_job,
        mock_get_job,
        mock_trigger,
    ):
        """action='run' should call run_job() immediately, not just trigger."""
        # Setup mocks
        mock_trigger.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "state": "scheduled",
        }
        mock_get_job.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "prompt": "test prompt",
        }
        mock_run_job.return_value = (True, "output doc", "final response", None)

        result = cronjob(action="run", job_id="test-job-123")
        data = json.loads(result)

        # Should trigger the job first
        mock_trigger.assert_called_once_with("test-job-123")
        # Should get the job details
        mock_get_job.assert_called_once_with("test-job-123")
        # Should run the job immediately
        mock_run_job.assert_called_once()
        # Should save output
        mock_save_output.assert_called_once_with("test-job-123", "output doc")
        # Should mark the run
        mock_mark_run.assert_called_once_with("test-job-123", True, None)
        # Result should include output
        assert data["success"] is True
        assert data["output"] == "final response"
        assert data["error"] is None

    @patch("tools.cronjob_tools.trigger_job")
    @patch("tools.cronjob_tools.get_job")
    @patch("tools.cronjob_tools._run_cron_job")
    @patch("tools.cronjob_tools._save_cron_output")
    @patch("tools.cronjob_tools.mark_job_run")
    def test_run_now_executes_job_immediately(
        self,
        mock_mark_run,
        mock_save_output,
        mock_run_job,
        mock_get_job,
        mock_trigger,
    ):
        """action='run_now' should also execute immediately."""
        mock_trigger.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "state": "scheduled",
        }
        mock_get_job.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "prompt": "test prompt",
        }
        mock_run_job.return_value = (True, "output", "response", None)

        result = cronjob(action="run_now", job_id="test-job-123")
        data = json.loads(result)

        mock_run_job.assert_called_once()
        assert data["success"] is True
        assert data["output"] == "response"

    @patch("tools.cronjob_tools.trigger_job")
    @patch("tools.cronjob_tools.get_job")
    @patch("tools.cronjob_tools._run_cron_job")
    def test_trigger_does_not_execute(
        self,
        mock_run_job,
        mock_get_job,
        mock_trigger,
    ):
        """action='trigger' should only schedule, not execute (backward compat)."""
        mock_trigger.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "state": "scheduled",
        }

        result = cronjob(action="trigger", job_id="test-job-123")
        data = json.loads(result)

        mock_run_job.assert_not_called()
        mock_get_job.assert_not_called()
        assert data["success"] is True
        assert "output" not in data

    @patch("tools.cronjob_tools.trigger_job")
    @patch("tools.cronjob_tools.get_job")
    @patch("tools.cronjob_tools._run_cron_job")
    @patch("tools.cronjob_tools._save_cron_output")
    @patch("tools.cronjob_tools.mark_job_run")
    def test_run_with_job_failure(
        self,
        mock_mark_run,
        mock_save_output,
        mock_run_job,
        mock_get_job,
        mock_trigger,
    ):
        """action='run' should report failure when job execution fails."""
        mock_trigger.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "state": "scheduled",
        }
        mock_get_job.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "prompt": "test prompt",
        }
        mock_run_job.return_value = (False, "", "", "API error")

        result = cronjob(action="run", job_id="test-job-123")
        data = json.loads(result)

        assert data["success"] is False
        assert data["error"] == "API error"
        mock_mark_run.assert_called_once_with("test-job-123", False, "API error")

    @patch("tools.cronjob_tools.trigger_job")
    @patch("tools.cronjob_tools.get_job")
    @patch("tools.cronjob_tools._run_cron_job")
    def test_run_with_exception(
        self,
        mock_run_job,
        mock_get_job,
        mock_trigger,
    ):
        """action='run' should gracefully handle exceptions during execution."""
        mock_trigger.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "state": "scheduled",
        }
        mock_get_job.return_value = {
            "id": "test-job-123",
            "name": "Test Job",
            "prompt": "test prompt",
        }
        mock_run_job.side_effect = RuntimeError("Scheduler crashed")

        result = cronjob(action="run", job_id="test-job-123")
        data = json.loads(result)

        assert data["success"] is False
        assert "Scheduler crashed" in data["error"]

    @patch("tools.cronjob_tools.trigger_job")
    def test_run_job_not_found(self, mock_trigger):
        """action='run' should error if trigger_job returns None (job not found)."""
        mock_trigger.return_value = None

        result = cronjob(action="run", job_id="missing-job")
        data = json.loads(result)

        assert data["success"] is False
        assert "Failed to trigger" in data["error"]
