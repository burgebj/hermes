"""Google image generation backend.

Wires the Gemini API's two image-gen surfaces into hermes' ``image_gen``
provider slot:

* **Imagen 4** family (``imagen-4.0-fast-generate-001``,
  ``imagen-4.0-generate-001``, ``imagen-4.0-ultra-generate-001``) via
  the ``:predict`` endpoint.
* **Gemini flash/pro image** models (``gemini-2.5-flash-image``,
  ``gemini-3.1-flash-image-preview``, ``gemini-3-pro-image-preview``)
  via ``:generateContent`` with ``responseModalities=["IMAGE"]``.

Auth: ``GEMINI_API_KEY`` (preferred) or ``GOOGLE_API_KEY``. Both endpoints
require Tier 1 (paid) on the project that minted the key — free-tier
quota for image gen is zero.

Selection precedence (first hit wins):
1. ``GOOGLE_IMAGE_MODEL`` env var
2. ``image_gen.google.model`` in ``config.yaml``
3. :data:`DEFAULT_MODEL`
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
#
# ``endpoint`` distinguishes the two API shapes:
#   - "predict"         → /v1beta/models/{m}:predict  (Imagen)
#   - "generateContent" → /v1beta/models/{m}:generateContent  (Gemini image)

_MODELS: Dict[str, Dict[str, Any]] = {
    "imagen-4.0-fast-generate-001": {
        "display": "Imagen 4 Fast",
        "speed": "~5s",
        "strengths": "Fast iteration, lowest cost in the Imagen 4 family",
        "endpoint": "predict",
    },
    "imagen-4.0-generate-001": {
        "display": "Imagen 4",
        "speed": "~10s",
        "strengths": "Balanced quality/cost — default Imagen 4 tier",
        "endpoint": "predict",
    },
    "imagen-4.0-ultra-generate-001": {
        "display": "Imagen 4 Ultra",
        "speed": "~20s",
        "strengths": "Highest fidelity, strongest prompt adherence",
        "endpoint": "predict",
    },
    "gemini-2.5-flash-image": {
        "display": "Gemini 2.5 Flash Image (Nano Banana)",
        "speed": "~5s",
        "strengths": "Conversational image edits, multimodal grounding",
        "endpoint": "generateContent",
    },
    "gemini-3.1-flash-image-preview": {
        "display": "Gemini 3.1 Flash Image (preview)",
        "speed": "~5s",
        "strengths": "Newer flash-tier image model",
        "endpoint": "generateContent",
    },
    "gemini-3-pro-image-preview": {
        "display": "Gemini 3 Pro Image (preview)",
        "speed": "~15s",
        "strengths": "Pro-tier reasoning + image generation",
        "endpoint": "generateContent",
    },
}

DEFAULT_MODEL = "imagen-4.0-fast-generate-001"

# Imagen accepts explicit aspect ratios; Gemini flash-image infers from the prompt.
_IMAGEN_ASPECTS: Dict[str, str] = {
    "landscape": "16:9",
    "square": "1:1",
    "portrait": "9:16",
}

API_BASE = "https://generativelanguage.googleapis.com/v1beta"


# ---------------------------------------------------------------------------
# Config / model resolution
# ---------------------------------------------------------------------------


def _load_google_config() -> Dict[str, Any]:
    """Read ``image_gen.google`` from config.yaml (returns {} on failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        google_section = section.get("google") if isinstance(section, dict) else None
        return google_section if isinstance(google_section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen.google config: %s", exc)
        return {}


def _resolve_model() -> Tuple[str, Dict[str, Any]]:
    """Decide which model to use and return ``(model_id, meta)``."""
    env_override = os.environ.get("GOOGLE_IMAGE_MODEL")
    if env_override and env_override in _MODELS:
        return env_override, _MODELS[env_override]

    cfg = _load_google_config()
    candidate = cfg.get("model") if isinstance(cfg.get("model"), str) else None
    if candidate and candidate in _MODELS:
        return candidate, _MODELS[candidate]

    return DEFAULT_MODEL, _MODELS[DEFAULT_MODEL]


def _resolve_api_key() -> str:
    return (
        os.getenv("GEMINI_API_KEY", "").strip()
        or os.getenv("GOOGLE_API_KEY", "").strip()
    )


# ---------------------------------------------------------------------------
# Endpoint dispatchers
# ---------------------------------------------------------------------------


def _call_imagen(
    *, api_key: str, model_id: str, prompt: str, aspect: str
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Hit Imagen's ``:predict`` endpoint. Returns ``(b64_png, error_dict)``."""
    url = f"{API_BASE}/models/{model_id}:predict"
    payload: Dict[str, Any] = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": _IMAGEN_ASPECTS.get(aspect, "1:1"),
        },
    }
    try:
        resp = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=120,
        )
    except requests.Timeout:
        return None, {"error": "Imagen request timed out (120s)", "error_type": "timeout"}
    except requests.ConnectionError as exc:
        return None, {"error": f"Connection error: {exc}", "error_type": "connection_error"}

    if resp.status_code != 200:
        try:
            err_msg = resp.json().get("error", {}).get("message", resp.text[:300])
        except Exception:
            err_msg = resp.text[:300]
        return None, {
            "error": f"Imagen API failed ({resp.status_code}): {err_msg}",
            "error_type": "api_error",
        }

    try:
        body = resp.json()
    except Exception as exc:
        return None, {"error": f"Imagen returned invalid JSON: {exc}", "error_type": "invalid_response"}

    preds = body.get("predictions") or []
    if not preds:
        return None, {"error": "Imagen returned no predictions", "error_type": "empty_response"}
    b64 = preds[0].get("bytesBase64Encoded")
    if not b64:
        return None, {"error": "Imagen prediction missing bytesBase64Encoded", "error_type": "empty_response"}
    return b64, None


