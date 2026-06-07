"""Regression tests for codex_responses stream retry on BrokenPipeError.

Before this fix: when Copilot's Responses API closed the upstream socket
with EPIPE (Errno 32) on long+xhigh requests, the raw BrokenPipeError
escaped run_codex_stream's retry handler (which only caught
RemoteProtocolError / ReadTimeout / ConnectError / ConnectionError).
It bubbled past the outer 3-retry conversation-loop and surfaced as:

    API call failed after 3 retries: [Errno 32] Broken pipe

After this fix: BrokenPipeError + OSError are in the same retry-catch
tuple, and HERMES_CODEX_STREAM_RETRIES bumps the default from 1 to 3.
"""

from __future__ import annotations

import os
import sys
import types
from types import SimpleNamespace

import pytest

# Stub optional heavy imports so run_agent imports cleanly in isolation
sys.modules.setdefault("fire", types.SimpleNamespace(Fire=lambda *a, **k: None))
sys.modules.setdefault("firecrawl", types.SimpleNamespace(Firecrawl=object))
sys.modules.setdefault("fal_client", types.SimpleNamespace())


def _make_codex_agent(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    (tmp_path / ".env").write_text("", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("{}\n", encoding="utf-8")
    from run_agent import AIAgent

    agent = AIAgent(
        model="gpt-5.5",
        provider="openai-codex",
        api_key="sk-dummy",
        base_url="https://chatgpt.com/backend-api/codex",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
        platform="cli",
    )
    agent.api_mode = "codex_responses"
    monkeypatch.setattr(agent, "_emit_status", lambda *a, **k: None)
    return agent


def _fake_terminal_response():
    """Construct a SimpleNamespace that looks enough like a completed
    Responses API result that _consume_codex_event_stream accepts it."""
    return SimpleNamespace(
        status="completed",
        incomplete_details=None,
        error=None,
        usage=None,
        id="resp_test",
        output=[],
    )


def test_broken_pipe_during_connect_is_retried(tmp_path, monkeypatch):
    """BrokenPipeError raised by responses.create(stream=True) is caught
    by the stream-retry handler instead of bubbling to the outer loop."""
    from agent import codex_runtime

    monkeypatch.setenv("HERMES_CODEX_STREAM_RETRIES", "3")
    agent = _make_codex_agent(tmp_path, monkeypatch)

    connect_count = {"n": 0}

    class _FakeResponses:
        def create(self, **kwargs):
            connect_count["n"] += 1
            if connect_count["n"] == 1:
                raise BrokenPipeError(32, "Broken pipe")
            # Returning an object with .output but not .__iter__ takes the
            # short-circuit branch in run_codex_stream (line 477 in current
            # code) so we don't need to fake the SSE event consumer.
            return _fake_terminal_response()

    class _FakeClient:
        def __init__(self):
            self.responses = _FakeResponses()

    monkeypatch.setattr(
        agent, "_ensure_primary_openai_client", lambda reason=None: _FakeClient()
    )

    result = codex_runtime.run_codex_stream(agent, {"model": "gpt-5.5", "input": "hi"})
    assert connect_count["n"] == 2, (
        f"expected exactly 2 connect attempts (1 EPIPE + 1 success), got {connect_count['n']}"
    )
    assert result.status == "completed"


def test_broken_pipe_exhausts_retries(tmp_path, monkeypatch):
    """If BrokenPipeError fires on every attempt, the final raise IS a
    BrokenPipeError — not silently turned into a success. This proves we
    didn't accidentally swallow the error."""
    from agent import codex_runtime

    monkeypatch.setenv("HERMES_CODEX_STREAM_RETRIES", "2")
    agent = _make_codex_agent(tmp_path, monkeypatch)

    call_count = {"n": 0}

    class _AlwaysEPIPE:
        def create(self, **kwargs):
            call_count["n"] += 1
            raise BrokenPipeError(32, "Broken pipe")

    class _FakeClient:
        def __init__(self):
            self.responses = _AlwaysEPIPE()

    monkeypatch.setattr(
        agent, "_ensure_primary_openai_client", lambda reason=None: _FakeClient()
    )

    with pytest.raises(BrokenPipeError):
        codex_runtime.run_codex_stream(agent, {"model": "gpt-5.5", "input": "hi"})

    # max_stream_retries=2 → total attempts = max_stream_retries + 1 = 3
    assert call_count["n"] == 3, (
        f"expected 3 attempts (max_stream_retries=2 + 1 initial), got {call_count['n']}"
    )


def test_oserror_during_connect_is_retried(tmp_path, monkeypatch):
    """Any OSError on stream connect (not just EPIPE) is also retried —
    catches other transport-layer OS errors that aren't ConnectionError
    subclasses (e.g. ECONNABORTED, ETIMEDOUT on some platforms)."""
    from agent import codex_runtime

    monkeypatch.setenv("HERMES_CODEX_STREAM_RETRIES", "3")
    agent = _make_codex_agent(tmp_path, monkeypatch)

    call_count = {"n": 0}

    class _FakeResponses:
        def create(self, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise OSError(104, "Connection reset by peer")
            return _fake_terminal_response()

    class _FakeClient:
        def __init__(self):
            self.responses = _FakeResponses()

    monkeypatch.setattr(
        agent, "_ensure_primary_openai_client", lambda reason=None: _FakeClient()
    )

    result = codex_runtime.run_codex_stream(agent, {"model": "gpt-5.5", "input": "hi"})
    assert call_count["n"] == 2
    assert result.status == "completed"


def test_default_stream_retries_is_three(tmp_path, monkeypatch):
    """Default max_stream_retries should be 3 when HERMES_CODEX_STREAM_RETRIES
    is unset — bumped from the legacy hard-coded 1 because one retry was
    empirically insufficient on Copilot Responses API with large prompts."""
    from agent import codex_runtime

    monkeypatch.delenv("HERMES_CODEX_STREAM_RETRIES", raising=False)
    agent = _make_codex_agent(tmp_path, monkeypatch)

    call_count = {"n": 0}

    class _AlwaysEPIPE:
        def create(self, **kwargs):
            call_count["n"] += 1
            raise BrokenPipeError(32, "Broken pipe")

    class _FakeClient:
        def __init__(self):
            self.responses = _AlwaysEPIPE()

    monkeypatch.setattr(
        agent, "_ensure_primary_openai_client", lambda reason=None: _FakeClient()
    )

    with pytest.raises(BrokenPipeError):
        codex_runtime.run_codex_stream(agent, {"model": "gpt-5.5", "input": "hi"})

    # Default max_stream_retries=3 → total attempts = 4
    assert call_count["n"] == 4, (
        f"expected 4 attempts (default max_stream_retries=3 + 1 initial), got {call_count['n']}"
    )


def test_env_var_can_override_retries(tmp_path, monkeypatch):
    """HERMES_CODEX_STREAM_RETRIES env var overrides default."""
    from agent import codex_runtime

    monkeypatch.setenv("HERMES_CODEX_STREAM_RETRIES", "0")
    agent = _make_codex_agent(tmp_path, monkeypatch)

    call_count = {"n": 0}

    class _AlwaysEPIPE:
        def create(self, **kwargs):
            call_count["n"] += 1
            raise BrokenPipeError(32, "Broken pipe")

    class _FakeClient:
        def __init__(self):
            self.responses = _AlwaysEPIPE()

    monkeypatch.setattr(
        agent, "_ensure_primary_openai_client", lambda reason=None: _FakeClient()
    )

    with pytest.raises(BrokenPipeError):
        codex_runtime.run_codex_stream(agent, {"model": "gpt-5.5", "input": "hi"})

    # max_stream_retries=0 → single attempt only
    assert call_count["n"] == 1
