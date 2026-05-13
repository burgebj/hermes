"""Regression tests for gateway /model support of config.yaml custom_providers."""

import yaml
import pytest
from unittest.mock import MagicMock

from gateway.config import Platform
from gateway.platforms.base import MessageEvent, MessageType
from gateway.run import GatewayRunner
from gateway.session import SessionSource


def _make_runner():
    runner = object.__new__(GatewayRunner)
    runner.adapters = {}
    runner._voice_mode = {}
    runner._session_model_overrides = {}
    return runner


def _make_event(text="/model"):
    return MessageEvent(
        text=text,
        message_type=MessageType.TEXT,
        source=SessionSource(platform=Platform.TELEGRAM, chat_id="12345", chat_type="dm"),
    )


@pytest.mark.asyncio
async def test_handle_model_command_routes_main_profile(monkeypatch):
    runner = _make_runner()
    runner._load_gateway_config = MagicMock(return_value={"model": {"default": "owl-alpha", "provider": "openrouter"}})
    save_calls = []

    def fake_save_config_value(key, value):
        save_calls.append((key, value))

    def fake_switch_model(**kwargs):
        return MagicMock(
            success=True,
            target_provider="openrouter",
            new_model="owl-alpha",
            base_url="https://openrouter.ai/api/v1",
            api_mode="chat_completions",
            warning_message=None,
            error_message=None,
        )

    monkeypatch.setattr("cli.save_config_value", fake_save_config_value)
    monkeypatch.setattr("hermes_cli.model_switch.switch_model", fake_switch_model)

    result = await runner._handle_model_command(_make_event("/model main openrouter/owl-alpha"))

    assert result is not None
    assert any(key == "model.main" for key, _ in save_calls)
    assert any(key == "model.default" for key, _ in save_calls)


@pytest.mark.asyncio
async def test_handle_model_command_routes_escalate_profile(monkeypatch):
    runner = _make_runner()
    runner._load_gateway_config = MagicMock(return_value={"model": {"default": "owl-alpha", "provider": "openrouter"}})
    save_calls = []

    def fake_save_config_value(key, value):
        save_calls.append((key, value))

    def fake_switch_model(**kwargs):
        return MagicMock(
            success=True,
            target_provider="openai-codex",
            new_model="gpt-5.4-mini",
            base_url="https://chatgpt.com/backend-api/codex",
            api_mode="chat_completions",
            warning_message=None,
            error_message=None,
        )

    monkeypatch.setattr("cli.save_config_value", fake_save_config_value)
    monkeypatch.setattr("hermes_cli.model_switch.switch_model", fake_switch_model)

    result = await runner._handle_model_command(_make_event("/model escalate openai/gpt-5.4-mini"))

    assert result is not None
    assert any(key == "model.escalate" for key, _ in save_calls)
    assert not any(key == "model.default" for key, _ in save_calls)


@pytest.mark.asyncio
async def test_handle_model_command_lists_saved_custom_provider(tmp_path, monkeypatch):
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "model": {
                    "default": "gpt-5.4",
                    "provider": "openai-codex",
                    "base_url": "https://chatgpt.com/backend-api/codex",
                },
                "providers": {},
                "custom_providers": [
                    {
                        "name": "Local (127.0.0.1:4141)",
                        "base_url": "http://127.0.0.1:4141/v1",
                        "model": "rotator-openrouter-coding",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    import gateway.run as gateway_run

    monkeypatch.setattr(gateway_run, "_hermes_home", hermes_home)
    monkeypatch.setattr("agent.models_dev.fetch_models_dev", lambda: {})

    result = await _make_runner()._handle_model_command(_make_event())

    assert result is not None
    assert "Local (127.0.0.1:4141)" in result
    assert "custom:local-(127.0.0.1:4141)" in result
    assert "rotator-openrouter-coding" in result
