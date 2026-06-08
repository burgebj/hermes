from __future__ import annotations

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.run import GatewayRunner


def _make_runner() -> GatewayRunner:
    runner = object.__new__(GatewayRunner)
    runner.config = GatewayConfig(
        platforms={Platform.FEISHU: PlatformConfig(enabled=True)},
        group_sessions_per_user=True,
        thread_sessions_per_user=False,
    )
    return runner


def test_apply_display_config_to_platform_extra_uses_per_platform_overrides(monkeypatch):
    runner = _make_runner()
    config = PlatformConfig(enabled=True, extra={})

    monkeypatch.setattr(
        "gateway.run._load_gateway_config",
        lambda: {
            "display": {
                "final_response_format": "legacy",
                "platforms": {
                    "feishu": {
                        "final_response_format": "card",
                        "markdown_tables": "code",
                    }
                },
            }
        },
    )

    runner._apply_display_config_to_platform_extra(Platform.FEISHU, config)

    assert config.extra["final_response_format"] == "card"
    assert config.extra["markdown_tables"] == "code"
    assert config.extra["card_schema"] == "2.0"


def test_apply_display_config_to_platform_extra_preserves_explicit_adapter_extra(monkeypatch):
    runner = _make_runner()
    config = PlatformConfig(
        enabled=True,
        extra={"final_response_format": "text", "markdown_tables": "text"},
    )

    monkeypatch.setattr(
        "gateway.run._load_gateway_config",
        lambda: {
            "display": {
                "platforms": {
                    "feishu": {
                        "final_response_format": "card",
                        "markdown_tables": "table",
                    }
                },
            }
        },
    )

    runner._apply_display_config_to_platform_extra(Platform.FEISHU, config)

    assert config.extra["final_response_format"] == "text"
    assert config.extra["markdown_tables"] == "text"
