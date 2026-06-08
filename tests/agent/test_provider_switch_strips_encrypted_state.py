"""Regression tests for #34205 — strip provider-specific reasoning state
from session messages when the provider changes mid-session.

Without this fix, encrypted_content blobs from one provider (e.g.
codex_reasoning_items from openai-codex) survived a model switch and
poisoned every subsequent request to the new provider (e.g. xai-oauth)
with HTTP 400 invalid_encrypted_content.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_test_agent():
    """Build a minimal AIAgent stub that has _strip_provider_specific_reasoning_state
    plus the attributes switch_model touches."""
    from run_agent import AIAgent

    agent = AIAgent.__new__(AIAgent)
    agent.model = "gpt-5"
    agent.provider = "openai-codex"
    agent.base_url = "https://api.openai.com/v1"
    agent.api_mode = "codex_responses"
    agent.api_key = "sk-old"
    agent._codex_reasoning_replay_enabled = True
    agent._session_messages = []
    return agent


def test_strip_removes_codex_reasoning_items():
    agent = _make_test_agent()
    msgs = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "hello",
            "codex_reasoning_items": [{"encrypted_content": "blob1"}, {"encrypted_content": "blob2"}],
        },
    ]
    stats = agent._strip_provider_specific_reasoning_state(msgs)
    assert stats["messages"] == 1
    assert stats["items"] == 2
    assert "codex_reasoning_items" not in msgs[1]


def test_strip_removes_codex_message_items():
    agent = _make_test_agent()
    msgs = [
        {
            "role": "assistant",
            "content": "hi",
            "codex_message_items": [{"phase": "final"}],
        },
    ]
    stats = agent._strip_provider_specific_reasoning_state(msgs)
    assert stats["items"] == 1
    assert "codex_message_items" not in msgs[0]


def test_strip_removes_reasoning_details():
    """reasoning_details is the OpenRouter/Anthropic structured-reasoning
    array; it also carries encrypted_content. Other providers reject it."""
    agent = _make_test_agent()
    msgs = [
        {
            "role": "assistant",
            "content": "answer",
            "reasoning_details": [
                {"signature": "sig", "encrypted_content": "encB64"},
            ],
        },
    ]
    stats = agent._strip_provider_specific_reasoning_state(msgs)
    assert stats["items"] == 1
    assert "reasoning_details" not in msgs[0]


def test_strip_preserves_plain_reasoning_string():
    """`reasoning` and `reasoning_content` plain strings are NOT
    provider-specific — they're safe to keep across providers."""
    agent = _make_test_agent()
    msgs = [
        {
            "role": "assistant",
            "content": "answer",
            "reasoning": "step 1...",
            "reasoning_content": "step 2...",
            "codex_reasoning_items": [{"encrypted_content": "blob"}],
        },
    ]
    agent._strip_provider_specific_reasoning_state(msgs)
    assert "reasoning" in msgs[0], "plain `reasoning` string should NOT be stripped"
    assert "reasoning_content" in msgs[0], "plain `reasoning_content` string should NOT be stripped"
    assert "codex_reasoning_items" not in msgs[0]


def test_strip_disables_codex_reasoning_replay_flag():
    agent = _make_test_agent()
    agent._codex_reasoning_replay_enabled = True
    agent._strip_provider_specific_reasoning_state([])
    assert agent._codex_reasoning_replay_enabled is False


def test_strip_ignores_user_messages():
    agent = _make_test_agent()
    msgs = [
        # User messages should never have reasoning_details, but the
        # stripper should also never modify them.
        {"role": "user", "content": "hi", "reasoning_details": [{"x": 1}]},
    ]
    stats = agent._strip_provider_specific_reasoning_state(msgs)
    assert stats["messages"] == 0
    # The stripper does not touch non-assistant messages even if they
    # contain the key by mistake.
    assert "reasoning_details" in msgs[0]


def test_strip_handles_empty_list():
    agent = _make_test_agent()
    stats = agent._strip_provider_specific_reasoning_state([])
    assert stats == {"messages": 0, "items": 0}


def test_strip_handles_none_messages():
    agent = _make_test_agent()
    stats = agent._strip_provider_specific_reasoning_state(None)
    assert stats == {"messages": 0, "items": 0}


