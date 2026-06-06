"""Regression tests for interrupted memory-provider shutdown.

When SIGTERM/Ctrl+C fires, the Python signal handler calls agent.interrupt(),
sets _interrupt_requested=True, then unwinds the main thread. The cleanup path
(_run_cleanup -> shutdown_memory_provider) must not call memory
``on_session_end()`` because Mnemosyne may enter local llama.cpp inference during
that hook. Native ggml worker threads cannot be interrupted from Python, so
starting consolidation during signal cleanup can race native tensor-buffer
lifetime. Resource cleanup still needs to call ``shutdown_all()``.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from run_agent import AIAgent


def _agent_with_memory_manager(*, interrupted: bool) -> tuple[AIAgent, MagicMock]:
    agent = object.__new__(AIAgent)
    memory_manager = MagicMock()
    agent._memory_manager = memory_manager
    agent._interrupt_requested = interrupted
    agent.context_compressor = None
    agent.session_id = "test-session"
    return agent, memory_manager


def test_shutdown_memory_provider_skips_on_session_end_when_interrupted():
    agent, memory_manager = _agent_with_memory_manager(interrupted=True)

    agent.shutdown_memory_provider([{"role": "user", "content": "hello"}])

    memory_manager.on_session_end.assert_not_called()
    memory_manager.shutdown_all.assert_called_once_with()


def test_shutdown_memory_provider_runs_on_session_end_when_not_interrupted():
    messages = [{"role": "user", "content": "hello"}]
    agent, memory_manager = _agent_with_memory_manager(interrupted=False)

    agent.shutdown_memory_provider(messages)

    memory_manager.on_session_end.assert_called_once_with(messages)
    memory_manager.shutdown_all.assert_called_once_with()
