"""
Tests for HermesAgentLoop parallel tool execution (parallel_tools=True).

Verifies that:
- Multiple tool calls in one turn execute concurrently (measurable speedup)
- Message order matches the original tool_calls order, regardless of completion order
- Errors in one tool don't prevent others from completing
- parallel_tools=False falls back to sequential behaviour
- Single tool calls are unaffected by the parallel_tools flag
"""

import asyncio
import json
import time
import uuid
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from environments.agent_loop import AgentResult, HermesAgentLoop, ToolError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool_call(name: str, args: Dict[str, Any], tc_id: str = None) -> Dict:
    return {
        "id": tc_id or f"call_{uuid.uuid4().hex[:8]}",
        "type": "function",
        "function": {"name": name, "arguments": json.dumps(args)},
    }


def _make_response(tool_calls=None, content=""):
    """Build a minimal ChatCompletion-shaped response."""
    msg = SimpleNamespace(
        tool_calls=tool_calls,
        content=content,
        reasoning_content=None,
        reasoning=None,
        reasoning_details=None,
    )
    choice = SimpleNamespace(message=msg)
    return SimpleNamespace(choices=[choice])


def _make_server(responses: List) -> AsyncMock:
    """Server whose chat_completion() returns responses in sequence."""
    server = MagicMock()
    server.chat_completion = AsyncMock(side_effect=responses)
    return server


