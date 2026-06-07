"""Regression guardrail for issue #36693: when ``api_mode == "anthropic_messages"``
(e.g. bedrock + Claude), ``_replace_primary_openai_client`` must short-circuit
to a no-op success instead of falling through to the OpenAI factory.

Background. In ``agent/agent_init.py`` the bedrock + Claude path explicitly
sets ``agent.client = None`` and ``agent._client_kwargs = {}``; all real
requests flow through ``agent._anthropic_client`` (an AnthropicBedrock SDK
instance). There is no shared OpenAI client to rebuild on this provider.

Without the guard, every rebuild trigger — stale_stream_pool_cleanup,
``<provider>_credential_refresh``, ``nous_credential_refresh``,
``copilot_credential_refresh``, ``credential_rotation``,
``dead_connection_cleanup``, ``fallback_timeout_apply``, and
``recreate_closed:*`` — falls through to ``OpenAI(**{})`` and emits a
misleading::

    WARNING run_agent: Failed to rebuild shared OpenAI client (...)
      provider=bedrock model=us.anthropic.claude-opus-4-7
      error=The api_key client option must be set ... or by setting the
            OPENAI_API_KEY environment variable

These tests pin the contract: under ``api_mode == "anthropic_messages"``,
``_replace_primary_openai_client`` returns ``True`` without invoking the
OpenAI factory at all, regardless of which trigger reason is supplied.
"""
from unittest.mock import patch

from run_agent import AIAgent


def _make_bedrock_like_agent():
    """Build a minimal agent stand-in that mirrors the bedrock + Claude
    runtime state set up by ``agent_init.py``: ``api_mode`` is
    ``anthropic_messages``, ``client`` is ``None``, and ``_client_kwargs``
    is the empty dict.
    """
    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="test/model",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    agent.api_mode = "anthropic_messages"
    agent.provider = "bedrock"
    agent.client = None
    agent._client_kwargs = {}
    return agent


def test_replace_primary_openai_client_short_circuits_for_anthropic_messages():
    """The rebuild entrypoint must return ``True`` without calling the OpenAI
    factory when ``api_mode == "anthropic_messages"``.

    If this test starts failing, either the api_mode-check guard was removed
    or the rebuild entrypoint was reorganised so the guard no longer fires
    before the factory call. Either way, issue #36693 has regressed and the
    bedrock + Claude session log will start emitting "OPENAI_API_KEY missing"
    warnings on every stale-stream / credential-refresh trigger.
    """
    agent = _make_bedrock_like_agent()

    with patch("run_agent.AIAgent._create_openai_client") as mock_create:
        ok = agent._replace_primary_openai_client(reason="stale_stream_pool_cleanup")

    assert ok is True, (
        "_replace_primary_openai_client should return True (no-op success) "
        "for anthropic_messages api_mode"
    )
    assert mock_create.call_count == 0, (
        "_replace_primary_openai_client must NOT call the OpenAI client "
        "factory when api_mode == 'anthropic_messages' "
        f"(got {mock_create.call_count} call(s))"
    )
    # And the no-op rebuild must not corrupt the bedrock invariant.
    assert agent.client is None, (
        "agent.client should remain None on the anthropic_messages path; "
        "the rebuild no-op must not overwrite it"
    )


def test_replace_primary_openai_client_short_circuits_for_all_rebuild_reasons():
    """Every known rebuild trigger must short-circuit on anthropic_messages.

    The fix lives in one place (``_replace_primary_openai_client`` entry),
    but the bug surfaces from at least eight call-sites across run_agent.py
    and agent/chat_completion_helpers.py. Walk through every reason string
    we've seen in the codebase to confirm the guard covers all of them.
    """
    reasons = [
        "stale_stream_pool_cleanup",
        "bedrock_credential_refresh",
        "nous_credential_refresh",
        "copilot_credential_refresh",
        "credential_rotation",
        "dead_connection_cleanup",
        "fallback_timeout_apply",
        "recreate_closed:codex_stream_direct",
    ]

    for reason in reasons:
        agent = _make_bedrock_like_agent()
        with patch("run_agent.AIAgent._create_openai_client") as mock_create:
            ok = agent._replace_primary_openai_client(reason=reason)
        assert ok is True, f"reason={reason!r} did not short-circuit"
        assert mock_create.call_count == 0, (
            f"reason={reason!r} fell through to the OpenAI factory "
            "(expected short-circuit on anthropic_messages api_mode)"
        )


def test_replace_primary_openai_client_still_rebuilds_for_openai_api_mode():
    """Sanity check: the guard must not fire for non-anthropic_messages
    api_modes. A regular OpenAI / OpenRouter session should still rebuild
    via the factory path.
    """
    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="test/model",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )
    # Default api_mode for the OpenRouter path is the chat-completions mode,
    # not anthropic_messages. Pin it explicitly so this test is independent
    # of init-time defaults.
    agent.api_mode = "chat_completions"
    agent._client_kwargs = {
        "api_key": "test-key-value",
        "base_url": "https://api.example.com/v1",
    }

    with patch("run_agent.AIAgent._create_openai_client") as mock_create:
        mock_create.return_value = object()  # opaque non-None replacement
        ok = agent._replace_primary_openai_client(reason="credential_rotation")

    assert ok is True
    assert mock_create.call_count == 1, (
        "Non-anthropic_messages rebuild must still go through the factory; "
        f"got {mock_create.call_count} call(s)"
    )
