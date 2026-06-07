"""FAL GPT Image 2 edit tool for reference-image image generation.

This bundled backend registers an ``image_edit`` tool under the existing
``image_gen`` toolset. It is intentionally a tool, not an
``ImageGenProvider``, because editing needs reference image inputs that the
legacy ``image_generate`` provider interface does not expose.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from agent.image_gen_provider import save_url_image
from tools.fal_common import import_fal_client

logger = logging.getLogger(__name__)

FAL_EDIT_MODEL = "openai/gpt-image-2/edit"
MAX_REFERENCE_IMAGE_BYTES = 20 * 1024 * 1024

_ASPECT_TO_IMAGE_SIZE = {
    "landscape": "landscape_16_9",
    "square": "square_hd",
    "portrait": "portrait_16_9",
}
_VALID_QUALITIES = {"low", "medium", "high"}
_VALID_OUTPUT_FORMATS = {"png", "jpeg", "webp"}
_SUPPORTED_IMAGE_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
_UPLOAD_HINT_RE = re.compile(r"\[Image attached at:\s*(?P<path>[^\]]+)\]")


class ImageEditError(ValueError):
    """User-facing image edit error with stable machine-readable type."""

    def __init__(self, message: str, error_type: str):
        super().__init__(message)
        self.error_type = error_type


def _json_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False)


def _error_response(prompt: str, message: str, error_type: str) -> str:
    return _json_response(
        {
            "success": False,
            "image": None,
            "provider": "fal",
            "model": FAL_EDIT_MODEL,
            "prompt": prompt,
            "error": message,
            "error_type": error_type,
        }
    )


def _listify(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value if item is not None and str(item).strip()]
    return [str(value)]


def _read_image_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _infer_mime_type(path: Path, data: bytes) -> str:
    suffix = path.suffix.lower()
    mime = _SUPPORTED_IMAGE_TYPES.get(suffix)
    if mime is None:
        raise ImageEditError(
            f"Unsupported reference image type: {path.suffix or 'unknown'}",
            "unsupported_image_type",
        )

    if mime == "image/png" and data.startswith(b"\x89PNG\r\n\x1a\n"):
        return mime
    if mime == "image/jpeg" and data.startswith(b"\xff\xd8\xff"):
        return mime
    if mime == "image/webp" and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return mime

    raise ImageEditError(
        f"Reference image is not a valid {mime} file: {path}",
        "unsupported_image_type",
    )


def _local_image_to_data_uri(path_value: str) -> str:
    path = Path(path_value).expanduser()
    if not path.exists():
        raise ImageEditError(f"Reference image does not exist: {path}", "missing_image_path")
    if not path.is_file():
        raise ImageEditError(f"Reference image path is not a file: {path}", "invalid_image_path")

    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ImageEditError(
            f"Cannot stat reference image: {path}: {exc}",
            "unreadable_image_path",
        ) from exc

    if size > MAX_REFERENCE_IMAGE_BYTES:
        raise ImageEditError(
            f"Reference image is too large: {path} ({size} bytes)",
            "image_too_large",
        )

    try:
        data = _read_image_bytes(path)
    except OSError as exc:
        raise ImageEditError(
            f"Cannot read reference image: {path}: {exc}",
            "unreadable_image_path",
        ) from exc

    mime = _infer_mime_type(path, data)
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _normalize_url(url_value: str, *, error_type: str = "invalid_image_url") -> str:
    url = str(url_value).strip()
    if url.startswith("data:image/"):
        return url

    parsed = urlparse(url)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return url

    raise ImageEditError(
        f"Image URL must be http(s) or a data:image URI: {url}",
        error_type,
    )


def _extract_upload_hint_paths(prompt: str) -> tuple[str, List[str]]:
    paths: List[str] = []

    def _collect(match: re.Match[str]) -> str:
        paths.append(match.group("path").strip())
        return ""

    cleaned = _UPLOAD_HINT_RE.sub(_collect, prompt)
    cleaned = re.sub(r"[ \t]+\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned, paths


def _split_reference_values(values: Iterable[str]) -> tuple[List[str], List[str]]:
    paths: List[str] = []
    urls: List[str] = []
    for raw in values:
        value = str(raw).strip()
        if not value:
            continue
        if value.startswith("data:image/") or urlparse(value).scheme in {"http", "https"}:
            urls.append(value)
        else:
            paths.append(value)
    return paths, urls


def _normalize_image_references(
    *,
    image_paths: Any = None,
    image_urls: Any = None,
) -> List[str]:
    normalized: List[str] = []

    for image_path in _listify(image_paths):
        normalized.append(_local_image_to_data_uri(image_path))

    for image_url in _listify(image_urls):
        normalized.append(_normalize_url(image_url))

    if not normalized:
        raise ImageEditError(
            "image_edit requires at least one reference image path or URL",
            "missing_reference_image",
        )

    return normalized


def _resolve_image_size(aspect_ratio: Optional[str]) -> str:
    aspect = str(aspect_ratio or "landscape").strip().lower()
    return _ASPECT_TO_IMAGE_SIZE.get(aspect, _ASPECT_TO_IMAGE_SIZE["landscape"])


def _resolve_quality(quality: Optional[str]) -> str:
    resolved = str(quality or "high").strip().lower()
    return resolved if resolved in _VALID_QUALITIES else "high"


def _resolve_output_format(output_format: Optional[str]) -> str:
    resolved = str(output_format or "png").strip().lower()
    return resolved if resolved in _VALID_OUTPUT_FORMATS else "png"


def _build_fal_payload(
    *,
    prompt: str,
    image_paths: Any = None,
    image_urls: Any = None,
    mask_image_path: Optional[str] = None,
    mask_url: Optional[str] = None,
    aspect_ratio: Optional[str] = None,
    quality: Optional[str] = None,
    output_format: Optional[str] = None,
) -> Dict[str, Any]:
    clean_prompt, hinted_refs = _extract_upload_hint_paths(str(prompt or ""))
    hinted_paths, hinted_urls = _split_reference_values(hinted_refs)

    merged_image_paths = _listify(image_paths) + hinted_paths
    merged_image_urls = _listify(image_urls) + hinted_urls

    payload: Dict[str, Any] = {
        "prompt": clean_prompt,
        "image_urls": _normalize_image_references(
            image_paths=merged_image_paths,
            image_urls=merged_image_urls,
        ),
        "image_size": _resolve_image_size(aspect_ratio),
        "quality": _resolve_quality(quality),
        "num_images": 1,
        "output_format": _resolve_output_format(output_format),
    }

    if mask_image_path:
        payload["mask_url"] = _local_image_to_data_uri(mask_image_path)
    elif mask_url:
        payload["mask_url"] = _normalize_url(mask_url, error_type="invalid_mask_url")

    return payload


def _ensure_fal_key_available() -> bool:
    key = os.environ.get("FAL_KEY")
    if not key:
        try:
            from hermes_cli.config import get_env_value

            key = get_env_value("FAL_KEY")
        except Exception:  # noqa: BLE001 - availability check must not raise
            key = None

    if key:
        os.environ.setdefault("FAL_KEY", key)
        return True
    return False


def _check_requirements() -> bool:
    if not _ensure_fal_key_available():
        return False
    try:
        _load_fal_client()
        return True
    except Exception:  # noqa: BLE001 - registry checks swallow availability failures
        return False


def _load_fal_client():
    return import_fal_client()


def _extract_result_image_url(result: Any) -> str:
    if isinstance(result, dict):
        images = result.get("images")
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, dict) and first.get("url"):
                return str(first["url"])
            if isinstance(first, str):
                return first

        image = result.get("image")
        if isinstance(image, dict) and image.get("url"):
            return str(image["url"])
        if isinstance(image, str):
            return image
        if result.get("url"):
            return str(result["url"])

    raise ImageEditError("FAL edit response did not include an image URL", "missing_result_image")


def _cache_generated_image(url: str, output_format: str) -> str:
    path = save_url_image(url, prefix="fal_gpt_image_edit")
    return str(path)


def image_edit_tool(args: Dict[str, Any], **_: Any) -> str:
    prompt = str(args.get("prompt") or "")
    if not prompt.strip():
        return _error_response(prompt, "prompt is required", "missing_prompt")

    try:
        payload = _build_fal_payload(
            prompt=prompt,
            image_paths=args.get("image_paths"),
            image_urls=args.get("image_urls"),
            mask_image_path=args.get("mask_image_path"),
            mask_url=args.get("mask_url"),
            aspect_ratio=args.get("aspect_ratio"),
            quality=args.get("quality"),
            output_format=args.get("output_format"),
        )
    except ImageEditError as exc:
        return _error_response(prompt, str(exc), exc.error_type)

    if not _ensure_fal_key_available():
        return _error_response(
            payload["prompt"],
            "FAL_KEY is required for image_edit",
            "missing_fal_key",
        )

    try:
        fal_client = _load_fal_client()
        handle = fal_client.submit(FAL_EDIT_MODEL, arguments=payload)
        result = handle.get()
        image_url = _extract_result_image_url(result)
    except ImageEditError as exc:
        return _error_response(payload["prompt"], str(exc), exc.error_type)
    except Exception as exc:  # noqa: BLE001 - convert provider failures to JSON
        logger.warning("FAL GPT Image 2 edit failed: %s", exc, exc_info=True)
        return _error_response(
            payload["prompt"],
            f"FAL GPT Image 2 edit failed: {exc}",
            type(exc).__name__,
        )

    response: Dict[str, Any] = {
        "success": True,
        "image": image_url,
        "remote_image": image_url,
        "provider": "fal",
        "model": FAL_EDIT_MODEL,
        "prompt": payload["prompt"],
        "aspect_ratio": str(args.get("aspect_ratio") or "landscape"),
        "quality": payload["quality"],
        "output_format": payload["output_format"],
    }

    try:
        response["image"] = _cache_generated_image(image_url, payload["output_format"])
    except Exception as exc:  # noqa: BLE001 - keep the remote URL usable
        logger.warning("Could not cache FAL edit result: %s", exc)
        response["cache_warning"] = str(exc)

    return _json_response(response)


IMAGE_EDIT_SCHEMA: Dict[str, Any] = {
    "name": "image_edit",
    "description": (
        "Generate an edited or composited image from one or more reference images "
        "using FAL GPT Image 2 edit. Use this when the user uploads/attaches an "
        "image and asks for a poster, product edit, restyle, composite, or other "
        "reference-image transformation. Pass local paths from Hermes upload hints "
        "like '[Image attached at: /path]' in image_paths, or pass HTTP(S) images "
        "in image_urls. Use aspect_ratio='portrait' for vertical 9:16 poster work."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Detailed edit/compositing instructions.",
            },
            "image_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Local PNG/JPEG/WebP reference image paths.",
            },
            "image_urls": {
                "type": "array",
                "items": {"type": "string"},
                "description": "HTTP(S) or data:image reference image URLs.",
            },
            "mask_image_path": {
                "type": "string",
                "description": "Optional local mask image path.",
            },
            "mask_url": {
                "type": "string",
                "description": "Optional HTTP(S) or data:image mask URL.",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["landscape", "square", "portrait"],
                "description": "Output aspect ratio. portrait maps to FAL portrait_16_9.",
                "default": "landscape",
            },
            "quality": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": "GPT Image 2 quality setting.",
                "default": "high",
            },
            "output_format": {
                "type": "string",
                "enum": ["png", "jpeg", "webp"],
                "description": "Output image format.",
                "default": "png",
            },
        },
        "required": ["prompt"],
    },
}


def register(ctx) -> None:
    ctx.register_tool(
        name="image_edit",
        toolset="image_gen",
        schema=IMAGE_EDIT_SCHEMA,
        handler=image_edit_tool,
        check_fn=_check_requirements,
        requires_env=["FAL_KEY"],
        description=IMAGE_EDIT_SCHEMA["description"],
        emoji="image",
    )
