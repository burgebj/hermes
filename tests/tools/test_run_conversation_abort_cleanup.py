"""Regression tests for the run_conversation() abort-cleanup wrapper.

The public ``run_conversation`` is a thin wrapper around
``_run_conversation_impl``. Its only job is to guarantee per-task resource
cleanup (the agent-browser daemon + its Chromium/Xvfb tree, sandbox VMs) runs
when the turn aborts with an exception or is interrupted — the impl already
cleans up on every normal return path, so the wrapper's ``finally`` must fire
ONLY on the error/interrupt path. Without this, an aborted browser turn orphans
its process tree and the gateway leaks memory over time.
"""

from unittest.mock import MagicMock, patch

import pytest

import agent.conversation_loop as cl


def _make_agent():
    agent = MagicMock()
    agent._cleanup_task_resources = MagicMock()
    return agent


def test_normal_return_does_not_trigger_wrapper_cleanup():
    """On success the impl owns cleanup; the wrapper must NOT double-reap."""
    agent = _make_agent()
    sentinel = {"completed": True}

    with patch.object(cl, "_run_conversation_impl", return_value=sentinel) as impl:
        result = cl.run_conversation(agent, "hi", task_id="t-1")

    assert result is sentinel
    impl.assert_called_once()
    agent._cleanup_task_resources.assert_not_called()


def test_exception_triggers_cleanup_and_repropagates():
    """An impl exception must reap the task, then re-raise unchanged."""
    agent = _make_agent()
    boom = RuntimeError("kaboom")

    with patch.object(cl, "_run_conversation_impl", side_effect=boom):
        with pytest.raises(RuntimeError, match="kaboom"):
            cl.run_conversation(agent, "hi", task_id="t-2")

    agent._cleanup_task_resources.assert_called_once_with("t-2")


def test_cancelled_interrupt_triggers_cleanup():
    """Interrupt (KeyboardInterrupt / CancelledError-like) also reaps."""
    agent = _make_agent()

    with patch.object(cl, "_run_conversation_impl", side_effect=KeyboardInterrupt()):
        with pytest.raises(KeyboardInterrupt):
            cl.run_conversation(agent, "hi", task_id="t-3")

    agent._cleanup_task_resources.assert_called_once_with("t-3")


def test_cleanup_uses_generated_task_id_when_none_given():
    """When no task_id is passed, the wrapper reaps the SAME id it generated
    and handed to the impl (so the reap targets exactly the task that ran)."""
    agent = _make_agent()
    captured = {}

    def _impl(_agent, _msg, **kwargs):
        captured["task_id"] = kwargs.get("task_id")
        raise RuntimeError("fail")

    with patch.object(cl, "_run_conversation_impl", side_effect=_impl):
        with pytest.raises(RuntimeError):
            cl.run_conversation(agent, "hi")

    assert captured["task_id"]  # a uuid was generated
    agent._cleanup_task_resources.assert_called_once_with(captured["task_id"])


def test_cleanup_failure_is_swallowed_not_masking_original_error():
    """If the cleanup itself raises, the ORIGINAL turn error must still win
    (a broken reaper can't escalate into a different exception)."""
    agent = _make_agent()
    agent._cleanup_task_resources.side_effect = OSError("reaper broke")

    with patch.object(cl, "_run_conversation_impl", side_effect=ValueError("original")):
        with pytest.raises(ValueError, match="original"):
            cl.run_conversation(agent, "hi", task_id="t-4")

    agent._cleanup_task_resources.assert_called_once_with("t-4")
