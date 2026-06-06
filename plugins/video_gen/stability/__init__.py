"""Stability AI video generation backend.

User-facing surface: pick a **model** (``svd`` or ``svd-xt``).
Stability AI's Stable Video Diffusion is **image-to-video only** — the user
must provide an ``image_url`` to animate.

Model tiers:
  svd       — Stable Video Diffusion, 14 frames (~2.5s)
  svd-xt    — Extended version, 25 frames (~4s)

Selection precedence:
    1. ``model=`` arg from the tool call
    2. ``STABILITY_VIDEO_MODEL`` env var
    3. ``video_gen.stability.model`` in ``config.yaml``
    4. ``video_gen.model`` in ``config.yaml`` (when it's one of our IDs)
    5. ``DEFAULT_MODEL`` (svd-xt)

Authentication via ``STABILITY_API_KEY`` (Bearer token). Output is a base64
video or an HTTPS URL from Stability's CDN.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from agent.video_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_RESOLUTION,
    VideoGenProvider,
    error_response,
    save_b64_video,
    success_response,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

STABILITY_MODELS: Dict[str, Dict[str, Any]] = {
    "svd": {
        "display": "Stable Video Diffusion",
        "model_id": "stable-video-diffusion",
        "speed": "~1-2 min",
        "price": "$0.05/s",
        "strengths": "Open-weight, reliable motion, 14 frames (~2.5s)",
        "modalities": ["image"],
    },
    "svd-xt": {
        "display": "Stable Video Diffusion XT",
        "model_id": "stable-video-diffusion-xt",
        "speed": "~1-2 min",
        "price": "$0.08/s",
        "strengths": "Extended version, 25 frames (~4s), smoother motion",
        "modalities": ["image"],
    },
}

DEFAULT_MODEL = "svd-xt"


class StabilityProvider(VideoGenProvider):
    """Stability AI Stable Video Diffusion backend."""

    @property
    def name(self) -> str:
        return "stability"

    @property
    def display_name(self) -> str:
        return "Stability AI"

    def is_available(self) -> bool:
        return bool(os.environ.get("STABILITY_API_KEY"))

    def list_models(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for mid, meta in STABILITY_MODELS.items():
            out.append({
                "id": mid,
                "display": meta["display"],
                "speed": meta["speed"],
                "strengths": meta["strengths"],
                "price": meta["price"],
                "modalities": meta["modalities"],
            })
        return out

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def capabilities(self) -> Dict[str, Any]:
        return {
            "modalities": ["image"],  # SVD is image-to-video only
            "aspect_ratios": ["16:9", "9:16"],
            "resolutions": ["576p", "768p", "1024p"],
            "min_duration": 2,
            "max_duration": 5,
            "supports_audio": False,
            "supports_negative_prompt": False,
            "max_reference_images": 0,
        }

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Stability AI",
            "badge": "paid",
            "tag": "Stable Video Diffusion — image-to-video only",
            "env_vars": [
                {
                    "key": "STABILITY_API_KEY",
                    "prompt": "Stability AI API key",
                    "url": "https://platform.stability.ai/account/keys",
                },
            ],
        }

    # -----------------------------------------------------------------------
    # Model resolution
    # -----------------------------------------------------------------------

    def _resolve_model(self, model: Optional[str]) -> str:
        if model and model in STABILITY_MODELS:
            return model
        env_model = os.environ.get("STABILITY_VIDEO_MODEL")
        if env_model and env_model in STABILITY_MODELS:
            return env_model
        try:
            from hermes_cli.config import load_config
            cfg = load_config()
            stab_cfg = (cfg or {}).get("video_gen", {}).get("stability", {})
            if isinstance(stab_cfg, dict):
                config_model = stab_cfg.get("model")
                if isinstance(config_model, str) and config_model in STABILITY_MODELS:
                    return config_model
                generic = (cfg or {}).get("video_gen", {}).get("model")
                if isinstance(generic, str) and generic in STABILITY_MODELS:
                    return generic
        except Exception:
            pass
        return DEFAULT_MODEL

    # -----------------------------------------------------------------------
    # Generation
    # -----------------------------------------------------------------------

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
        """Generate video via Stability AI.

        SVD is image-to-video ONLY — image_url is required.
        """
        resolved_model = self._resolve_model(model)
        model_meta = STABILITY_MODELS[resolved_model]

        # SVD requires an image
        if not image_url or not image_url.strip():
            return error_response(
                error="Stability AI (SVD) requires an image_url. It is image-to-video only.",
                error_type="modality_unsupported",
                provider=self.name,
                model=resolved_model,
                prompt=prompt,
            )

        api_key = os.environ.get("STABILITY_API_KEY")
        if not api_key:
            return error_response(
                error="STABILITY_API_KEY not set. Set it via `hermes tools` → Video Generation.",
                error_type="missing_api_key",
                provider=self.name,
                model=resolved_model,
                prompt=prompt,
            )

        # Stability API v1/generation endpoint
        model_id = model_meta["model_id"]
        url = f"https://api.stability.ai/v1/generation/{model_id}/image-to-video"

        # Build multipart form data
        form_data: Dict[str, Any] = {
            "image": image_url.strip(),
        }
        if seed is not None:
            form_data["seed"] = seed
        # cfg_scale controls how closely the output follows the input image
        # motion_bucket_id controls the amount of motion (1-255)
        form_data["motion_bucket_id"] = 127  # default
        form_data["cfg_scale"] = 1.0  # default

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        try:
            return self._submit_and_poll(
                url=url,
                form_data=form_data,
                headers=headers,
                resolved_model=resolved_model,
                prompt=prompt,
                aspect_ratio=aspect_ratio,
                duration=duration or 4,
            )
        except requests.exceptions.RequestException as exc:
            logger.error("Stability API request failed: %s", exc)
            return error_response(
                error=f"Stability API error: {exc}",
                error_type="api_error",
                provider=self.name,
                model=resolved_model,
                prompt=prompt,
            )
        except Exception as exc:
            logger.error("Stability generation failed: %s", exc)
            return error_response(
                error=f"Generation error: {exc}",
                error_type="generation_error",
                provider=self.name,
                model=resolved_model,
                prompt=prompt,
            )

    def _submit_and_poll(
        self,
        url: str,
        form_data: Dict[str, Any],
        headers: Dict[str, str],
        resolved_model: str,
        prompt: str,
        aspect_ratio: str,
        duration: int,
    ) -> Dict[str, Any]:
        """Submit generation job and poll until complete."""
        logger.info("Submitting Stability generation with image: %s", form_data.get("image", "")[:80])

        # Submit
        resp = requests.post(url, data=form_data, headers=headers, timeout=30)
        if resp.status_code not in (200, 201, 202):
            raise RuntimeError(f"Submit failed: HTTP {resp.status_code} — {resp.text}")

        job_data = resp.json()
        generation_id = job_data.get("id")
        if not generation_id:
            raise RuntimeError(f"No generation ID in response: {job_data}")

        logger.info("Stability task submitted: %s", generation_id)

        # Poll
        max_wait = 300  # SVD is relatively fast, 5 min max
        poll_interval = 5
        elapsed = 0

        status_url = f"https://api.stability.ai/v1/generation/status/{generation_id}"

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            status_resp = requests.get(status_url, headers=headers, timeout=15)
            if status_resp.status_code != 200:
                raise RuntimeError(f"Status check failed: HTTP {status_resp.status_code}")

            status_data = status_resp.json()
            state = status_data.get("status", "").lower()

            if state in ("success", "succeeded", "completed"):
                # Fetch the result
                result_url = f"https://api.stability.ai/v1/generation/status/{generation_id}/b64-json"
                result_resp = requests.get(result_url, headers=headers, timeout=30)
                if result_resp.status_code != 200:
                    raise RuntimeError(f"Result fetch failed: HTTP {result_resp.status_code}")

                result_data = result_resp.json()
                # Stability returns base64 video data
                artifacts = result_data.get("artifacts", [])
                if artifacts:
                    b64_data = artifacts[0].get("base64")
                    if b64_data:
                        saved_path = save_b64_video(b64_data, prefix="stability_svd", extension="mp4")
                        return success_response(
                            video=str(saved_path),
                            model=resolved_model,
                            prompt=prompt,
                            modality="image",
                            aspect_ratio=aspect_ratio,
                            duration=duration,
                            provider=self.name,
                        )
                raise RuntimeError(f"No video artifacts in result: {result_data}")

            elif state in ("error", "failed"):
                error_msg = status_data.get("message", "Unknown error")
                raise RuntimeError(f"Generation failed: {error_msg}")

            logger.info(
                "Stability generation in progress: %s%% (%ds elapsed)",
                status_data.get("progress", status_data.get("meta", {}).get("progress", "?")),
                elapsed,
            )

        return error_response(
            error=f"Stability generation timed out after {max_wait}s. Generation ID: {generation_id}",
            error_type="timeout",
            provider=self.name,
            model=resolved_model,
            prompt=prompt,
            aspect_ratio=aspect_ratio,
        )


def register(ctx) -> None:
    """Register the Stability AI video generation provider."""
    ctx.register_video_gen_provider(StabilityProvider())
