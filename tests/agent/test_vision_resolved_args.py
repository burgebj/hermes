"""Test that call_llm vision path passes resolved provider args, not raw ones."""

from unittest.mock import patch, MagicMock


def test_vision_call_uses_resolved_provider_args():
    """Resolved provider/model/key/url from config must reach resolve_vision_provider_client."""
    from agent.auxiliary_client import call_llm

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="description"))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5),
    )

    with patch(
        "agent.auxiliary_client._resolve_task_provider_model",
        return_value=("my-resolved-provider", "my-resolved-model", "http://resolved", "resolved-key", "chat_completions"),
    ), patch(
        "agent.auxiliary_client.resolve_vision_provider_client",
        return_value=("my-resolved-provider", fake_client, "my-resolved-model"),
    ) as mock_vision:
        call_llm(
            "vision",
            provider="raw-provider",
            model="raw-model",
            base_url="http://raw",
            api_key="raw-key",
            messages=[{"role": "user", "content": "describe this"}],
        )

    # The resolved values must be passed, not the raw call_llm arguments
    call_args = mock_vision.call_args
    assert call_args.kwargs["provider"] == "my-resolved-provider"
    assert call_args.kwargs["model"] == "my-resolved-model"
    assert call_args.kwargs["base_url"] == "http://resolved"
    assert call_args.kwargs["api_key"] == "resolved-key"


def test_vision_base_url_override_keeps_explicit_provider():
    """Explicit provider should still drive credential resolution with custom base_url."""
    from agent.auxiliary_client import resolve_vision_provider_client

    fake_client = MagicMock()
    with patch(
        "agent.auxiliary_client._resolve_task_provider_model",
        return_value=(
            "zai",
            "glm-4v",
            "https://open.bigmodel.cn/api/paas/v4",
            None,
            "chat_completions",
        ),
    ), patch(
        "agent.auxiliary_client.resolve_provider_client",
        return_value=(fake_client, "glm-4v"),
    ) as mock_resolve:
        provider, client, model = resolve_vision_provider_client()

    assert provider == "zai"
    assert client is fake_client
    assert model == "glm-4v"
    assert mock_resolve.call_args.args[0] == "zai"
    assert mock_resolve.call_args.kwargs["explicit_base_url"] == "https://open.bigmodel.cn/api/paas/v4"


def test_vision_call_passes_main_runtime():
    """main_runtime must be forwarded to resolve_vision_provider_client."""
    from agent.auxiliary_client import call_llm

    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="description"))],
        usage=MagicMock(prompt_tokens=10, completion_tokens=5),
    )
    runtime = {"model": "mimo-v2.6", "provider": "opencode-go"}

    with (
        patch(
            "agent.auxiliary_client._resolve_task_provider_model",
            return_value=("auto", None, None, None, None),
        ),
        patch(
            "agent.auxiliary_client.resolve_vision_provider_client",
            return_value=("opencode-go", fake_client, "mimo-v2.6"),
        ) as mock_vision,
    ):
        call_llm(
            "vision",
            main_runtime=runtime,
            messages=[{"role": "user", "content": "describe this"}],
        )

    call_args = mock_vision.call_args
    assert call_args.kwargs["main_runtime"] is runtime


def test_vision_auto_detect_uses_runtime_model():
    """Auto-detection must prefer runtime model over config default."""
    from agent.auxiliary_client import resolve_vision_provider_client

    mock_client = MagicMock()

    with (
        patch(
            "agent.auxiliary_client._read_main_provider",
            return_value="opencode-go",
        ),
        patch(
            "agent.auxiliary_client._read_main_model",
            return_value="deepseek-v4-flash",
        ),
        patch(
            "agent.auxiliary_client.resolve_provider_client",
            return_value=(mock_client, "mimo-v2.6"),
        ) as mock_resolve,
    ):
        provider, client, model = resolve_vision_provider_client(
            provider="auto",
            main_runtime={"model": "mimo-v2.6", "provider": "opencode-go"},
        )

    assert provider == "opencode-go"
    assert client is mock_client
    assert model == "mimo-v2.6"
    # Must have been called with runtime model, not config default
    call_args = mock_resolve.call_args
    assert call_args.args[1] == "mimo-v2.6"