def _call_gemini_image(
    *, api_key: str, model_id: str, prompt: str
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Hit Gemini's ``:generateContent`` with IMAGE response modality."""
    url = f"{API_BASE}/models/{model_id}:generateContent"
    payload: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    }
    try:
        resp = requests.post(
            url,
            params={"key": api_key},
            json=payload,
            timeout=120,
        )
    except requests.Timeout:
        return None, {"error": "Gemini request timed out (120s)", "error_type": "timeout"}
    except requests.ConnectionError as exc:
        return None, {"error": f"Connection error: {exc}", "error_type": "connection_error"}

    if resp.status_code != 200:
        try:
            err_msg = resp.json().get("error", {}).get("message", resp.text[:300])
        except Exception:
            err_msg = resp.text[:300]
        return None, {
            "error": f"Gemini API failed ({resp.status_code}): {err_msg}",
            "error_type": "api_error",
        }

    try:
        body = resp.json()
    except Exception as exc:
        return None, {"error": f"Gemini returned invalid JSON: {exc}", "error_type": "invalid_response"}

    cands = body.get("candidates") or []
    if not cands:
        return None, {"error": "Gemini returned no candidates", "error_type": "empty_response"}
    parts = (cands[0].get("content") or {}).get("parts") or []
    for part in parts:
        inline = part.get("inlineData") or part.get("inline_data")
        if isinstance(inline, dict) and inline.get("data"):
            return inline["data"], None
    return None, {"error": "Gemini response had no image inlineData", "error_type": "empty_response"}


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class GoogleImageGenProvider(ImageGenProvider):
    """Google Gemini API image generation backend (Imagen + flash-image)."""

    @property
    def name(self) -> str:
        return "google"

    @property
    def display_name(self) -> str:
        return "Google (Imagen + Gemini)"

    def is_available(self) -> bool:
        return bool(_resolve_api_key())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta.get("display", model_id),
                "speed": meta.get("speed", ""),
                "strengths": meta.get("strengths", ""),
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Google (Imagen + Gemini)",
            "badge": "paid",
            "tag": "Imagen 4 family + Gemini flash-image via Gemini API (Tier 1 required)",
            "env_vars": [
                {
                    "key": "GEMINI_API_KEY",
                    "prompt": "Gemini API key (or GOOGLE_API_KEY)",
                    "url": "https://aistudio.google.com/apikey",
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
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="google",
                aspect_ratio=aspect,
            )

        api_key = _resolve_api_key()
        if not api_key:
            return error_response(
                error=(
                    "GEMINI_API_KEY (or GOOGLE_API_KEY) not set. Get a key at "
                    "https://aistudio.google.com/apikey — note that image-gen "
                    "models require Tier 1 (paid) billing on the project."
                ),
                error_type="auth_required",
                provider="google",
                aspect_ratio=aspect,
            )

        model_id, meta = _resolve_model()
        endpoint = meta.get("endpoint", "predict")

        if endpoint == "predict":
            b64, err = _call_imagen(
                api_key=api_key, model_id=model_id, prompt=prompt, aspect=aspect
            )
        else:
            b64, err = _call_gemini_image(
                api_key=api_key, model_id=model_id, prompt=prompt
            )

        if err:
            return error_response(
                provider="google",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
                **err,
            )

        try:
            saved_path = save_b64_image(b64, prefix=f"google_{model_id}")
        except Exception as exc:
            return error_response(
                error=f"Could not save image to cache: {exc}",
                error_type="io_error",
                provider="google",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {"endpoint": endpoint}
        if endpoint == "predict":
            extra["aspect_ratio_sent"] = _IMAGEN_ASPECTS.get(aspect, "1:1")

        return success_response(
            image=str(saved_path),
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="google",
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx: Any) -> None:
    """Plugin entry point — wire ``GoogleImageGenProvider`` into the registry."""
    ctx.register_image_gen_provider(GoogleImageGenProvider())
