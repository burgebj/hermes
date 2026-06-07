"""Tests for plugins/image_gen/azure-foundry — Azure AI Foundry image generation.

Covers:
- Provider metadata (name, display_name)
- is_available() credential checks
- generate() happy path: quality resolved from config/env and sent to API
- generate() error paths: no credentials, missing openai, API error, empty response
- list_models() — one entry per configured deployment
- get_setup_schema() shape validation
- Plugin register() entry point
- Credential / config resolution (including quality)
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_plugin():
    spec_path = (
        Path(__file__).parent.parent.parent
        / "plugins" / "image_gen" / "azure-foundry" / "__init__.py"
    )
    spec = importlib.util.spec_from_file_location(
        "plugins.image_gen.azure_foundry", spec_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fake_url_client(url: str = "https://example.com/img.png"):
    fake_item = MagicMock()
    fake_item.b64_json = None
    fake_item.url = url
    fake_item.revised_prompt = None
    fake_resp = MagicMock()
    fake_resp.data = [fake_item]
    fake_client = MagicMock()
    fake_client.images.generate.return_value = fake_resp
    return fake_client


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def plugin():
    return _load_plugin()


@pytest.fixture
def provider(plugin):
    return plugin.AzureFoundryImageGenProvider()


def _set_creds(monkeypatch):
    monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_KEY", "sk-test")
    monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_ENDPOINT", "https://my.openai.azure.com")


# ---------------------------------------------------------------------------
# Provider metadata
# ---------------------------------------------------------------------------

class TestProviderMetadata:
    def test_name(self, provider):
        assert provider.name == "azure-foundry"

    def test_display_name_contains_azure(self, provider):
        assert "Azure" in provider.display_name

    def test_is_image_gen_provider(self, provider):
        from agent.image_gen_provider import ImageGenProvider
        assert isinstance(provider, ImageGenProvider)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

class TestConstants:
    def test_default_deployment(self, plugin):
        assert plugin.DEFAULT_DEPLOYMENT == "gpt-image-2"

    def test_valid_quality_values(self, plugin):
        assert plugin.VALID_QUALITY_VALUES == {"low", "medium", "high"}

    def test_default_quality_is_medium(self, plugin):
        assert plugin.DEFAULT_QUALITY == "medium"

    def test_default_quality_in_valid_values(self, plugin):
        assert plugin.DEFAULT_QUALITY in plugin.VALID_QUALITY_VALUES

    def test_sizes_landscape(self, plugin):
        assert plugin._SIZES["landscape"] == "1536x1024"

    def test_sizes_portrait(self, plugin):
        assert plugin._SIZES["portrait"] == "1024x1536"

    def test_sizes_square(self, plugin):
        assert plugin._SIZES["square"] == "1024x1024"


# ---------------------------------------------------------------------------
# _resolve_quality() — reads from config/env, not from generate() call
# ---------------------------------------------------------------------------

class TestResolveQuality:
    def test_default_when_nothing_set(self, plugin, monkeypatch, tmp_path):
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_QUALITY", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        assert plugin._resolve_quality() == "medium"

    def test_env_var_sets_quality_low(self, plugin, monkeypatch):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_QUALITY", "low")
        assert plugin._resolve_quality() == "low"

    def test_env_var_sets_quality_high(self, plugin, monkeypatch):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_QUALITY", "high")
        assert plugin._resolve_quality() == "high"

    def test_env_var_unknown_falls_back_to_default(self, plugin, monkeypatch, tmp_path):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_QUALITY", "ultra")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        assert plugin._resolve_quality() == "medium"

    def test_config_yaml_sets_quality(self, plugin, monkeypatch, tmp_path):
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_QUALITY", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            "image_gen:\n  azure_foundry:\n    quality: high\n"
        )
        assert plugin._resolve_quality() == "high"

    def test_env_var_wins_over_config(self, plugin, monkeypatch, tmp_path):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_QUALITY", "low")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            "image_gen:\n  azure_foundry:\n    quality: high\n"
        )
        assert plugin._resolve_quality() == "low"


# ---------------------------------------------------------------------------
# generate() — quality comes from config, not from caller
# ---------------------------------------------------------------------------

class TestGenerateQualityFromConfig:
    def test_default_quality_medium_sent_to_api(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_QUALITY", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a fox")
        assert result["success"] is True
        assert fake_client.images.generate.call_args.kwargs["quality"] == "medium"

    def test_quality_low_from_env(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_QUALITY", "low")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a fox")
        assert result["success"] is True
        assert fake_client.images.generate.call_args.kwargs["quality"] == "low"

    def test_quality_high_from_config_yaml(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_QUALITY", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            "image_gen:\n  azure_foundry:\n    quality: high\n"
        )
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a fox")
        assert result["success"] is True
        assert fake_client.images.generate.call_args.kwargs["quality"] == "high"

    def test_quality_echoed_in_response(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_QUALITY", "high")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a fox")
        assert result.get("quality") == "high"

    def test_generate_has_no_quality_parameter(self, provider):
        """generate() must not accept a quality kwarg — quality is config-only."""
        import inspect
        sig = inspect.signature(provider.generate)
        assert "quality" not in sig.parameters


# ---------------------------------------------------------------------------
# generate() — deployment used as API model param
# ---------------------------------------------------------------------------

class TestGenerateDeployment:
    def test_deployment_sent_as_model_param(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", "my-deploy")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            provider.generate("a fox")
        assert fake_client.images.generate.call_args.kwargs["model"] == "my-deploy"

    def test_default_deployment_when_not_set(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            provider.generate("a fox")
        assert fake_client.images.generate.call_args.kwargs["model"] == "gpt-image-2"

    def test_response_model_is_deployment_name(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", "my-deploy")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a fox")
        assert result["model"] == "my-deploy"


# ---------------------------------------------------------------------------
# generate() — happy path
# ---------------------------------------------------------------------------

class TestGenerateHappyPath:
    def test_url_response_returned_directly(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client("https://cdn.example.com/out.png")
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a cat")
        assert result["success"] is True
        assert result["image"] == "https://cdn.example.com/out.png"

    def test_b64_response_saves_file(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        import base64
        fake_item = MagicMock()
        fake_item.b64_json = base64.b64encode(b"PNG").decode()
        fake_item.url = None
        fake_item.revised_prompt = None
        fake_resp = MagicMock()
        fake_resp.data = [fake_item]
        fake_client = MagicMock()
        fake_client.images.generate.return_value = fake_resp
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a dog")
        assert result["success"] is True
        assert result["image"].endswith(".png")

    def test_revised_prompt_in_response(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_item = MagicMock()
        fake_item.b64_json = None
        fake_item.url = "https://cdn.example.com/out.png"
        fake_item.revised_prompt = "a swift arctic fox"
        fake_resp = MagicMock()
        fake_resp.data = [fake_item]
        fake_client = MagicMock()
        fake_client.images.generate.return_value = fake_resp
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a fox")
        assert result.get("revised_prompt") == "a swift arctic fox"

    def test_landscape_size(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            provider.generate("a fox", aspect_ratio="landscape")
        assert fake_client.images.generate.call_args.kwargs["size"] == "1536x1024"

    def test_portrait_size(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = _fake_url_client()
        with patch("openai.OpenAI", return_value=fake_client):
            provider.generate("a fox", aspect_ratio="portrait")
        assert fake_client.images.generate.call_args.kwargs["size"] == "1024x1536"


# ---------------------------------------------------------------------------
# generate() — error paths
# ---------------------------------------------------------------------------

class TestGenerateErrors:
    def test_empty_prompt_returns_error(self, provider, monkeypatch):
        _set_creds(monkeypatch)
        result = provider.generate("")
        assert result["success"] is False
        assert result["error_type"] == "invalid_argument"

    def test_missing_credentials_returns_auth_error(self, provider, monkeypatch, tmp_path):
        for k in ("AZURE_FOUNDRY_IMAGE_KEY", "AZURE_FOUNDRY_IMAGE_ENDPOINT"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "auth_required"

    def test_missing_openai_package_returns_error(self, provider, monkeypatch):
        _set_creds(monkeypatch)
        with patch.dict(sys.modules, {"openai": None}):
            result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "missing_dependency"

    def test_api_error_returns_api_error(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_client = MagicMock()
        fake_client.images.generate.side_effect = RuntimeError("quota exceeded")
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "api_error"
        assert "quota exceeded" in result["error"]

    def test_empty_response_returns_error(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_resp = MagicMock()
        fake_resp.data = []
        fake_client = MagicMock()
        fake_client.images.generate.return_value = fake_resp
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "empty_response"

    def test_no_b64_or_url_returns_error(self, provider, monkeypatch, tmp_path):
        _set_creds(monkeypatch)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        fake_item = MagicMock()
        fake_item.b64_json = None
        fake_item.url = None
        fake_resp = MagicMock()
        fake_resp.data = [fake_item]
        fake_client = MagicMock()
        fake_client.images.generate.return_value = fake_resp
        with patch("openai.OpenAI", return_value=fake_client):
            result = provider.generate("a cat")
        assert result["success"] is False
        assert result["error_type"] == "empty_response"


# ---------------------------------------------------------------------------
# is_available()
# ---------------------------------------------------------------------------

class TestIsAvailable:
    def test_false_when_no_env(self, provider, monkeypatch, tmp_path):
        for k in ("AZURE_FOUNDRY_IMAGE_KEY", "AZURE_FOUNDRY_IMAGE_ENDPOINT"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        assert not provider.is_available()

    def test_false_when_only_key(self, provider, monkeypatch, tmp_path):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_KEY", "sk-test")
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_ENDPOINT", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        assert not provider.is_available()

    def test_false_when_only_endpoint(self, provider, monkeypatch, tmp_path):
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_KEY", raising=False)
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_ENDPOINT", "https://my.openai.azure.com")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        assert not provider.is_available()

    def test_true_when_both_set(self, provider, monkeypatch):
        _set_creds(monkeypatch)
        assert provider.is_available()


# ---------------------------------------------------------------------------
# list_models()
# ---------------------------------------------------------------------------

class TestListModels:
    def test_returns_list(self, provider):
        assert isinstance(provider.list_models(), list)

    def test_includes_default_deployment(self, provider, monkeypatch, tmp_path):
        monkeypatch.delenv("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        ids = [m["id"] for m in provider.list_models()]
        assert "gpt-image-2" in ids

    def test_custom_deployment_shown(self, provider, monkeypatch):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", "my-custom-deploy")
        ids = [m["id"] for m in provider.list_models()]
        assert "my-custom-deploy" in ids

    def test_no_dalle(self, provider, monkeypatch, tmp_path):
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        ids = [m["id"] for m in provider.list_models()]
        assert not any("dall-e" in mid for mid in ids)


# ---------------------------------------------------------------------------
# get_setup_schema()
# ---------------------------------------------------------------------------

class TestSetupSchema:
    def test_has_name(self, provider):
        assert "name" in provider.get_setup_schema()

    def test_has_env_vars(self, provider):
        # env_vars may be empty when setup_interactive() handles setup
        assert isinstance(provider.get_setup_schema()["env_vars"], list)

    def test_has_badge(self, provider):
        assert "badge" in provider.get_setup_schema()


# ---------------------------------------------------------------------------
# Plugin register()
# ---------------------------------------------------------------------------

class TestRegister:
    def test_register_calls_ctx(self, plugin):
        ctx = MagicMock()
        plugin.register(ctx)
        ctx.register_image_gen_provider.assert_called_once()

    def test_registered_provider_name(self, plugin):
        captured = []
        ctx = MagicMock()
        ctx.register_image_gen_provider.side_effect = lambda p: captured.append(p)
        plugin.register(ctx)
        assert captured[0].name == "azure-foundry"


# ---------------------------------------------------------------------------
# Credential / config resolution
# ---------------------------------------------------------------------------

class TestConfigResolution:
    def test_load_config_from_yaml(self, plugin, monkeypatch, tmp_path):
        monkeypatch.setenv("MY_AZURE_KEY", "key-from-env")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            "image_gen:\n"
            "  azure_foundry:\n"
            "    endpoint: \"https://my.openai.azure.com\"\n"
            "    api_key_env: MY_AZURE_KEY\n"
            "    deployment_name: gpt-image-2\n"
            "    api_version: \"2025-04-01-preview\"\n"
        )
        cfg = plugin._load_azure_foundry_config()
        assert cfg.get("endpoint") == "https://my.openai.azure.com"
        assert cfg.get("deployment_name") == "gpt-image-2"

    def test_resolve_credentials_from_env(self, plugin, monkeypatch, tmp_path):
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_KEY", "sk-test")
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_ENDPOINT", "https://env.openai.azure.com")
        monkeypatch.setenv("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", "my-deploy")
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text("image_gen: {}\n")
        creds = plugin._resolve_credentials()
        assert creds["api_key"] == "sk-test"
        assert creds["endpoint"] == "https://env.openai.azure.com"
        assert creds["deployment"] == "my-deploy"

    def test_resolve_credentials_from_config_endpoint(self, plugin, monkeypatch, tmp_path):
        """Endpoint and deployment resolve from config.yaml when env vars absent."""
        for k in ("AZURE_FOUNDRY_IMAGE_KEY", "AZURE_FOUNDRY_IMAGE_ENDPOINT",
                  "AZURE_FOUNDRY_IMAGE_DEPLOYMENT"):
            monkeypatch.delenv(k, raising=False)
        monkeypatch.setenv("HERMES_HOME", str(tmp_path))
        (tmp_path / "config.yaml").write_text(
            "image_gen:\n"
            "  azure_foundry:\n"
            "    endpoint: \"https://cfg.openai.azure.com\"\n"
            "    deployment_name: cfg-deploy\n"
        )
        creds = plugin._resolve_credentials()
        assert creds["endpoint"] == "https://cfg.openai.azure.com"
        assert creds["deployment"] == "cfg-deploy"
