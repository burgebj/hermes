"""Google Gemini image generation backend.

Provides a pluggable image_gen provider for Google's Gemini image models via
OpenAI-compatible endpoints. This preserves 北冥's local Google/Gemini image
workflow while fitting Hermes v0.11's plugin image generation architecture.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_b64_image,
    success_response,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash-image"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

_SIZES = {
    "landscape": "1536x1024",
    "square": "1024x1024",
    "portrait": "1024x1536",
}


def _api_key() -> str:
    # Prefer GOOGLE_API_KEY; GEMINI_API_KEY is accepted for compatibility.
    return (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()


def _base_url() -> str:
    return (os.environ.get("GEMINI_BASE_URL") or os.environ.get("GOOGLE_IMAGE_BASE_URL") or DEFAULT_BASE_URL).strip()


def _model() -> str:
    return (os.environ.get("GOOGLE_IMAGE_MODEL") or os.environ.get("GEMINI_IMAGE_MODEL") or DEFAULT_MODEL).strip()


class GoogleImageGenProvider(ImageGenProvider):
    @property
    def name(self) -> str:
        return "google"

    @property
    def display_name(self) -> str:
        return "Google Gemini"

    def is_available(self) -> bool:
        if not _api_key():
            return False
        try:
            import openai  # noqa: F401
        except ImportError:
            return False
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return [{
            "id": DEFAULT_MODEL,
            "display": "Gemini 2.5 Flash Image",
            "speed": "varies",
            "strengths": "Google/Gemini image generation via OpenAI-compatible API",
            "price": "varies",
        }]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Google Gemini",
            "badge": "paid/free-tier",
            "tag": "Gemini image generation via GOOGLE_API_KEY or GEMINI_API_KEY",
            "env_vars": [
                {
                    "key": "GOOGLE_API_KEY",
                    "prompt": "Google AI Studio API key",
                    "url": "https://aistudio.google.com/app/apikey",
                },
                {
                    "key": "GEMINI_API_KEY",
                    "prompt": "Gemini API key (alternative)",
                    "url": "https://aistudio.google.com/app/apikey",
                },
            ],
        }

    def generate(self, prompt: str, aspect_ratio: str = DEFAULT_ASPECT_RATIO, **kwargs: Any) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)
        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="google",
                aspect_ratio=aspect,
            )
        key = _api_key()
        if not key:
            return error_response(
                error="GOOGLE_API_KEY or GEMINI_API_KEY not set",
                error_type="auth_required",
                provider="google",
                prompt=prompt,
                aspect_ratio=aspect,
            )
        try:
            import openai
        except ImportError:
            return error_response(
                error="openai Python package not installed",
                error_type="missing_dependency",
                provider="google",
                prompt=prompt,
                aspect_ratio=aspect,
            )

        model = _model()
        size = _SIZES.get(aspect, _SIZES["square"])
        client = openai.OpenAI(api_key=key, base_url=_base_url())
        try:
            response = client.images.generate(model=model, prompt=prompt, size=size, n=1)
        except Exception as exc:
            logger.debug("Google image generation failed", exc_info=True)
            return error_response(
                error=f"Google image generation failed: {exc}",
                error_type="api_error",
                provider="google",
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        data = getattr(response, "data", None) or []
        if not data:
            return error_response(
                error="Google image API returned no image data",
                error_type="empty_response",
                provider="google",
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        first = data[0]
        b64 = getattr(first, "b64_json", None)
        url = getattr(first, "url", None)
        if b64:
            try:
                image_ref = str(save_b64_image(b64, prefix="google_gemini_image"))
            except Exception as exc:
                return error_response(
                    error=f"Could not save image to cache: {exc}",
                    error_type="io_error",
                    provider="google",
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
        elif url:
            image_ref = url
        else:
            return error_response(
                error="Google response contained neither b64_json nor URL",
                error_type="empty_response",
                provider="google",
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=image_ref,
            model=model,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="google",
            extra={"size": size, "base_url": _base_url()},
        )


def register(ctx) -> None:
    ctx.register_image_gen_provider(GoogleImageGenProvider())
