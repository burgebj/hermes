"""Lemonade image generation backend.

Exposes lemonade's local inference server (sd-cpp / Stable Diffusion) as an
:class:`ImageGenProvider` implementation.

Models are from the lemonade collection:
- **SD-Turbo** — Lite Collection (text-to-image only)
- **Flux-2-Klein-9B-GGUF** — Ultra Collection (text-to-image + image editing)
- **Z-Image-Turbo** — Ultra Collection (text-to-image)

Features:
- Local image generation via lemonade server (sd-cpp / Stable Diffusion)
- Configurable inference steps, CFG scale, and seed
- Optional auth via ``LEMONADE_API_KEY`` (only sent when set; the default
  stock lemonade server is unauthenticated)
- Base64 or URL output both cached locally under
  ``$HERMES_HOME/cache/images/`` so the gateway never has to refetch
  an expired URL

Lemonade server runs on ``localhost:13305`` by default and exposes an
OpenAI-compatible ``/v1/images/generations`` endpoint.

Model selection precedence (first hit wins):
1. ``LEMONADE_IMAGE_MODEL`` env var
2. ``image_gen.lemonade.model`` in ``config.yaml``
3. :data:`DEFAULT_MODEL`
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
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
# Model catalog — from lemonade collection
# ---------------------------------------------------------------------------

_MODELS: Dict[str, Dict[str, Any]] = {
    "SD-Turbo": {
        "display": "SD-Turbo",
        "speed": "~1-3s",
        "strengths": "Fastest, Lite Collection, text-to-image only",
        "steps": 4,
        "cfg_scale": 1.0,
    },
    "Flux-2-Klein-9B-GGUF": {
        "display": "Flux 2 Klein 9B",
        "speed": "~15-30s",
        "strengths": "Ultra Collection, text-to-image + image editing",
        "steps": 4,
        "cfg_scale": 1.0,
    },
    "Z-Image-Turbo": {
        "display": "Z Image Turbo",
        "speed": "~3-6s",
        "strengths": "Fast distilled diffusion model, text-to-image",
        "steps": 9,
        "cfg_scale": 1.0,
    },
}

DEFAULT_MODEL = "SD-Turbo"

# Maps our aspect ratios to WIDTHxHEIGHT dimensions.
# Default resolution is 1024x1024 — works for SDXL-class models (Flux-2,
# Z-Image) and is still servable from SD-Turbo. Override per-model via
# ``image_gen.lemonade.size_<aspect>`` in config.yaml if needed.
_ASPECT_SIZES: Dict[str, str] = {
    "landscape": "1024x768",
    "square": "1024x1024",
    "portrait": "768x1024",
}

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def _load_lemonade_config() -> Dict[str, Any]:
    """Read ``image_gen.lemonade`` from ``config.yaml`` (returns {} on failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else {}
        lemonade_section = section.get("lemonade") if isinstance(section, dict) else {}
        return lemonade_section if isinstance(lemonade_section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen.lemonade config: %s", exc)
        return {}


def _load_image_gen_section() -> Dict[str, Any]:
    """Read the top-level ``image_gen`` section from ``config.yaml``."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else {}
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen config: %s", exc)
        return {}


def _resolve_model() -> Tuple[str, Dict[str, Any]]:
    """Decide which model to use and return ``(model_id, meta)``."""
    env_override = os.environ.get("LEMONADE_IMAGE_MODEL")
    if env_override and env_override in _MODELS:
        return env_override, _MODELS[env_override]

    cfg = _load_lemonade_config()
    candidate = cfg.get("model") if isinstance(cfg.get("model"), str) else None
    if candidate and candidate in _MODELS:
        return candidate, _MODELS[candidate]

    # Fallback to top-level image_gen.model
    top = _load_image_gen_section()
    top_model = top.get("model") if isinstance(top, dict) else None
    if top_model and top_model in _MODELS:
        return top_model, _MODELS[top_model]

    return DEFAULT_MODEL, _MODELS[DEFAULT_MODEL]


def _resolve_base_url() -> str:
    """Return the lemonade server base URL."""
    env_url = os.environ.get("LEMONADE_BASE_URL")
    if env_url:
        return env_url.strip().rstrip("/")
    cfg = _load_lemonade_config()
    url = cfg.get("base_url")
    if isinstance(url, str) and url.strip():
        return url.strip().rstrip("/")
    return "http://localhost:13305/api/v1"


def _resolve_steps(model_meta: Dict[str, Any]) -> Optional[int]:
    """Return configured steps, falling back to model default."""
    cfg = _load_lemonade_config()
    steps = cfg.get("steps")
    if isinstance(steps, int) and steps > 0:
        return steps
    return model_meta.get("steps")


def _resolve_cfg_scale(model_meta: Dict[str, Any]) -> Optional[float]:
    """Return configured CFG scale, falling back to model default."""
    cfg = _load_lemonade_config()
    cfg_val = cfg.get("cfg_scale")
    if isinstance(cfg_val, (int, float)) and cfg_val > 0:
        return float(cfg_val)
    return model_meta.get("cfg_scale")


def _resolve_seed() -> Optional[int]:
    """Return configured seed, or None for random."""
    cfg = _load_lemonade_config()
    seed = cfg.get("seed")
    if isinstance(seed, int) and seed >= 0:
        return seed
    return None


# ---------------------------------------------------------------------------
# URL caching
# ---------------------------------------------------------------------------


# Maximum size we will buffer for a single lemonade image. The default
# lemonade output is well under 25 MB even at 1024x1024, but cap defensively
# so a misconfigured server can't fill the disk.
_URL_CACHE_MAX_BYTES = 25 * 1024 * 1024

# Map of Content-Type → file extension. We deliberately keep this small
# (mirrors ``agent.image_gen_provider._URL_IMAGE_CONTENT_TYPES``) — the
# default lemonade server always serves ``image/png`` for SD outputs.
_URL_CONTENT_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/webp": "webp",
}


def _cache_url_bytes(url: str, *, prefix: str) -> Path:
    """Download ``url`` and write the bytes under ``$HERMES_HOME/cache/images/``.

    Inlined here (rather than depending on ``agent.image_gen_provider``'s
    :func:`save_url_image` helper) to keep this plugin self-contained —
    lemonade runs locally so the download endpoint is on ``localhost`` and
    the wire format is well known.

    Returns the absolute :class:`Path` to the cached file. Raises on any
    network / HTTP / oversize / non-image-content-type error so callers can
    fall back to the bare URL.
    """
    from agent.image_gen_provider import _images_cache_dir

    response = requests.get(url, timeout=60, stream=True)
    response.raise_for_status()

    content_type = (
        (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    )
    extension = _URL_CONTENT_TYPES.get(content_type, "png")

    import datetime as _dt
    import uuid as _uuid

    cache_dir = _images_cache_dir()
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = _uuid.uuid4().hex[:8]
    path = cache_dir / f"{prefix}_{ts}_{short}.{extension}"

    bytes_written = 0
    with path.open("wb") as fh:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            bytes_written += len(chunk)
            if bytes_written > _URL_CACHE_MAX_BYTES:
                fh.close()
                try:
                    path.unlink()
                except OSError:
                    pass
                raise ValueError(
                    f"Image at {url} exceeds {_URL_CACHE_MAX_BYTES // (1024 * 1024)}MB cap"
                )
            fh.write(chunk)

    if bytes_written == 0:
        try:
            path.unlink()
        except OSError:
            pass
        raise ValueError(f"Image at {url} returned 0 bytes")

    return path


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class LemonadeImageGenProvider(ImageGenProvider):
    """Lemonade local inference server (sd-cpp / Stable Diffusion) backend."""

    @property
    def name(self) -> str:
        return "lemonade"

    @property
    def display_name(self) -> str:
        return "Lemonade"

    def is_available(self) -> bool:
        try:
            import requests  # noqa: F401  (also imported at module top)
        except ImportError:
            return False
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta.get("display", model_id),
                "speed": meta.get("speed", ""),
                "strengths": meta.get("strengths", ""),
                "price": "free (local)",
            }
            for model_id, meta in _MODELS.items()
        ]

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Lemonade (local)",
            "badge": "free",
            "tag": "sd-cpp / Stable Diffusion — local inference server",
            "env_vars": [],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate an image using the lemonade local inference server."""
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="lemonade",
                aspect_ratio=aspect,
            )

        model_id, meta = _resolve_model()
        base_url = _resolve_base_url()
        size = _ASPECT_SIZES.get(aspect, _ASPECT_SIZES["square"])
        steps = _resolve_steps(meta)
        cfg_scale = _resolve_cfg_scale(meta)
        seed = _resolve_seed()

        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt,
            "size": size,
            "n": 1,
            "response_format": "b64_json",
        }
        if steps is not None:
            payload["steps"] = steps
        if cfg_scale is not None:
            payload["cfg_scale"] = cfg_scale
        if seed is not None:
            payload["seed"] = seed

        api_key = os.environ.get("LEMONADE_API_KEY", "")

        try:
            url = f"{base_url}/images/generations"
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            data = result.get("data", [])
        except ImportError:
            return error_response(
                error="requests package not installed (pip install requests)",
                error_type="missing_dependency",
                provider="lemonade",
                aspect_ratio=aspect,
            )
        except requests.Timeout:
            return error_response(
                error="Lemonade image generation timed out (300s)",
                error_type="timeout",
                provider="lemonade",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except requests.ConnectionError as exc:
            return error_response(
                error=f"Lemonade connection error: {exc}",
                error_type="connection_error",
                provider="lemonade",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except requests.HTTPError as exc:
            response = exc.response
            status = response.status_code if response is not None else 0
            try:
                detail = response.json().get("error", {}).get("message", response.text[:300])
            except Exception:
                detail = response.text[:300] if response is not None else str(exc)
            logger.debug("Lemonade image gen failed (%d): %s", status, detail)
            return error_response(
                error=f"Lemonade image generation failed ({status}): {detail}",
                error_type="api_error",
                provider="lemonade",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except Exception as exc:
            logger.debug("Lemonade image generation failed", exc_info=True)
            return error_response(
                error=f"Lemonade image generation failed: {exc}",
                error_type="api_error",
                provider="lemonade",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        if not data:
            return error_response(
                error="Lemonade returned no image data",
                error_type="empty_response",
                provider="lemonade",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        first = data[0]
        b64 = first.get("b64_json")
        url = first.get("url")

        if b64:
            try:
                saved_path = save_b64_image(b64, prefix=f"lemonade_{model_id}")
            except Exception as exc:
                return error_response(
                    error=f"Could not save image to cache: {exc}",
                    error_type="io_error",
                    provider="lemonade",
                    model=model_id,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
            image_ref = str(saved_path)
        elif url:
            # Lemonade's URL output points at a download endpoint on the local
            # server (typically ``http://localhost:13305/...``). It's not a
            # signed/expiring link like xAI or OpenAI return, so the bare URL
            # is normally safe to pass through to the gateway — but we cache
            # the bytes locally anyway as a belt-and-suspenders measure for
            # the cases where the server has been shut down by the time the
            # gateway goes to deliver the image.
            try:
                saved_path = _cache_url_bytes(url, prefix=f"lemonade_{model_id}")
            except Exception as exc:
                logger.warning(
                    "Lemonade image URL %s could not be cached (%s); falling back to bare URL.",
                    url,
                    exc,
                )
                image_ref = url
            else:
                image_ref = str(saved_path)
        else:
            return error_response(
                error="Lemonade response contained neither b64_json nor URL",
                error_type="empty_response",
                provider="lemonade",
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {"size": size}
        if steps is not None:
            extra["steps"] = steps
        if cfg_scale is not None:
            extra["cfg_scale"] = cfg_scale

        return success_response(
            image=image_ref,
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="lemonade",
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — register the Lemonade image-gen provider."""
    ctx.register_image_gen_provider(LemonadeImageGenProvider())
