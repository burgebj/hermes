"""OpenRouter image generation backend.

Uses OpenRouter's chat completions API with multimodal image-output models.
Supported models:

    google/gemini-3.1-flash-image-preview  ~5s   fast, cheap, good quality
    google/gemini-3-pro-image-preview       ~10s  best quality, slower
    openai/gpt-5.4-image-2                  ~20s  highest fidelity

All models return base64 image data via chat completions with
``modalities: ["image", "text"]``. Output saved under
``$HERMES_HOME/cache/images/``.

Selection precedence (first hit wins):
1. ``OPENROUTER_IMAGE_MODEL`` env var
2. ``image_gen.openrouter.model`` in ``config.yaml``
3. ``image_gen.model`` in ``config.yaml``
4. ``DEFAULT_MODEL`` — ``google/gemini-3.1-flash-image-preview``
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

_MODELS: Dict[str, Dict[str, Any]] = {
    "google/gemini-3.1-flash-image-preview": {
        "display": "Gemini 3.1 Flash Image",
        "speed": "~5s",
        "strengths": "Fast, cheap, good quality — daily driver",
    },
    "google/gemini-3-pro-image-preview": {
        "display": "Gemini 3 Pro Image",
        "speed": "~10s",
        "strengths": "Best quality, slower — for important images",
    },
    "openai/gpt-5.4-image-2": {
        "display": "GPT-5.4 Image 2",
        "speed": "~20s",
        "strengths": "Highest fidelity, best prompt adherence",
    },
}

DEFAULT_MODEL = "google/gemini-3.1-flash-image-preview"

_ASPECT_TO_SIZE: Dict[str, str] = {
    "landscape": "1536x1024",
    "square": "1024x1024",
    "portrait": "1024x1536",
}

OPENROUTER_BASE = "https://openrouter.ai/api/v1"


def _load_openrouter_config() -> Dict[str, Any]:
    """Read ``image_gen`` from config.yaml."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen config: %s", exc)
        return {}


def _resolve_model() -> Tuple[str, Dict[str, Any]]:
    """Decide which model to use."""
    env_override = os.environ.get("OPENROUTER_IMAGE_MODEL")
    if env_override and env_override in _MODELS:
        return env_override, _MODELS[env_override]

    cfg = _load_openrouter_config()
    openrouter_cfg = cfg.get("openrouter") if isinstance(cfg.get("openrouter"), dict) else {}

    candidate: Optional[str] = None
    if isinstance(openrouter_cfg, dict):
        value = openrouter_cfg.get("model")
        if isinstance(value, str) and value in _MODELS:
            candidate = value

    if candidate is None:
        top = cfg.get("model")
        if isinstance(top, str) and top in _MODELS:
            candidate = top

    if candidate is not None:
        return candidate, _MODELS[candidate]

    return DEFAULT_MODEL, _MODELS[DEFAULT_MODEL]


def _extract_image_from_response(resp_data: dict) -> Optional[str]:
    """Extract base64 image data from an OpenRouter chat completion response.

    Handles both ``images`` array (Gemini-style) and ``content`` parts (GPT-style).
    Returns base64 data URL string or None.
    """
    choices = resp_data.get("choices", [])
    if not choices:
        return None
    msg = choices[0].get("message", {})

    # Gemini-style: images array
    images = msg.get("images", [])
    if images:
        img = images[0]
        if isinstance(img, dict):
            url = img.get("image_url", {}).get("url", "") or img.get("url", "")
        else:
            url = str(img)
        if url.startswith("data:"):
            return url

    # GPT-style: content array with image_url parts
    content = msg.get("content")
    if isinstance(content, list):
        for part in content:
            if part.get("type") == "image_url":
                url = part["image_url"].get("url", "")
                if url.startswith("data:"):
                    return url

    return None


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class OpenRouterImageGenProvider(ImageGenProvider):
    """OpenRouter image generation via chat completions with multimodal models."""

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def display_name(self) -> str:
        return "OpenRouter"

    def is_available(self) -> bool:
        if not os.environ.get("OPENROUTER_API_KEY"):
            return False
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta["display"],
                "speed": meta["speed"],
                "strengths": meta["strengths"],
                "price": "varies",
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "OpenRouter",
            "badge": "paid",
            "tag": "Multimodal image generation via OpenRouter (Gemini, GPT-5.4, etc.)",
            "env_vars": [
                {
                    "key": "OPENROUTER_API_KEY",
                    "prompt": "OpenRouter API key",
                    "url": "https://openrouter.ai/keys",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        if not prompt:
            return error_response(
                error="Prompt is required",
                error_type="invalid_argument",
                provider="openrouter",
                aspect_ratio=aspect,
            )

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            return error_response(
                error="OPENROUTER_API_KEY not set. Run `hermes setup` to add the key.",
                error_type="auth_required",
                provider="openrouter",
                aspect_ratio=aspect,
            )

        model_id, meta = _resolve_model()
        size = _ASPECT_TO_SIZE.get(aspect, "1024x1024")

        payload = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": f"Generate an image: {prompt}. Size: {size}.",
                }
            ],
            "modalities": ["image", "text"],
            "max_tokens": 4096,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                f"{OPENROUTER_BASE}/chat/completions",
                json=payload,
                headers=headers,
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.debug("OpenRouter image generation failed", exc_info=True)
            return error_response(
                error=f"OpenRouter API error: {exc}",
                error_type="api_error",
                provider="openrouter",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        b64_url = _extract_image_from_response(data)
        if not b64_url:
            # Try error in response
            err = data.get("error", {})
            if err:
                return error_response(
                    error=f"OpenRouter: {err.get('message', str(err))}",
                    error_type="api_error",
                    provider="openrouter",
                    model=model_id,
                )
            return error_response(
                error="OpenRouter returned no image data",
                error_type="empty_response",
                provider="openrouter",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            # b64_url is like "data:image/png;base64,..."
            header, b64data = b64_url.split(",", 1)
            saved_path = save_b64_image(b64data, prefix=f"openrouter_{model_id.replace('/', '_')}")
        except Exception as exc:
            return error_response(
                error=f"Could not save image: {exc}",
                error_type="io_error",
                provider="openrouter",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=str(saved_path),
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="openrouter",
            extra={"model_full": model_id, "size": size},
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point."""
    ctx.register_image_gen_provider(OpenRouterImageGenProvider())
