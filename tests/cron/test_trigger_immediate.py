"""Tests for run_job_immediate() — immediate job dispatch on action=run.

These verify the fix for #41037: the cronjob tool's action='run' now
dispatches the job immediately to the parallel pool instead of only
writing metadata and waiting for the next scheduled tick.
"""

import json
import threading
import time
from unittest.mock import patch, MagicMock

import pytest


class TestActionRunDispatchesImmediately:
    """run_job_immediate() submits a job to the parallel pool immediately."""

    def test_action_run_dispatches_immediately(self, tmp_path, monkeypatch):
        """action='run' dispatches the job via run_job_immediate, not just metadata."""
        import cron.scheduler as sched
        from tools.cronjob_tools import cronjob
        from cron.jobs import create_job

        # Reset pool state.
        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Create a job.
        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="immediate-test"
        )
        job_id = job["id"]

        # Track whether run_job was called (indicating dispatch, not just metadata).
        run_job_calls = []

        original_run_job = sched.run_job

        def mock_run_job(j):
            run_job_calls.append(j["id"])
            # Return a fast result without actually running the agent.
            return True, "output", "response", None

        monkeypatch.setattr(sched, "run_job", mock_run_job)
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        # Call the tool with action='run'.
        result = cronjob(action="run", job_id=job_id)
        result_dict = json.loads(result)

        # Assert the tool returned success.
        assert result_dict["success"]

        # Assert dispatched=True (immediate dispatch occurred).
        assert result_dict.get("dispatched") is True

        # Give the background thread a moment to run.
        time.sleep(0.2)

        # Assert run_job was invoked (dispatch happened).
        assert job_id in run_job_calls

        sched._shutdown_parallel_pool()

    def test_action_run_skips_already_running(self, monkeypatch):
        """action='run' returns dispatched=False if the job is already running."""
        import cron.scheduler as sched
        from tools.cronjob_tools import cronjob
        from cron.jobs import create_job

        # Reset pool state.
        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Create a job.
        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="already-running-test"
        )
        job_id = job["id"]

        # Simulate the job already running.
        sched._running_job_ids.add(job_id)

        # Call the tool with action='run'.
        result = cronjob(action="run", job_id=job_id)
        result_dict = json.loads(result)

        # Assert the tool returned success (metadata was written).
        assert result_dict["success"]

        # Assert dispatched=False (job was already running).
        assert result_dict.get("dispatched") is False

        # Assert a note is present.
        assert "note" in result_dict
        assert "already running" in result_dict["note"].lower()

        sched._running_job_ids.discard(job_id)
        sched._shutdown_parallel_pool()

    def test_action_run_returns_not_found_error(self, monkeypatch):
        """action='run' with invalid job_id returns error (trigger_job fails)."""
        import cron.scheduler as sched
        from tools.cronjob_tools import cronjob

        # Reset pool state.
        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Call the tool with a non-existent job ID.
        result = cronjob(action="run", job_id="nonexistent-job-id")
        result_dict = json.loads(result)

        # Assert the tool returned failure (trigger_job failed to find the job).
        # When trigger_job returns None, the tool returns success=False.
        assert not result_dict["success"]

        sched._shutdown_parallel_pool()


class TestRunJobImmediate:
    """run_job_immediate() function directly."""

    def test_run_job_immediate_returns_true_on_success(self, monkeypatch):
        """run_job_immediate returns (True, None) on successful dispatch."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        # Reset pool state.
        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Create a job.
        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="run-immediate-test"
        )
        job_id = job["id"]

        run_job_calls = []

        def mock_run_job(j):
            run_job_calls.append(j["id"])
            return True, "output", "response", None

        monkeypatch.setattr(sched, "run_job", mock_run_job)
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        # Call run_job_immediate directly.
        dispatched, error = sched.run_job_immediate(job_id)

        # Assert success.
        assert dispatched is True
        assert error is None

        # Give the background thread a moment.
        time.sleep(0.2)

        # Assert run_job was called.
        assert job_id in run_job_calls

        sched._shutdown_parallel_pool()

    def test_run_job_immediate_returns_false_on_not_found(self):
        """run_job_immediate returns (False, error_msg) for nonexistent job."""
        import cron.scheduler as sched

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Call with a non-existent job.
        dispatched, error = sched.run_job_immediate("nonexistent-id")

        # Assert failure.
        assert dispatched is False
        assert error is not None
        assert "not found" in error.lower()

        sched._shutdown_parallel_pool()

    def test_run_job_immediate_returns_false_if_already_running(self, monkeypatch):
        """run_job_immediate returns (False, error_msg) if job is already running."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        # Reset pool state.
        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Create a job.
        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="already-running-immediate"
        )
        job_id = job["id"]

        # Simulate the job already running.
        sched._running_job_ids.add(job_id)

        # Call run_job_immediate.
        dispatched, error = sched.run_job_immediate(job_id)

        # Assert failure.
        assert dispatched is False
        assert error is not None
        assert "already running" in error.lower()

        sched._running_job_ids.discard(job_id)
        sched._shutdown_parallel_pool()

    def test_run_job_immediate_cleans_up_on_job_failure(self, monkeypatch):
        """run_job_immediate removes job from _running_job_ids even if run_job fails."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        # Reset pool state.
        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        # Create a job.
        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="cleanup-test"
        )
        job_id = job["id"]

        # Mock run_job to raise an exception.
        def mock_run_job(j):
            raise RuntimeError("Simulated run_job failure")

        monkeypatch.setattr(sched, "run_job", mock_run_job)
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        # Call run_job_immediate.
        dispatched, error = sched.run_job_immediate(job_id)

        # Assert dispatch succeeded (submitted to pool).
        assert dispatched is True
        assert error is None

        # Give the background thread time to run and clean up.
        time.sleep(0.3)

        # Assert the job was removed from _running_job_ids (cleanup happened).
        assert job_id not in sched._running_job_ids

        sched._shutdown_parallel_pool()
