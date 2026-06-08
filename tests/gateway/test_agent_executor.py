"""Tests for the dedicated gateway agent thread pool.

Agent turns run on ``GatewayRunner._agent_executor`` instead of asyncio's
default executor so that a turn parked on a HITL approval (which blocks its
worker thread for up to the approval timeout) cannot starve other sessions'
turns or contend with compression / MCP discovery on the shared default pool.
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

import gateway.run as gateway_run

DEFAULT = gateway_run._GATEWAY_AGENT_WORKERS_DEFAULT


def test_load_agent_executor_workers_prefers_env_then_config_then_default(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)
    monkeypatch.delenv("HERMES_GATEWAY_MAX_CONCURRENT_TURNS", raising=False)

    # Nothing configured -> default.
    assert gateway_run.GatewayRunner._load_agent_executor_workers() == DEFAULT

    # config.yaml wins over the default.
    (tmp_path / "config.yaml").write_text(
        "agent:\n  gateway_max_concurrent_turns: 8\n", encoding="utf-8"
    )
    assert gateway_run.GatewayRunner._load_agent_executor_workers() == 8

    # env wins over config.yaml.
    monkeypatch.setenv("HERMES_GATEWAY_MAX_CONCURRENT_TURNS", "16")
    assert gateway_run.GatewayRunner._load_agent_executor_workers() == 16


@pytest.mark.parametrize("bad", ["not-a-number", "0", "-4"])
def test_load_agent_executor_workers_falls_back_on_invalid(tmp_path, monkeypatch, bad):
    monkeypatch.setattr(gateway_run, "_hermes_home", tmp_path)
    monkeypatch.setenv("HERMES_GATEWAY_MAX_CONCURRENT_TURNS", bad)
    # Invalid / non-positive must never yield a 0-worker (deadlocked) pool.
    assert gateway_run.GatewayRunner._load_agent_executor_workers() == DEFAULT


@pytest.mark.asyncio
async def test_run_in_executor_with_context_uses_dedicated_pool():
    """An agent turn must run on the dedicated 'hermes-agent-turn' pool, not
    the default executor."""
    executor = ThreadPoolExecutor(
        max_workers=2, thread_name_prefix="hermes-agent-turn"
    )
    try:
        fake_self = SimpleNamespace(_agent_executor=executor)

        def _turn() -> str:
            return threading.current_thread().name

        # Call the unbound coroutine with a minimal fake self — the method only
        # touches self._agent_executor.
        thread_name = await gateway_run.GatewayRunner._run_in_executor_with_context(
            fake_self, _turn
        )
        assert thread_name.startswith("hermes-agent-turn")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


@pytest.mark.asyncio
async def test_dedicated_pool_isolates_parked_turn_from_other_sessions():
    """A turn blocked (parked on approval) holds one worker but does not block a
    turn for another session on the same dedicated pool."""
    executor = ThreadPoolExecutor(
        max_workers=2, thread_name_prefix="hermes-agent-turn"
    )
    try:
        fake_self = SimpleNamespace(_agent_executor=executor)
        release = threading.Event()

        def _parked_turn() -> str:
            # Simulates _await_gateway_decision blocking on the approval event.
            release.wait(timeout=5)
            return "parked-done"

        def _other_turn() -> str:
            return "other-done"

        parked = asyncio.ensure_future(
            gateway_run.GatewayRunner._run_in_executor_with_context(
                fake_self, _parked_turn
            )
        )
        # The other session's turn must complete while the first is still parked.
        other = await asyncio.wait_for(
            gateway_run.GatewayRunner._run_in_executor_with_context(
                fake_self, _other_turn
            ),
            timeout=5,
        )
        assert other == "other-done"
        assert not parked.done()  # still parked, unaffected

        release.set()
        assert await asyncio.wait_for(parked, timeout=5) == "parked-done"
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
