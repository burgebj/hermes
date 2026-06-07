"""Regression test: Cerebras reasoning_content echo rejection (#34716).

Cerebras (``api.cerebras.ai``) emits ``reasoning_content`` on a turn-1 response
but REJECTS that field when it is echoed back in assistant message history on
the next turn::

    HTTP 400: messages.2.assistant.reasoning_content:
    property 'messages.2.assistant.reasoning_content' is unsupported
    code: wrong_api_format

This is the exact inverse of the DeepSeek / Kimi / MiMo thinking-mode
requirement (where ``reasoning_content`` MUST be replayed). Before this fix the
first branch of ``copy_reasoning_content_for_api`` forwarded any non-empty
``reasoning_content`` string verbatim, so the second message always 400'd and
multi-turn tool use was impossible on Cerebras.

The fix adds ``_rejects_reasoning_content_echo()`` (the inverse of
``_needs_thinking_reasoning_pad()``) and strips ``reasoning_content`` from the
outgoing API copy for providers that reject it.
"""

from __future__ import annotations

from run_agent import AIAgent


def _make_agent(provider: str = "", model: str = "", base_url: str = "") -> AIAgent:
    agent = object.__new__(AIAgent)
    agent.provider = provider
    agent.model = model
    agent.base_url = base_url
    agent.verbose_logging = False
    agent.reasoning_callback = None
    agent.stream_delta_callback = None
    agent._stream_callback = None
    return agent


class TestRejectsReasoningContentEcho:
    """_rejects_reasoning_content_echo() recognises Cerebras by provider and host."""

    def test_provider_cerebras(self) -> None:
        agent = _make_agent(provider="cerebras", model="gpt-oss-120b")
        assert agent._rejects_reasoning_content_echo() is True

    def test_provider_case_insensitive(self) -> None:
        agent = _make_agent(provider="Cerebras", model="zai-glm-4.7")
        assert agent._rejects_reasoning_content_echo() is True

    def test_base_url_host_custom_provider(self) -> None:
        # The issue's configuration: provider='custom', base_url at Cerebras.
        agent = _make_agent(
            provider="custom",
            model="gpt-oss-120b",
            base_url="https://api.cerebras.ai/v1",
        )
        assert agent._rejects_reasoning_content_echo() is True

    def test_base_url_bare_domain(self) -> None:
        agent = _make_agent(provider="custom", base_url="https://cerebras.ai/v1")
        assert agent._rejects_reasoning_content_echo() is True

    def test_substring_false_positive_rejected(self) -> None:
        # A host that merely contains "cerebras.ai" in its path must NOT match.
        agent = _make_agent(
            provider="custom",
            model="gpt-oss-120b",
            base_url="https://evil.com/cerebras.ai/v1",
        )
        assert agent._rejects_reasoning_content_echo() is False

    def test_non_cerebras_provider(self) -> None:
        agent = _make_agent(
            provider="openrouter",
            model="deepseek/deepseek-v4-pro",
            base_url="https://openrouter.ai/api/v1",
        )
        assert agent._rejects_reasoning_content_echo() is False

    def test_empty_everything(self) -> None:
        agent = _make_agent()
        assert agent._rejects_reasoning_content_echo() is False

    def test_result_is_cached(self) -> None:
        agent = _make_agent(provider="cerebras", model="gpt-oss-120b")
        assert agent._rejects_reasoning_content_echo() is True
        # Cache is keyed by (provider, model, base_url); a stale True cache must
        # not survive a provider change away from Cerebras.
        agent.provider = "openrouter"
        agent.base_url = "https://openrouter.ai/api/v1"
        assert agent._rejects_reasoning_content_echo() is False


class TestCopyReasoningContentStripsForCerebras:
    """copy_reasoning_content_for_api strips reasoning_content for Cerebras."""

    def test_explicit_reasoning_content_stripped(self) -> None:
        """The turn-2 failure: a stored reasoning_content string is NOT echoed."""
        agent = _make_agent(
            provider="custom",
            model="gpt-oss-120b",
            base_url="https://api.cerebras.ai/v1",
        )
        source = {
            "role": "assistant",
            "content": "Casablanca is 22C and sunny.",
            "reasoning_content": "Okay, the user asked about the weather...",
        }
        api_msg: dict = {}
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert "reasoning_content" not in api_msg

    def test_tool_call_turn_reasoning_content_stripped(self) -> None:
        """Reproduces the issue exactly: an assistant tool-call turn carrying
        reasoning_content must ship to Cerebras without it."""
        agent = _make_agent(
            provider="cerebras",
            model="zai-glm-4.7",
            base_url="https://api.cerebras.ai/v1",
        )
        source = {
            "role": "assistant",
            "content": "",
            "reasoning_content": "I should call the weather tool.",
            "tool_calls": [{"id": "call_1", "function": {"name": "web_search"}}],
        }
        api_msg = {"reasoning_content": "I should call the weather tool."}
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert "reasoning_content" not in api_msg

    def test_reasoning_field_not_promoted_for_cerebras(self) -> None:
        """The 'reasoning' field must NOT be promoted into reasoning_content."""
        agent = _make_agent(
            provider="custom",
            model="gpt-oss-120b",
            base_url="https://api.cerebras.ai/v1",
        )
        source = {
            "role": "assistant",
            "content": "answer",
            "reasoning": "chain of thought from a prior provider",
        }
        api_msg: dict = {}
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert "reasoning_content" not in api_msg

    def test_non_cerebras_preserves_reasoning_content(self) -> None:
        """Regression guard: providers that don't reject the echo keep it."""
        agent = _make_agent(
            provider="openrouter",
            model="deepseek/deepseek-v4-pro",
            base_url="https://openrouter.ai/api/v1",
        )
        source = {
            "role": "assistant",
            "content": "answer",
            "reasoning_content": "<think>real chain of thought</think>",
        }
        api_msg: dict = {}
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert api_msg.get("reasoning_content") == "<think>real chain of thought</think>"