def test_strip_counts_multiple_messages():
    agent = _make_test_agent()
    msgs = [
        {"role": "user", "content": "1"},
        {"role": "assistant", "content": "a1", "codex_reasoning_items": [{"x": 1}]},
        {"role": "user", "content": "2"},
        {"role": "assistant", "content": "a2", "reasoning_details": [{"y": 2}, {"z": 3}]},
        {"role": "user", "content": "3"},
        {"role": "assistant", "content": "a3"},  # no replay state
    ]
    stats = agent._strip_provider_specific_reasoning_state(msgs)
    assert stats["messages"] == 2
    assert stats["items"] == 3


def test_switch_model_strips_state_on_provider_change():
    """End-to-end: switch_model() with a different provider should strip
    encrypted reasoning state from _session_messages."""
    from agent.agent_runtime_helpers import switch_model

    agent = _make_test_agent()
    agent._session_messages = [
        {
            "role": "assistant",
            "content": "first response",
            "codex_reasoning_items": [{"encrypted_content": "openai-blob"}],
            "reasoning_details": [{"signature": "sig", "encrypted_content": "more-openai"}],
        },
    ]
    # Stub out the heavy parts of switch_model so we can run it in
    # isolation: model_metadata, transport rebuild, anthropic adapter.
    agent._config_context_length = None
    agent._client_kwargs = {}
    agent._anthropic_client = None
    agent._anthropic_api_key = ""
    agent._anthropic_base_url = ""
    agent._is_anthropic_oauth = False
    agent.client = None
    agent._anthropic_prompt_cache_policy = MagicMock(return_value=(False, False))
    agent._ensure_lmstudio_runtime_loaded = MagicMock()
    agent.context_compressor = None
    agent._cached_system_prompt = "old"
    agent._primary_runtime = {}
    agent._create_openai_client = MagicMock(return_value=MagicMock())

    with patch("hermes_cli.providers.determine_api_mode", return_value="chat_completions"):
        switch_model(
            agent,
            new_model="grok-4.3",
            new_provider="xai-oauth",
            api_key="grok-key",
            base_url="https://api.x.ai/v1",
            api_mode="chat_completions",
        )

    # Encrypted state from the OpenAI provider is gone.
    assert "codex_reasoning_items" not in agent._session_messages[0]
    assert "reasoning_details" not in agent._session_messages[0]
    # The non-encrypted parts of the message survived.
    assert agent._session_messages[0]["content"] == "first response"
    # The new provider was applied.
    assert agent.model == "grok-4.3"
    assert agent.provider == "xai-oauth"


def test_switch_model_does_not_strip_when_provider_unchanged():
    """If the user only changes model but keeps the same provider, the
    encrypted state is still valid and must NOT be stripped."""
    from agent.agent_runtime_helpers import switch_model

    agent = _make_test_agent()
    agent.provider = "openai-codex"
    agent._session_messages = [
        {
            "role": "assistant",
            "content": "first response",
            "codex_reasoning_items": [{"encrypted_content": "blob"}],
        },
    ]
    agent._config_context_length = None
    agent._client_kwargs = {}
    agent._anthropic_client = None
    agent._anthropic_api_key = ""
    agent._anthropic_base_url = ""
    agent._is_anthropic_oauth = False
    agent.client = None
    agent._anthropic_prompt_cache_policy = MagicMock(return_value=(False, False))
    agent._ensure_lmstudio_runtime_loaded = MagicMock()
    agent.context_compressor = None
    agent._cached_system_prompt = "old"
    agent._primary_runtime = {}
    agent._create_openai_client = MagicMock(return_value=MagicMock())

    with patch("hermes_cli.providers.determine_api_mode", return_value="codex_responses"):
        switch_model(
            agent,
            new_model="gpt-5.5",  # different model, same provider
            new_provider="openai-codex",
            api_key="sk-new",
            base_url="https://api.openai.com/v1",
            api_mode="codex_responses",
        )

    # Encrypted state preserved because provider didn't change.
    assert "codex_reasoning_items" in agent._session_messages[0]
