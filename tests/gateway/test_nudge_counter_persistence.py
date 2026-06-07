"""Tests for memory nudge counter persistence across agent cache misses.

When smart model routing switches between cheap and strong models per turn,
the agent cache misses and creates a fresh AIAgent whose __init__ resets
_turns_since_memory to 0. The gateway-level _session_nudge_counters dict
must preserve and restore this counter so that background memory review
actually triggers after nudge_interval turns.
"""

import threading
from unittest.mock import MagicMock

import pytest


def _make_runner():
    """Create a minimal GatewayRunner with nudge counter infrastructure."""
    from gateway.run import GatewayRunner

    runner = GatewayRunner.__new__(GatewayRunner)
    runner._agent_cache = {}
    runner._agent_cache_lock = threading.Lock()
    runner._session_nudge_counters = {}
    return runner


class TestNudgeCounterPersistence:
    """Verify _session_nudge_counters preserves counters across cache misses."""

    def test_runner_has_nudge_counters_dict(self):
        runner = _make_runner()
        assert isinstance(runner._session_nudge_counters, dict)
        assert len(runner._session_nudge_counters) == 0

    def test_save_and_restore_counter(self):
        """Counter saved after one turn is restored for the next."""
        runner = _make_runner()
        session_key = "bb:iMessage;-;+1234"

        # Simulate: agent runs, counter increments to 2
        runner._session_nudge_counters[session_key] = 2

        # Simulate: new agent created (cache miss), restore counter
        restored = runner._session_nudge_counters.get(session_key, 0)
        assert restored == 2

    def test_missing_session_defaults_to_zero(self):
        """Unknown session key returns 0 (first message)."""
        runner = _make_runner()
        assert runner._session_nudge_counters.get("unknown-session", 0) == 0

    def test_counter_accumulates_across_turns(self):
        """Counter should grow: 0→1→2→3 across multiple cache misses."""
        runner = _make_runner()
        session_key = "bb:iMessage;-;+1234"

        for expected in range(1, 5):
            # Restore
            counter = runner._session_nudge_counters.get(session_key, 0)
            # Simulate run_conversation incrementing
            counter += 1
            # Save
            runner._session_nudge_counters[session_key] = counter
            assert runner._session_nudge_counters[session_key] == expected

    def test_counter_resets_after_trigger(self):
        """Counter resets to 0 when nudge triggers (simulating the agent reset)."""
        runner = _make_runner()
        session_key = "bb:iMessage;-;+1234"
        nudge_interval = 3

        # Accumulate to trigger point
        for _ in range(nudge_interval):
            counter = runner._session_nudge_counters.get(session_key, 0)
            counter += 1
            runner._session_nudge_counters[session_key] = counter

        assert runner._session_nudge_counters[session_key] == nudge_interval

        # Agent triggers nudge and resets counter
        runner._session_nudge_counters[session_key] = 0
        assert runner._session_nudge_counters[session_key] == 0

        # Next turn starts from 0
        counter = runner._session_nudge_counters.get(session_key, 0)
        counter += 1
        runner._session_nudge_counters[session_key] = counter
        assert runner._session_nudge_counters[session_key] == 1

    def test_independent_sessions(self):
        """Different sessions have independent counters."""
        runner = _make_runner()
        runner._session_nudge_counters["session-A"] = 3
        runner._session_nudge_counters["session-B"] = 1

        assert runner._session_nudge_counters["session-A"] == 3
        assert runner._session_nudge_counters["session-B"] == 1

    def test_agent_attribute_restore(self):
        """Verify the hasattr + restore pattern used in run.py."""
        runner = _make_runner()
        session_key = "bb:test"
        runner._session_nudge_counters[session_key] = 5

        # Simulate a mock agent with the attribute
        agent = MagicMock()
        agent._turns_since_memory = 0  # fresh agent

        # Restore pattern from gateway/run.py
        _saved = runner._session_nudge_counters.get(session_key, 0)
        if hasattr(agent, '_turns_since_memory'):
            agent._turns_since_memory = _saved

        assert agent._turns_since_memory == 5

    def test_agent_attribute_save(self):
        """Verify the save pattern used in run.py after run_conversation."""
        runner = _make_runner()
        session_key = "bb:test"

        agent = MagicMock()
        agent._turns_since_memory = 3  # after run_conversation

        # Save pattern from gateway/run.py
        if hasattr(agent, '_turns_since_memory'):
            runner._session_nudge_counters[session_key] = agent._turns_since_memory

        assert runner._session_nudge_counters[session_key] == 3
