"""Tests for interrupt handling in concurrent tool execution."""

import threading
import time
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _isolate_hermes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    (tmp_path / ".hermes").mkdir(exist_ok=True)


def _make_agent(monkeypatch):
    """Create a minimal AIAgent-like object with just the methods under test."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("HERMES_INFERENCE_PROVIDER", "")
    # Avoid full AIAgent init — just import the class and build a stub
    import run_agent as _ra

    class _Stub:
        _interrupt_requested = False
        _interrupt_message = None
        # Bind to this thread's ident so interrupt() targets a real tid.
        _execution_thread_id = threading.current_thread().ident
        _interrupt_thread_signal_pending = False
        log_prefix = ""
        quiet_mode = True
        verbose_logging = False
        log_prefix_chars = 200
        _checkpoint_mgr = MagicMock(enabled=False)
        _subdirectory_hints = MagicMock()
        _subdirectory_hints.check_tool_call.return_value = ""
        tool_progress_callback = None
        tool_start_callback = None
        tool_complete_callback = None
        _todo_store = MagicMock()
        _session_db = None
        valid_tool_names = set()
        _turns_since_memory = 0
        _iters_since_skill = 0
        _current_tool = None
        _last_activity = 0
        _print_fn = print
        # Worker-thread tracking state mirrored from AIAgent.__init__ so the
        # real interrupt() method can fan out to concurrent-tool workers.
        _active_children: list = []
        # Guardrails stub — returns allows_execution=True for all tools
        _tool_guardrails = MagicMock()
        _tool_guardrails.before_call.return_value = MagicMock(allows_execution=True)

        def __init__(self):
            # Instance-level (not class-level) so each test gets a fresh set.
            self._tool_worker_threads: set = set()
            self._tool_worker_threads_lock = threading.Lock()
            self._active_children_lock = threading.Lock()

        def _touch_activity(self, desc):
            self._last_activity = time.time()

        def _vprint(self, msg, force=False):
            pass

        def _safe_print(self, msg):
            pass

        def _should_emit_quiet_tool_messages(self):
            return False

        def _should_start_quiet_spinner(self):
            return False

        def _has_stream_consumers(self):
            return False

    stub = _Stub()
    # Bind the real methods under test
    stub._execute_tool_calls_concurrent = _ra.AIAgent._execute_tool_calls_concurrent.__get__(stub)
    stub.interrupt = _ra.AIAgent.interrupt.__get__(stub)
    stub.clear_interrupt = _ra.AIAgent.clear_interrupt.__get__(stub)
    # /steer injection (added in PR #12116) fires after every concurrent
    # tool batch. Stub it as a no-op — this test exercises interrupt
    # fanout, not steer injection.
    stub._apply_pending_steer_to_tool_results = lambda *a, **kw: None
    stub._invoke_tool = MagicMock(side_effect=lambda *a, **kw: '{"ok": true}')
    # Post-execution callbacks — stubbed as no-ops
    stub._append_guardrail_observation = lambda *a, **kw: a[2] if len(a) > 2 else None
    stub._record_file_mutation_result = lambda *a, **kw: None
    stub._tool_result_content_for_active_model = lambda *a, **kw: str(a[1]) if len(a) > 1 else ""
    return stub


class _FakeToolCall:
    def __init__(self, name, args="{}", call_id="tc_1"):
        self.function = MagicMock(name=name, arguments=args)
        self.function.name = name
        self.id = call_id


class _FakeAssistantMsg:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls




def test_concurrent_preflight_interrupt_skips_all(monkeypatch):
    """When _interrupt_requested is already set before concurrent execution,
    all tools are skipped with cancellation messages."""
    agent = _make_agent(monkeypatch)
    agent._interrupt_requested = True

    tc1 = _FakeToolCall("tool_a", call_id="tc_a")
    tc2 = _FakeToolCall("tool_b", call_id="tc_b")
    msg = _FakeAssistantMsg([tc1, tc2])
    messages = []

    agent._execute_tool_calls_concurrent(msg, messages, "test_task")

    assert len(messages) == 2
    assert "skipped due to user interrupt" in messages[0]["content"]
    assert "skipped due to user interrupt" in messages[1]["content"]
    # _invoke_tool should never have been called
    agent._invoke_tool.assert_not_called()




def test_clear_interrupt_clears_worker_tids(monkeypatch):
    """After clear_interrupt(), stale worker-tid bits must be cleared so the
    next turn's tools — which may be scheduled onto recycled tids — don't
    see a false interrupt."""
    from tools.interrupt import is_interrupted, set_interrupt

    agent = _make_agent(monkeypatch)
    # Simulate a worker having registered but not yet exited cleanly (e.g. a
    # hypothetical bug in the tear-down).  Put a fake tid in the set and
    # flag it interrupted.
    fake_tid = threading.current_thread().ident  # use real tid so is_interrupted can see it
    with agent._tool_worker_threads_lock:
        agent._tool_worker_threads.add(fake_tid)
    set_interrupt(True, fake_tid)
    assert is_interrupted() is True  # sanity

    agent.clear_interrupt()

    assert is_interrupted() is False, (
        "clear_interrupt() did not clear the interrupt bit for a tracked "
        "worker tid — stale interrupt can leak into the next turn"
    )


def test_concurrent_mid_execution_interrupt_detected_promptly(monkeypatch):
    """When _interrupt_requested is set DURING concurrent tool execution,
    the interrupt is detected on the next poll (<=0.5s) even if all
    tools completed before that poll (issue #35267).

    Before the fix, the interrupt check only ran when not_done was
    non-empty, so fast-completing batches never noticed the interrupt
    until the main loop's top-of-iteration check.  Now the interrupt
    flag is checked unconditionally after every wait() call.
    """
    agent = _make_agent(monkeypatch)
    agent._interrupt_requested = False

    _start_time = time.time()

    # Tools that sleep briefly then return a simple result
    def _slow_tool(*a, **kw):
        time.sleep(0.15)
        return '{"ok": true}'

    agent._invoke_tool = MagicMock(side_effect=_slow_tool)

    tcs = [_FakeToolCall(f"tool_{i}", call_id=f"tc_{i}") for i in range(5)]
    msg = _FakeAssistantMsg(tcs)
    messages = []

    def _run():
        agent._execute_tool_calls_concurrent(msg, messages, "test_task")

    t = threading.Thread(target=_run, daemon=True)
    t.start()

    # Let all tools start, then inject interrupt before the first poll
    time.sleep(0.05)
    agent._interrupt_requested = True
    t.join(timeout=3.0)
    assert not t.is_alive(), "concurrent execution did not finish within 3s"

    elapsed = time.time() - _start_time
    # With 0.5s polling, interrupt should be detected within ~0.5s of
    # being set.  Even if all tools already completed, the +break on
    # interrupt should return quickly.
    assert elapsed < 1.5, (
        f"Execution took {elapsed:.2f}s; interrupt should be detected "
        f"within ~0.5s (polling window) even when tools complete fast"
    )

    # All 5 tools should have results (they completed before interrupt
    # was detected — this is expected for concurrent fast tools).
    # The key fix is that the function returns quickly instead of
    # waiting for the full 5s old polling interval.
    assert len(messages) == 5, (
        f"Expected 5 tool result messages, got {len(messages)}"
    )
    # Verify all messages are proper tool results (not cancellation stubs
    # from pre-flight — the tools actually ran).
    for m in messages:
        assert m["role"] == "tool", f"Unexpected role: {m['role']}"
        assert '"ok"' in m.get("content", ""), (
            f"Tool should have completed with result, got: {m.get('content', '')}"
        )

