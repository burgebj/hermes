"""Pin the cascade-saturation bailout in preflight compression.

When a session's pre-API-call token estimate exceeds the compression
threshold AND the 3-pass preflight cascade can't get back under,
``run_conversation`` used to silently continue into the main while loop
— at which point the first API call would return context-overflow,
the post-API recovery chain would also saturate, the function would
return ``compression_exhausted=True`` after wasting 4+ seconds of
doomed work, and (per oneshot.py's bug A) wrappers would never see the
error.

Audit of one user's ``~/.hermes/state.db`` found 103 incidents in 20
days (76 in the last 24h) with this exact fingerprint on the
qwen3.6-35b-a3b model: compression chain depth = exactly 3 (the
``range(3)`` cap), parent session ``api_call_count = 0`` AND
``message_count = 0`` (a transient compression-only stub), then a
child session with messages bulk-loaded and the process dying before
any new API call.

After this fix, the preflight loop sets a ``_preflight_saturated``
flag in two cases:

1. ``len(messages) >= _orig_len`` after a ``_compress_context`` call —
   compression made no progress, we know we're still over threshold
   (we entered the block precisely because we were).
2. The 3-pass ``for`` loop completes without ever hitting the
   under-threshold break (``for ... else`` clause).

When the flag is set, ``run_conversation`` returns a structured
failed-result dict immediately (same shape as the existing
post-API-call compression-exhausted return paths) so callers see a
clean failure at session start instead of after the doomed first API
call.
"""

import pytest

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.context_compressor import SUMMARY_PREFIX
from run_agent import AIAgent
import run_agent


@pytest.fixture(autouse=True)
def _no_compression_sleep(monkeypatch):
    """Short-circuit the 2s ``time.sleep`` between compression retries
    so tests don't burn real wall-time."""
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda *_a, **_k: None)
    monkeypatch.setattr(run_agent, "jittered_backoff", lambda *a, **k: 0.0)


def _make_tool_defs(*names):
    return [
        {
            "type": "function",
            "function": {
                "name": n,
                "description": f"{n} tool",
                "parameters": {"type": "object", "properties": {}},
            },
        }
        for n in names
    ]


