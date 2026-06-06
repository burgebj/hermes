#!/usr/bin/env python3
"""
Image Generation V2 Tools Module
================================

Clone of ``image_generate`` with added ``image_url`` parameter for
img2img (image-to-image) editing via xAI's ``/v1/images/edits`` endpoint.

When ``image_url`` is absent, behaviour is identical to the original
``image_generate`` — the call is delegated straight through to the
existing plugin dispatch path.

When ``image_url`` is present, xAI OAuth credentials are resolved
and the request is sent to ``POST /v1/images/edits``. The result
URL (or base64 path) is returned in the standard success shape.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import uuid
from typing import Any, Dict, List, Optional

import requests

from tools.image_generation_tool import (
    DEFAULT_ASPECT_RATIO,
    VALID_ASPECT_RATIOS,
    _dispatch_to_plugin_provider,
    check_image_generation_requirements,
)
from tools.registry import registry
from tools.xai_http import hermes_xai_user_agent, resolve_xai_http_credentials

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema — identical to image_generate plus an optional image_url field
# ---------------------------------------------------------------------------

IMAGE_GENERATE_V2_SCHEMA: Dict[str, Any] = {
    "name": "image_generate_v2",
    "description": (
        "Generate high-quality images from text prompts, or edit an existing "
        "image with img2img by providing a source ``image_url``. "
        "Without ``image_url``: plain text-to-image (same as image_generate). "
        "With ``image_url``: the source image is edited according to the prompt "
        "via xAI's image edits endpoint. The image_url can be a public HTTP(S) URL "
        "or a local file path (auto-encoded to base64 data URL). "
        "Returns a URL or absolute file path in the ``image`` field; display it with "
        "markdown ``![description](url-or-path)`` and the gateway will deliver it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The text prompt describing the desired image or edit.",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": list(VALID_ASPECT_RATIOS),
                "description": (
                    "The aspect ratio of the generated image. "
                    "'landscape' is 16:9 wide, 'portrait' is 16:9 tall, "
                    "'square' is 1:1. Ignored when image_url is set."
                ),
                "default": DEFAULT_ASPECT_RATIO,
            },
            "image_url": {
                "type": "string",
                "description": (
                    "Optional. A public HTTP(S) URL or local file path of a source image to edit "
                    "(img2img). Local paths are auto-encoded to base64 data URLs. "
                    "When provided, the prompt is used as an edit "
                    "instruction rather than a generation prompt. When omitted, "
                    "behaves as plain text-to-image generation."
                ),
            },
        },
        "required": ["prompt"],
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _images_cache_dir():
    """Return ``$HERMES_HOME/cache/images/``, creating parents as needed."""
    from hermes_constants import get_hermes_home

    path = get_hermes_home() / "cache" / "images"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _save_b64(data: str, *, prefix: str = "xai_edit", extension: str = "png"):
    """Decode base64 data and write it under the images cache dir. Returns path."""
    import datetime

    raw = base64.b64decode(data)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    short = uuid.uuid4().hex[:8]
    path = _images_cache_dir() / f"{prefix}_{ts}_{short}.{extension}"
    path.write_bytes(raw)
    return str(path)


def _tool_error(message: str) -> str:
    """Return a JSON error string in the standard shape."""
    return json.dumps({"success": False, "image": None, "error": message})


def _resolve_edit_model() -> str:
    """Return the model id to use for image edits.

    Precedence: ``XAI_IMAGE_MODEL`` env var → ``image_gen.model`` config
    (if it's a grok-imagine variant) → ``grok-imagine-image`` default.
    """
    env_model = os.environ.get("XAI_IMAGE_MODEL", "").strip()
    if env_model and env_model.startswith("grok-imagine-image"):
        return env_model

    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        if isinstance(section, dict):
            model = section.get("model", "")
            if isinstance(model, str) and model.strip().startswith("grok-imagine-image"):
                return model.strip()
    except Exception:
        pass

    return "grok-imagine-image"


# ---------------------------------------------------------------------------
# xAI image edit (img2img)
# ---------------------------------------------------------------------------


def _xai_image_edit(
    prompt: str,
    image_url: str,
    model_id: Optional[str] = None,
    extra_image_urls: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Call xAI ``/v1/images/edits`` using OAuth credentials.

    Returns a dict compatible with the standard image_gen success/error shape.
    If *extra_image_urls* is provided, uses the multi-image ``images`` array format.
    """
    creds = resolve_xai_http_credentials()
    api_key = str(creds.get("api_key") or "").strip()
    provider_name = str(creds.get("provider") or "xai").strip() or "xai"
    base_url = str(creds.get("base_url") or "https://api.x.ai/v1").strip().rstrip("/")

    if not api_key:
        return {
            "success": False,
            "image": None,
            "error": (
                "No xAI credentials found. Configure xAI OAuth in "
                "`hermes model` or set XAI_API_KEY."
            ),
            "error_type": "missing_api_key",
            "provider": provider_name,
        }

    model = model_id or _resolve_edit_model()

    if extra_image_urls:
        # Multi-image format: "images" array
        all_images = [{"type": "image_url", "url": image_url}]
        for u in extra_image_urls:
            all_images.append({"type": "image_url", "url": u})
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "images": all_images,
            "response_format": "url",
            "n": 1,
        }
    else:
        # Single-image format: "image" object
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "image": {
                "url": image_url,
                "type": "image_url",
            },
            "response_format": "url",
            "n": 1,
        }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": hermes_xai_user_agent(),
    }

    try:
        response = requests.post(
            f"{base_url}/images/edits",
            headers=headers,
            json=payload,
            timeout=120,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        resp = exc.response
        status = resp.status_code if resp is not None else 0
        if resp is not None:
            try:
                err_body = resp.json()
                err_msg = err_body.get("error", {}).get("message", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300]
        else:
            err_msg = str(exc)
        logger.error("xAI image edit failed (%d): %s", status, err_msg)
        return {
            "success": False,
            "image": None,
            "error": f"xAI image edit failed ({status}): {err_msg}",
            "error_type": "api_error",
            "provider": provider_name,
            "model": model,
        }
    except requests.Timeout:
        return {
            "success": False,
            "image": None,
            "error": "xAI image edit timed out (120s)",
            "error_type": "timeout",
            "provider": provider_name,
            "model": model,
        }
    except requests.ConnectionError as exc:
        return {
            "success": False,
            "image": None,
            "error": f"xAI connection error: {exc}",
            "error_type": "connection_error",
            "provider": provider_name,
            "model": model,
        }

    try:
        result = response.json()
    except Exception as exc:
        return {
            "success": False,
            "image": None,
            "error": f"xAI returned invalid JSON: {exc}",
            "error_type": "invalid_response",
            "provider": provider_name,
            "model": model,
        }

    data = result.get("data", [])
    if not data:
        return {
            "success": False,
            "image": None,
            "error": "xAI image edit returned no image data",
            "error_type": "empty_response",
            "provider": provider_name,
            "model": model,
        }

    first = data[0]
    b64 = first.get("b64_json")
    url = first.get("url")

    if b64:
        try:
            saved_path = _save_b64(b64, prefix=f"xai_edit_{model}")
        except Exception as exc:
            return {
                "success": False,
                "image": None,
                "error": f"Could not save edited image to cache: {exc}",
                "error_type": "io_error",
                "provider": provider_name,
                "model": model,
            }
        image_ref = saved_path
    elif url:
        image_ref = url
    else:
        return {
            "success": False,
            "image": None,
            "error": "xAI edit response contained neither b64_json nor URL",
            "error_type": "empty_response",
            "provider": provider_name,
            "model": model,
        }

    return {
        "success": True,
        "image": image_ref,
        "model": model,
        "prompt": prompt,
        "source_image": image_url,
        "provider": provider_name,
    }


# ---------------------------------------------------------------------------
# Main handler
# ---------------------------------------------------------------------------


def _handle_image_generate_v2(args, **kw):
    """Route text2img (no image_url) or img2img (has image_url)."""
    prompt = args.get("prompt", "")
    if not prompt:
        return _tool_error("prompt is required")

    image_url = (args.get("image_url") or "").strip()
    image_urls = args.get("image_urls") or []
    aspect_ratio = args.get("aspect_ratio", DEFAULT_ASPECT_RATIO)

    # Helper to resolve a single URL (local path → base64 data URL)
    def _resolve_url(url: str) -> str:
        url = url.strip()
        if not url.startswith(("http://", "https://", "data:")):
            local_path = Path(url).expanduser().resolve()
            if not local_path.is_file():
                raise ValueError(f"Not a valid URL or local file: {url}")
            raw = local_path.read_bytes()
            b64 = base64.b64encode(raw).decode()
            ext = local_path.suffix.lstrip(".").lower()
            mime = f"image/{ext}" if ext in ("jpg", "jpeg", "png", "gif", "webp") else "image/jpeg"
            return f"data:{mime};base64,{b64}"
        return url

    # ── Img2img path: image_url (or image_urls) provided ──
    if image_url:
        from pathlib import Path

        resolved_url = _resolve_url(image_url)
        extra_urls = [_resolve_url(u) for u in image_urls] if image_urls else None

        result = _xai_image_edit(prompt=prompt, image_url=resolved_url, extra_image_urls=extra_urls)
        return json.dumps(result)

    # ── Text2img path: delegate to existing plugin dispatch ──
    dispatched = _dispatch_to_plugin_provider(prompt, aspect_ratio)
    if dispatched is not None:
        return dispatched

    # Fallback to legacy FAL path
    from tools.image_generation_tool import image_generate_tool

    return image_generate_tool(
        prompt=prompt,
        aspect_ratio=aspect_ratio,
    )


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="image_generate_v2",
    toolset="image_gen",
    schema=IMAGE_GENERATE_V2_SCHEMA,
    handler=_handle_image_generate_v2,
    check_fn=check_image_generation_requirements,
    requires_env=[],
    is_async=False,
    emoji="🎨",
)
