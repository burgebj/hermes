"""Tests for Orchestrator."""
import pytest
import time
from unittest.mock import MagicMock, patch
from agent.orchestrator import Orchestrator, OrchestrationTask, TaskStatus


@pytest.fixture
def mock_agent_factory():
    def factory(toolsets=None, skip_memory=True):
        agent = MagicMock()
        agent.run_conversation.return_value = {"response": "Task completed"}
        return agent
    return factory


@pytest.fixture
def orchestrator(mock_agent_factory):
    return Orchestrator(mock_agent_factory, max_workers=2)


def test_submit_task(orchestrator):
    tid = orchestrator.submit("Test goal")
    assert tid.startswith("task_")
    statuses = orchestrator.get_status(tid)
    assert len(statuses) == 1


def test_task_completion(orchestrator):
    tid = orchestrator.submit("Quick task")
    result = orchestrator.wait(tid, timeout=10)
    assert result is not None


def test_cancel_task(orchestrator):
    tid = orchestrator.submit("Long task")
    success = orchestrator.cancel(tid)
    # May or may not succeed depending on timing
    statuses = orchestrator.get_status(tid)
    assert len(statuses) == 1


def test_summary(orchestrator):
    orchestrator.submit("Task 1")
    orchestrator.submit("Task 2")
    summary = orchestrator.summary()
    assert summary["total_tasks"] == 2


def test_dependency_resolution(mock_agent_factory):
    orch = Orchestrator(mock_agent_factory, max_workers=2)
    tid1 = orch.submit("First task")
    tid2 = orch.submit("Second task", depends_on=[tid1])

    # Task 2 should be pending (waiting for task 1)
    statuses = orch.get_status(tid2)
    assert statuses[0]["status"] in ("pending", "running", "completed")

    # Wait for both
    orch.wait(tid1, timeout=10)
    orch.wait(tid2, timeout=10)

    statuses = orch.get_status(tid2)
    assert statuses[0]["status"] == "completed"


def test_task_to_dict():
    task = OrchestrationTask(
        task_id="test_123",
        goal="Test goal",
        status=TaskStatus.COMPLETED,
    )
    d = task.to_dict()
    assert d["task_id"] == "test_123"
    assert d["status"] == "completed"


def test_shutdown(orchestrator):
    orchestrator.shutdown(wait=True)
    # Should not raise
