"""Apertis AI provider profile."""

from providers import register_provider
from providers.base import ProviderProfile

apertis = ProviderProfile(
    name="apertis",
    aliases=("apertis-ai", "apertis-api"),
    display_name="Apertis AI",
    description="Apertis AI — multi-model inference platform",
    signup_url="https://apertis.ai/",
    env_vars=("APERTIS_API_KEY", "APERTIS_BASE_URL"),
    base_url="https://api.apertis.ai/v1",
    auth_type="api_key",
    default_aux_model="gpt-5.4-mini",
    fallback_models=(
        "claude-opus-4-7",
        "claude-sonnet-4-6",
        "gpt-5.5",
        "deepseek-v4-pro",
        "glm-5.1",
    ),
)

register_provider(apertis)
