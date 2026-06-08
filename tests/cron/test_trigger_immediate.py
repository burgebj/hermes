"""Tests for run_job_immediate() — immediate job dispatch on action=run.

These verify the fix for #41037: the cronjob tool's action='run' now
dispatches the job immediately to the parallel pool instead of only
writing metadata and waiting for the next scheduled tick.
"""

import json
import tempfile
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
        from cron.jobs import resolve_job_ref
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
        original_next_run_at = resolve_job_ref(job_id)["next_run_at"]

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
        assert resolve_job_ref(job_id)["next_run_at"] == original_next_run_at

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

    def test_run_job_immediate_returns_false_if_claimed_in_other_process(self, tmp_path):
        """Immediate runs must respect the cross-process per-job run lock."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        lock_dir = tmp_path / "cron"
        lock_dir.mkdir()
        tick_lock = lock_dir / ".tick.lock"

        with patch("cron.scheduler._get_lock_paths", return_value=(lock_dir, tick_lock)):
            job = create_job(
                prompt="test prompt",
                schedule="every 5m",
                name="cross-process-running-immediate"
            )
            job_id = job["id"]

            foreign_lock = open(sched._get_job_run_lock_path(job_id), "a+", encoding="utf-8")
            assert sched._try_lock_file(foreign_lock) is True
            try:
                dispatched, error = sched.run_job_immediate(job_id)
            finally:
                sched._unlock_file(foreign_lock)
                foreign_lock.close()

        assert dispatched is False
        assert error is not None
        assert "already running" in error.lower()
        assert job_id not in sched._running_job_ids

        sched._shutdown_parallel_pool()

    def test_run_job_immediate_does_not_advance_when_already_running(self, monkeypatch):
        """Already-running jobs must not consume the next scheduled run."""
        import cron.scheduler as sched
        import cron.jobs as jobsmod
        from cron.jobs import create_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="already-running-no-advance"
        )
        job_id = job["id"]

        advance_calls = []
        monkeypatch.setattr(jobsmod, "advance_next_run", lambda *_a, **_kw: advance_calls.append(job_id))

        sched._running_job_ids.add(job_id)
        dispatched, error = sched.run_job_immediate(job_id)

        assert dispatched is False
        assert error is not None
        assert advance_calls == []

        sched._running_job_ids.discard(job_id)
        sched._shutdown_parallel_pool()

    def test_run_job_immediate_uses_sequential_pool_for_workdir_jobs(self, monkeypatch):
        """Immediate runs must keep workdir/profile jobs on the serialized pool."""
        import cron.scheduler as sched
        from cron.jobs import create_job, update_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="sequential-pool-test"
        )
        job = update_job(job["id"], {"workdir": tempfile.mkdtemp(prefix="cron-workdir-")})
        job_id = job["id"]

        used = []

        class _DummyPool:
            def __init__(self, label):
                self.label = label

            def submit(self, fn):
                used.append(self.label)
                fn()
                return MagicMock()

        monkeypatch.setattr(sched, "_get_sequential_pool", lambda: _DummyPool("sequential"))
        monkeypatch.setattr(sched, "_get_parallel_pool", lambda *_a, **_kw: _DummyPool("parallel"))
        monkeypatch.setattr(sched, "run_job", lambda *_a, **_kw: (True, "output", "response", None))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        dispatched, error = sched.run_job_immediate(job_id)

        assert dispatched is True
        assert error is None
        assert used == ["sequential"]

        sched._shutdown_parallel_pool()

    def test_run_job_immediate_respects_parallel_pool_cap(self, monkeypatch):
        """Immediate parallel jobs should use the configured shared pool cap."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="parallel-pool-cap-test"
        )
        job_id = job["id"]

        seen = {}

        class _DummyPool:
            def submit(self, fn):
                fn()
                return MagicMock()

        monkeypatch.setattr(sched, "_resolve_max_parallel_workers", lambda: 3)
        def fake_get_parallel_pool(max_workers):
            seen["value"] = max_workers
            return _DummyPool()
        monkeypatch.setattr(sched, "_get_parallel_pool", fake_get_parallel_pool)
        monkeypatch.setattr(sched, "run_job", lambda *_a, **_kw: (True, "output", "response", None))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        dispatched, error = sched.run_job_immediate(job_id)

        assert dispatched is True
        assert error is None
        assert seen["value"] == 3

        sched._shutdown_parallel_pool()

    def test_run_job_immediate_passes_live_adapter_context(self, monkeypatch):
        """Immediate runs should reuse cached gateway adapters and loop when present."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="live-adapter-context-test"
        )
        job_id = job["id"]

        class _InlinePool:
            def submit(self, fn):
                fn()
                return MagicMock()

        captured = {}
        adapter_sentinel = {"matrix": object()}
        loop_sentinel = object()
        sched._live_delivery_adapters = adapter_sentinel
        sched._live_delivery_loop = loop_sentinel

        monkeypatch.setattr(sched, "_get_parallel_pool", lambda *_a, **_kw: _InlinePool())
        monkeypatch.setattr(sched, "run_job", lambda *_a, **_kw: (True, "output", "response", None))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)

        def fake_deliver(_job, _content, adapters=None, loop=None):
            captured["adapters"] = adapters
            captured["loop"] = loop
            return None

        monkeypatch.setattr(sched, "_deliver_result", fake_deliver)

        dispatched, error = sched.run_job_immediate(job_id)

        assert dispatched is True
        assert error is None
        assert captured["adapters"] is adapter_sentinel
        assert captured["loop"] is loop_sentinel

        sched._live_delivery_adapters = None
        sched._live_delivery_loop = None
        sched._shutdown_parallel_pool()

    def test_action_run_failed_manual_run_restores_schedule(self, monkeypatch):
        """A failed immediate manual run must not consume the next scheduled run."""
        import cron.scheduler as sched
        from cron.jobs import create_job, resolve_job_ref
        from tools.cronjob_tools import cronjob

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 1h",
            name="failed-manual-run"
        )
        job_id = job["id"]
        original_next_run_at = resolve_job_ref(job_id)["next_run_at"]

        class _InlinePool:
            def submit(self, fn):
                fn()
                return MagicMock()

        monkeypatch.setattr(sched, "_get_parallel_pool", lambda *_a, **_kw: _InlinePool())
        monkeypatch.setattr(sched, "_get_sequential_pool", lambda: _InlinePool())
        monkeypatch.setattr(sched, "run_job", lambda *_a, **_kw: (False, "output", "", "boom"))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        result = json.loads(cronjob(action="run", job_id=job_id))

        assert result["success"] is True
        assert result["dispatched"] is True
        assert resolve_job_ref(job_id)["next_run_at"] == original_next_run_at

        sched._shutdown_parallel_pool()

    def test_action_run_does_not_force_due_timestamp_before_dispatch(self, monkeypatch):
        """Manual runs should not stamp next_run_at=now before the immediate worker starts."""
        import cron.scheduler as sched
        from cron.jobs import create_job, resolve_job_ref
        from tools.cronjob_tools import cronjob

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 1h",
            name="manual-run-preserve-next-run"
        )
        job_id = job["id"]
        original_next_run_at = resolve_job_ref(job_id)["next_run_at"]
        seen_next_run_at = {}

        def fake_run_job_immediate(job_ref, schedule_snapshot=None):
            seen_next_run_at["value"] = resolve_job_ref(job_ref)["next_run_at"]
            return False, "not dispatched for inspection"

        monkeypatch.setattr(sched, "run_job_immediate", fake_run_job_immediate)

        result = json.loads(cronjob(action="run", job_id=job_id))

        assert result["success"] is True
        assert result["dispatched"] is False
        assert seen_next_run_at["value"] == original_next_run_at

        sched._shutdown_parallel_pool()

    def test_action_run_queues_for_next_tick_when_live_delivery_context_is_required(self, monkeypatch):
        """Jobs that require a live gateway adapter should queue instead of failing delivery."""
        import cron.scheduler as sched
        from cron.jobs import create_job, resolve_job_ref
        from tools.cronjob_tools import cronjob

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 1h",
            name="queued-live-delivery-manual-run",
            deliver="matrix",
        )
        job_id = job["id"]
        original_next_run_at = resolve_job_ref(job_id)["next_run_at"]

        monkeypatch.setattr(sched, "_job_requires_live_delivery_context", lambda _job: True)
        monkeypatch.setattr(sched, "_resolve_live_delivery_context", lambda: (None, None))
        monkeypatch.setattr(
            sched,
            "run_job_immediate",
            lambda *_a, **_kw: (_ for _ in ()).throw(AssertionError("run_job_immediate should not be called")),
        )

        result = json.loads(cronjob(action="run", job_id=job_id))
        queued_job = resolve_job_ref(job_id)

        assert result["success"] is True
        assert result["dispatched"] is False
        assert "queued for the next gateway tick" in result["note"].lower()
        assert queued_job["next_run_at"] != original_next_run_at
        assert queued_job["manual_run_schedule_snapshot"]["next_run_at"] == original_next_run_at

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

    def test_run_job_immediate_sweeps_mcp_orphans_after_completion(self, monkeypatch):
        """Immediate runs should perform the same orphan sweep as tick()-driven runs."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="mcp-orphan-sweep-immediate"
        )
        job_id = job["id"]
        sweeps = []

        class _InlinePool:
            def submit(self, fn):
                fn()
                return MagicMock()

        monkeypatch.setattr(sched, "_get_parallel_pool", lambda *_a, **_kw: _InlinePool())
        monkeypatch.setattr(sched, "run_job", lambda *_a, **_kw: (True, "output", "response", None))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_sweep_mcp_orphans", lambda: sweeps.append(job_id))

        dispatched, error = sched.run_job_immediate(job_id)

        assert dispatched is True
        assert error is None
        assert sweeps == [job_id]

        sched._shutdown_parallel_pool()

    def test_run_job_immediate_releases_claim_if_pool_creation_fails(self, monkeypatch):
        """Pool-construction failures must not strand the per-job running lock."""
        import cron.scheduler as sched
        from cron.jobs import create_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 5m",
            name="pool-create-failure-cleanup"
        )
        job_id = job["id"]

        monkeypatch.setattr(sched, "_get_parallel_pool", lambda *_a, **_kw: (_ for _ in ()).throw(RuntimeError("pool boom")))

        with pytest.raises(RuntimeError, match="pool boom"):
            sched.run_job_immediate(job_id)

        assert job_id not in sched._running_job_ids

        sched._shutdown_parallel_pool()

    def test_tick_restores_schedule_after_queued_manual_run(self, tmp_path, monkeypatch):
        """Queued manual runs should restore the original schedule after the gateway tick."""
        import cron.scheduler as sched
        from cron.jobs import create_job, resolve_job_ref, update_job

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        job = create_job(
            prompt="test prompt",
            schedule="every 1h",
            name="queued-manual-run-restore"
        )
        job_id = job["id"]
        schedule_snapshot = {
            "enabled": job.get("enabled", True),
            "state": job.get("state"),
            "paused_at": job.get("paused_at"),
            "paused_reason": job.get("paused_reason"),
            "next_run_at": job.get("next_run_at"),
        }
        update_job(
            job_id,
            {
                "next_run_at": "2000-01-01T00:00:00+00:00",
                "manual_run_schedule_snapshot": schedule_snapshot,
            },
        )
        due_job = resolve_job_ref(job_id)
        lock_dir = tmp_path / "cron"
        lock_dir.mkdir()
        tick_lock = lock_dir / ".tick.lock"

        monkeypatch.setattr(sched, "get_due_jobs", lambda: [due_job])
        monkeypatch.setattr(sched, "run_job", lambda *_a, **_kw: (True, "output", "response", None))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        with patch("cron.scheduler._get_lock_paths", return_value=(lock_dir, tick_lock)):
            dispatched_count = sched.tick(sync=True)

        restored = resolve_job_ref(job_id)
        assert dispatched_count == 1
        assert restored["next_run_at"] == schedule_snapshot["next_run_at"]
        assert restored.get("manual_run_schedule_snapshot") is None

        sched._shutdown_parallel_pool()

    def test_tick_skips_job_claimed_in_other_process(self, tmp_path, monkeypatch):
        """tick() must share the same cross-process running claim as manual runs."""
        import cron.scheduler as sched

        sched._parallel_pool = None
        sched._parallel_pool_max_workers = None
        sched._running_job_ids.clear()

        lock_dir = tmp_path / "cron"
        lock_dir.mkdir()
        tick_lock = lock_dir / ".tick.lock"
        job = {
            "id": "cross-process-due-job",
            "name": "Cross-process due job",
            "schedule": {"kind": "interval", "minutes": 5},
        }
        run_job_calls = []

        monkeypatch.setattr(sched, "get_due_jobs", lambda: [job])
        monkeypatch.setattr(sched, "advance_next_run", lambda *_a, **_kw: True)
        monkeypatch.setattr(sched, "run_job", lambda j: run_job_calls.append(j["id"]) or (True, "output", "response", None))
        monkeypatch.setattr(sched, "save_job_output", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "mark_job_run", lambda *_a, **_kw: None)
        monkeypatch.setattr(sched, "_deliver_result", lambda *_a, **_kw: None)

        with patch("cron.scheduler._get_lock_paths", return_value=(lock_dir, tick_lock)):
            foreign_lock = open(sched._get_job_run_lock_path(job["id"]), "a+", encoding="utf-8")
            assert sched._try_lock_file(foreign_lock) is True
            try:
                dispatched_count = sched.tick(sync=True)
            finally:
                sched._unlock_file(foreign_lock)
                foreign_lock.close()

        assert dispatched_count == 0
        assert run_job_calls == []
        assert job["id"] not in sched._running_job_ids

        sched._shutdown_parallel_pool()
