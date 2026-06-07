"""Tests for memory.review_on_reset / review_on_session_end / review_on_compression (#31597).

Each flag gates a call to ``_spawn_background_review`` at the matching
session boundary.  Tests exercise the *real* code paths
(``HermesCLI.new_session``, ``AIAgent.shutdown_memory_provider``,
``compress_context``) rather than re-implementing the wiring.
"""

from __future__ import annotations

import threading
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# review_on_reset — HermesCLI.new_session
# ---------------------------------------------------------------------------

class TestReviewOnReset:
    """``HermesCLI.new_session`` spawns a background review when the flag is on."""

    @patch("hermes_cli.plugins.invoke_hook")
    def test_spawns_review_when_flag_set(self, _mock_hook):
        from cli import HermesCLI

        cli = HermesCLI()
        cli.agent = MagicMock()
        cli.agent.session_id = "old-session-id"
        cli.agent._memory_review_on_reset = True
        cli.conversation_history = [{"role": "user", "content": "hello"}]

        cli.new_session(silent=True)

        cli.agent._spawn_background_review.assert_called_once()
        args, kwargs = cli.agent._spawn_background_review.call_args
        assert kwargs.get("review_memory") is True

    @patch("hermes_cli.plugins.invoke_hook")
    def test_no_review_when_flag_off(self, _mock_hook):
        from cli import HermesCLI

        cli = HermesCLI()
        cli.agent = MagicMock()
        cli.agent.session_id = "old-session-id"
        cli.agent._memory_review_on_reset = False
        cli.conversation_history = []

        cli.new_session(silent=True)

        cli.agent._spawn_background_review.assert_not_called()

    @patch("hermes_cli.plugins.invoke_hook")
    def test_spawn_exception_does_not_break_reset(self, _mock_hook):
        """A raising ``_spawn_background_review`` must not abort /new."""
        from cli import HermesCLI

        cli = HermesCLI()
        cli.agent = MagicMock()
        cli.agent.session_id = "old-session-id"
        cli.agent._memory_review_on_reset = True
        cli.agent._spawn_background_review.side_effect = RuntimeError("boom")
        cli.conversation_history = []

        # Must not raise — the new session must still be created.
        cli.new_session(silent=True)


# ---------------------------------------------------------------------------
# review_on_session_end — AIAgent.shutdown_memory_provider
# ---------------------------------------------------------------------------

def _bare_agent():
    """Build a minimal AIAgent without running __init__."""
    from run_agent import AIAgent

    agent = object.__new__(AIAgent)
    agent._memory_manager = None
    agent.context_compressor = None
    agent.session_id = "test-session"
    return agent


