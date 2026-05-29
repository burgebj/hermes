"""Regression test for the Anthropic stale-stream abort path.

Root cause (fixed in fix/anthropic-stale-stream-abort):
The streaming poll loop's stale-stream detector
(``agent/chat_completion_helpers.py::interruptible_streaming_api_call``)
only ever called the OpenAI-wire cleanup helpers
(``_close_request_client_once`` / ``_replace_primary_openai_client``).
In ``anthropic_messages`` mode the live request is owned by
``agent._anthropic_client`` via ``messages.stream()`` — those OpenAI
helpers are no-ops for it.  So when an Anthropic stream wedged (provider
accepts the connection, then delivers no chunks — the classic
"Overloaded"/500 outage), the detector fired but killed nothing: the
worker thread stayed blocked in recv() indefinitely, the turn never
ended, and queued inbound gateway messages were never read.

The fix branches on ``api_mode`` in the stale-kill block, mirroring the
interrupt handler a few lines below it:
    if api_mode == "anthropic_messages":
        agent._anthropic_client.close(); agent._rebuild_anthropic_client()
    else:
        _close_request_client_once(...) ; _replace_primary_openai_client(...)

This test drives a deliberately-hung Anthropic stream against a tiny
stale timeout and asserts the Anthropic abort path runs.  Against the
pre-fix code it hangs/fails because close() is never called.
"""
import os
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from run_agent import AIAgent


def _make_tool_defs(*names):
    return [
        {
            "type": "function",
            "function": {"name": n, "description": n, "parameters": {"type": "object", "properties": {}}},
        }
        for n in names
    ]


@pytest.fixture()
def anthropic_agent():
    """AIAgent pinned to anthropic_messages mode with mocked clients."""
    with (
        patch("run_agent.get_tool_definitions", return_value=_make_tool_defs("web_search")),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        a = AIAgent(
            api_key="test-key-1234567890",
            base_url="https://api.anthropic.com",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
    a.api_mode = "anthropic_messages"
    a.reasoning_config = None
    # Silence the noisy recovery/diagnostic helpers so the test focuses on
    # the abort branch.  Credential refresh is a no-op here.
    a._try_refresh_anthropic_client_credentials = MagicMock()
    a._emit_stream_drop = MagicMock()
    a._log_stream_retry = MagicMock()
    a._buffer_status = MagicMock()
    a._stream_diag_init = MagicMock(return_value={})
    a._stream_diag_capture_response = MagicMock()
    a._touch_activity = MagicMock()
    # Track the OpenAI-wire pool cleanup — it must NOT be called in
    # anthropic mode (proves we took the Anthropic branch, not the old
    # no-op OpenAI path).
    a._replace_primary_openai_client = MagicMock()
    return a


def test_stale_anthropic_stream_is_aborted_and_client_rebuilt(anthropic_agent, monkeypatch):
    agent = anthropic_agent

    # Tiny stale timeout so the detector fires within the test.
    monkeypatch.setenv("HERMES_STREAM_STALE_TIMEOUT", "0.5")
    # No retries — once aborted, surface the error and return immediately.
    monkeypatch.setenv("HERMES_STREAM_RETRIES", "0")

    close_event = threading.Event()
    close_calls = {"n": 0}
    rebuild_calls = {"n": 0}

    class HungStream:
        """Anthropic stream that delivers no events until the connection
        is aborted via client.close() — simulating a wedged provider."""

        response = None

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def __iter__(self):
            return self

        def __next__(self):
            # Block as if waiting on recv(); unblock only when the
            # stale-stream kill calls close(), then raise as a dropped
            # connection would.
            if close_event.wait(timeout=10):
                raise ConnectionError("aborted by stale-stream kill")
            raise AssertionError("stream was never aborted — stale detector did not fire")

        def get_final_message(self):  # pragma: no cover - should never reach
            raise AssertionError("should not reach get_final_message on a hung stream")

    mock_client = MagicMock()
    mock_client.messages.stream.return_value = HungStream()

    def _on_close():
        close_calls["n"] += 1
        close_event.set()

    mock_client.close.side_effect = _on_close
    agent._anthropic_client = mock_client

    def _rebuild():
        rebuild_calls["n"] += 1

    agent._rebuild_anthropic_client = MagicMock(side_effect=_rebuild)

    # The hung stream is aborted -> ConnectionError -> retries disabled ->
    # the error propagates out.  We only care that the abort path ran.
    with pytest.raises(Exception):
        agent._interruptible_streaming_api_call({"messages": [], "model": "claude-opus-4-8"})

    assert close_calls["n"] >= 1, "stale detector must close the wedged Anthropic client"
    assert rebuild_calls["n"] >= 1, "stale detector must rebuild the Anthropic client after abort"
    assert agent._replace_primary_openai_client.call_count == 0, (
        "OpenAI-wire pool cleanup must NOT run in anthropic_messages mode "
        "(would be a no-op for the live Anthropic request and signals the "
        "wrong branch was taken)"
    )
