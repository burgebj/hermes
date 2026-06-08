"""BytePlus ModelArk Coding Plan provider profile."""

from hermes_cli.ark_providers import (
    BYTEPLUS_CODING_DEFAULT_MODEL,
    BYTEPLUS_CODING_PLAN_BASE_URL,
    BYTEPLUS_CODING_PLAN_MODELS,
    BYTEPLUS_CODING_PROVIDER,
    StaticArkProviderProfile,
)
from providers import register_provider

byteplus_coding_plan = StaticArkProviderProfile(
    name=BYTEPLUS_CODING_PROVIDER,
    aliases=("byteplus_coding_plan", "byteplus-coding", "byteplus_coding"),
    display_name="BytePlus Coding Plan",
    description="BytePlus ModelArk Coding Plan — Subscription Plan",
    signup_url="https://console.byteplus.com/ark",
    env_vars=(
        "BYTEPLUS_CODING_PLAN_API_KEY",
        "BYTEPLUS_CODING_PLAN_BASE_URL",
    ),
    base_url=BYTEPLUS_CODING_PLAN_BASE_URL,
    auth_type="api_key",
    supports_health_check=False,
    fallback_models=BYTEPLUS_CODING_PLAN_MODELS,
    default_aux_model=BYTEPLUS_CODING_DEFAULT_MODEL,
)

register_provider(byteplus_coding_plan)
