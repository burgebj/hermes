from unittest.mock import MagicMock, patch

from run_agent import AIAgent


@patch("run_agent.OpenAI")
def test_explicit_custom_endpoint_passes_user_default_headers(mock_openai):
    mock_openai.return_value = MagicMock()

    AIAgent(
        api_key="test-key",
        base_url="https://api.example.com/v1",
        default_headers={"User-Agent": "DuckCodeClient/1.0", "X-Channel": "relay"},
        model="gpt-5.4",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )

    kwargs = mock_openai.call_args.kwargs
    assert kwargs["default_headers"]["User-Agent"] == "DuckCodeClient/1.0"
    assert kwargs["default_headers"]["X-Channel"] == "relay"


@patch("run_agent.OpenAI")
def test_openrouter_auto_headers_merge_with_user_default_headers(mock_openai):
    mock_openai.return_value = MagicMock()

    agent = AIAgent(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        default_headers={"User-Agent": "DuckCodeClient/1.0"},
        model="test/model",
        quiet_mode=True,
        skip_context_files=True,
        skip_memory=True,
    )

    headers = agent._client_kwargs["default_headers"]
    assert headers["User-Agent"] == "DuckCodeClient/1.0"
    assert headers["HTTP-Referer"] == "https://hermes-agent.nousresearch.com"
    assert headers["X-Title"] == "Hermes Agent"
