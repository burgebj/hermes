"""Inception provider profile.

Inception (https://www.inceptionlabs.ai/) serves the Mercury family of
diffusion LLMs behind an OpenAI-compatible API at
``https://api.inceptionlabs.ai/v1``. Standard ``/v1/chat/completions`` —
so the default ``chat_completions`` transport applies and no
``HERMES_OVERLAYS`` entry is needed.

We deliberately surface only ``mercury-2`` in the picker (the live
``/v1/models`` endpoint may list additional models), so ``fetch_models``
is pinned to that single id.
"""

from __future__ import annotations

from providers import register_provider
from providers.base import ProviderProfile


class InceptionProfile(ProviderProfile):
    """Inception — direct Inception API, only mercury-2 surfaced."""

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        # Pin the picker to mercury-2 regardless of what the live catalog
        # returns. Returning the curated list (rather than None) keeps the
        # picker fast and deterministic without a network round-trip.
        return ["mercury-2"]


inception = InceptionProfile(
    name="inception",
    aliases=("inception-labs", "inceptionlabs"),
    display_name="Inception",
    description="Inception (direct Inception API)",
    signup_url="https://platform.inceptionlabs.ai/",
    env_vars=("INCEPTION_API_KEY", "INCEPTION_BASE_URL"),
    base_url="https://api.inceptionlabs.ai/v1",
    auth_type="api_key",
    default_aux_model="mercury-2",
    fallback_models=("mercury-2",),
)

register_provider(inception)
