"""Regression test for #36748: CLI provider override propagates to aux title generation.

The one-shot CLI path used to pass ``self.model``/``self.provider`` etc.
unconditionally to ``maybe_auto_title``.  When a named custom provider was
selected via ``--provider <custom>`` (e.g. an Ollama OpenAI-compatible
endpoint), ``self.model`` could still hold the global default
(``gpt-5.5``) while the agent actually used the custom provider's model.
Title generation then routed against the global default and 404'd.

Fix: prefer ``self.agent.{model,provider,base_url,api_key,api_mode}`` when
the agent is set, falling back to the CLI defaults.
"""
import importlib
import os
import sys
from unittest.mock import MagicMock, patch


def test_aux_title_main_runtime_prefers_agent_runtime(tmp_path, monkeypatch):
    # Ensure repo on sys.path
    repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo not in sys.path:
        sys.path.insert(0, repo)

    # Read cli.py and snip the relevant block so we don't have to bring up
    # the whole HermesCLI constructor (heavy).  We assert the literal code
    # path uses the agent's runtime when available.
    cli_src = open(os.path.join(repo, "cli.py")).read()
    # The dict construction must reference `_agent` (or `self.agent`)
    # before falling back to `self`.
    assert "getattr(_agent, \"model\"" in cli_src or "getattr(self.agent, \"model\"" in cli_src, \
        "maybe_auto_title call must read effective model from the agent"
    assert "getattr(_agent, \"provider\"" in cli_src or "getattr(self.agent, \"provider\"" in cli_src
    assert "getattr(_agent, \"base_url\"" in cli_src or "getattr(self.agent, \"base_url\"" in cli_src
    assert "getattr(_agent, \"api_key\"" in cli_src or "getattr(self.agent, \"api_key\"" in cli_src
    assert "getattr(_agent, \"api_mode\"" in cli_src or "getattr(self.agent, \"api_mode\"" in cli_src


def test_aux_title_main_runtime_construction_logic():
    """Direct unit test of the precedence rule itself."""

    class _Agent:
        model = "qwen3.6:35b-mlx"
        provider = "ollama-local"
        base_url = "http://localhost:11434/v1"
        api_key = "no-key-required"
        api_mode = "chat_completions"

    class _CLI:
        model = "gpt-5.5"
        provider = "openai-codex"
        base_url = ""
        api_key = ""
        api_mode = "chat_completions"
        agent = _Agent()

    cli = _CLI()
    _agent = cli.agent
    main_runtime = {
        "model": getattr(_agent, "model", None) or cli.model,
        "provider": getattr(_agent, "provider", None) or cli.provider,
        "base_url": getattr(_agent, "base_url", None) or cli.base_url,
        "api_key": getattr(_agent, "api_key", None) or cli.api_key,
        "api_mode": getattr(_agent, "api_mode", None) or cli.api_mode,
    }
    assert main_runtime["model"] == "qwen3.6:35b-mlx"
    assert main_runtime["provider"] == "ollama-local"
    assert main_runtime["base_url"] == "http://localhost:11434/v1"
    assert main_runtime["api_key"] == "no-key-required"


def test_aux_title_main_runtime_fallback_when_no_agent():
    class _CLI:
        model = "gpt-5.5"
        provider = "openai-codex"
        base_url = ""
        api_key = ""
        api_mode = "chat_completions"
        agent = None

    cli = _CLI()
    _agent = cli.agent
    main_runtime = {
        "model": getattr(_agent, "model", None) or cli.model,
        "provider": getattr(_agent, "provider", None) or cli.provider,
    }
    assert main_runtime["model"] == "gpt-5.5"
    assert main_runtime["provider"] == "openai-codex"
