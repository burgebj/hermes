"""DGX Spark Ollama provider profile.

Registers the DGX Spark as a named provider so it appears in `hermes model`
alongside OpenRouter, Anthropic, etc. Selecting it queries the active DGX
node's Ollama endpoint for the model list.

The base_url tracks whichever node is active via `hermes dgx node use <name>`;
it is re-read at fetch_models() time so mid-session node switches are reflected.

No API key is required — Ollama on the DGX is unauthenticated.
"""

from __future__ import annotations

from typing import Any, Optional

from providers import register_provider
from providers.base import ProviderProfile


def _dgx_ollama_url() -> Optional[str]:
    """Read the active DGX node's Ollama URL from config.

    Returns None when no DGX host is configured yet — the provider then sits
    in the picker as inert until the user runs ``hermes dgx setup``.
    """
    try:
        from plugins.dgx._dgx_config import load_dgx_config, ollama_base
        return ollama_base(load_dgx_config()) + "/v1"
    except Exception:
        return None


class DGXOllamaProfile(ProviderProfile):
    """DGX Spark Ollama — Ollama quirks + dynamic URL from dgx config."""

    def build_api_kwargs_extras(
        self,
        *,
        reasoning_config: dict | None = None,
        ollama_num_ctx: int | None = None,
        **ctx: Any,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        extra_body: dict[str, Any] = {}
        # Ollama context window override
        if ollama_num_ctx:
            extra_body.setdefault("options", {})["num_ctx"] = ollama_num_ctx
        # Disable extended thinking when reasoning is off
        if reasoning_config and isinstance(reasoning_config, dict):
            effort = (reasoning_config.get("effort") or "").strip().lower()
            enabled = reasoning_config.get("enabled", True)
            if effort == "none" or enabled is False:
                extra_body["think"] = False
        return extra_body, {}

    def fetch_models(
        self,
        *,
        api_key: str | None = None,
        timeout: float = 8.0,
    ) -> list[str] | None:
        # Refresh URL at call time — active node may have changed since import.
        # If no DGX host is configured, return None (picker falls back to
        # fallback_models or hides the provider, depending on caller).
        url = _dgx_ollama_url()
        if not url:
            return None
        self.base_url = url
        # Ollama doesn't require auth; pass a placeholder so the SDK is happy
        return super().fetch_models(api_key=api_key or "no-key-required", timeout=timeout)


dgx_ollama = DGXOllamaProfile(
    name="dgx-ollama",
    aliases=("dgx", "dgx-spark", "dgx_ollama"),
    display_name="DGX Spark (Ollama)",
    description="Local DGX Spark inference via Ollama — configure with: hermes dgx setup",
    env_vars=(),         # no API key required
    auth_type="api_key", # use OpenAI-wire protocol; hermes picker includes api_key providers
    base_url=_dgx_ollama_url() or "http://localhost:11434/v1",
    default_aux_model="nemotron-mini:4b",
    # Shown when Ollama is unreachable or returns no models
    fallback_models=(
        "nemotron3:33b",
        "qwen3-coder:30b",
        "deepseek-r1:70b",
        "qwen2.5-coder:32b",
        "qwen2.5-coder:14b",
        "codestral:22b",
        "gemma4:26b",
        "nemotron-mini:4b",
    ),
)

register_provider(dgx_ollama)
