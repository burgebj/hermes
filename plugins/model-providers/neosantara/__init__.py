"""Neosantara provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

neosantara = ProviderProfile(
    name="neosantara",
    aliases=("ns",),
    display_name="Neosantara",
    description="Neosantara - AI Gateway Indonesia",
    signup_url="https://app.neosantara.xyz/api-keys",
    env_vars=("NEOSANTARA_API_KEY", "NEOSANTARA_BASE_URL"),
    base_url="https://api.neosantara.xyz/v1",
    models_url="https://api.neosantara.xyz/v1/models",
    auth_type="api_key",
    default_aux_model="garda-core",
    fallback_models=(
        "garda-core",
        "neosantara-gen-2045",
        "grok-4.1-fast-non-reasoning",
        "claude-3-haiku",
        "gemini-3.1-flash-lite-preview",
    ),
)

register_provider(neosantara)
