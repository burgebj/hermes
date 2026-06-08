"""Regression tests for the compression wall-clock timeout (issue #24098).

When the auxiliary compression worker fails or hangs (e.g. HTTP 400 from a
provider that rejects the hardcoded ``temperature`` parameter, or a stuck
httpx stream), the agent response loop must not block indefinitely. The
fix wraps the summary LLM call in a hard wall-clock guard and degrades to
the static-marker fallback when it expires.
"""

import threading
import time

from unittest.mock import patch

import pytest

from agent import context_compressor
from agent.context_compressor import (
    ContextCompressor,
    SummaryWallClockTimeout,
    _call_llm_with_wall_clock,
)


def _short_timeout(monkeypatch, seconds: float = 0.05) -> None:
    monkeypatch.setattr(
        context_compressor,
        "_SUMMARY_WALL_CLOCK_TIMEOUT_SECONDS",
        seconds,
    )


def _msgs():
    return [
        {"role": "user", "content": "do something"},
        {"role": "assistant", "content": "ok"},
    ]


class TestCallLLMWithWallClock:
    """Direct coverage of the helper that bounds a single call_llm invocation."""

    def test_returns_result_when_call_completes_in_time(self):
        sentinel = object()

        def _fast_call(**_):
            return sentinel

        with patch("agent.context_compressor.call_llm", side_effect=_fast_call):
            assert _call_llm_with_wall_clock({}) is sentinel

    def test_propagates_call_llm_exception(self):
        def _boom(**_):
            raise RuntimeError("provider rejected request")

        with patch("agent.context_compressor.call_llm", side_effect=_boom):
            with pytest.raises(RuntimeError, match="provider rejected"):
                _call_llm_with_wall_clock({})

    def test_raises_timeout_when_call_hangs(self, monkeypatch):
        _short_timeout(monkeypatch, seconds=0.05)
        # Use an event the test can set to release the worker thread, so
        # the daemon doesn't sit blocked for the rest of the suite.
        release = threading.Event()

        def _hang(**_):
            release.wait(timeout=5)  # released by the test cleanup below
            return None

        try:
            with patch("agent.context_compressor.call_llm", side_effect=_hang):
                with pytest.raises(SummaryWallClockTimeout):
                    _call_llm_with_wall_clock({})
        finally:
            release.set()


class TestGenerateSummaryWallClock:
    """End-to-end: a hung summary call must surface as a transient failure,
    not a hang that bubbles up into the response loop."""

    def test_timeout_returns_none_and_sets_cooldown(self, monkeypatch):
        _short_timeout(monkeypatch, seconds=0.05)
        release = threading.Event()

        def _hang(**_):
            release.wait(timeout=5)
            return None

        with patch("agent.context_compressor.get_model_context_length", return_value=100_000):
            c = ContextCompressor(model="anthropic/claude-opus-4-7", quiet_mode=True)

        try:
            with patch("agent.context_compressor.call_llm", side_effect=_hang):
                start = time.monotonic()
                result = c._generate_summary(_msgs())
                elapsed = time.monotonic() - start
        finally:
            release.set()

        assert result is None
        # Must return promptly — within a small multiple of the wall-clock
        # bound, not the 5s safety release above.
        assert elapsed < 2.0
        # Cooldown set so the next preflight pass skips the call rather
        # than re-arming a fresh hang.
        assert c._summary_failure_cooldown_until > time.monotonic()
        # Error message surfaced for the gateway-level warning emitter.
        assert c._last_summary_error is not None
        assert "wall-clock" in c._last_summary_error

    def test_timeout_does_not_attempt_fallback_to_main(self, monkeypatch):
        """If the call hangs, retrying on the main provider would just hang
        again (it's the same chain).  Don't fall through to that path."""
        _short_timeout(monkeypatch, seconds=0.05)
        release = threading.Event()
        call_count = {"n": 0}

        def _hang(**_):
            call_count["n"] += 1
            release.wait(timeout=5)
            return None

        with patch("agent.context_compressor.get_model_context_length", return_value=100_000):
            c = ContextCompressor(
                model="main-model",
                summary_model_override="broken-aux-model",
                quiet_mode=True,
            )

        try:
            with patch("agent.context_compressor.call_llm", side_effect=_hang):
                result = c._generate_summary(_msgs())
        finally:
            release.set()

        assert result is None
        assert call_count["n"] == 1
        assert getattr(c, "_summary_model_fallen_back", False) is False
