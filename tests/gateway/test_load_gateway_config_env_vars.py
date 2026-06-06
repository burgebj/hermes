"""Regression test: _load_gateway_config() expands ${VAR} env var references."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from hermes_cli.config import _expand_env_vars


@pytest.fixture
def hermes_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return home


def _load_gateway_config_via_module(hermes_home):
    import gateway.run as gr

    with patch.object(gr, "_hermes_home", hermes_home):
        return gr._load_gateway_config()


def test_load_gateway_config_expands_env_vars(hermes_home, monkeypatch):
    monkeypatch.setenv("MY_TEST_BASE_URL", "https://api.example.com/v1")
    monkeypatch.setenv("MY_TEST_API_KEY", "sk-test-123")

    config = {
        "model": {
            "default": "test-model",
            "base_url": "${MY_TEST_BASE_URL}",
            "api_key": "${MY_TEST_API_KEY}",
        },
        "custom_providers": [
            {
                "name": "TestProvider",
                "base_url": "${MY_TEST_BASE_URL}",
                "api_key": "${MY_TEST_API_KEY}",
                "model": "test-model",
            }
        ],
    }
    (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

    result = _load_gateway_config_via_module(hermes_home)

    assert result["model"]["base_url"] == "https://api.example.com/v1"
    assert result["model"]["api_key"] == "sk-test-123"
    assert result["custom_providers"][0]["base_url"] == "https://api.example.com/v1"


def test_load_gateway_config_preserves_unresolved_vars(hermes_home, monkeypatch):
    monkeypatch.delenv("NONEXISTENT_VAR", raising=False)

    config = {
        "model": {
            "base_url": "${NONEXISTENT_VAR}",
        },
    }
    (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

    result = _load_gateway_config_via_module(hermes_home)

    assert result["model"]["base_url"] == "${NONEXISTENT_VAR}"


def test_load_gateway_config_no_env_vars_needed(hermes_home):
    config = {
        "model": {
            "default": "test-model",
            "base_url": "https://hardcoded.example.com/v1",
        },
    }
    (hermes_home / "config.yaml").write_text(yaml.dump(config), encoding="utf-8")

    result = _load_gateway_config_via_module(hermes_home)

    assert result["model"]["base_url"] == "https://hardcoded.example.com/v1"
