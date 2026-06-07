"""AWS Bedrock Stability AI image generation backend.

Exposes Stability AI's three currently-active text-to-image models on Bedrock:

* ``stability.sd3-5-large-v1:0`` — Stable Diffusion 3.5 Large (default)
* ``stability.stable-image-core-v1:1`` — Stable Image Core (fast tier)
* ``stability.stable-image-ultra-v1:1`` — Stable Image Ultra (highest quality)

All three share the same request/response envelope on
``bedrock-runtime.invoke_model`` (verified against the AWS docs and live API
calls). Currently only available in ``us-west-2``.

Schema reference:
    https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-stability-diffusion.html

Authentication piggybacks on the standard AWS credential chain via boto3 —
env vars, ``~/.aws/credentials``, ``AWS_PROFILE``, EC2/ECS/EKS instance roles,
and ``AWS_BEARER_TOKEN_BEDROCK`` are all honored. We share the same probes as
the inference Bedrock plugin (``agent.bedrock_adapter``) so a user with Bedrock
inference already configured gets image generation for free.

Selection precedence for region (first hit wins):

1. ``image_gen.bedrock-stability.region`` in ``config.yaml``
2. ``bedrock.region`` in ``config.yaml`` (shared with the inference provider)
3. ``AWS_REGION`` / ``AWS_DEFAULT_REGION``
4. boto3/botocore configured region (from ``~/.aws/config``)
5. ``us-west-2`` fallback (the only region where Stability text-to-image is
   currently ACTIVE — ``us-east-1`` only has Stability editing tools, not
   text-to-image)

Selection precedence for model (first hit wins):

1. ``image_gen.bedrock-stability.model`` in ``config.yaml``
2. ``DEFAULT_MODEL`` (``stability.sd3-5-large-v1:0``)
"""

from __future__ import annotations

import json
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


# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

SD3_5_LARGE_MODEL_ID = "stability.sd3-5-large-v1:0"
STABLE_IMAGE_CORE_MODEL_ID = "stability.stable-image-core-v1:1"
STABLE_IMAGE_ULTRA_MODEL_ID = "stability.stable-image-ultra-v1:1"

_MODELS: Dict[str, Dict[str, Any]] = {
    SD3_5_LARGE_MODEL_ID: {
        "display": "Stable Diffusion 3.5 Large",
        "speed": "~10s",
        "strengths": "Flagship general-purpose; 8B params; high prompt adherence",
        "price": "varies",
    },
    STABLE_IMAGE_CORE_MODEL_ID: {
        "display": "Stable Image Core",
        "speed": "~5s",
        "strengths": "Fast and affordable; ideal for high-volume generation",
        "price": "varies",
    },
    STABLE_IMAGE_ULTRA_MODEL_ID: {
        "display": "Stable Image Ultra",
        "speed": "~15s",
        "strengths": "Highest quality; photorealistic; premium imagery",
        "price": "varies",
    },
}

DEFAULT_MODEL = SD3_5_LARGE_MODEL_ID

