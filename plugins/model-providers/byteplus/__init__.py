"""BytePlus Ark provider profile."""

from hermes_cli.ark_providers import (
    BYTEPLUS_BASE_URL,
    BYTEPLUS_DEFAULT_MODEL,
    BYTEPLUS_PROVIDER,
    BYTEPLUS_STANDARD_MODELS,
    StaticArkProviderProfile,
)
from providers import register_provider

byteplus = StaticArkProviderProfile(
    name=BYTEPLUS_PROVIDER,
    aliases=("byteplus-api", "byteplus-standard"),
    display_name="BytePlus",
    description="BytePlus ModelArk — direct API key endpoint",
    signup_url="https://console.byteplus.com/ark",
    env_vars=("BYTEPLUS_API_KEY", "BYTEPLUS_BASE_URL"),
    base_url=BYTEPLUS_BASE_URL,
    auth_type="api_key",
    supports_health_check=False,
    fallback_models=BYTEPLUS_STANDARD_MODELS,
    default_aux_model=BYTEPLUS_DEFAULT_MODEL,
)

register_provider(byteplus)
