"""Focused tests for the Neosantara model provider profile."""

from __future__ import annotations


def test_neosantara_profile_fields():
    from providers import get_provider_profile

    profile = get_provider_profile("neosantara")

    assert profile is not None
    assert profile.name == "neosantara"
    assert profile.aliases == ("ns",)
    assert profile.display_name == "Neosantara"
    assert profile.signup_url == "https://app.neosantara.xyz/api-keys"
    assert profile.env_vars == (
        "NEOSANTARA_API_KEY",
        "NEOSANTARA_BASE_URL",
    )
    assert profile.base_url == "https://api.neosantara.xyz/v1"
    assert profile.models_url == "https://api.neosantara.xyz/v1/models"
    assert profile.default_aux_model == "garda-core"
    assert profile.fallback_models


def test_neosantara_provider_alias_resolves():
    from providers import get_provider_profile

    assert get_provider_profile("ns").name == "neosantara"


def test_neosantara_auto_registers_auth_config():
    from hermes_cli.auth import PROVIDER_REGISTRY

    config = PROVIDER_REGISTRY["neosantara"]

    assert config.name == "Neosantara"
    assert config.auth_type == "api_key"
    assert config.inference_base_url == "https://api.neosantara.xyz/v1"
    assert config.api_key_env_vars == ("NEOSANTARA_API_KEY",)
    assert config.base_url_env_var == "NEOSANTARA_BASE_URL"


def test_neosantara_env_vars_are_exposed_to_setup():
    from hermes_cli.config import OPTIONAL_ENV_VARS

    assert OPTIONAL_ENV_VARS["NEOSANTARA_API_KEY"]["url"] == (
        "https://app.neosantara.xyz/api-keys"
    )
    assert OPTIONAL_ENV_VARS["NEOSANTARA_API_KEY"]["category"] == "provider"
    assert OPTIONAL_ENV_VARS["NEOSANTARA_API_KEY"]["password"] is True
    assert OPTIONAL_ENV_VARS["NEOSANTARA_BASE_URL"]["password"] is False


def test_neosantara_provider_model_ids_falls_back_to_profile_models(monkeypatch):
    from providers import get_provider_profile
    from hermes_cli.models import provider_model_ids

    monkeypatch.setattr(
        "hermes_cli.auth.resolve_api_key_provider_credentials",
        lambda provider_id: {
            "provider": provider_id,
            "api_key": "",
            "base_url": "https://api.neosantara.xyz/v1",
            "source": "test",
        },
    )

    models = provider_model_ids("neosantara")

    assert models == list(get_provider_profile("neosantara").fallback_models)