class TestReviewOnSessionEnd:
    """``shutdown_memory_provider`` spawns a non-daemon, joined review thread."""

    def test_spawns_non_daemon_thread_when_flag_set(self, monkeypatch):
        agent = _bare_agent()
        agent._memory_review_on_session_end = True

        captured = {}

        def fake_spawn(ag, msgs, *, review_memory=False, review_skills=False):
            captured["agent"] = ag
            captured["messages"] = list(msgs)
            captured["review_memory"] = review_memory
            captured["ran"] = False
            return (lambda: captured.__setitem__("ran", True)), "prompt"

        import agent.background_review as br_mod
        monkeypatch.setattr(br_mod, "spawn_background_review_thread", fake_spawn)

        spawned = []
        orig_thread_cls = threading.Thread

        def capturing_thread(*args, **kwargs):
            t = orig_thread_cls(*args, **kwargs)
            spawned.append((t, kwargs))
            return t

        import run_agent as ra
        monkeypatch.setattr(ra.threading, "Thread", capturing_thread)

        messages = [{"role": "user", "content": "bye"}]
        agent.shutdown_memory_provider(messages)

        assert len(spawned) == 1
        _, kwargs = spawned[0]
        assert kwargs.get("daemon") is True
        assert kwargs.get("name") == "bg-review-session-end"
        assert captured["review_memory"] is True
        assert captured["messages"] == messages
        # join(timeout=10) must have run; thread target executed inline-fast.
        assert captured["ran"] is True

    def test_no_thread_when_flag_is_false(self, monkeypatch):
        agent = _bare_agent()
        agent._memory_review_on_session_end = False

        spawned = []
        orig_thread_cls = threading.Thread

        def capturing_thread(*args, **kwargs):
            t = orig_thread_cls(*args, **kwargs)
            spawned.append(t)
            return t

        import run_agent as ra
        monkeypatch.setattr(ra.threading, "Thread", capturing_thread)

        agent.shutdown_memory_provider([])

        assert spawned == []

    def test_spawn_exception_does_not_break_shutdown(self, monkeypatch):
        """A raising spawn must not prevent the rest of shutdown from running."""
        agent = _bare_agent()
        agent._memory_review_on_session_end = True

        # Add a real memory_manager so we can verify on_session_end still runs.
        agent._memory_manager = MagicMock()

        import agent.background_review as br_mod
        monkeypatch.setattr(
            br_mod, "spawn_background_review_thread",
            MagicMock(side_effect=RuntimeError("explode")),
        )

        agent.shutdown_memory_provider([])  # must not raise
        agent._memory_manager.on_session_end.assert_called_once()
        agent._memory_manager.shutdown_all.assert_called_once()


# ---------------------------------------------------------------------------
# review_on_compression — agent.conversation_compression.compress_context
# ---------------------------------------------------------------------------

class TestReviewOnCompression:
    """``compress_context`` triggers background review before discarding messages."""

    def _make_agent(self, *, review_on_compression):
        agent = MagicMock()
        agent._memory_review_on_compression = review_on_compression
        agent._memory_manager = None
        agent._compression_feasibility_checked = True
        agent._compression_warning = None
        agent.session_id = "s"
        agent.model = "fake"
        agent.status_callback = None
        # Force the compressor into the "aborted" early-return branch so we
        # exercise the review trigger without running the full post-compression
        # session-rotation path (which needs many more agent attributes).
        agent.context_compressor = MagicMock()
        agent.context_compressor.compress.side_effect = lambda msgs, **kw: msgs
        agent.context_compressor._last_compress_aborted = True
        agent.context_compressor._last_summary_error = "test-abort"
        agent._cached_system_prompt = "cached-sys"
        agent._last_compression_summary_warning = None
        agent._emit_status = MagicMock()
        agent._emit_warning = MagicMock()
        return agent

    def test_spawns_review_when_flag_set(self):
        from agent.conversation_compression import compress_context

        messages = [{"role": "user", "content": "lots of context"}]
        agent = self._make_agent(review_on_compression=True)

        compress_context(agent, messages, system_message="sys")

        agent._spawn_background_review.assert_called_once()
        args, kwargs = agent._spawn_background_review.call_args
        assert kwargs.get("review_memory") is True
        # Snapshot must be a copy so subsequent compression cannot mutate it.
        passed_messages = args[0]
        assert passed_messages == messages
        assert passed_messages is not messages

    def test_no_review_when_flag_off(self):
        from agent.conversation_compression import compress_context

        messages = [{"role": "user", "content": "x"}]
        agent = self._make_agent(review_on_compression=False)

        compress_context(agent, messages, system_message="sys")

        agent._spawn_background_review.assert_not_called()

    def test_spawn_exception_does_not_break_compression(self):
        from agent.conversation_compression import compress_context

        messages = [{"role": "user", "content": "x"}]
        agent = self._make_agent(review_on_compression=True)
        agent._spawn_background_review.side_effect = RuntimeError("boom")

        # Must not raise; compression still proceeds.
        compress_context(agent, messages, system_message="sys")
        agent.context_compressor.compress.assert_called_once()
