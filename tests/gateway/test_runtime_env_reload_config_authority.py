"""Regression tests for gateway per-turn env reload preserving config authority.

Issue #19158: startup bridges config.yaml agent.max_turns into
HERMES_MAX_ITERATIONS, but a later per-turn load_dotenv(..., override=True)
can restore a stale .env HERMES_MAX_ITERATIONS value before the next turn.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from gateway import run as gateway_run


def test_reload_runtime_env_preserves_config_max_turns(tmp_path: Path, monkeypatch) -> None:
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        yaml.safe_dump({"agent": {"max_turns": 9000}}),
        encoding="utf-8",
    )
    (hermes_home / ".env").write_text(
        "HERMES_MAX_ITERATIONS=90\nOPENROUTER_API_KEY=fresh-key\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(gateway_run, "_hermes_home", hermes_home)
    monkeypatch.setenv("HERMES_MAX_ITERATIONS", "9000")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    gateway_run._reload_runtime_env_preserving_config_authority()

    assert os.environ["OPENROUTER_API_KEY"] == "fresh-key"
    assert os.environ["HERMES_MAX_ITERATIONS"] == "9000"


def test_reload_runtime_env_preserves_other_config_authority(
    tmp_path: Path, monkeypatch
) -> None:
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(
        yaml.safe_dump(
            {
                "agent": {
                    "gateway_timeout": 1800,
                    "gateway_timeout_warning": 900,
                    "gateway_notify_interval": 120,
                    "restart_drain_timeout": 45,
                    "gateway_auto_continue_freshness": 300,
                },
                "display": {
                    "busy_input_mode": "interrupt",
                    "busy_ack_enabled": False,
                },
                "timezone": "America/New_York",
                "security": {"redact_secrets": True},
            }
        ),
        encoding="utf-8",
    )
    (hermes_home / ".env").write_text(
        "\n".join(
            [
                "HERMES_AGENT_TIMEOUT=60",
                "HERMES_AGENT_TIMEOUT_WARNING=30",
                "HERMES_AGENT_NOTIFY_INTERVAL=15",
                "HERMES_RESTART_DRAIN_TIMEOUT=5",
                "HERMES_AUTO_CONTINUE_FRESHNESS=10",
                "HERMES_GATEWAY_BUSY_INPUT_MODE=queue",
                "HERMES_GATEWAY_BUSY_ACK_ENABLED=true",
                "HERMES_TIMEZONE=UTC",
                "HERMES_REDACT_SECRETS=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(gateway_run, "_hermes_home", hermes_home)

    gateway_run._reload_runtime_env_preserving_config_authority()

    assert os.environ["HERMES_AGENT_TIMEOUT"] == "1800"
    assert os.environ["HERMES_AGENT_TIMEOUT_WARNING"] == "900"
    assert os.environ["HERMES_AGENT_NOTIFY_INTERVAL"] == "120"
    assert os.environ["HERMES_RESTART_DRAIN_TIMEOUT"] == "45"
    assert os.environ["HERMES_AUTO_CONTINUE_FRESHNESS"] == "300"
    assert os.environ["HERMES_GATEWAY_BUSY_INPUT_MODE"] == "interrupt"
    assert os.environ["HERMES_GATEWAY_BUSY_ACK_ENABLED"] == "False"
    assert os.environ["HERMES_TIMEZONE"] == "America/New_York"
    assert os.environ["HERMES_REDACT_SECRETS"] == "true"


def test_reload_runtime_env_keeps_env_max_iterations_when_config_omits_key(
    tmp_path: Path, monkeypatch
) -> None:
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text(yaml.safe_dump({"agent": {}}), encoding="utf-8")
    (hermes_home / ".env").write_text("HERMES_MAX_ITERATIONS=123\n", encoding="utf-8")

    monkeypatch.setattr(gateway_run, "_hermes_home", hermes_home)
    monkeypatch.delenv("HERMES_MAX_ITERATIONS", raising=False)

    gateway_run._reload_runtime_env_preserving_config_authority()

    assert os.environ["HERMES_MAX_ITERATIONS"] == "123"


def test_reload_runtime_env_restores_authoritative_values_on_bad_config(
    tmp_path: Path, monkeypatch
) -> None:
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir()
    (hermes_home / "config.yaml").write_text("agent: [unterminated\n", encoding="utf-8")
    (hermes_home / ".env").write_text(
        "HERMES_MAX_ITERATIONS=90\nHERMES_AGENT_TIMEOUT=60\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(gateway_run, "_hermes_home", hermes_home)
    monkeypatch.setenv("HERMES_MAX_ITERATIONS", "9000")
    monkeypatch.setenv("HERMES_AGENT_TIMEOUT", "1800")

    gateway_run._reload_runtime_env_preserving_config_authority()

    assert os.environ["HERMES_MAX_ITERATIONS"] == "9000"
    assert os.environ["HERMES_AGENT_TIMEOUT"] == "1800"
