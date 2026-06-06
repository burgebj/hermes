"""Tests that switch_model does not inherit stale context_length overrides."""

from unittest.mock import MagicMock, patch

from run_agent import AIAgent
from agent.context_compressor import ContextCompressor


def _make_agent_with_compressor(config_context_length=None, threshold_tokens_override=None) -> AIAgent:
    """Build a minimal AIAgent with a context_compressor, skipping __init__."""
    agent = AIAgent.__new__(AIAgent)

    # Primary model settings
    agent.model = "primary-model"
    agent.provider = "openrouter"
    agent.base_url = "https://openrouter.ai/api/v1"
    agent.api_key = "sk-primary"
    agent.api_mode = "chat_completions"
    agent.client = MagicMock()
    agent.quiet_mode = True

    # Store the initial config_context_length override used at agent construction.
    agent._config_context_length = config_context_length

    # Context compressor with primary model values
    compressor = ContextCompressor(
        model="primary-model",
        threshold_percent=0.50,
        base_url="https://openrouter.ai/api/v1",
        api_key="sk-primary",
        provider="openrouter",
        quiet_mode=True,
        config_context_length=config_context_length,
        threshold_tokens_override=threshold_tokens_override,
    )
    agent.context_compressor = compressor

    # For switch_model
    agent._primary_runtime = {}

    return agent


@patch("agent.model_metadata.get_model_context_length", return_value=131_072)
def test_switch_model_clears_previous_config_context_length(mock_ctx_len):
    """Switching models must not reuse the previous model.context_length override."""
    agent = _make_agent_with_compressor(config_context_length=32_768)

    assert agent.context_compressor.model == "primary-model"
    assert agent.context_compressor.context_length == 32_768  # From config override

    # Switch model
    agent.switch_model("new-model", "openrouter", api_key="sk-new", base_url="https://openrouter.ai/api/v1")

    # Verify the old config override is not passed to the new model.
    mock_ctx_len.assert_called_once()
    call_kwargs = mock_ctx_len.call_args.kwargs
    assert call_kwargs.get("config_context_length") is None

    # Verify compressor was updated from the newly resolved model metadata.
    assert agent.context_compressor.model == "new-model"
    assert agent.context_compressor.context_length == 131_072


def test_switch_model_without_config_context_length():
    """When switching models without config override, config_context_length should be None."""
    agent = _make_agent_with_compressor(config_context_length=None)

    with patch("agent.model_metadata.get_model_context_length", return_value=128_000) as mock_ctx_len:
        # Switch model
        agent.switch_model("new-model", "openrouter", api_key="sk-new", base_url="https://openrouter.ai/api/v1")

        # Verify get_model_context_length was called with None
        mock_ctx_len.assert_called_once()
        call_kwargs = mock_ctx_len.call_args.kwargs
        assert call_kwargs.get("config_context_length") is None


def test_switch_model_preserves_threshold_tokens_override():
    """Absolute compression thresholds should not be re-derived on model switch."""
    agent = _make_agent_with_compressor(
        config_context_length=None,
        threshold_tokens_override=80_000,
    )

    with patch("agent.model_metadata.get_model_context_length", return_value=200_000):
        agent.switch_model(
            "new-model",
            "openrouter",
            api_key="sk-new",
            base_url="https://openrouter.ai/api/v1",
        )

    compressor = getattr(agent, "context_compressor")
    assert compressor.threshold_tokens_override == 80_000
    assert compressor.threshold_tokens == 80_000


def test_switch_model_clamps_active_threshold_but_preserves_stored_override():
    agent = _make_agent_with_compressor(
        config_context_length=None,
        threshold_tokens_override=180_000,
    )

    with patch("agent.model_metadata.get_model_context_length", return_value=128_000):
        agent.switch_model(
            "small-model",
            "openrouter",
            api_key="sk-new",
            base_url="https://openrouter.ai/api/v1",
        )

    compressor = getattr(agent, "context_compressor")
    assert compressor.threshold_tokens_override == 180_000
    assert compressor.threshold_tokens == 128_000


def test_restore_primary_runtime_restores_explicit_threshold_override_only():
    agent = _make_agent_with_compressor(
        config_context_length=None,
        threshold_tokens_override=180_000,
    )
    agent._create_openai_client = MagicMock(return_value=MagicMock())
    agent._fallback_activated = True
    agent._fallback_index = 1
    agent._primary_runtime = {
        "model": "primary-model",
        "provider": "openrouter",
        "base_url": "https://openrouter.ai/api/v1",
        "api_mode": "chat_completions",
        "api_key": "sk-primary",
        "client_kwargs": {"api_key": "sk-primary", "base_url": "https://openrouter.ai/api/v1"},
        "use_prompt_caching": False,
        "use_native_cache_layout": False,
        "compressor_model": "primary-model",
        "compressor_base_url": "https://openrouter.ai/api/v1",
        "compressor_api_key": "sk-primary",
        "compressor_provider": "openrouter",
        "compressor_context_length": 128_000,
        "compressor_api_mode": "chat_completions",
        "compressor_threshold_tokens": 80_000,
        "compressor_threshold_tokens_override": 180_000,
    }

    agent.context_compressor.threshold_tokens = 80_000
    agent.context_compressor.threshold_percent = 0.625

    assert agent._restore_primary_runtime() is True

    compressor = getattr(agent, "context_compressor")
    assert compressor.threshold_tokens_override == 180_000
    assert compressor.threshold_tokens == 80_000
