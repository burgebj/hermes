"""Tests for Azure Foundry integration in the /model picker (#27989).

`provider_model_ids("azure-foundry")` used to fall straight through to the
static `_PROVIDER_MODELS["azure-foundry"] = []` table, so the in-app
``/model azure-foundry`` picker reported "0 models" even when the user's
Foundry resource exposed many deployments.

This file pins the live-discovery branch added to ``hermes_cli.models``:

  * Probe ``GET <base>/models`` (the same probe the setup wizard uses) and
    return the discovered deployment IDs.
  * Resolve ``base_url`` from ``config.yaml`` (``model.base_url`` when
    ``model.provider == "azure-foundry"``), falling back to the
    ``AZURE_FOUNDRY_BASE_URL`` env var.
  * Resolve the API key from ``~/.hermes/.env`` via ``get_env_value`` and
    fall back to ``AZURE_FOUNDRY_API_KEY`` in ``os.environ``.
  * Fall back to the static (empty) catalog without raising when either
    credential is missing or the probe blows up.

No real Azure endpoint is contacted — every test stubs
``hermes_cli.azure_detect._probe_openai_models``.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest


_FAKE_FOUNDRY_DEPLOYMENTS = [
    "gpt-5.4",
    "gpt-5.3-codex",
    "kimi-k2.6",
    "deepseek-v4-pro",
    "grok-4.3",
]


# ---------------------------------------------------------------------------
# Live-discovery branch — the bug
# ---------------------------------------------------------------------------


class TestProviderModelIdsAzureFoundry:
    """`provider_model_ids("azure-foundry")` must populate from a live probe."""

    def test_returns_live_discovered_ids_when_credentials_present(self, monkeypatch):
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://r.openai.azure.com/openai/v1")

        with patch(
            "hermes_cli.azure_detect._probe_openai_models",
            return_value=(True, list(_FAKE_FOUNDRY_DEPLOYMENTS)),
        ) as probe:
            ids = provider_model_ids("azure-foundry")

        assert ids == _FAKE_FOUNDRY_DEPLOYMENTS
        probe.assert_called_once()
        called_base, called_key = probe.call_args.args
        assert called_base == "https://r.openai.azure.com/openai/v1"
        assert called_key == "az-secret"

    def test_prefers_config_base_url_over_env_var(self, monkeypatch, tmp_path):
        from hermes_cli import models as models_mod
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://env.example/v1")

        def _fake_load_config():
            return {
                "model": {
                    "provider": "azure-foundry",
                    "base_url": "https://config.example/openai/v1",
                }
            }

        monkeypatch.setattr("hermes_cli.config.load_config", _fake_load_config)

        with patch(
            "hermes_cli.azure_detect._probe_openai_models",
            return_value=(True, ["gpt-5.4"]),
        ) as probe:
            ids = provider_model_ids("azure-foundry")

        assert ids == ["gpt-5.4"]
        called_base, _ = probe.call_args.args
        assert called_base == "https://config.example/openai/v1"

    def test_reads_api_key_from_dotenv_when_env_missing(self, monkeypatch):
        """`.env` API keys must be honoured even when the process env is empty."""
        from hermes_cli.models import provider_model_ids

        monkeypatch.delenv("AZURE_FOUNDRY_API_KEY", raising=False)
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://r.openai.azure.com/openai/v1")
        monkeypatch.setattr(
            "hermes_cli.config.get_env_value",
            lambda key: "dotenv-secret" if key == "AZURE_FOUNDRY_API_KEY" else "",
        )

        with patch(
            "hermes_cli.azure_detect._probe_openai_models",
            return_value=(True, ["gpt-5.4"]),
        ) as probe:
            ids = provider_model_ids("azure-foundry")

        assert ids == ["gpt-5.4"]
        _, called_key = probe.call_args.args
        assert called_key == "dotenv-secret"


