"""Regression tests for empty content normalization to None (issue #11906).

Anthropic proxies reject empty-string content with HTTP 400.  The fix
normalizes falsy assistant content to None in _build_assistant_message().
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from run_agent import AIAgent


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


def _mock_msg(content="Hello", tool_calls=None):
    return SimpleNamespace(content=content, tool_calls=tool_calls)


@pytest.fixture()
def agent():
    with (
        patch("run_agent.get_tool_definitions", return_value=_make_tool_defs("web_search")),
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
    return a


class TestEmptyContentNormalization:
    """Test that _build_assistant_message normalizes empty content to None."""

    def test_normalizes_empty_string_to_none(self, agent):
        """Empty string content must become None to avoid Anthropic HTTP 400."""
        msg = _mock_msg(content="")
        result = agent._build_assistant_message(msg, "stop")
        assert result["content"] is None

    def test_preserves_nonempty_content(self, agent):
        """Non-empty content passes through unchanged."""
        msg = _mock_msg(content="hello")
        result = agent._build_assistant_message(msg, "stop")
        assert result["content"] == "hello"

    def test_preserves_none_content(self, agent):
        """None content stays None."""
        msg = _mock_msg(content=None)
        result = agent._build_assistant_message(msg, "stop")
        assert result["content"] is None

    def test_whitespace_only_content_becomes_none(self, agent):
        """Whitespace-only content is stripped first, then normalized to None.

        The real code path strips think blocks + whitespace before checking
        for empty content, so '   ' → '' → None.
        """
        msg = _mock_msg(content="   ")
        result = agent._build_assistant_message(msg, "stop")
        assert result["content"] is None
