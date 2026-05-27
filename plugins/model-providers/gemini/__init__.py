"""Google Gemini provider profiles.

gemini:            Google AI Studio (API key) — uses GeminiNativeClient
google-gemini-cli: Google Cloud Code Assist (OAuth) — uses GeminiCloudCodeClient

Both report api_mode="chat_completions" but use custom native clients
that bypass the standard OpenAI transport. The profile captures auth
and endpoint metadata for auth.py / runtime_provider.py migration, and
carries the thinking_config translation hook so the transport's profile
path produces the same extra_body shape the legacy flag path did.
"""

from typing import Any

from providers import register_provider
from providers.base import ProviderProfile


class GeminiProfile(ProviderProfile):
    """Gemini — translate reasoning_config to thinking_config in extra_body."""

    def cache_strategy_for(self, model: str) -> Any:
        # Only the API-key Gemini provider supports context caching.
        # google-gemini-cli uses Cloud Code OAuth and a different auth path.
        if self.name == "gemini" and "gemini" in model.lower():
            from agent.prompt_cache_strategy import GeminiResourceCacheStrategy
            return GeminiResourceCacheStrategy()
        return super().cache_strategy_for(model)

    def build_extra_body(
        self, *, session_id: str | None = None, **context: Any
    ) -> dict[str, Any]:
        """Emit thinking_config and (when available) gemini_cached_content_name."""
        from agent.transports.chat_completions import (
            _build_gemini_thinking_config,
            _is_gemini_openai_compat_base_url,
            _snake_case_gemini_thinking_config,
        )

        model = context.get("model") or ""
        reasoning_config = context.get("reasoning_config")
        base_url = context.get("base_url") or self.base_url

        body: dict[str, Any] = {}

        raw_thinking_config = _build_gemini_thinking_config(model, reasoning_config)
        if raw_thinking_config:
            if self.name == "gemini" and _is_gemini_openai_compat_base_url(base_url):
                thinking_config = _snake_case_gemini_thinking_config(raw_thinking_config)
                if thinking_config:
                    body["extra_body"] = {"google": {"thinking_config": thinking_config}}
            else:
                body["thinking_config"] = raw_thinking_config

        cache_name = context.get("gemini_cached_content_name")
        if cache_name:
            body["gemini_cached_content_name"] = cache_name

        return body


gemini = GeminiProfile(
    name="gemini",
    aliases=("google", "google-gemini", "google-ai-studio"),
    api_mode="chat_completions",
    env_vars=("GOOGLE_API_KEY", "GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta",
    auth_type="api_key",
    default_aux_model="gemini-3-flash-preview",
)

google_gemini_cli = GeminiProfile(
    name="google-gemini-cli",
    aliases=("gemini-cli", "gemini-oauth"),
    api_mode="chat_completions",
    env_vars=(),  # OAuth — no API key
    base_url="cloudcode-pa://google",  # Cloud Code Assist internal scheme
    auth_type="oauth_external",
)

register_provider(gemini)
register_provider(google_gemini_cli)
