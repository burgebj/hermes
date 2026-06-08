"""Tests for unrepairable tool-call argument handling.

Unrepairable model-emitted tool arguments must stay API-valid without letting
Hermes execute the original tool with silently-empty/default arguments.
"""

import json
import threading
import time
from unittest.mock import MagicMock

import pytest

from agent.message_sanitization import (
    INVALID_TOOL_ARGUMENTS_ERROR_KEY,
    INVALID_TOOL_ARGUMENTS_ERROR_MESSAGE,
    _repair_tool_call_arguments,
)
from agent.tool_executor import execute_tool_calls_concurrent, execute_tool_calls_sequential


@pytest.fixture(autouse=True)
def _isolate_hermes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    (tmp_path / ".hermes").mkdir(exist_ok=True)
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    monkeypatch.setenv("HERMES_INFERENCE_PROVIDER", "")


class _FakeToolCall:
    def __init__(self, name="terminal", args="{}", call_id="tc_invalid"):
        self.function = MagicMock(name=name, arguments=args)
        self.function.name = name
        self.id = call_id


class _FakeAssistantMsg:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls


class _SubdirHints:
    def check_tool_call(self, name, args):
        return ""


class _MinimalAgent:
    _interrupt_requested = False
    _interrupt_message = None
    _execution_thread_id = threading.current_thread().ident
    _interrupt_thread_signal_pending = False
    log_prefix = ""
    quiet_mode = True
    verbose_logging = False
    log_prefix_chars = 200
    tool_progress_callback = None
    tool_start_callback = None
    tool_complete_callback = None
    valid_tool_names = set()
    tool_delay = 0
    _turns_since_memory = 0
    _iters_since_skill = 0
    _current_tool = None
    _last_activity = 0
    _print_fn = print
    _active_children = []

    def __init__(self):
        self._checkpoint_mgr = MagicMock(enabled=False)
        self._subdirectory_hints = _SubdirHints()
        self._tool_worker_threads = set()
        self._tool_worker_threads_lock = threading.Lock()
        self._active_children_lock = threading.Lock()
        self._todo_store = MagicMock()
        self._session_db = None
        self._tool_guardrails = MagicMock()
        self._invoke_tool = MagicMock(return_value=json.dumps({"executed": True}))

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

    def _append_guardrail_observation(self, function_name, function_args, result, failed=False):
        return result

    def _record_file_mutation_result(self, function_name, function_args, result, is_error):
        pass

    def _tool_result_content_for_active_model(self, function_name, function_result):
        return function_result

    def _apply_pending_steer_to_tool_results(self, *args, **kwargs):
        pass


def _agent():
    return _MinimalAgent()


def _sentinel_args():
    return json.dumps({INVALID_TOOL_ARGUMENTS_ERROR_KEY: INVALID_TOOL_ARGUMENTS_ERROR_MESSAGE})


def _tool_error_content(messages):
    assert len(messages) == 1
    assert messages[0]["role"] == "tool"
    assert messages[0]["tool_call_id"] == "tc_invalid"
    return json.loads(messages[0]["content"])["error"]


def test_unrepairable_arguments_repair_to_error_sentinel_not_empty_object():
    raw = '{"command": "ls -la /tmp", "timeout": 30, "background":'

    repaired = _repair_tool_call_arguments(raw, "terminal")

    parsed = json.loads(repaired)
    assert parsed == {INVALID_TOOL_ARGUMENTS_ERROR_KEY: INVALID_TOOL_ARGUMENTS_ERROR_MESSAGE}
    assert parsed != {}


def test_concurrent_executor_blocks_invalid_argument_sentinel_without_dispatch():
    agent = _agent()
    messages = []
    assistant = _FakeAssistantMsg([_FakeToolCall(args=_sentinel_args())])

    execute_tool_calls_concurrent(agent, assistant, messages, "task")

    agent._invoke_tool.assert_not_called()
    error = _tool_error_content(messages)
    assert "truncated or malformed" in error
    assert "valid JSON" in error


def test_sequential_executor_blocks_invalid_argument_sentinel_without_dispatch():
    agent = _agent()
    messages = []
    assistant = _FakeAssistantMsg([_FakeToolCall(args=_sentinel_args())])

    execute_tool_calls_sequential(agent, assistant, messages, "task")

    agent._invoke_tool.assert_not_called()
    error = _tool_error_content(messages)
    assert "truncated or malformed" in error
    assert "valid JSON" in error
