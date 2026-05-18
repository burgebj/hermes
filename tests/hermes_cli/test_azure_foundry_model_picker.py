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

    def test_ignores_config_base_url_for_non_foundry_provider(self, monkeypatch):
        """A `model.base_url` set for a different provider must not leak through."""
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.delenv("AZURE_FOUNDRY_BASE_URL", raising=False)

        def _fake_load_config():
            # User's main provider is custom; the URL belongs to that endpoint.
            return {"model": {"provider": "custom", "base_url": "https://localhost:8000/v1"}}

        monkeypatch.setattr("hermes_cli.config.load_config", _fake_load_config)

        with patch("hermes_cli.azure_detect._probe_openai_models") as probe:
            ids = provider_model_ids("azure-foundry")

        # No base_url for azure-foundry → probe never runs → falls back to static [].
        probe.assert_not_called()
        assert ids == []

    def test_falls_back_to_static_when_api_key_missing(self, monkeypatch):
        from hermes_cli.models import provider_model_ids

        monkeypatch.delenv("AZURE_FOUNDRY_API_KEY", raising=False)
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://r.openai.azure.com/openai/v1")
        # Pin `.env` resolver to empty so we don't read a real key from disk.
        monkeypatch.setattr("hermes_cli.config.get_env_value", lambda _k: "")

        with patch("hermes_cli.azure_detect._probe_openai_models") as probe:
            ids = provider_model_ids("azure-foundry")

        probe.assert_not_called()
        assert ids == []

    def test_falls_back_to_static_when_base_url_missing(self, monkeypatch):
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.delenv("AZURE_FOUNDRY_BASE_URL", raising=False)
        monkeypatch.setattr("hermes_cli.config.load_config", lambda: {"model": {}})

        with patch("hermes_cli.azure_detect._probe_openai_models") as probe:
            ids = provider_model_ids("azure-foundry")

        probe.assert_not_called()
        assert ids == []

    def test_falls_back_to_static_when_probe_returns_not_ok(self, monkeypatch):
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://r.openai.azure.com/openai/v1")

        with patch(
            "hermes_cli.azure_detect._probe_openai_models",
            return_value=(False, []),
        ):
            ids = provider_model_ids("azure-foundry")

        assert ids == []

    def test_falls_back_to_static_when_probe_returns_empty_list(self, monkeypatch):
        """A 200 OK with an OpenAI-shaped empty list must not block the picker."""
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://r.openai.azure.com/openai/v1")

        with patch(
            "hermes_cli.azure_detect._probe_openai_models",
            return_value=(True, []),
        ):
            ids = provider_model_ids("azure-foundry")

        # ok=True but ids=[]; gracefully fall through rather than returning the
        # empty live result and shadowing the static [] (semantically identical
        # here, but the contract is "fall through, not crash").
        assert ids == []

    def test_does_not_raise_when_probe_raises(self, monkeypatch):
        from hermes_cli.models import provider_model_ids

        monkeypatch.setenv("AZURE_FOUNDRY_API_KEY", "az-secret")
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://r.openai.azure.com/openai/v1")

        with patch(
            "hermes_cli.azure_detect._probe_openai_models",
            side_effect=RuntimeError("network down"),
        ):
            ids = provider_model_ids("azure-foundry")

        assert ids == []  # graceful fallback

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


# ---------------------------------------------------------------------------
# _get_azure_foundry_base_url helper
# ---------------------------------------------------------------------------


class TestGetAzureFoundryBaseUrl:
    """Direct contract for the helper backing the picker's base-URL lookup."""

    def test_returns_config_url_when_provider_matches(self, monkeypatch):
        from hermes_cli.models import _get_azure_foundry_base_url

        monkeypatch.setattr(
            "hermes_cli.config.load_config",
            lambda: {"model": {"provider": "azure-foundry", "base_url": "https://r.openai.azure.com/openai/v1/"}},
        )
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://other.example/v1")

        assert _get_azure_foundry_base_url() == "https://r.openai.azure.com/openai/v1"

    def test_falls_back_to_env_when_no_config(self, monkeypatch):
        from hermes_cli.models import _get_azure_foundry_base_url

        monkeypatch.setattr("hermes_cli.config.load_config", lambda: {"model": {}})
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://env.example/v1/")

        assert _get_azure_foundry_base_url() == "https://env.example/v1"

    def test_returns_empty_when_provider_is_different(self, monkeypatch):
        from hermes_cli.models import _get_azure_foundry_base_url

        monkeypatch.setattr(
            "hermes_cli.config.load_config",
            lambda: {"model": {"provider": "custom", "base_url": "https://localhost:8000/v1"}},
        )
        monkeypatch.delenv("AZURE_FOUNDRY_BASE_URL", raising=False)

        assert _get_azure_foundry_base_url() == ""

    def test_load_config_failure_does_not_crash(self, monkeypatch):
        from hermes_cli.models import _get_azure_foundry_base_url

        def _boom():
            raise RuntimeError("bad config.yaml")

        monkeypatch.setattr("hermes_cli.config.load_config", _boom)
        monkeypatch.setenv("AZURE_FOUNDRY_BASE_URL", "https://env.example/v1")

        # Helper must swallow the load failure and return the env fallback.
        assert _get_azure_foundry_base_url() == "https://env.example/v1"


