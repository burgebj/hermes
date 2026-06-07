"""MiniMax Hailuo video generation backend.

Implements Hermes' unified ``video_generate`` provider interface against the
MiniMax asynchronous video API:

* ``POST /v1/video_generation`` creates a task.
* ``GET /v1/query/video_generation?task_id=...`` polls the task.
* ``GET /v1/files/retrieve?file_id=...`` resolves the downloadable MP4 URL.

The unified Hermes surface supports text-to-video and image-to-video. MiniMax
image-to-video is mapped by sending ``image_url`` as ``first_frame_image``.
First/last-frame and subject-reference modes are intentionally left out because
``video_generate`` does not expose stable generic parameters for them yet.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import httpx

from agent.video_gen_provider import VideoGenProvider, error_response, success_response

logger = logging.getLogger(__name__)


DEFAULT_MINIMAX_BASE_URL = "https://api.minimax.io"
CREATE_PATH = "/v1/video_generation"
QUERY_PATH = "/v1/query/video_generation"
RETRIEVE_PATH = "/v1/files/retrieve"
DEFAULT_MODEL = "MiniMax-Hailuo-2.3"
DEFAULT_DURATION = 6
DEFAULT_RESOLUTION = "768P"
DEFAULT_TIMEOUT_SECONDS = 240
DEFAULT_POLL_INTERVAL_SECONDS = 5
SUCCESS_STATUS = "Success"
FAIL_STATUS = "Fail"
_PENDING_STATUSES = {"Preparing", "Queueing", "Processing"}


_MODELS: Dict[str, Dict[str, Any]] = {
    "MiniMax-Hailuo-2.3": {
        "display": "MiniMax Hailuo 2.3",
        "speed": "~60-120s",
        "strengths": "Current Hailuo generation model; text-to-video and image-to-video.",
        "price": "paid",
        "modalities": ["text", "image"],
        "durations": (6, 10),
        "resolutions": ("768P", "1080P"),
    },
    "MiniMax-Hailuo-02": {
        "display": "MiniMax Hailuo 02",
        "speed": "~60-120s",
        "strengths": "Hailuo 02 generation model; text-to-video and image-to-video.",
        "price": "paid",
        "modalities": ["text", "image"],
        "durations": (6, 10),
        "resolutions": ("768P", "1080P"),
    },
    "T2V-01-Director": {
        "display": "MiniMax T2V-01 Director",
        "speed": "~60-120s",
        "strengths": "Text-to-video model with director/camera-control prompting.",
        "price": "paid",
        "modalities": ["text"],
        "durations": (6,),
        "resolutions": ("720P",),
    },
    "T2V-01": {
        "display": "MiniMax T2V-01",
        "speed": "~60-120s",
        "strengths": "Text-to-video model.",
        "price": "paid",
        "modalities": ["text"],
        "durations": (6,),
        "resolutions": ("720P",),
    },
}


_COMMON_RESOLUTIONS = ("720P", "768P", "1080P")


def _load_video_gen_section() -> Dict[str, Any]:
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("video_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:  # pragma: no cover - defensive config path
        logger.debug("Could not load video_gen config: %s", exc)
        return {}


def _resolve_minimax_credentials() -> Tuple[str, str]:
    """Return ``(api_key, base_url)`` from env/config.

    ``MINIMAX_API_KEY`` is the canonical credential. ``MINIMAX_BASE_URL`` is
    optional and mainly exists for tests or enterprise proxies.
    """
    cfg = _load_video_gen_section()
    minimax_cfg = cfg.get("minimax") if isinstance(cfg.get("minimax"), dict) else {}
    dotenv_values: Dict[str, str] = {}
    try:
        from hermes_cli.config import load_env

        dotenv_values = load_env() or {}
    except Exception as exc:  # pragma: no cover - defensive config path
        logger.debug("Could not load Hermes .env for MiniMax video credentials: %s", exc)

    api_key = str(
        os.getenv("MINIMAX_API_KEY")
        or dotenv_values.get("MINIMAX_API_KEY")
        or (minimax_cfg.get("api_key") if isinstance(minimax_cfg, dict) else "")
        or ""
    ).strip()
    base_url = str(
        os.getenv("MINIMAX_BASE_URL")
        or dotenv_values.get("MINIMAX_BASE_URL")
        or (minimax_cfg.get("base_url") if isinstance(minimax_cfg, dict) else "")
        or DEFAULT_MINIMAX_BASE_URL
    ).strip().rstrip("/")
    return api_key, base_url


def _headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "hermes-agent/video_gen/minimax",
    }


def _normalize_model(model: Optional[str]) -> str:
    requested = (model or "").strip()
    return requested if requested in _MODELS else DEFAULT_MODEL


def _nearest_supported_int(value: Optional[int], allowed: Tuple[int, ...], default: int) -> int:
    if value is None:
        return default if default in allowed else allowed[0]
    if value in allowed:
        return value
    return min(allowed, key=lambda item: abs(item - value))


def _normalize_duration(model_id: str, duration: Optional[int]) -> int:
    meta = _MODELS.get(model_id, {})
    allowed = tuple(meta.get("durations") or (DEFAULT_DURATION,))
    return _nearest_supported_int(duration, allowed, DEFAULT_DURATION)


def _normalize_resolution(model_id: str, resolution: str) -> str:
    meta = _MODELS.get(model_id, {})
    allowed = tuple(meta.get("resolutions") or _COMMON_RESOLUTIONS)
    raw = (resolution or DEFAULT_RESOLUTION).strip()
    normalized = raw.upper()
    if normalized.endswith("P"):
        candidate = normalized
    elif normalized.endswith("p"):
        candidate = f"{normalized[:-1]}P"
    else:
        candidate = f"{normalized}P" if normalized.isdigit() else normalized
    if candidate in allowed:
        return candidate
    return DEFAULT_RESOLUTION if DEFAULT_RESOLUTION in allowed else allowed[0]


def _model_supports_modality(model_id: str, modality: str) -> bool:
    modalities = _MODELS.get(model_id, {}).get("modalities") or ["text"]
    return modality in modalities


def _build_payload(
    *,
    prompt: str,
    model_id: str,
    image_url: Optional[str],
    duration: Optional[int],
    resolution: str,
) -> Tuple[Dict[str, Any], int, str, str]:
    modality = "image" if image_url else "text"
    clamped_duration = _normalize_duration(model_id, duration)
    normalized_resolution = _normalize_resolution(model_id, resolution)
    payload: Dict[str, Any] = {
        "model": model_id,
        "prompt": prompt,
        "duration": clamped_duration,
        "resolution": normalized_resolution,
    }
    if image_url:
        payload["first_frame_image"] = image_url
    return payload, clamped_duration, normalized_resolution, modality


async def _submit_task(
    client: httpx.AsyncClient,
    payload: Dict[str, Any],
    *,
    api_key: str,
    base_url: str,
) -> str:
    response = await client.post(
        f"{base_url}{CREATE_PATH}",
        headers=_headers(api_key),
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    task_id = body.get("task_id") or body.get("id")
    if not task_id:
        raise RuntimeError("MiniMax video_generation response did not include task_id")
    return str(task_id)


async def _poll_task(
    client: httpx.AsyncClient,
    task_id: str,
    *,
    api_key: str,
    base_url: str,
    timeout_seconds: int,
    poll_interval: int,
) -> Dict[str, Any]:
    elapsed = 0.0
    last_status = ""
    while elapsed < timeout_seconds:
        response = await client.get(
            f"{base_url}{QUERY_PATH}",
            headers=_headers(api_key),
            params={"task_id": task_id},
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        status = str(body.get("status") or body.get("task_status") or "")
        last_status = status
        if status == SUCCESS_STATUS:
            return {"status": SUCCESS_STATUS, "body": body}
        if status == FAIL_STATUS:
            return {"status": FAIL_STATUS, "body": body}
        if status and status not in _PENDING_STATUSES:
            logger.debug("MiniMax video task %s returned unknown status %r", task_id, status)
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return {"status": "timeout", "body": {"status": last_status}}


async def _retrieve_file_url(
    client: httpx.AsyncClient,
    file_id: str,
    *,
    api_key: str,
    base_url: str,
) -> str:
    response = await client.get(
        f"{base_url}{RETRIEVE_PATH}",
        headers=_headers(api_key),
        params={"file_id": file_id},
        timeout=30,
    )
    response.raise_for_status()
    body = response.json()
    file_info = body.get("file") if isinstance(body, dict) else None
    if isinstance(file_info, dict):
        url = file_info.get("download_url") or file_info.get("url")
        if url:
            return str(url)
    url = body.get("download_url") if isinstance(body, dict) else None
    if url:
        return str(url)
    raise RuntimeError("MiniMax file retrieve response did not include file.download_url")


def _extract_file_id(body: Dict[str, Any]) -> Optional[str]:
    for key in ("file_id", "video_file_id"):
        value = body.get(key)
        if value:
            return str(value)
    file_info = body.get("file")
    if isinstance(file_info, dict) and file_info.get("file_id"):
        return str(file_info["file_id"])
    return None


class MiniMaxVideoGenProvider(VideoGenProvider):
    """MiniMax direct API video backend."""

    @property
    def name(self) -> str:
        return "minimax"

    @property
    def display_name(self) -> str:
        return "MiniMax"

    def is_available(self) -> bool:
        api_key, _ = _resolve_minimax_credentials()
        return bool(api_key)

    def list_models(self) -> List[Dict[str, Any]]:
        return [{"id": model_id, **meta} for model_id, meta in _MODELS.items()]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "MiniMax",
            "badge": "paid",
            "tag": "Hailuo video generation via MiniMax API — text-to-video and image-to-video",
            "env_vars": [
                {
                    "key": "MINIMAX_API_KEY",
                    "prompt": "MiniMax API key",
                    "url": "https://platform.minimaxi.com/",
                },
            ],
        }

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["text", "image"],
            "aspect_ratios": [],
            "resolutions": list(_COMMON_RESOLUTIONS),
            "max_duration": 10,
            "min_duration": 6,
            "supports_audio": False,
            "supports_negative_prompt": False,
            "max_reference_images": 0,
        }

    def generate(
        self,
        prompt: str,
        *,
        model: Optional[str] = None,
        image_url: Optional[str] = None,
        reference_image_urls: Optional[List[str]] = None,
        duration: Optional[int] = None,
        aspect_ratio: str = "16:9",
        resolution: str = DEFAULT_RESOLUTION,
        negative_prompt: Optional[str] = None,
        audio: Optional[bool] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        try:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self._generate_async(
                        prompt=prompt,
                        model=model,
                        image_url=image_url,
                        duration=duration,
                        resolution=resolution,
                    )
                )
            finally:
                loop.close()
        except Exception as exc:
            logger.warning("MiniMax video gen unexpected failure: %s", exc, exc_info=True)
            return error_response(
                error=f"MiniMax video generation failed: {exc}",
                error_type="api_error",
                provider="minimax",
                model=model or DEFAULT_MODEL,
                prompt=prompt,
            )

    async def _generate_async(
        self,
        *,
        prompt: str,
        model: Optional[str],
        image_url: Optional[str],
        duration: Optional[int],
        resolution: str,
    ) -> Dict[str, Any]:
        api_key, base_url = _resolve_minimax_credentials()
        prompt = (prompt or "").strip()
        if not api_key:
            return error_response(
                error="No MiniMax credentials found. Set MINIMAX_API_KEY or configure MiniMax via `hermes tools`.",
                error_type="auth_required",
                provider="minimax",
                prompt=prompt,
            )
        if not prompt:
            return error_response(
                error="prompt is required for MiniMax video generation.",
                error_type="missing_prompt",
                provider="minimax",
                prompt=prompt,
            )

        model_id = _normalize_model(model)
        image_url_norm = (image_url or "").strip() or None
        modality = "image" if image_url_norm else "text"
        if not _model_supports_modality(model_id, modality):
            return error_response(
                error=f"MiniMax model {model_id} does not support {modality}-to-video in Hermes' unified surface.",
                error_type="modality_unsupported",
                provider="minimax",
                model=model_id,
                prompt=prompt,
            )

        payload, clamped_duration, normalized_resolution, modality = _build_payload(
            prompt=prompt,
            model_id=model_id,
            image_url=image_url_norm,
            duration=duration,
            resolution=resolution,
        )

        async with httpx.AsyncClient() as client:
            try:
                task_id = await _submit_task(client, payload, api_key=api_key, base_url=base_url)
            except httpx.HTTPStatusError as exc:
                detail = ""
                try:
                    detail = exc.response.text[:500]
                except Exception:
                    pass
                return error_response(
                    error=f"MiniMax submit failed ({exc.response.status_code}): {detail or exc}",
                    error_type="api_error",
                    provider="minimax",
                    model=model_id,
                    prompt=prompt,
                )

            poll_result = await _poll_task(
                client,
                task_id,
                api_key=api_key,
                base_url=base_url,
                timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
                poll_interval=DEFAULT_POLL_INTERVAL_SECONDS,
            )
            status = poll_result["status"]
            body = poll_result["body"]

            if status == SUCCESS_STATUS:
                file_id = _extract_file_id(body)
                if not file_id:
                    return error_response(
                        error="MiniMax video generation completed without file_id",
                        error_type="empty_response",
                        provider="minimax",
                        model=model_id,
                        prompt=prompt,
                    )
                try:
                    download_url = await _retrieve_file_url(
                        client,
                        file_id,
                        api_key=api_key,
                        base_url=base_url,
                    )
                except httpx.HTTPStatusError as exc:
                    detail = ""
                    try:
                        detail = exc.response.text[:500]
                    except Exception:
                        pass
                    return error_response(
                        error=f"MiniMax file retrieve failed ({exc.response.status_code}): {detail or exc}",
                        error_type="api_error",
                        provider="minimax",
                        model=model_id,
                        prompt=prompt,
                    )

                extra: Dict[str, Any] = {
                    "task_id": task_id,
                    "file_id": file_id,
                    "resolution": normalized_resolution,
                }
                for key in ("video_width", "video_height"):
                    if body.get(key) is not None:
                        extra[key] = body[key]
                return success_response(
                    video=download_url,
                    model=model_id,
                    prompt=prompt,
                    modality=modality,
                    aspect_ratio="",
                    duration=clamped_duration,
                    provider="minimax",
                    extra=extra,
                )

            if status == "timeout":
                return error_response(
                    error=f"Timed out waiting for MiniMax video generation after {DEFAULT_TIMEOUT_SECONDS}s",
                    error_type="timeout",
                    provider="minimax",
                    model=model_id,
                    prompt=prompt,
                )

            message = (
                body.get("message")
                or body.get("error")
                or body.get("fail_reason")
                or f"MiniMax video generation ended with status '{status}'"
            )
            return error_response(
                error=str(message),
                error_type="minimax_fail",
                provider="minimax",
                model=model_id,
                prompt=prompt,
            )


def register(ctx) -> None:
    """Plugin entry point — wire ``MiniMaxVideoGenProvider`` into the registry."""
    ctx.register_video_gen_provider(MiniMaxVideoGenProvider())
