"""Regression test for RLM _rlm_env initialization in refresh_context.

Bug: on_session_start() only initialized _rlm_env when kwargs.get("rlm_context")
was truthy. In normal agent flow it is not passed. refresh_context() only mutated
an existing _rlm_env, never created one. Result: rlm_peek / rlm_grep / rlm_partition
always returned "No context loaded".

Fix: in refresh_context(), if _rlm_env is None and context was built, call
self._init_rlm_env(context) to create it on first call.
"""
import json
import pytest

from plugins.context_engine.rlm import RlmContextEngine


class TestRlmRefreshContextInit:
    def test_rlm_peek_returns_content_after_refresh(self):
        """After on_session_start (no rlm_context) + refresh_context, rlm_peek
        should return real content, not 'No context loaded'."""
        plugin = RlmContextEngine()
        plugin.on_session_start(session_id="test-session-1")

        messages = [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris."},
        ]
        plugin.refresh_context(messages)

        result_json = plugin.handle_tool_call("rlm_peek", {"start": 0, "length": 500})
        result = json.loads(result_json)

        assert "error" not in result, f"Expected content but got error: {result}"
        assert "snippet" in result
        assert len(result["snippet"]) > 0
        assert "France" in result["snippet"] or "Paris" in result["snippet"]

    def test_rlm_env_initialized_after_refresh(self):
        """_rlm_env should be None before refresh, non-None after."""
        plugin = RlmContextEngine()
        plugin.on_session_start(session_id="test-session-2")

        assert plugin._rlm_env is None

        messages = [{"role": "user", "content": "Hello world"}]
        plugin.refresh_context(messages)

        assert plugin._rlm_env is not None
        assert plugin._session_context is not None

    def test_rlm_grep_returns_matches_after_refresh(self):
        """rlm_grep should find matches from the refreshed context."""
        plugin = RlmContextEngine()
        plugin.on_session_start(session_id="test-session-3")

        messages = [
            {"role": "user", "content": "error: something went wrong"},
            {"role": "assistant", "content": "I see the error in your code."},
        ]
        plugin.refresh_context(messages)

        result_json = plugin.handle_tool_call("rlm_grep", {"pattern": "error"})
        result = json.loads(result_json)

        assert "error" not in result or result.get("error") is None, f"Got error: {result}"
        assert "matches" in result
        assert result["total_found"] >= 1

    def test_rlm_context_passed_via_on_session_start_still_works(self):
        """The original path (rlm_context in kwargs) should still work."""
        plugin = RlmContextEngine()
        plugin.on_session_start(
            session_id="test-session-4",
            rlm_context="Pre-loaded context content here."
        )

        assert plugin._rlm_env is not None
        result_json = plugin.handle_tool_call("rlm_peek", {"start": 0, "length": 100})
        result = json.loads(result_json)
        assert "snippet" in result
        assert "Pre-loaded" in result["snippet"]

    def test_refresh_context_updates_existing_env(self):
        """When _rlm_env already exists, refresh_context updates it in place."""
        plugin = RlmContextEngine()
        plugin.on_session_start(
            session_id="test-session-5",
            rlm_context="Old context."
        )
        first_env = plugin._rlm_env

        plugin.refresh_context([{"role": "user", "content": "New context content."}])

        # Same object is updated, not replaced
        assert plugin._rlm_env is first_env
        assert "New context content" in plugin._session_context
