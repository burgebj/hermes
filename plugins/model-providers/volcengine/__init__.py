"""Volcengine Ark provider profile."""

from hermes_cli.ark_providers import (
    VOLCENGINE_BASE_URL,
    VOLCENGINE_DEFAULT_MODEL,
    VOLCENGINE_PROVIDER,
    VOLCENGINE_STANDARD_MODELS,
    StaticArkProviderProfile,
)
from providers import register_provider

volcengine = StaticArkProviderProfile(
    name=VOLCENGINE_PROVIDER,
    aliases=(
        "volcano",
        "volcano-engine",
        "volcengine-api",
        "volcengine-standard",
    ),
    display_name="Volcengine",
    description="Volcengine Ark — direct API key endpoint",
    signup_url="https://console.volcengine.com/ark",
    env_vars=("VOLCENGINE_API_KEY", "VOLCENGINE_BASE_URL"),
    base_url=VOLCENGINE_BASE_URL,
    auth_type="api_key",
    supports_health_check=False,
    fallback_models=VOLCENGINE_STANDARD_MODELS,
    default_aux_model=VOLCENGINE_DEFAULT_MODEL,
)

register_provider(volcengine)
