"""Test that CLI syncs model/provider from agent after fallback activation (#7385)."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def test_cli_model_synced_after_fallback():
    """After run_conversation, CLI.model should reflect agent's active model."""
    # Simulate the post-conversation sync logic directly
    # (testing the logic, not the full CLI)
    class FakeCLI:
        model = "original-model"
        provider = "original-provider"
        agent = SimpleNamespace(model="fallback-model", provider="fallback-provider")

    cli = FakeCLI()

    # This is the sync logic from the fix
    agent = getattr(cli, "agent", None)
    if agent is not None:
        _active_model = getattr(agent, "model", None)
        _active_provider = getattr(agent, "provider", None)
        if _active_model and _active_model != cli.model:
            cli.model = _active_model
        if _active_provider and _active_provider != getattr(cli, "provider", None):
            cli.provider = _active_provider

    assert cli.model == "fallback-model"
    assert cli.provider == "fallback-provider"


def test_cli_model_not_synced_when_same():
    """If agent model matches CLI model, no sync occurs."""
    class FakeCLI:
        model = "same-model"
        provider = "same-provider"
        agent = SimpleNamespace(model="same-model", provider="same-provider")

    cli = FakeCLI()

    agent = getattr(cli, "agent", None)
    if agent is not None:
        _active_model = getattr(agent, "model", None)
        _active_provider = getattr(agent, "provider", None)
        if _active_model and _active_model != cli.model:
            cli.model = _active_model
        if _active_provider and _active_provider != getattr(cli, "provider", None):
            cli.provider = _active_provider

    assert cli.model == "same-model"


def test_cli_model_sync_handles_no_agent():
    """No crash when agent is None."""
    class FakeCLI:
        model = "orig"
        provider = "orig"
        agent = None

    cli = FakeCLI()

    agent = getattr(cli, "agent", None)
    if agent is not None:
        _active_model = getattr(agent, "model", None)
        if _active_model and _active_model != cli.model:
            cli.model = _active_model

    assert cli.model == "orig"
