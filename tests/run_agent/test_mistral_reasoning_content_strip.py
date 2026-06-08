"""Regression: Mistral rejects ``reasoning_content`` echo on replayed history.

When the agent falls back to Mistral after a reasoning-capable provider
(e.g. Gemini / Codex) populated assistant turns with ``reasoning_content``,
Mistral's strict API returns HTTP 422 (``extra_forbidden`` on
``messages[].reasoning_content``). The turn then cascades down the fallback
chain to a weaker last-resort model, visibly degrading answer quality.

``copy_reasoning_content_for_api`` must strip ``reasoning_content`` for
providers that reject it, while leaving DeepSeek/Kimi/MiMo (which *require*
the echo) and OpenRouter (which may route to a thinking model) untouched.
"""

from __future__ import annotations

from run_agent import AIAgent


def _make_agent(provider: str = "", model: str = "", base_url: str = "") -> AIAgent:
    agent = object.__new__(AIAgent)
    agent.provider = provider
    agent.model = model
    agent.base_url = base_url  # property setter also populates _base_url_lower
    agent.verbose_logging = False
    agent.reasoning_callback = None
    agent.stream_delta_callback = None
    agent._stream_callback = None
    return agent


class TestRejectsReasoningContentDetector:
    def test_matches_mistral_provider(self) -> None:
        agent = _make_agent(provider="mistral", model="mistral-small-latest")
        assert agent._rejects_reasoning_content_echo() is True

    def test_matches_mistral_host_with_custom_provider(self) -> None:
        agent = _make_agent(
            provider="custom",
            model="mistral-small-latest",
            base_url="https://api.mistral.ai/v1/",
        )
        assert agent._rejects_reasoning_content_echo() is True

    def test_matches_groq_host_with_custom_provider(self) -> None:
        # Groq rejects reasoning_content with HTTP 400 'unsupported'; it is
        # configured as a custom provider, so detection is host-based.
        agent = _make_agent(
            provider="custom",
            model="llama-3.3-70b-versatile",
            base_url="https://api.groq.com/openai/v1",
        )
        assert agent._rejects_reasoning_content_echo() is True

    def test_excludes_deepseek(self) -> None:
        agent = _make_agent(provider="deepseek", model="deepseek-v4-flash")
        assert agent._rejects_reasoning_content_echo() is False

    def test_excludes_openrouter(self) -> None:
        agent = _make_agent(
            provider="openrouter",
            model="anthropic/claude-sonnet-4.6",
            base_url="https://openrouter.ai/api/v1",
        )
        assert agent._rejects_reasoning_content_echo() is False


class TestMistralStripsReasoningContentOnReplay:
    def test_inherited_reasoning_content_stripped(self) -> None:
        """``api_msg`` starts as a copy of the source (carrying
        reasoning_content). The helper must remove it for Mistral so the
        replayed request does not 422."""
        agent = _make_agent(provider="mistral", model="mistral-small-latest")
        source = {
            "role": "assistant",
            "content": "ok",
            "reasoning_content": "prior provider chain of thought",
        }
        api_msg = dict(source)  # mirrors `api_msg = msg.copy()` in the loop
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert "reasoning_content" not in api_msg

    def test_reasoning_field_not_promoted(self) -> None:
        """A bare ``reasoning`` field must not be promoted to
        ``reasoning_content`` for Mistral either."""
        agent = _make_agent(provider="mistral", model="mistral-small-latest")
        source = {"role": "assistant", "content": "ok", "reasoning": "thought trace"}
        api_msg = dict(source)
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert "reasoning_content" not in api_msg

    def test_tool_call_turn_reasoning_content_stripped(self) -> None:
        agent = _make_agent(provider="mistral", model="mistral-small-latest")
        source = {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "c1", "type": "function",
                            "function": {"name": "x", "arguments": "{}"}}],
            "reasoning_content": "leaked trace",
        }
        api_msg = dict(source)
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert "reasoning_content" not in api_msg


class TestThinkingProvidersUnaffected:
    def test_deepseek_still_preserves_reasoning_content(self) -> None:
        agent = _make_agent(provider="deepseek", model="deepseek-v4-flash")
        source = {
            "role": "assistant",
            "content": "ok",
            "reasoning_content": "<think>real chain of thought</think>",
        }
        api_msg = dict(source)
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert api_msg["reasoning_content"] == "<think>real chain of thought</think>"

    def test_deepseek_poisoned_history_still_padded(self) -> None:
        agent = _make_agent(provider="deepseek", model="deepseek-v4-flash")
        source = {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "c1", "type": "function",
                            "function": {"name": "x", "arguments": "{}"}}],
        }
        api_msg = dict(source)
        agent._copy_reasoning_content_for_api(source, api_msg)
        assert api_msg.get("reasoning_content") == " "
