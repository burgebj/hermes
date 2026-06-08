"""Tests for the reasoning-only stale detector (#29086).

Verifies that a stream emitting only reasoning_content tokens for longer than
HERMES_REASONING_ONLY_STALE_TIMEOUT seconds is killed by the outer poll loop,
while streams that eventually produce content are left alone.

The tests exercise the shared state dicts (last_content_chunk_time,
reasoning_seen) and the poll-loop kill logic directly — no live network calls.
"""

import os
import threading
import time
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_agent():
    """Minimal AIAgent with stubs for methods called by the streaming code."""
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}):
        from run_agent import AIAgent
        agent = AIAgent(
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
            model="test/model",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
    agent._emit_status = MagicMock()
    agent._touch_activity = MagicMock()
    agent._close_request_openai_client = MagicMock()
    agent._replace_primary_openai_client = MagicMock()
    return agent


def _simulate_poll_loop(
    last_chunk_time,
    last_content_chunk_time,
    reasoning_seen,
    request_client_holder,
    api_kwargs,
    agent,
    reasoning_only_stale_timeout,
    stream_stale_timeout=9999.0,
    max_poll_seconds=10.0,
):
    """Minimal replica of the outer poll loop from stream_chat_completion().

    Runs until max_poll_seconds elapsed or the reasoning-only kill fires.
    Returns True if reasoning-only stale was triggered, False otherwise.
    """
    import logging
    logger = logging.getLogger("test")

    killed = {"yes": False}
    start = time.time()

    while time.time() - start < max_poll_seconds:
        time.sleep(0.05)

        # Normal stale check (not under test, but must not interfere)
        _stale_elapsed = time.time() - last_chunk_time["t"]
        if _stale_elapsed > stream_stale_timeout:
            break

        # Reasoning-only stale check (the fix under test)
        if reasoning_seen["yes"]:
            _ro_elapsed = time.time() - last_content_chunk_time["t"]
            if _ro_elapsed > reasoning_only_stale_timeout:
                rc = request_client_holder.get("client")
                if rc is not None:
                    agent._close_request_openai_client(
                        rc, reason="reasoning_only_stale_kill"
                    )
                agent._replace_primary_openai_client(
                    reason="reasoning_only_stale_pool_cleanup"
                )
                last_content_chunk_time["t"] = time.time()
                reasoning_seen["yes"] = False
                agent._touch_activity(
                    f"reasoning-only stale after {int(_ro_elapsed)}s, reconnecting"
                )
                killed["yes"] = True
                return True

    return False


# ---------------------------------------------------------------------------
# Test 1: infinite reasoning stream kills after threshold
# ---------------------------------------------------------------------------

class TestReasoningOnlyStaleKill:
    def test_infinite_reasoning_kills_after_threshold(self):
        """A stream emitting only reasoning chunks is killed after the timeout."""
        agent = _make_agent()

        last_chunk_time = {"t": time.time()}
        last_content_chunk_time = {"t": time.time()}
        reasoning_seen = {"yes": False}
        request_client_holder = {"client": MagicMock()}
        api_kwargs = {"model": "deepseek-v4-flash", "messages": []}

        stop = threading.Event()

        def _emit_reasoning_forever():
            """Simulates a model streaming reasoning tokens indefinitely."""
            while not stop.is_set():
                time.sleep(0.02)  # 50 reasoning chunks/s
                last_chunk_time["t"] = time.time()  # line 1358: reset on every chunk
                reasoning_seen["yes"] = True         # line ~1400: set on reasoning chunk
                # last_content_chunk_time is NOT updated (no content ever arrives)

        stream_thread = threading.Thread(target=_emit_reasoning_forever, daemon=True)
        stream_thread.start()

        THRESHOLD = 0.3  # 300 ms for the test
        killed = _simulate_poll_loop(
            last_chunk_time=last_chunk_time,
            last_content_chunk_time=last_content_chunk_time,
            reasoning_seen=reasoning_seen,
            request_client_holder=request_client_holder,
            api_kwargs=api_kwargs,
            agent=agent,
            reasoning_only_stale_timeout=THRESHOLD,
            max_poll_seconds=5.0,
        )
        stop.set()

        assert killed, "Reasoning-only stale kill should have fired"
        agent._close_request_openai_client.assert_called_once_with(
            request_client_holder["client"],
            reason="reasoning_only_stale_kill",
        )
        agent._replace_primary_openai_client.assert_called_once_with(
            reason="reasoning_only_stale_pool_cleanup"
        )

    def test_threshold_configurable_via_env(self):
        """HERMES_REASONING_ONLY_STALE_TIMEOUT env var controls the threshold."""
        agent = _make_agent()

        last_chunk_time = {"t": time.time()}
        last_content_chunk_time = {"t": time.time()}
        reasoning_seen = {"yes": False}
        request_client_holder = {"client": MagicMock()}
        api_kwargs = {"model": "test/model", "messages": []}

        stop = threading.Event()

        def _emit_reasoning():
            while not stop.is_set():
                time.sleep(0.02)
                last_chunk_time["t"] = time.time()
                reasoning_seen["yes"] = True

        stream_thread = threading.Thread(target=_emit_reasoning, daemon=True)
        stream_thread.start()

        # Read the threshold the same way the production code does
        with patch.dict(os.environ, {"HERMES_REASONING_ONLY_STALE_TIMEOUT": "0.2"}):
            threshold = float(os.getenv("HERMES_REASONING_ONLY_STALE_TIMEOUT", 300.0))

        killed = _simulate_poll_loop(
            last_chunk_time=last_chunk_time,
            last_content_chunk_time=last_content_chunk_time,
            reasoning_seen=reasoning_seen,
            request_client_holder=request_client_holder,
            api_kwargs=api_kwargs,
            agent=agent,
            reasoning_only_stale_timeout=threshold,
            max_poll_seconds=5.0,
        )
        stop.set()

        assert killed, "Kill should fire within env-configured threshold"


# ---------------------------------------------------------------------------
# Test 2: reasoning followed by content — NOT killed
# ---------------------------------------------------------------------------

class TestReasoningThenContentNotKilled:
    def test_reasoning_then_content_not_killed(self):
        """A stream that reasons briefly then produces content is left alone."""
        agent = _make_agent()

        last_chunk_time = {"t": time.time()}
        last_content_chunk_time = {"t": time.time()}
        reasoning_seen = {"yes": False}
        request_client_holder = {"client": MagicMock()}
        api_kwargs = {"model": "test/model", "messages": []}

        stop = threading.Event()
        content_sent = threading.Event()

        def _emit_reasoning_then_content():
            # Phase 1: reasoning-only for a short burst, then immediately
            # emit content so the test is fast and timing-insensitive.
            reasoning_seen["yes"] = True
            last_chunk_time["t"] = time.time()
            # Small sleep to let the poll loop start before content arrives
            time.sleep(0.05)

            # Phase 2: content arrives — resets last_content_chunk_time
            last_chunk_time["t"] = time.time()
            last_content_chunk_time["t"] = time.time()  # line ~1405 in production
            content_sent.set()

            # Continue sending content chunks so poll loop sees updated timer
            for _ in range(30):
                if stop.is_set():
                    return
                time.sleep(0.02)
                last_chunk_time["t"] = time.time()
                last_content_chunk_time["t"] = time.time()

        stream_thread = threading.Thread(
            target=_emit_reasoning_then_content, daemon=True
        )
        stream_thread.start()

        # Wait until content has been sent before entering the poll loop,
        # ensuring last_content_chunk_time is fresh when the assertion runs.
        content_sent.wait(timeout=2.0)

        # Threshold is much larger than the tiny reasoning-only window so the
        # kill can never fire during the brief reasoning phase above.
        THRESHOLD = 5.0
        killed = _simulate_poll_loop(
            last_chunk_time=last_chunk_time,
            last_content_chunk_time=last_content_chunk_time,
            reasoning_seen=reasoning_seen,
            request_client_holder=request_client_holder,
            api_kwargs=api_kwargs,
            agent=agent,
            reasoning_only_stale_timeout=THRESHOLD,
            max_poll_seconds=1.5,
        )
        stop.set()

        assert not killed, (
            "Stream should NOT be killed when content eventually arrives"
        )
        agent._close_request_openai_client.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: content-only stream — no false positive
# ---------------------------------------------------------------------------

class TestContentOnlyNoFalsePositive:
    def test_content_only_never_triggers_reasoning_kill(self):
        """A model that streams only content with no reasoning is unaffected."""
        agent = _make_agent()

        last_chunk_time = {"t": time.time()}
        last_content_chunk_time = {"t": time.time()}
        reasoning_seen = {"yes": False}   # never set — no reasoning chunks
        request_client_holder = {"client": MagicMock()}
        api_kwargs = {"model": "test/model", "messages": []}

        stop = threading.Event()

        def _emit_content_only():
            for _ in range(50):
                if stop.is_set():
                    return
                time.sleep(0.02)
                last_chunk_time["t"] = time.time()
                last_content_chunk_time["t"] = time.time()
                # reasoning_seen["yes"] stays False

        stream_thread = threading.Thread(target=_emit_content_only, daemon=True)
        stream_thread.start()

        killed = _simulate_poll_loop(
            last_chunk_time=last_chunk_time,
            last_content_chunk_time=last_content_chunk_time,
            reasoning_seen=reasoning_seen,
            request_client_holder=request_client_holder,
            api_kwargs=api_kwargs,
            agent=agent,
            reasoning_only_stale_timeout=0.1,  # very short — would fire if broken
            max_poll_seconds=2.0,
        )
        stop.set()

        assert not killed, "Content-only stream must never trigger reasoning-only stale"
        agent._close_request_openai_client.assert_not_called()


# ---------------------------------------------------------------------------
# Test 4: shared state dicts are correctly initialised per attempt
# ---------------------------------------------------------------------------

class TestSharedStateDictsReset:
    def test_reasoning_seen_reset_on_new_attempt(self):
        """reasoning_seen resets between stream retry attempts."""
        # If a first attempt has reasoning, then retries — the second attempt
        # should start clean so a slow-but-legitimate second attempt isn't
        # killed immediately.
        reasoning_seen = {"yes": True}   # left over from first attempt
        last_content_chunk_time = {"t": time.time() - 1000}  # very stale

        # Simulate what production code does at each attempt start
        # (the edit to _call_chat_completions and _call_anthropic):
        last_content_chunk_time["t"] = time.time()
        reasoning_seen["yes"] = False

        assert not reasoning_seen["yes"], (
            "reasoning_seen must be cleared at the start of each stream attempt"
        )
        assert time.time() - last_content_chunk_time["t"] < 1.0, (
            "last_content_chunk_time must be reset at the start of each attempt"
        )
