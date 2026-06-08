"""Session environment propagation regression tests."""

import os
from unittest.mock import MagicMock, patch

from run_agent import AIAgent


def _agent(**kwargs):
    defaults = {
        "api_key": "test-key",
        "base_url": "https://example.test/v1",
        "model": "test/model",
        "quiet_mode": True,
        "skip_context_files": True,
        "skip_memory": True,
    }
    defaults.update(kwargs)
    return AIAgent(**defaults)


@patch("run_agent.OpenAI")
def test_top_level_agent_publishes_session_id_to_environment(mock_openai, monkeypatch):
    mock_openai.return_value = MagicMock()
    monkeypatch.delenv("HERMES_SESSION_ID", raising=False)

    agent = _agent(session_id="parent-session")

    assert getattr(agent, "session_id") == "parent-session"
    assert os.environ["HERMES_SESSION_ID"] == "parent-session"


@patch("run_agent.OpenAI")
def test_subagent_session_id_does_not_clobber_parent_environment(mock_openai, monkeypatch):
    mock_openai.return_value = MagicMock()
    monkeypatch.setenv("HERMES_SESSION_ID", "parent-session")

    child = _agent(session_id="child-session", parent_session_id="parent-session")

    assert getattr(child, "session_id") == "child-session"
    assert getattr(child, "_parent_session_id") == "parent-session"
    assert os.environ["HERMES_SESSION_ID"] == "parent-session"