# Stability returns appropriate dimensions natively from these aspect ratios —
# no manual width/height math. Documented enum:
# 16:9, 1:1, 21:9, 2:3, 3:2, 4:5, 5:4, 9:16, 9:21
_ASPECT_RATIO_MAP: Dict[str, str] = {
    "landscape": "16:9",
    "square": "1:1",
    "portrait": "9:16",
}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _load_image_gen_config() -> Dict[str, Any]:
    """Return the ``image_gen`` section of ``config.yaml`` ({} on failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        section = cfg.get("image_gen") if isinstance(cfg, dict) else None
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen config: %s", exc)
        return {}


def _load_root_config() -> Dict[str, Any]:
    """Return the full top-level config dict ({} on failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        return cfg if isinstance(cfg, dict) else {}
    except Exception as exc:
        logger.debug("Could not load config: %s", exc)
        return {}


def _backend_config() -> Dict[str, Any]:
    """Return the ``image_gen.bedrock-stability`` config block ({} on failure)."""
    cfg = _load_image_gen_config()
    block = cfg.get("bedrock-stability") if isinstance(cfg.get("bedrock-stability"), dict) else {}
    return block if isinstance(block, dict) else {}


def _resolve_region() -> str:
    """Resolve the AWS region for Bedrock Stability calls.

    Defaults to ``us-west-2`` because that's the only region where Stability
    text-to-image models are currently ACTIVE on Bedrock — differs from the
    inference plugin's ``us-east-1`` default for that reason.
    """
    backend_cfg = _backend_config()
    region = backend_cfg.get("region")
    if isinstance(region, str) and region.strip():
        return region.strip()

    root = _load_root_config()
    bedrock_cfg = root.get("bedrock") if isinstance(root.get("bedrock"), dict) else {}
    if isinstance(bedrock_cfg, dict):
        region = bedrock_cfg.get("region")
        if isinstance(region, str) and region.strip():
            return region.strip()

    env_region = (
        os.environ.get("AWS_REGION", "").strip()
        or os.environ.get("AWS_DEFAULT_REGION", "").strip()
    )
    if env_region:
        return env_region

    # Try botocore session for ~/.aws/config region.
    try:
        import botocore.session  # type: ignore

        session_region = botocore.session.Session().get_config_variable("region")
        if isinstance(session_region, str) and session_region.strip():
            return session_region.strip()
    except Exception:
        pass

    return "us-west-2"


def _resolve_model() -> str:
    """Resolve which Stability model to use (config override → default)."""
    backend_cfg = _backend_config()
    model = backend_cfg.get("model")
    if isinstance(model, str) and model.strip():
        candidate = model.strip()
        if candidate in _MODELS:
            return candidate
        logger.warning(
            "image_gen.bedrock-stability.model=%r is not in the catalog; "
            "falling back to default %s",
            candidate,
            DEFAULT_MODEL,
        )
    return DEFAULT_MODEL


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class BedrockStabilityImageGenProvider(ImageGenProvider):
    """AWS Bedrock Stability AI backend (SD 3.5 Large / Core / Ultra)."""

    @property
    def name(self) -> str:
        return "bedrock-stability"

    @property
    def display_name(self) -> str:
        return "AWS Bedrock Stability AI"

    def is_available(self) -> bool:
        # Cheap probe: boto3 importable AND some AWS credential resolvable.
        try:
            import boto3  # noqa: F401
        except ImportError:
            return False
        try:
            from agent.bedrock_adapter import has_aws_credentials
            return has_aws_credentials()
        except Exception:
            # If the inference adapter isn't usable for some reason, fall back
            # to a minimal env-var sniff so we don't false-positive on a
            # totally unconfigured machine.
            return any(
                os.environ.get(k, "").strip()
                for k in (
                    "AWS_BEARER_TOKEN_BEDROCK",
                    "AWS_ACCESS_KEY_ID",
                    "AWS_PROFILE",
                    "AWS_CONTAINER_CREDENTIALS_RELATIVE_URI",
                    "AWS_WEB_IDENTITY_TOKEN_FILE",
                )
            )

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": model_id,
                "display": meta["display"],
                "speed": meta["speed"],
                "strengths": meta["strengths"],
                "price": meta["price"],
            }
            for model_id, meta in _MODELS.items()
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "AWS Bedrock Stability AI",
            "badge": "paid",
            "tag": (
                "stability.sd3-5-large-v1:0 / stable-image-core-v1:1 / "
                "stable-image-ultra-v1:1 via AWS SDK credential chain"
            ),
            # No env_vars to prompt for — boto3 picks up creds from
            # ~/.aws/credentials, AWS_PROFILE, IMDS, IRSA, etc.
            "env_vars": [],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)
        model_id = _resolve_model()

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider=self.name,
                model=model_id,
                aspect_ratio=aspect,
            )

        # Lazy boto3 install — same hook the inference plugin uses.
        try:
            from tools.lazy_deps import ensure
            ensure("provider.bedrock", prompt=False)
        except Exception:
            # Non-fatal: the import below will surface the real error if boto3
            # is genuinely missing and lazy_deps couldn't install it.
            pass

        try:
            import boto3  # noqa: F401
        except ImportError:
            return error_response(
                error=(
                    "boto3 is required for Bedrock Stability image generation. "
                    "Install with: pip install boto3"
                ),
                error_type="missing_dependency",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            from agent.bedrock_adapter import (
                _get_bedrock_runtime_client,
                has_aws_credentials,
            )
        except Exception as exc:  # pragma: no cover — adapter import must work
            logger.error("Failed to import bedrock_adapter helpers", exc_info=True)
            return error_response(
                error=f"Internal: could not load bedrock adapter helpers: {exc}",
                error_type="internal_error",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        if not has_aws_credentials():
            return error_response(
                error=(
                    "No AWS credentials found. Configure via `aws configure`, "
                    "set AWS_PROFILE, or export AWS_ACCESS_KEY_ID / "
                    "AWS_SECRET_ACCESS_KEY (or AWS_BEARER_TOKEN_BEDROCK) before "
                    "using Bedrock Stability image generation."
                ),
                error_type="auth_required",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        stability_aspect = _ASPECT_RATIO_MAP.get(aspect, "1:1")
        region = _resolve_region()

        # Stability text-to-image schema (shared by all three models per AWS docs):
        # required: prompt; optional: aspect_ratio, output_format, seed, negative_prompt, mode.
        body: Dict[str, Any] = {
            "prompt": prompt,
            "mode": "text-to-image",
            "aspect_ratio": stability_aspect,
            "output_format": "png",
        }

        try:
            client = _get_bedrock_runtime_client(region)
            response = client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                accept="application/json",
                contentType="application/json",
            )
        except Exception as exc:
            logger.debug("Bedrock Stability invoke_model failed", exc_info=True)
            return error_response(
                error=f"Bedrock Stability invocation failed: {exc}",
                error_type="api_error",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            raw_body = response["body"].read()
            payload = json.loads(raw_body)
        except Exception as exc:
            logger.debug("Could not parse Bedrock response", exc_info=True)
            return error_response(
                error=f"Could not parse Bedrock response: {exc}",
                error_type="invalid_response",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        # Stability response envelope:
        #   success: {"seeds": [...], "finish_reasons": [null], "images": ["base64..."]}
        #   filtered: {"finish_reasons": ["Filter reason: prompt"]}  (no images key)
        if not isinstance(payload, dict):
            return error_response(
                error="Bedrock Stability returned a non-object response",
                error_type="invalid_response",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        finish_reasons = payload.get("finish_reasons") or []
        non_null_reasons = [r for r in finish_reasons if r]
        images = payload.get("images") or []

        if not images:
            reason = non_null_reasons[0] if non_null_reasons else "no images returned"
            return error_response(
                error=f"Bedrock Stability returned no images: {reason}",
                error_type="empty_response",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        b64 = images[0]
        if not isinstance(b64, str) or not b64:
            return error_response(
                error="Bedrock Stability returned empty image data",
                error_type="empty_response",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            saved_path = save_b64_image(b64, prefix="bedrock_stability")
        except Exception as exc:
            logger.debug("Could not persist Stability image", exc_info=True)
            return error_response(
                error=f"Could not save image to cache: {exc}",
                error_type="io_error",
                provider=self.name,
                model=model_id,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {
            "aspect": stability_aspect,
            "region": region,
        }
        if non_null_reasons:
            extra["finish_reasons"] = non_null_reasons

        return success_response(
            image=str(saved_path),
            model=model_id,
            prompt=prompt,
            aspect_ratio=aspect,
            provider=self.name,
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — wire the Stability provider into the registry."""
    ctx.register_image_gen_provider(BedrockStabilityImageGenProvider())
