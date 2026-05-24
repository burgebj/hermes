import logging
from unittest.mock import MagicMock, call, patch

from run_agent import AIAgent


def _make_uninitialized_agent(session_id: str, current_task_id: str | None = None):
    agent = AIAgent.__new__(AIAgent)
    agent.session_id = session_id
    if current_task_id is not None:
        agent._current_task_id = current_task_id
    agent._active_children_lock = MagicMock()
    agent._active_children_lock.__enter__.return_value = None
    agent._active_children_lock.__exit__.return_value = None
    agent._active_children = []
    agent.client = None
    return agent


def test_close_skips_resolved_default_by_default(caplog):
    caplog.set_level(logging.DEBUG, logger="run_agent")
    agent = _make_uninitialized_agent("session-123", "turn-456")

    killed = []
    cleaned_vm = []
    cleaned_browser = []
    registry = MagicMock()
    registry.kill_all.side_effect = lambda task_id=None: killed.append(task_id) or 0

    with (
        patch("tools.process_registry.process_registry", registry),
        patch("run_agent.cleanup_vm", side_effect=lambda task_id: cleaned_vm.append(task_id)),
        patch("run_agent.cleanup_browser", side_effect=lambda task_id: cleaned_browser.append(task_id)),
        patch("tools.terminal_tool._resolve_container_task_id", return_value="default"),
    ):
        agent.close()

    assert killed == ["turn-456", "session-123"]
    assert cleaned_vm == ["turn-456", "session-123"]
    assert cleaned_browser == ["turn-456", "session-123"]
    assert "Suppressing shared default cleanup" in caplog.text


def test_close_global_shutdown_can_cleanup_default():
    agent = _make_uninitialized_agent("session-123", "turn-456")

    killed = []
    cleaned_vm = []
    cleaned_browser = []
    registry = MagicMock()
    registry.kill_all.side_effect = lambda task_id=None: killed.append(task_id) or 0

    with (
        patch("tools.process_registry.process_registry", registry),
        patch("run_agent.cleanup_vm", side_effect=lambda task_id: cleaned_vm.append(task_id)),
        patch("run_agent.cleanup_browser", side_effect=lambda task_id: cleaned_browser.append(task_id)),
        patch("tools.terminal_tool._resolve_container_task_id", return_value="default"),
    ):
        agent.close(cleanup_shared_default=True)

    assert killed == ["turn-456", "session-123", "default"]
    assert cleaned_vm == ["turn-456", "session-123", "default"]
    assert cleaned_browser == ["turn-456", "session-123", "default"]


def test_closing_one_default_session_preserves_other_session_resources():
    agent_a = _make_uninitialized_agent("session-a", "turn-a")
    agent_b = _make_uninitialized_agent("session-b", "turn-b")
    registry = MagicMock()

    with (
        patch("tools.process_registry.process_registry", registry),
        patch("run_agent.cleanup_vm") as cleanup_vm,
        patch("run_agent.cleanup_browser") as cleanup_browser,
        patch("tools.terminal_tool._resolve_container_task_id", return_value="default"),
    ):
        agent_a.close()

    registry.kill_all.assert_has_calls(
        [call(task_id="turn-a"), call(task_id="session-a")]
    )
    assert call(task_id="default") not in registry.kill_all.call_args_list
    assert call(task_id="turn-b") not in registry.kill_all.call_args_list
    assert call(task_id="session-b") not in registry.kill_all.call_args_list
    assert call("default") not in cleanup_vm.call_args_list
    assert call("default") not in cleanup_browser.call_args_list

    with (
        patch("tools.process_registry.process_registry", registry),
        patch("run_agent.cleanup_vm") as cleanup_vm,
        patch("run_agent.cleanup_browser") as cleanup_browser,
        patch("tools.terminal_tool._resolve_container_task_id", return_value="default"),
    ):
        agent_b.close_for_gateway_shutdown()

    assert call(task_id="default") in registry.kill_all.call_args_list
    assert call("default") in cleanup_vm.call_args_list
    assert call("default") in cleanup_browser.call_args_list
