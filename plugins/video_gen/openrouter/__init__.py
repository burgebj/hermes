"""OpenRouter video generation backend.

Surface: text-to-video and image-to-video through OpenRouter's async
``/videos`` API. One ``OPENROUTER_API_KEY`` routes to Veo, Sora, Kling,
Seedance, Hailuo, Wan, and Grok Imagine — the same key the agent already
uses for its main model, so no extra setup is needed when Hermes runs on
OpenRouter.

Routing: when ``image_url`` is supplied we pass it as the first frame via
``frame_images`` (``frame_type: first_frame``) so the chosen model animates
the image; otherwise it's a plain text-to-video request. ``reference_image_urls``
map onto OpenRouter's ``input_references``.

Flow (OpenRouter async videos API):
  1. ``POST {base}/videos``        -> ``{id, polling_url, status}`` (202)
  2. ``GET  {base}/videos/{id}``   -> poll until ``status == completed``
  3. completed response carries ``unsigned_urls`` (CDN URLs); we return the
     first. The gateway downloads and delivers it.

Model capabilities (aspect ratios, resolutions, durations, audio, frame
support) are fetched live from ``GET {base}/videos/models`` and cached for
the process, with a static fallback catalog when the network call fails.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import httpx

from agent.video_gen_provider import (
    COMMON_ASPECT_RATIOS,
    COMMON_RESOLUTIONS,
    VideoGenProvider,
    error_response,
    success_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL = "google/veo-3.1"
DEFAULT_DURATION = 8
DEFAULT_ASPECT_RATIO = "16:9"
DEFAULT_RESOLUTION = "720p"
DEFAULT_TIMEOUT_SECONDS = 600
DEFAULT_POLL_INTERVAL_SECONDS = 5
MODELS_CACHE_TTL_SECONDS = 3600

# Static fallback catalog — used only when the live /videos/models call
# fails (offline, transient error). Kept intentionally small; the live
# fetch is the source of truth. Each entry mirrors the shape list_models()
# returns. NOT asserted by any test (catalog data changes upstream).
_FALLBACK_MODELS: List[Dict[str, Any]] = [
    {"id": "google/veo-3.1", "display": "Veo 3.1", "modalities": ["text", "image"]},
    {"id": "google/veo-3.1-fast", "display": "Veo 3.1 Fast", "modalities": ["text", "image"]},
    {"id": "openai/sora-2-pro", "display": "Sora 2 Pro", "modalities": ["text"]},
    {"id": "kwaivgi/kling-v3.0-pro", "display": "Kling v3.0 Pro", "modalities": ["text", "image"]},
    {"id": "bytedance/seedance-2.0", "display": "Seedance 2.0", "modalities": ["text", "image"]},
    {"id": "x-ai/grok-imagine-video", "display": "Grok Imagine Video", "modalities": ["text", "image"]},
]

# Process-wide cache for the live model catalog: (timestamp, raw_models).
_models_cache: tuple[float, List[Dict[str, Any]]] | None = None


# ---------------------------------------------------------------------------
# Credential + HTTP helpers
# ---------------------------------------------------------------------------


def _resolve_credentials() -> tuple[str, str]:
    """Return ``(api_key, base_url)`` from the shared OpenRouter resolver."""
    try:
        from tools.tool_backend_helpers import resolve_openrouter_credentials

        creds = resolve_openrouter_credentials()
        return creds["api_key"], creds["base_url"]
    except Exception as exc:  # noqa: BLE001
        logger.debug("OpenRouter credential resolver failed: %s", exc)
        return "", "https://openrouter.ai/api/v1"


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/NousResearch/hermes-agent",
        "X-Title": "Hermes Agent",
    }


def _fetch_models_raw() -> List[Dict[str, Any]]:
    """Fetch the live video-model catalog, cached for the process.

    Returns the raw ``data`` list from ``GET /videos/models``. On any
    failure returns the static fallback so the picker / capabilities never
    crash on a network blip.
    """
    global _models_cache
    now = time.time()
    if _models_cache is not None and (now - _models_cache[0]) < MODELS_CACHE_TTL_SECONDS:
        return _models_cache[1]

    api_key, base_url = _resolve_credentials()
    if not api_key:
        return _FALLBACK_MODELS
    try:
        resp = httpx.get(
            f"{base_url}/videos/models",
            headers=_headers(api_key),
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json().get("data", [])
        if isinstance(data, list) and data:
            _models_cache = (now, data)
            return data
    except Exception as exc:  # noqa: BLE001
        logger.debug("OpenRouter video model fetch failed: %s", exc)
    return _FALLBACK_MODELS


def _model_entry(model_id: str) -> Optional[Dict[str, Any]]:
    """Return the raw catalog entry for *model_id*, or None."""
    for entry in _fetch_models_raw():
        if entry.get("id") == model_id:
            return entry
    return None


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class OpenRouterVideoGenProvider(VideoGenProvider):
    """OpenRouter video backend (text-to-video + image-to-video)."""

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def display_name(self) -> str:
        return "OpenRouter"

    def is_available(self) -> bool:
        api_key, _ = _resolve_credentials()
        return bool(api_key)

    def list_models(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for entry in _fetch_models_raw():
            mid = entry.get("id")
            if not mid:
                continue
            frames = entry.get("supported_frame_images") or []
            modalities = ["text"]
            if frames:
                modalities.append("image")
            out.append({
                "id": mid,
                "display": entry.get("name", mid),
                "strengths": (entry.get("description") or "")[:120],
                "modalities": modalities,
            })
        return out or [
            {"id": m["id"], "display": m.get("display", m["id"]), "modalities": m.get("modalities", ["text"])}
            for m in _FALLBACK_MODELS
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "OpenRouter Video",
            "badge": "paid",
            "tag": (
                "One OpenRouter key for Veo / Sora / Kling / Seedance — "
                "text-to-video + image-to-video; uses OPENROUTER_API_KEY"
            ),
            "env_vars": [
                {
                    "key": "OPENROUTER_API_KEY",
                    "prompt": "OpenRouter API key",
                    "url": "https://openrouter.ai/keys",
                },
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        # Aggregate across the catalog so soft validation in the tool layer
        # accepts anything any model supports; per-model clamping happens
        # server-side at OpenRouter.
        aspect_ratios: set[str] = set()
        resolutions: set[str] = set()
        max_dur = 0
        supports_audio = False
        supports_frames = False
        for entry in _fetch_models_raw():
            aspect_ratios.update(entry.get("supported_aspect_ratios") or [])
            resolutions.update(entry.get("supported_resolutions") or [])
            for d in entry.get("supported_durations") or []:
                if isinstance(d, int):
                    max_dur = max(max_dur, d)
            if entry.get("generate_audio"):
                supports_audio = True
            if entry.get("supported_frame_images"):
                supports_frames = True
        return {
            "modalities": ["text", "image"] if supports_frames else ["text"],
            "aspect_ratios": sorted(aspect_ratios) or list(COMMON_ASPECT_RATIOS),
            "resolutions": sorted(resolutions) or list(COMMON_RESOLUTIONS),
            "max_duration": max_dur or 15,
            "min_duration": 1,
            "supports_audio": supports_audio,
            "supports_negative_prompt": False,
            "max_reference_images": 4,
        }

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        resolution: str = DEFAULT_RESOLUTION,
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(self._generate_async(
                    prompt=prompt,
                    model=model,
                    image_url=image_url,
                    reference_image_urls=reference_image_urls,
                    duration=duration,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                    audio=audio,
                    seed=seed,
                ))
            finally:
                loop.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenRouter video gen unexpected failure: %s", exc, exc_info=True)
            return error_response(
                error=f"OpenRouter video generation failed: {exc}",
                error_type="api_error",
                provider="openrouter",
                model=model or DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
            )

    async def _generate_async(
        self,
        *,
        prompt: str,
        model: Optional[str],
        image_url: Optional[str],
        reference_image_urls: Optional[List[str]],
        duration: Optional[int],
        aspect_ratio: str,
        resolution: str,
        audio: Optional[bool],
        seed: Optional[int],
    ) -> Dict[str, Any]:
        api_key, base_url = _resolve_credentials()
        if not api_key:
            return error_response(
                error=(
                    "No OpenRouter credentials found. Set OPENROUTER_API_KEY "
                    "(https://openrouter.ai/keys) or run `hermes setup`."
                ),
                error_type="auth_required",
                provider="openrouter", prompt=prompt,
            )

        prompt = (prompt or "").strip()
        if not prompt:
            return error_response(
                error="prompt is required for OpenRouter video generation",
                error_type="missing_prompt",
                provider="openrouter", prompt=prompt,
            )

        resolved_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
        modality_used = "image" if (image_url or "").strip() else "text"

        payload: Dict[str, Any] = {
            "model": resolved_model,
            "prompt": prompt,
            "aspect_ratio": (aspect_ratio or DEFAULT_ASPECT_RATIO).strip(),
            "resolution": (resolution or DEFAULT_RESOLUTION).strip(),
        }
        if duration is not None:
            try:
                payload["duration"] = max(1, int(duration))
            except (TypeError, ValueError):
                pass
        if seed is not None:
            payload["seed"] = seed
        if audio is not None:
            payload["generate_audio"] = bool(audio)

        # image-to-video: pass the still as the first frame.
        if modality_used == "image":
            payload["frame_images"] = [{
                "type": "image_url",
                "image_url": {"url": image_url.strip()},
                "frame_type": "first_frame",
            }]

        refs = [u.strip() for u in (reference_image_urls or []) if isinstance(u, str) and u.strip()]
        if refs:
            payload["input_references"] = [
                {"type": "image_url", "image_url": {"url": u}} for u in refs
            ]

        async with httpx.AsyncClient() as client:
            # 1. Submit
            try:
                submit = await client.post(
                    f"{base_url}/videos",
                    headers=_headers(api_key),
                    json=payload,
                    timeout=60,
                )
                submit.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = ""
                try:
                    detail = exc.response.text[:500]
                except Exception:
                    pass
                return error_response(
                    error=f"OpenRouter video submit failed ({exc.response.status_code}): {detail or exc}",
                    error_type="api_error",
                    provider="openrouter", model=resolved_model, prompt=prompt,
                )

            body = submit.json()
            job_id = body.get("id")
            if not job_id:
                return error_response(
                    error="OpenRouter video response did not include a job id",
                    error_type="empty_response",
                    provider="openrouter", model=resolved_model, prompt=prompt,
                )

            # 2. Poll
            elapsed = 0.0
            last_body = body
            status = (body.get("status") or "").lower()
            while status in {"", "pending", "in_progress"} and elapsed < DEFAULT_TIMEOUT_SECONDS:
                await asyncio.sleep(DEFAULT_POLL_INTERVAL_SECONDS)
                elapsed += DEFAULT_POLL_INTERVAL_SECONDS
                try:
                    poll = await client.get(
                        f"{base_url}/videos/{job_id}",
                        headers=_headers(api_key),
                        timeout=30,
                    )
                    poll.raise_for_status()
                    last_body = poll.json()
                    status = (last_body.get("status") or "").lower()
                except httpx.HTTPError as exc:
                    logger.debug("OpenRouter video poll error (will retry): %s", exc)

        if status == "completed":
            urls = last_body.get("unsigned_urls") or []
            video_url = urls[0] if urls else None
            if not video_url:
                # Fall back to the content endpoint when no direct URL is given.
                video_url = f"{base_url}/videos/{job_id}/content"
            extra: Dict[str, Any] = {"job_id": job_id, "resolution": payload["resolution"]}
            if last_body.get("usage"):
                extra["usage"] = last_body["usage"]
            return success_response(
                video=video_url,
                model=resolved_model,
                prompt=prompt,
                modality=modality_used,
                aspect_ratio=payload["aspect_ratio"],
                duration=payload.get("duration", 0),
                provider="openrouter",
                extra=extra,
            )

        if status in {"", "pending", "in_progress"}:
            return error_response(
                error=f"Timed out waiting for OpenRouter video after {DEFAULT_TIMEOUT_SECONDS}s",
                error_type="timeout",
                provider="openrouter", model=resolved_model, prompt=prompt,
            )

        message = last_body.get("error") or f"OpenRouter video generation ended with status '{status}'"
        return error_response(
            error=str(message),
            error_type=f"openrouter_{status or 'unknown'}",
            provider="openrouter", model=resolved_model, prompt=prompt,
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — wire ``OpenRouterVideoGenProvider`` into the registry."""
    ctx.register_video_gen_provider(OpenRouterVideoGenProvider())
