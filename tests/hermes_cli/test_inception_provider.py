"""Tests for Inception provider support — standard direct, OpenAI-compatible
API provider wired purely through its ``ProviderProfile`` plugin.

Inception serves the Mercury family of diffusion LLMs at
``https://api.inceptionlabs.ai/v1`` over the OpenAI ``chat/completions`` API,
so it needs no ``HERMES_OVERLAYS`` entry, URL→provider mapping, or
prefix-strip rule — the profile auto-wires the registry, picker, and runtime
credential resolution. These tests assert that auto-wiring, plus the curated
``mercury-2``-only catalog and the picker ordering (right before DeepSeek).
"""

import pytest

from hermes_cli.auth import (
    PROVIDER_REGISTRY,
    resolve_provider,
    get_api_key_provider_status,
    resolve_api_key_provider_credentials,
)


_OTHER_PROVIDER_KEYS = (
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "DEEPSEEK_API_KEY",
    "GOOGLE_API_KEY", "GEMINI_API_KEY", "DASHSCOPE_API_KEY",
    "XAI_API_KEY", "KIMI_API_KEY", "KIMI_CN_API_KEY",
    "MINIMAX_API_KEY", "MINIMAX_CN_API_KEY",
    "KILOCODE_API_KEY", "HF_TOKEN", "GLM_API_KEY", "ZAI_API_KEY",
    "XIAOMI_API_KEY", "TOKENHUB_API_KEY", "ARCEEAI_API_KEY",
    "COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN",
)


# =============================================================================
# Provider profile (the single source of truth)
# =============================================================================


class TestInceptionProfile:
    def test_registered(self):
        from providers import get_provider_profile
        assert get_provider_profile("inception") is not None

    def test_profile_fields(self):
        from providers import get_provider_profile
        p = get_provider_profile("inception")
        assert p.name == "inception"
        assert p.display_name == "Inception"
        assert p.base_url == "https://api.inceptionlabs.ai/v1"
        assert p.auth_type == "api_key"
        assert "INCEPTION_API_KEY" in p.env_vars
        assert "INCEPTION_BASE_URL" in p.env_vars

    @pytest.mark.parametrize("alias", ["inception-labs", "inceptionlabs"])
    def test_profile_alias_resolves(self, alias):
        from providers import get_provider_profile
        assert get_provider_profile(alias).name == "inception"

    def test_fetch_models_pinned_to_mercury_2(self):
        """fetch_models is deliberately pinned: only mercury-2 is surfaced,
        regardless of what the live /v1/models endpoint returns."""
        from providers import get_provider_profile
        p = get_provider_profile("inception")
        assert p.fetch_models(api_key="anything") == ["mercury-2"]
        assert p.fallback_models == ("mercury-2",)


# =============================================================================
# Provider registry (auth.py — auto-extended from the api-key profile)
# =============================================================================


class TestInceptionProviderRegistry:
    def test_registered(self):
        assert "inception" in PROVIDER_REGISTRY

    def test_name(self):
        assert PROVIDER_REGISTRY["inception"].name == "Inception"

    def test_auth_type(self):
        assert PROVIDER_REGISTRY["inception"].auth_type == "api_key"

    def test_inference_base_url(self):
        assert (
            PROVIDER_REGISTRY["inception"].inference_base_url
            == "https://api.inceptionlabs.ai/v1"
        )

    def test_api_key_env_vars(self):
        assert PROVIDER_REGISTRY["inception"].api_key_env_vars == ("INCEPTION_API_KEY",)

    def test_base_url_env_var(self):
        assert PROVIDER_REGISTRY["inception"].base_url_env_var == "INCEPTION_BASE_URL"


# =============================================================================
# Aliases (auth resolution)
# =============================================================================


class TestInceptionAliases:
    @pytest.mark.parametrize("alias", ["inception", "inception-labs", "inceptionlabs"])
    def test_alias_resolves(self, alias, monkeypatch):
        for key in _OTHER_PROVIDER_KEYS + ("OPENROUTER_API_KEY",):
            monkeypatch.delenv(key, raising=False)
        monkeypatch.setenv("INCEPTION_API_KEY", "inc-test-12345")
        assert resolve_provider(alias) == "inception"


# =============================================================================
# Credentials
# =============================================================================


class TestInceptionCredentials:
    def test_status_configured(self, monkeypatch):
        monkeypatch.setenv("INCEPTION_API_KEY", "inc-test")
        assert get_api_key_provider_status("inception")["configured"]

    def test_status_not_configured(self, monkeypatch):
        for key in _OTHER_PROVIDER_KEYS + ("OPENROUTER_API_KEY", "INCEPTION_API_KEY"):
            monkeypatch.delenv(key, raising=False)
        assert not get_api_key_provider_status("inception")["configured"]

    def test_openrouter_key_does_not_make_inception_configured(self, monkeypatch):
        """OpenRouter users should NOT see inception as configured."""
        monkeypatch.delenv("INCEPTION_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
        assert not get_api_key_provider_status("inception")["configured"]

    def test_resolve_credentials(self, monkeypatch):
        monkeypatch.setenv("INCEPTION_API_KEY", "inc-direct-key")
        monkeypatch.delenv("INCEPTION_BASE_URL", raising=False)
        creds = resolve_api_key_provider_credentials("inception")
        assert creds["api_key"] == "inc-direct-key"
        assert creds["base_url"] == "https://api.inceptionlabs.ai/v1"

    def test_custom_base_url_override(self, monkeypatch):
        monkeypatch.setenv("INCEPTION_API_KEY", "inc-x")
        monkeypatch.setenv("INCEPTION_BASE_URL", "https://staging.inceptionlabs.ai/v1")
        creds = resolve_api_key_provider_credentials("inception")
        assert creds["base_url"] == "https://staging.inceptionlabs.ai/v1"


# =============================================================================
# Model catalog + picker
# =============================================================================


class TestInceptionModelCatalog:
    def test_static_model_list(self):
        from hermes_cli.models import _PROVIDER_MODELS
        assert _PROVIDER_MODELS["inception"] == ["mercury-2"]

    def test_provider_model_ids(self):
        from hermes_cli.models import provider_model_ids
        assert provider_model_ids("inception") == ["mercury-2"]

    def test_canonical_provider_entry(self):
        from hermes_cli.models import CANONICAL_PROVIDERS
        entry = next(p for p in CANONICAL_PROVIDERS if p.slug == "inception")
        assert entry.label == "Inception"
        assert entry.tui_desc == "Inception (direct Inception API)"

    def test_label(self):
        from hermes_cli.models import _PROVIDER_LABELS
        assert _PROVIDER_LABELS["inception"] == "Inception"

    def test_ordered_immediately_before_deepseek(self):
        """The picker lists Inception right after the Google providers and
        immediately before DeepSeek (explicit placement, not auto-appended)."""
        from hermes_cli.models import CANONICAL_PROVIDERS
        slugs = [p.slug for p in CANONICAL_PROVIDERS]
        assert slugs[slugs.index("inception") + 1] == "deepseek"
        assert slugs[slugs.index("inception") - 1] == "google-gemini-cli"
