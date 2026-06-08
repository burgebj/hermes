"""Regression tests for #34179 — direct Copilot gpt-5.5 large resumes
were killed by the 12s TTFB watchdog before Copilot's admission queue
released the first SSE event.

Fix: extend _is_openai_codex_backend to recognize provider='copilot'
and api.githubcopilot.com so the large-prefill TTFB exemption applies
to them too.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest


def _make_agent(provider: str = "", base_url: str = "", api_mode: str = "codex_responses"):
    """Build a minimal agent stub with the fields _is_openai_codex_backend reads."""
    agent = SimpleNamespace(
        provider=provider,
        api_mode=api_mode,
        base_url=base_url,
        _base_url_lower=base_url.lower(),
        _base_url_hostname=base_url.replace("https://", "").replace("http://", "").split("/")[0].lower(),
    )
    return agent


def test_openai_codex_provider_recognized():
    """Pre-existing behavior: provider='openai-codex' is still treated as
    a codex backend."""
    from agent.chat_completion_helpers import _is_openai_codex_backend

    agent = _make_agent(provider="openai-codex", base_url="https://chatgpt.com/backend-api/codex")
    assert _is_openai_codex_backend(agent) is True


def test_chatgpt_codex_url_recognized():
    """Pre-existing behavior: chatgpt.com/backend-api/codex URL is still
    treated as a codex backend even without the provider name."""
    from agent.chat_completion_helpers import _is_openai_codex_backend

    agent = _make_agent(provider="custom", base_url="https://chatgpt.com/backend-api/codex/v1")
    assert _is_openai_codex_backend(agent) is True


def test_copilot_provider_now_recognized():
    """#34179 fix: provider='copilot' is now treated as a codex-like backend
    so the large-prefill TTFB exemption applies."""
    from agent.chat_completion_helpers import _is_openai_codex_backend

    agent = _make_agent(provider="copilot", base_url="https://api.githubcopilot.com")
    assert _is_openai_codex_backend(agent) is True


def test_githubcopilot_url_now_recognized():
    """#34179 fix: api.githubcopilot.com URL is now treated as codex-like
    even when the provider name is generic ('custom', 'openai', etc.)."""
    from agent.chat_completion_helpers import _is_openai_codex_backend

    agent = _make_agent(provider="custom", base_url="https://api.githubcopilot.com/v1")
    assert _is_openai_codex_backend(agent) is True


def test_unrelated_backend_still_false():
    """Don't regress: OpenAI direct, OpenRouter, etc. are NOT codex backends."""
    from agent.chat_completion_helpers import _is_openai_codex_backend

    for provider, base_url in [
        ("openai", "https://api.openai.com/v1"),
        ("openrouter", "https://openrouter.ai/api/v1"),
        ("anthropic", "https://api.anthropic.com"),
        ("xai-oauth", "https://api.x.ai/v1"),
        ("custom", "https://my-self-hosted.example.com/v1"),
    ]:
        agent = _make_agent(provider=provider, base_url=base_url)
        assert _is_openai_codex_backend(agent) is False, (
            f"{provider} @ {base_url} should NOT be treated as codex backend"
        )


def test_empty_agent_safe():
    """Defensive: empty provider + empty base_url returns False without crashing."""
    from agent.chat_completion_helpers import _is_openai_codex_backend

    agent = _make_agent(provider="", base_url="")
    assert _is_openai_codex_backend(agent) is False
