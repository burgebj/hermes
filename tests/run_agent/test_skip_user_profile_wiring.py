"""Integration guard for the identity-isolation gate.

`gateway/run.py` computes `skip_user_profile` from the inbound source
(`_should_skip_user_profile_for_source`) so that non-owner contacts never get
the owner-describing USER.md injected as "USER PROFILE (who the user is)".

That boolean must actually reach the agent and suppress USER.md. A prior
regression (commit removing `skip_user_profile=` from the AIAgent constructor)
left the value computed-but-unused, so USER.md leaked into every contact's
prompt and the model addressed contacts by the owner's name. The existing
`tests/gateway/test_user_profile_identity.py` only asserts the helper returns
the right boolean — it never proved the boolean was applied. These tests close
that gap by exercising the full constructor → init_agent → MemoryStore path.

MEMORY.md must remain available in both modes (it carries contact-specific
facts, not a single pinned identity).
"""

import json
from types import SimpleNamespace

import pytest


def _fake_client_factory():
    class _FakeChatCompletions:
        def create(self, **kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="ok", reasoning=None, tool_calls=[]),
                        finish_reason="stop",
                    )
                ],
                usage=None,
            )

    class _FakeClient:
        def __init__(self):
            self.chat = SimpleNamespace(completions=_FakeChatCompletions())

    return _FakeClient


@pytest.fixture
def _memories_home(tmp_path, monkeypatch):
    """Point get_hermes_home() at a temp dir with USER.md + MEMORY.md and
    memory enabled in config."""
    home = tmp_path / "hermes_home"
    mem_dir = home / "memories"
    mem_dir.mkdir(parents=True)
    (mem_dir / "USER.md").write_text(
        "**Name:** Aldo Eliacim Alvarez Lemus\n"
        "**What to call them:** Aldo\n"
    )
    (mem_dir / "MEMORY.md").write_text(
        "Contact-specific notes that should always survive.\n"
    )

    # Both the constants module and memory_tool import get_hermes_home.
    monkeypatch.setattr("hermes_constants.get_hermes_home", lambda: home)
    monkeypatch.setattr("tools.memory_tool.get_hermes_home", lambda: home)
    monkeypatch.setattr("agent.agent_init.get_hermes_home", lambda: home)

    # Force memory + user_profile on regardless of the developer's real config.
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda *a, **k: {
            "memory": {
                "memory_enabled": True,
                "user_profile_enabled": True,
                "memory_char_limit": 2200,
                "user_char_limit": 1375,
                "nudge_interval": 10,
            }
        },
    )
    return home


def _build_agent(monkeypatch, *, skip_user_profile):
    import run_agent

    monkeypatch.setattr("run_agent.OpenAI", lambda **kwargs: _fake_client_factory()())
    monkeypatch.setattr(
        "run_agent.get_tool_definitions",
        lambda *args, **kwargs: [{"function": {"name": "read_file"}}],
    )
    return run_agent.AIAgent(
        model="test-model",
        api_key="test-key",
        base_url="http://localhost:8080/v1",
        platform="whatsapp",
        max_iterations=2,
        quiet_mode=True,
        skip_user_profile=skip_user_profile,
    )


def test_skip_user_profile_true_suppresses_user_md_keeps_memory(_memories_home, monkeypatch):
    from agent.system_prompt import build_system_prompt

    agent = _build_agent(monkeypatch, skip_user_profile=True)

    # The gate: USER.md is disabled for this (non-owner) source ...
    assert agent._user_profile_enabled is False
    # ... but MEMORY.md stays enabled.
    assert agent._memory_enabled is True

    # The real surface that leaked: the assembled system prompt must NOT
    # contain the owner-identity block, but MUST still carry MEMORY.md.
    prompt = build_system_prompt(agent)
    assert "USER PROFILE (who the user is)" not in prompt
    assert "What to call them" not in prompt
    assert "Contact-specific notes" in prompt


def test_skip_user_profile_false_keeps_user_md(_memories_home, monkeypatch):
    from agent.system_prompt import build_system_prompt

    agent = _build_agent(monkeypatch, skip_user_profile=False)

    assert agent._user_profile_enabled is True

    prompt = build_system_prompt(agent)
    assert "USER PROFILE (who the user is)" in prompt
    assert "Contact-specific notes" in prompt

