import threading
import time
from unittest.mock import MagicMock

import pytest

from run_agent import AIAgent


def _make_agent(*, last_activity_ts: float, last_activity_desc: str, current_tool: str | None):
    agent = AIAgent.__new__(AIAgent)
    agent._last_activity_ts = last_activity_ts
    agent._last_activity_desc = last_activity_desc
    agent._current_tool = current_tool
    agent._api_call_count = 6
    agent.max_iterations = 90
    agent.iteration_budget = MagicMock(used=4, max_total=90)
    agent._active_children = []
    agent._active_children_lock = threading.Lock()
    return agent


def test_get_activity_summary_uses_parent_state_without_children():
    now = time.time()
    agent = _make_agent(
        last_activity_ts=now - 12,
        last_activity_desc="executing tool: delegate_task",
        current_tool="delegate_task",
    )

    summary = agent.get_activity_summary()

    assert summary["last_activity_desc"] == "executing tool: delegate_task"
    assert summary["current_tool"] == "delegate_task"
    assert summary["seconds_since_activity"] == pytest.approx(12, abs=0.5)


def test_get_activity_summary_prefers_more_recent_child_activity():
    now = time.time()
    parent = _make_agent(
        last_activity_ts=now - 610,
        last_activity_desc="executing tool: delegate_task",
        current_tool="delegate_task",
    )

    child = MagicMock()
    child.get_activity_summary.return_value = {
        "last_activity_ts": now - 3,
        "last_activity_desc": "executing tool: read_file",
        "seconds_since_activity": 3.0,
        "current_tool": "read_file",
        "api_call_count": 2,
        "max_iterations": 50,
        "budget_used": 1,
        "budget_max": 50,
    }

    with parent._active_children_lock:
        parent._active_children.append(child)

    summary = parent.get_activity_summary()

    assert summary["seconds_since_activity"] == pytest.approx(3.0, abs=0.1)
    assert "read_file" in summary["last_activity_desc"]
    assert summary["current_tool"] == "delegate_task"