@pytest.fixture()
def agent():
    """AIAgent fixture mirrors test_413_compression.py's setup so the
    preflight code path runs through the same code without any real
    network or DB hits."""
    with (
        patch("run_agent.get_tool_definitions",
              return_value=_make_tool_defs("web_search")),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        a = AIAgent(
            api_key="test-key-1234567890",
            base_url="https://openrouter.ai/api/v1",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )
        a.client = MagicMock()
        a._cached_system_prompt = "You are helpful."
        a._use_prompt_caching = False
        a.tool_delay = 0
        a.compression_enabled = True
        a.save_trajectories = False
        # Set a small context so a moderately-sized history triggers
        # preflight, and a generous threshold so 3 passes are needed
        # to exhaust the cap.
        a.context_compressor.context_length = 2000
        a.context_compressor.threshold_tokens = 200
        return a


def _make_big_history():
    """40 messages large enough to push estimate over 200-token threshold."""
    h = []
    for i in range(20):
        h.append({"role": "user",
                   "content": f"Message number {i} with extra text padding"})
        h.append({"role": "assistant",
                   "content": f"Response number {i} with extra text padding"})
    return h


class TestPreflightCascadeSaturation:
    """Bug B (this PR): preflight must bail with a structured
    failed-result dict when 3 passes can't get under threshold."""

    def test_compression_no_progress_triggers_bailout(self, agent):
        """When ``_compress_context`` returns the same (or more)
        messages, preflight should bail immediately on the first
        pass rather than continuing into the main loop.
        """
        big_history = _make_big_history()

        with (
            # side_effect returns the INPUT messages unchanged so
            # ``len(messages) >= _orig_len`` triggers the no-progress
            # break on the very first pass. (Setting return_value to a
            # fixed list of length 40 doesn't fire the break because
            # the caller passes in 41 messages — history + the new
            # user message.)
            patch.object(
                agent, "_compress_context",
                side_effect=lambda msgs, sysm, **kw: (
                    list(msgs), "still long system prompt",
                ),
            ) as mock_compress,
            patch.object(agent, "_persist_session"),
            patch.object(agent, "_save_trajectory"),
            patch.object(agent, "_cleanup_task_resources"),
        ):
            result = agent.run_conversation(
                "hello", conversation_history=big_history,
            )

        # Only one compress attempt should fire — the no-progress
        # check breaks immediately.
        assert mock_compress.call_count == 1, (
            f"expected 1 compress attempt (no-progress break), "
            f"got {mock_compress.call_count}"
        )
        # The API call must NEVER happen — the bailout returns before
        # the main while loop.
        agent.client.chat.completions.create.assert_not_called()
        # Structured failed-result dict.
        assert result["failed"] is True
        assert result["partial"] is True
        assert result["compression_exhausted"] is True
        assert result["api_calls"] == 0
        assert "Preflight compression saturated" in result["error"]
        assert "1 compression pass" in result["error"]

    def test_three_pass_exhaustion_triggers_bailout(self, agent):
        """When all 3 passes reduce messages by a tiny amount but
        never get under threshold, preflight should bail after the
        third pass.
        """
        big_history = _make_big_history()

        # Each compression pass shrinks by exactly 2 messages.
        # 40 → 38 → 36 → 34, but the threshold logic is driven by the
        # token estimate, which our patched estimate keeps "over" the
        # threshold for all three passes.
        compress_call_counter = {"n": 0}

        def fake_compress(messages, system_message, **kwargs):
            compress_call_counter["n"] += 1
            return (messages[2:], "compressed prompt")

        with (
            patch.object(agent, "_compress_context",
                          side_effect=fake_compress) as mock_compress,
            patch.object(agent, "_persist_session"),
            patch.object(agent, "_save_trajectory"),
            patch.object(agent, "_cleanup_task_resources"),
            # Pin the post-compression estimate ABOVE the threshold so
            # the under-threshold break never fires.
            patch(
                "agent.conversation_loop.estimate_request_tokens_rough",
                return_value=300,  # > 200 threshold
            ),
        ):
            result = agent.run_conversation(
                "hello", conversation_history=big_history,
            )

        # All 3 passes should have run before the for-else bailout.
        assert compress_call_counter["n"] == 3, (
            f"expected exactly 3 compress attempts (for-else bailout), "
            f"got {compress_call_counter['n']}"
        )
        # API call still never happens.
        agent.client.chat.completions.create.assert_not_called()
        assert result["failed"] is True
        assert result["compression_exhausted"] is True
        assert "3 compression pass" in result["error"]

    def test_under_threshold_after_one_pass_does_not_bail(self, agent):
        """Sanity: if the first pass gets under threshold, preflight
        must NOT bail — the main while loop continues normally."""
        big_history = _make_big_history()

        from tests.run_agent.test_413_compression import _mock_response
        agent.client.chat.completions.create.side_effect = [
            _mock_response(content="OK", finish_reason="stop"),
        ]

        # Patch estimate_request_tokens_rough so the pre-compression
        # estimate is over threshold (enters the preflight block) but
        # the post-compression estimate is under threshold (the
        # under-threshold break fires after exactly one pass). Without
        # the patch, the tool-schema tokens push every estimate above
        # 200, and saturation would fire instead.
        estimate_calls = {"n": 0}

        def fake_estimate(messages, **kwargs):
            estimate_calls["n"] += 1
            return 800 if estimate_calls["n"] == 1 else 50

        with (
            patch.object(agent, "_compress_context") as mock_compress,
            patch.object(agent, "_persist_session"),
            patch.object(agent, "_save_trajectory"),
            patch.object(agent, "_cleanup_task_resources"),
            patch(
                "agent.conversation_loop.estimate_request_tokens_rough",
                side_effect=fake_estimate,
            ),
        ):
            # Compress to a tiny tape (any length < input is enough,
            # estimate patch decides the under-threshold break).
            mock_compress.return_value = (
                [
                    {"role": "user",
                      "content": f"{SUMMARY_PREFIX}\nPrior turn"},
                    {"role": "user", "content": "hi"},
                ],
                "compressed prompt",
            )
            result = agent.run_conversation(
                "hello", conversation_history=big_history,
            )

        # One compress call (under-threshold break fires immediately).
        assert mock_compress.call_count == 1
        # API call DOES happen.
        agent.client.chat.completions.create.assert_called_once()
        assert result["completed"] is True
        assert result["final_response"] == "OK"
        assert not result.get("compression_exhausted")

    def test_bailout_persists_session_before_returning(self, agent):
        """The bailout must call ``_persist_session`` so the partial
        compressed-message tape isn't lost — same as the existing
        post-API-call exhaustion return paths.
        """
        big_history = _make_big_history()

        with (
            patch.object(agent, "_compress_context") as mock_compress,
            patch.object(agent, "_persist_session") as mock_persist,
            patch.object(agent, "_save_trajectory"),
            patch.object(agent, "_cleanup_task_resources"),
        ):
            mock_compress.return_value = (
                list(big_history), "no-progress prompt",
            )
            result = agent.run_conversation(
                "hello", conversation_history=big_history,
            )

        # Must have persisted before the bailout return.
        mock_persist.assert_called()
        assert result["compression_exhausted"] is True

    def test_bailout_emits_warning_to_status_callback(self, agent):
        """The bailout must surface a human-readable warning via
        ``agent._emit_warning`` so the gateway/CLI shows the operator
        a real reason instead of an opaque failure.
        """
        big_history = _make_big_history()
        warnings = []

        # _emit_warning routes through emit_warning_callback, which
        # falls back to printing if no callback set. Patch the agent's
        # _emit_warning directly to capture.
        with (
            patch.object(agent, "_compress_context") as mock_compress,
            patch.object(agent, "_persist_session"),
            patch.object(agent, "_save_trajectory"),
            patch.object(agent, "_cleanup_task_resources"),
            patch.object(
                agent, "_emit_warning",
                side_effect=lambda msg: warnings.append(msg),
            ),
        ):
            mock_compress.return_value = (
                list(big_history), "still long",
            )
            agent.run_conversation(
                "hello", conversation_history=big_history,
            )

        assert any(
            "Preflight compression saturated" in w for w in warnings
        ), f"expected a saturation warning, got {warnings!r}"
