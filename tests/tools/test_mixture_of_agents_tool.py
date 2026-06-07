import importlib
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

moa = importlib.import_module("tools.mixture_of_agents_tool")


def _assert_model_spec_is_valid(spec):
    if isinstance(spec, str):
        assert "/" in spec and not spec.startswith("/")
        return
    assert isinstance(spec, dict)
    assert isinstance(spec.get("provider"), str) and spec["provider"].strip()
    assert isinstance(spec.get("model"), str) and spec["model"].strip()


@pytest.mark.usefixtures("moa_config")
def test_moa_defaults_are_well_formed():
    """Config-loaded models must be well-formed provider/model specs."""
    moa._ensure_moa_config()
    assert isinstance(moa.REFERENCE_MODELS, list)
    assert len(moa.REFERENCE_MODELS) >= 1
    for m in moa.REFERENCE_MODELS:
        _assert_model_spec_is_valid(m)
    _assert_model_spec_is_valid(moa.AGGREGATOR_MODEL)


@pytest.mark.usefixtures("moa_config")
def test_moa_config_is_loaded_from_config():
    """Config must contain the moa section with correct structure."""
    config = moa.get_moa_configuration()
    assert len(config["reference_model_labels"]) >= 1
    assert config["aggregator_model_label"]
    # No adversarial stances — count removed from config dict
    assert "adversarial_reference_count" not in config
    # Provider-routed defaults don't require OpenRouter
    assert moa.check_moa_requirements() is True


def test_registered_moa_tool_does_not_require_openrouter():
    entry = moa.registry.get_entry("mixture_of_agents")
    assert entry is not None
    assert entry.requires_env == []
    assert entry.check_fn is moa.check_moa_requirements


def test_reference_messages_are_neutral():
    """All reference models get the same neutral user-message treatment — no adversarial stances."""
    model1 = {"provider": "opencode-go", "model": "kimi-k2.6"}
    model2 = {"provider": "openai-codex", "model": "gpt-5.5"}

    msgs1 = moa._build_messages_for_reference(model1, "question")
    msgs2 = moa._build_messages_for_reference(model2, "question")

    assert msgs1 == [{"role": "user", "content": "question"}]
    assert msgs2 == [{"role": "user", "content": "question"}]


def test_model_stance_always_empty():
    """Stances are removed — all models get neutral treatment."""
    assert moa._model_stance({"provider": "x", "model": "y", "stance": "anything"}) == ""


@pytest.mark.asyncio
async def test_provider_routed_reference_uses_async_call_llm(monkeypatch):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="answer"))])
    call = AsyncMock(return_value=response)
    monkeypatch.setattr(moa, "async_call_llm", call)

    model, content, success = await moa._run_reference_model_safe(
        {"provider": "opencode-go", "model": "kimi-k2.6"}, "hello", max_retries=1
    )

    assert success is True
    assert model == "opencode-go/kimi-k2.6"
    assert content == "answer"
    call.assert_awaited_once()
    assert call.await_args is not None
    kwargs = call.await_args.kwargs
    assert kwargs["provider"] == "opencode-go"
    assert kwargs["model"] == "kimi-k2.6"
    assert kwargs["task"] == "moa"


@pytest.mark.asyncio
async def test_provider_routed_aggregator_uses_requested_model(monkeypatch):
    response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="final"))])
    call = AsyncMock(return_value=response)
    monkeypatch.setattr(moa, "async_call_llm", call)

    content = await moa._run_aggregator_model(
        "system", "question", aggregator_model={"provider": "openai-codex", "model": "gpt-5.5"}
    )

    assert content == "final"
    assert call.await_args is not None
    kwargs = call.await_args.kwargs
    assert kwargs["provider"] == "openai-codex"
    assert kwargs["model"] == "gpt-5.5"
    assert kwargs["messages"][0] == {"role": "system", "content": "system"}


@pytest.mark.asyncio
async def test_reference_model_retry_warnings_avoid_exc_info_until_terminal_failure(monkeypatch):
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=AsyncMock(side_effect=RuntimeError("rate limited"))
            )
        )
    )
    warn = MagicMock()
    err = MagicMock()

    monkeypatch.setattr(moa, "_get_openrouter_client", lambda: fake_client)
    monkeypatch.setattr(moa.logger, "warning", warn)
    monkeypatch.setattr(moa.logger, "error", err)

    model, message, success = await moa._run_reference_model_safe(
        "openai/gpt-5.4-pro", "hello", max_retries=2
    )

    assert model == "openai/gpt-5.4-pro"
    assert success is False
    assert "failed after 2 attempts" in message
    assert warn.call_count == 2
    assert all(call.kwargs.get("exc_info") is None for call in warn.call_args_list)
    err.assert_called_once()
    assert err.call_args.kwargs.get("exc_info") is True


@pytest.mark.asyncio
@pytest.mark.usefixtures("moa_config")
async def test_moa_top_level_error_logs_single_traceback_on_aggregator_failure(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(
        moa,
        "_run_reference_model_safe",
        AsyncMock(return_value=("anthropic/claude-opus-4.6", "ok", True)),
    )
    monkeypatch.setattr(
        moa,
        "_run_aggregator_model",
        AsyncMock(side_effect=RuntimeError("aggregator boom")),
    )
    monkeypatch.setattr(
        moa,
        "_debug",
        SimpleNamespace(log_call=MagicMock(), save=MagicMock(), active=False),
    )

    err = MagicMock()
    monkeypatch.setattr(moa.logger, "error", err)

    result = json.loads(
        await moa.mixture_of_agents_tool(
            "solve this",
            reference_models=["anthropic/claude-opus-4.6"],
        )
    )

    assert result["success"] is False
    assert "Error in MoA processing" in result["error"]
    err.assert_called_once()
    assert err.call_args.kwargs.get("exc_info") is True