def _make_loop(server, tool_names, parallel: bool = True) -> HermesAgentLoop:
    schemas = [{"name": n, "description": n} for n in tool_names]
    return HermesAgentLoop(
        server=server,
        tool_schemas=schemas,
        valid_tool_names=set(tool_names),
        max_turns=5,
        parallel_tools=parallel,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestParallelToolExecution:
    """Parallel execution dispatches all tool calls concurrently."""

    @pytest.mark.asyncio
    async def test_parallel_is_faster_than_sequential(self):
        """Two 0.1s tools finish in ~0.1s (parallel) not ~0.2s (sequential)."""
        TOOL_DELAY = 0.12

        def slow_tool(name, args, task_id, user_task):
            time.sleep(TOOL_DELAY)
            return json.dumps({"result": name})

        tc1 = _make_tool_call("tool_a", {}, "id_a")
        tc2 = _make_tool_call("tool_b", {}, "id_b")
        responses = [
            _make_response(tool_calls=[tc1, tc2]),
            _make_response(content="done"),
        ]
        server = _make_server(responses)
        loop = _make_loop(server, ["tool_a", "tool_b"], parallel=True)

        with patch("environments.agent_loop.handle_function_call", side_effect=slow_tool):
            with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
                with patch("environments.agent_loop.enforce_turn_budget"):
                    start = time.monotonic()
                    result = await loop.run([{"role": "user", "content": "go"}])
                    elapsed = time.monotonic() - start

        assert result.finished_naturally
        # Parallel: should finish in roughly one tool's time, not two
        assert elapsed < TOOL_DELAY * 1.8, f"Expected parallel speedup, took {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_sequential_takes_additive_time(self):
        """Same two slow tools with parallel_tools=False take ~2x the time."""
        TOOL_DELAY = 0.08

        def slow_tool(name, args, task_id, user_task):
            time.sleep(TOOL_DELAY)
            return json.dumps({"result": name})

        tc1 = _make_tool_call("tool_a", {}, "id_a")
        tc2 = _make_tool_call("tool_b", {}, "id_b")
        responses = [
            _make_response(tool_calls=[tc1, tc2]),
            _make_response(content="done"),
        ]
        server = _make_server(responses)
        loop = _make_loop(server, ["tool_a", "tool_b"], parallel=False)

        with patch("environments.agent_loop.handle_function_call", side_effect=slow_tool):
            with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
                with patch("environments.agent_loop.enforce_turn_budget"):
                    start = time.monotonic()
                    result = await loop.run([{"role": "user", "content": "go"}])
                    elapsed = time.monotonic() - start

        assert result.finished_naturally
        # Sequential: both tools must complete before moving on
        assert elapsed >= TOOL_DELAY * 1.8, f"Expected sequential timing, took {elapsed:.3f}s"


class TestMessageOrdering:
    """Tool result messages appear in the same order as the tool_calls list."""

    @pytest.mark.asyncio
    async def test_result_order_matches_tool_call_order(self):
        """Results are appended in original tool_calls order even if execution order differs."""
        execution_order = []

        def tracking_tool(name, args, task_id, user_task):
            # Tool B completes instantly, Tool A sleeps briefly
            if name == "tool_a":
                time.sleep(0.05)
            execution_order.append(name)
            return json.dumps({"result": name})

        tc1 = _make_tool_call("tool_a", {}, "id_a")
        tc2 = _make_tool_call("tool_b", {}, "id_b")
        responses = [
            _make_response(tool_calls=[tc1, tc2]),
            _make_response(content="done"),
        ]
        server = _make_server(responses)
        loop = _make_loop(server, ["tool_a", "tool_b"], parallel=True)

        with patch("environments.agent_loop.handle_function_call", side_effect=tracking_tool):
            with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
                with patch("environments.agent_loop.enforce_turn_budget"):
                    result = await loop.run([{"role": "user", "content": "go"}])

        # Find the two tool result messages in the conversation
        tool_msgs = [m for m in result.messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 2
        # Order must match tool_calls list order (a before b), not execution order
        assert tool_msgs[0]["tool_call_id"] == "id_a"
        assert tool_msgs[1]["tool_call_id"] == "id_b"
        assert json.loads(tool_msgs[0]["content"])["result"] == "tool_a"
        assert json.loads(tool_msgs[1]["content"])["result"] == "tool_b"

    @pytest.mark.asyncio
    async def test_three_tools_preserve_order(self):
        """Order is preserved for three parallel tool calls."""
        call_order = []

        def tracking_tool(name, args, task_id, user_task):
            delays = {"tool_c": 0.06, "tool_b": 0.03, "tool_a": 0.0}
            time.sleep(delays.get(name, 0))
            call_order.append(name)
            return json.dumps({"done": name})

        tcs = [
            _make_tool_call("tool_a", {}, "id_a"),
            _make_tool_call("tool_b", {}, "id_b"),
            _make_tool_call("tool_c", {}, "id_c"),
        ]
        responses = [_make_response(tool_calls=tcs), _make_response(content="done")]
        server = _make_server(responses)
        loop = _make_loop(server, ["tool_a", "tool_b", "tool_c"], parallel=True)

        with patch("environments.agent_loop.handle_function_call", side_effect=tracking_tool):
            with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
                with patch("environments.agent_loop.enforce_turn_budget"):
                    result = await loop.run([{"role": "user", "content": "go"}])

        tool_msgs = [m for m in result.messages if m.get("role") == "tool"]
        assert [m["tool_call_id"] for m in tool_msgs] == ["id_a", "id_b", "id_c"]


class TestErrorIsolation:
    """One failing tool should not prevent others from completing."""

    @pytest.mark.asyncio
    async def test_one_tool_error_does_not_block_others(self):
        """If tool_a raises, tool_b still executes and returns a result."""
        def dispatch(name, args, task_id, user_task):
            if name == "tool_a":
                raise RuntimeError("tool_a exploded")
            return json.dumps({"result": name})

        tc1 = _make_tool_call("tool_a", {}, "id_a")
        tc2 = _make_tool_call("tool_b", {}, "id_b")
        responses = [
            _make_response(tool_calls=[tc1, tc2]),
            _make_response(content="done"),
        ]
        server = _make_server(responses)
        loop = _make_loop(server, ["tool_a", "tool_b"], parallel=True)

        with patch("environments.agent_loop.handle_function_call", side_effect=dispatch):
            with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
                with patch("environments.agent_loop.enforce_turn_budget"):
                    result = await loop.run([{"role": "user", "content": "go"}])

        assert result.finished_naturally

        tool_msgs = [m for m in result.messages if m.get("role") == "tool"]
        assert len(tool_msgs) == 2

        # tool_a should have an error
        a_content = json.loads(tool_msgs[0]["content"])
        assert "error" in a_content
        assert "tool_a exploded" in a_content["error"]

        # tool_b should have succeeded
        b_content = json.loads(tool_msgs[1]["content"])
        assert b_content["result"] == "tool_b"

        # tool_a error should be recorded
        assert len(result.tool_errors) >= 1
        assert result.tool_errors[0].tool_name == "tool_a"

    @pytest.mark.asyncio
    async def test_unknown_tool_name_recorded_as_error(self):
        tc = _make_tool_call("nonexistent_tool", {}, "id_x")
        responses = [
            _make_response(tool_calls=[tc]),
            _make_response(content="done"),
        ]
        server = _make_server(responses)
        loop = _make_loop(server, ["web_search"], parallel=True)

        with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
            with patch("environments.agent_loop.enforce_turn_budget"):
                result = await loop.run([{"role": "user", "content": "go"}])

        assert len(result.tool_errors) == 1
        assert result.tool_errors[0].tool_name == "nonexistent_tool"


class TestFlagBehaviour:
    """parallel_tools flag controls execution mode."""

    @pytest.mark.asyncio
    async def test_single_tool_call_unaffected_by_parallel_flag(self):
        """A single tool call behaves the same regardless of parallel_tools."""
        for parallel in (True, False):
            def dispatch(name, args, task_id, user_task):
                return json.dumps({"result": "ok"})

            tc = _make_tool_call("web_search", {"query": "test"}, "id_1")
            responses = [
                _make_response(tool_calls=[tc]),
                _make_response(content="done"),
            ]
            server = _make_server(responses)
            loop = _make_loop(server, ["web_search"], parallel=parallel)

            with patch("environments.agent_loop.handle_function_call", side_effect=dispatch):
                with patch("environments.agent_loop.maybe_persist_tool_result", side_effect=lambda content, **kw: content):
                    with patch("environments.agent_loop.enforce_turn_budget"):
                        result = await loop.run([{"role": "user", "content": "go"}])

            assert result.finished_naturally
            tool_msgs = [m for m in result.messages if m.get("role") == "tool"]
            assert len(tool_msgs) == 1
            assert json.loads(tool_msgs[0]["content"])["result"] == "ok"

    @pytest.mark.asyncio
    async def test_parallel_tools_defaults_to_true(self):
        """HermesAgentLoop should enable parallel execution by default."""
        server = _make_server([_make_response(content="done")])
        loop = HermesAgentLoop(
            server=server,
            tool_schemas=[],
            valid_tool_names=set(),
        )
        assert loop.parallel_tools is True

    @pytest.mark.asyncio
    async def test_no_tools_produces_natural_finish(self):
        """A response with no tool calls finishes naturally on the first turn."""
        server = _make_server([_make_response(content="All done.")])
        loop = _make_loop(server, [], parallel=True)

        result = await loop.run([{"role": "user", "content": "hi"}])

        assert result.finished_naturally
        assert result.turns_used == 1
        assert result.messages[-1]["content"] == "All done."
