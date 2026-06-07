"""Azure AI Foundry image generation backend.

Exposes Azure AI Foundry's gpt-image-2 as an :class:`ImageGenProvider`
implementation using the Azure OpenAI v1 API (``openai.OpenAI`` with
``base_url`` pointing to ``/openai/v1/``).

The user configures one deployment (e.g. ``gpt-image-2``). Quality is
configured globally (``"low"`` / ``"medium"`` / ``"high"``) via the
``AZURE_FOUNDRY_IMAGE_QUALITY`` env var or ``image_gen.azure_foundry.quality``
in ``config.yaml``, defaulting to ``"medium"``.

Configuration
-------------
Resolution order (first hit wins):

1. Environment variables::

       AZURE_FOUNDRY_IMAGE_ENDPOINT   — Azure resource endpoint
                                        e.g. https://my-resource.openai.azure.com
       AZURE_FOUNDRY_IMAGE_KEY        — API key (not needed for Entra ID)
       AZURE_FOUNDRY_IMAGE_DEPLOYMENT — deployment name (default: gpt-image-2)
       AZURE_FOUNDRY_IMAGE_AUTH_MODE  — ``api_key`` (default) or ``entra_id``
       AZURE_FOUNDRY_IMAGE_QUALITY    — quality tier: low / medium / high (default: medium)

2. ``image_gen.azure_foundry`` section in ``config.yaml``::

       image_gen:
         provider: azure_foundry
         azure_foundry:
           endpoint: "https://my-resource.openai.azure.com"
           deployment_name: "gpt-image-2"
           auth_mode: "api_key"         # or "entra_id" for keyless auth

Authentication
--------------
**API key** (default): set ``AZURE_FOUNDRY_IMAGE_KEY`` in ``.env``.

**Microsoft Entra ID**: keyless RBAC auth via ``azure-identity``'s
``DefaultAzureCredential`` chain (az login, managed identity, workload
identity, service principal env vars). Set
``image_gen.azure_foundry.auth_mode: entra_id`` in ``config.yaml``
or ``AZURE_FOUNDRY_IMAGE_AUTH_MODE=entra_id``. No API key needed;
requires the ``Azure AI User`` role on the Foundry resource.

Quality
-------
Set quality via ``AZURE_FOUNDRY_IMAGE_QUALITY`` env var or
``image_gen.azure_foundry.quality`` in ``config.yaml``.
Valid values: ``"low"``, ``"medium"``, ``"high"``. Default: ``"medium"``.

Sizes
-----
``1024x1024`` (square), ``1536x1024`` (landscape), ``1024x1536`` (portrait).
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_DEPLOYMENT = "gpt-image-2"

VALID_QUALITY_VALUES = {"low", "medium", "high"}
DEFAULT_QUALITY = "medium"


def _resolve_quality() -> str:
    """Resolve quality setting from env var or config.yaml.

    Precedence:
    1. ``AZURE_FOUNDRY_IMAGE_QUALITY`` env var
    2. ``image_gen.azure_foundry.quality`` in config.yaml
    3. :data:`DEFAULT_QUALITY` (``"medium"``)

    Unknown values are silently ignored and fall back to the default.
    """
    env_val = os.environ.get("AZURE_FOUNDRY_IMAGE_QUALITY", "").strip().lower()
    if env_val:
        return env_val if env_val in VALID_QUALITY_VALUES else DEFAULT_QUALITY

    cfg = _load_azure_foundry_config()
    cfg_val = str(cfg.get("quality") or "").strip().lower()
    if cfg_val and cfg_val in VALID_QUALITY_VALUES:
        return cfg_val

    return DEFAULT_QUALITY

_SIZES: Dict[str, str] = {
    "landscape": "1536x1024",
    "square": "1024x1024",
    "portrait": "1024x1536",
}


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------


def _load_azure_foundry_config() -> Dict[str, Any]:
    """Read ``image_gen.azure_foundry`` from config.yaml (returns {} on failure)."""
    try:
        from hermes_cli.config import load_config

        cfg = load_config()
        img_cfg = cfg.get("image_gen") if isinstance(cfg, dict) else None
        if not isinstance(img_cfg, dict):
            return {}
        section = img_cfg.get("azure_foundry")
        return section if isinstance(section, dict) else {}
    except Exception as exc:
        logger.debug("Could not load image_gen.azure_foundry config: %s", exc)
        return {}


def _resolve_credentials() -> Dict[str, Any]:
    """Resolve endpoint, API key, deployment name, and auth mode.

    Returns a dict with keys: ``endpoint``, ``api_key``, ``deployment``,
    ``auth_mode``. ``api_key`` is empty string when ``auth_mode`` is
    ``"entra_id"``.
    """
    # 1. Dedicated env vars
    endpoint = os.environ.get("AZURE_FOUNDRY_IMAGE_ENDPOINT", "").strip()
    api_key = os.environ.get("AZURE_FOUNDRY_IMAGE_KEY", "").strip()
    deployment = os.environ.get("AZURE_FOUNDRY_IMAGE_DEPLOYMENT", "").strip()
    auth_mode = os.environ.get("AZURE_FOUNDRY_IMAGE_AUTH_MODE", "").strip().lower()

    # 2. config.yaml fills gaps
    cfg = _load_azure_foundry_config()
    if not endpoint:
        endpoint = str(cfg.get("endpoint") or "").strip()
    if not deployment:
        deployment = str(cfg.get("deployment_name") or "").strip()
    if not auth_mode:
        auth_mode = str(cfg.get("auth_mode") or "").strip().lower()

    return {
        "endpoint": endpoint,
        "api_key": api_key,
        "deployment": deployment or DEFAULT_DEPLOYMENT,
        "auth_mode": auth_mode or "api_key",
    }


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


class AzureFoundryImageGenProvider(ImageGenProvider):
    """Azure AI Foundry gpt-image-2 image generation backend.

    Uses ``openai.OpenAI`` with Azure OpenAI v1 ``base_url``.
    Supports API key and Microsoft Entra ID (keyless) authentication.
    Quality (low / medium / high) is resolved from config, not from the caller.
    """

    @property
    def name(self) -> str:
        return "azure-foundry"

    @property
    def display_name(self) -> str:
        return "Azure AI Foundry"

    def is_available(self) -> bool:
        creds = _resolve_credentials()
        if not creds.get("endpoint"):
            return False
        if creds.get("auth_mode") == "entra_id":
            return True
        return bool(creds.get("api_key"))

    def list_models(self) -> List[Dict[str, Any]]:
        """Return one entry for the configured deployment."""
        creds = _resolve_credentials()
        deployment = creds["deployment"]
        return [
            {
                "id": deployment,
                "display": f"Azure AI Foundry — {deployment}",
                "speed": "varies by quality",
                "strengths": "Quality configured globally: low / medium / high",
                "price": "varies",
            }
        ]

    def default_model(self) -> Optional[str]:
        return _resolve_credentials()["deployment"]

    def setup_interactive(self, config: dict) -> bool:
        """Interactive setup wizard for hermes tools.

        Prompts for endpoint URL, deployment name, and auth mode (API key
        or Microsoft Entra ID).  Saves endpoint/deployment/auth_mode to
        ``image_gen.azure_foundry`` in config and (for API key mode) the
        key to ``AZURE_FOUNDRY_IMAGE_KEY`` in .env.
        """
        import getpass
        from hermes_cli.config import get_env_value, save_env_value
        from hermes_cli.cli_output import print_success

        # Load existing values so the wizard can show defaults.
        _img = config.get("image_gen") or {}
        _az = _img.get("azure_foundry") if isinstance(_img, dict) else None
        cur: dict = _az if isinstance(_az, dict) else {}
        current_endpoint = str(cur.get("endpoint") or "").strip()
        current_deployment = str(cur.get("deployment_name") or "").strip()
        current_auth_mode = str(cur.get("auth_mode") or "api_key").strip().lower()
        current_key = get_env_value("AZURE_FOUNDRY_IMAGE_KEY") or ""

        print()
        print("  Azure AI Foundry \u2014 Image Generation Setup")
        print("  " + "\u2500" * 46)
        print()

        # ── Step 1: Endpoint URL ──────────────────────────────────────
        _ep_placeholder = current_endpoint or "https://<resource>.openai.azure.com"
        try:
            endpoint_input = input(f"  Endpoint URL [{_ep_placeholder}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Cancelled.")
            return False
        effective_endpoint = endpoint_input or current_endpoint
        if not effective_endpoint:
            print("  No endpoint provided. Cancelled.")
            return False
        if not effective_endpoint.startswith(("http://", "https://")):
            print(f"  Invalid URL: {effective_endpoint!r} (must start with https://)")
            return False

        # ── Step 2: Deployment name ───────────────────────────────────
        _dep_default = current_deployment or DEFAULT_DEPLOYMENT
        try:
            dep_input = input(f"  Deployment name [{_dep_default}]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Cancelled.")
            return False
        effective_deployment = dep_input or _dep_default

        # ── Step 3: Auth mode ─────────────────────────────────────────
        print()
        print("  Authentication:")
        print("    1. API key          (saved to AZURE_FOUNDRY_IMAGE_KEY in .env)")
        print("    2. Microsoft Entra ID  (keyless \u2014 az login / managed identity / workload identity)")
        print("       Requires the 'Azure AI User' role on the Foundry resource.")
        try:
            _auth_default = "2" if current_auth_mode == "entra_id" else "1"
            auth_input = (
                input(f"  Auth mode [1/2] ({_auth_default}): ").strip() or _auth_default
            )
        except (KeyboardInterrupt, EOFError):
            print("\n  Cancelled.")
            return False
        use_entra = auth_input == "2"
        auth_mode_label = "entra_id" if use_entra else "api_key"

        # ── Step 4: Credentials ───────────────────────────────────────
        effective_key = ""

        if use_entra:
            try:
                from agent.azure_identity_adapter import (
                    EntraIdentityConfig,
                    describe_active_credential,
                    has_azure_identity_installed,
                )
            except ImportError as exc:
                print(f"\n  \u26a0 Could not import azure-identity adapter: {exc}")
                print("  Falling back to API key auth.")
                use_entra = False
                auth_mode_label = "api_key"

        if use_entra:
            print()
            if not has_azure_identity_installed():
                print("  azure-identity is not installed.")
                print("  It will be auto-installed on first use, or run: pip install azure-identity")
            else:
                print("  \u25d0 Probing Microsoft Entra ID credential chain (up to 10 s)...")
                _entra_cfg = EntraIdentityConfig()
                info = describe_active_credential(config=_entra_cfg, timeout_seconds=10.0)
                if info.get("ok"):
                    _sources = info.get("env_sources") or []
                    _tag = ", ".join(_sources) if _sources else "default chain"
                    print(f"  \u2713 Entra ID token acquired ({_tag})")
                else:
                    _err = info.get("error") or "credential chain exhausted"
                    _hint = info.get("hint") or (
                        "Run `az login`, attach a managed identity, or set "
                        "AZURE_TENANT_ID / AZURE_CLIENT_ID / AZURE_CLIENT_SECRET."
                    )
                    print(f"  \u26a0 {_err}")
                    print(f"    Hint: {_hint}")
                    try:
                        _ans = input("  Save Entra config anyway and validate later? [Y/n]: ").strip().lower()
                    except (KeyboardInterrupt, EOFError):
                        print("\n  Cancelled.")
                        return False
                    if _ans and _ans not in ("y", "yes"):
                        print("  Cancelled.")
                        return False
        else:
            print()
            try:
                _key_hint = current_key[:8] + "..." if current_key else "required"
                key_input = getpass.getpass(f"  API key [{_key_hint}]: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n  Cancelled.")
                return False
            effective_key = key_input or current_key
            if not effective_key:
                print("  No API key provided. Cancelled.")
                return False

        # ── Persist ───────────────────────────────────────────────────
        if not use_entra:
            save_env_value("AZURE_FOUNDRY_IMAGE_KEY", effective_key)

        img_section = config.setdefault("image_gen", {})
        if not isinstance(img_section, dict):
            img_section = {}
            config["image_gen"] = img_section

        az_section = img_section.setdefault("azure_foundry", {})
        if not isinstance(az_section, dict):
            az_section = {}
            img_section["azure_foundry"] = az_section

        az_section["endpoint"] = effective_endpoint
        az_section["deployment_name"] = effective_deployment
        az_section["auth_mode"] = auth_mode_label

        img_section["provider"] = self.name
        img_section["use_gateway"] = False

        _auth_label = "Microsoft Entra ID (keyless)" if use_entra else "API key"
        print_success(f"  Azure AI Foundry image gen configured:")
        print_success(f"    Endpoint:   {effective_endpoint}")
        print_success(f"    Deployment: {effective_deployment}")
        print_success(f"    Auth:       {_auth_label}")
        return True

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Azure AI Foundry",
            "badge": "paid",
            "tag": (
                "gpt-image-2 via Azure AI Foundry — requires an Azure "
                "resource with an image generation deployment."
            ),
            "env_vars": [
            ],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate an image using Azure AI Foundry.

        Quality is resolved from configuration (``AZURE_FOUNDRY_IMAGE_QUALITY``
        env var or ``image_gen.azure_foundry.quality`` in config.yaml).
        It is not a per-call parameter.

        Args:
            prompt:       Text description of the image to generate.
            aspect_ratio: ``"landscape"``, ``"square"``, or ``"portrait"``.
            **kwargs:     Ignored (forward-compat).

        Returns:
            A dict from :func:`success_response` or :func:`error_response`.
        """
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        # --- quality from config ---
        resolved_quality = _resolve_quality()

        # --- input validation ---
        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string.",
                error_type="invalid_argument",
                provider=self.name,
                aspect_ratio=aspect,
            )

        # --- credentials ---
        creds = _resolve_credentials()
        endpoint = creds.get("endpoint", "")
        api_key = creds.get("api_key", "")
        auth_mode = creds.get("auth_mode", "api_key")

        if not endpoint:
            return error_response(
                error=(
                    "Azure AI Foundry endpoint not configured. "
                    "Set AZURE_FOUNDRY_IMAGE_ENDPOINT or configure "
                    "image_gen.azure_foundry.endpoint in config.yaml."
                ),
                error_type="auth_required",
                provider=self.name,
                aspect_ratio=aspect,
            )

        if auth_mode != "entra_id" and not api_key:
            return error_response(
                error=(
                    "Azure AI Foundry API key not configured. "
                    "Set AZURE_FOUNDRY_IMAGE_KEY in .env, or set "
                    "image_gen.azure_foundry.auth_mode: entra_id for keyless auth."
                ),
                error_type="auth_required",
                provider=self.name,
                aspect_ratio=aspect,
            )

        # --- openai SDK ---
        try:
            import openai
        except ImportError:
            return error_response(
                error="openai Python package not installed (pip install openai)",
                error_type="missing_dependency",
                provider=self.name,
                aspect_ratio=aspect,
            )

        deployment = creds["deployment"]
        base_url = endpoint.rstrip("/") + "/openai/v1/"
        size = _SIZES.get(aspect, _SIZES["square"])

        # --- build auth (API key or Entra ID token provider) ---
        if auth_mode == "entra_id":
            try:
                from agent.azure_identity_adapter import (
                    EntraIdentityConfig,
                    build_token_provider,
                )
                _entra_cfg = EntraIdentityConfig()
                effective_api_key: Any = build_token_provider(config=_entra_cfg)
            except ImportError as exc:
                return error_response(
                    error=(
                        "Microsoft Entra ID auth requires azure-identity: "
                        f"pip install azure-identity ({exc})"
                    ),
                    error_type="missing_dependency",
                    provider=self.name,
                    aspect_ratio=aspect,
                )
        else:
            effective_api_key = api_key

        # --- API call (Azure OpenAI v1) ---
        try:
            client = openai.OpenAI(
                api_key=effective_api_key,
                base_url=base_url,
            )
            response = client.images.generate(
                model=deployment,
                prompt=prompt,
                size=size,  # type: ignore[arg-type]
                n=1,
                quality=resolved_quality,  # type: ignore[arg-type]
            )
        except Exception as exc:
            logger.debug("Azure Foundry image generation failed", exc_info=True)
            return error_response(
                error=f"Azure Foundry image generation failed: {exc}",
                error_type="api_error",
                provider=self.name,
                model=deployment,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        # --- response parsing ---
        data = getattr(response, "data", None) or []
        if not data:
            return error_response(
                error="Azure Foundry returned no image data.",
                error_type="empty_response",
                provider=self.name,
                model=deployment,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        first = data[0]
        b64 = getattr(first, "b64_json", None)
        url = getattr(first, "url", None)
        revised_prompt = getattr(first, "revised_prompt", None)

        if b64:
            try:
                saved_path = save_b64_image(b64, prefix=f"azure_foundry_{deployment}")
            except Exception as exc:
                return error_response(
                    error=f"Could not save image to cache: {exc}",
                    error_type="io_error",
                    provider=self.name,
                    model=deployment,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
            image_ref = str(saved_path)
        elif url:
            image_ref = url
        else:
            return error_response(
                error="Azure Foundry response contained neither b64_json nor URL.",
                error_type="empty_response",
                provider=self.name,
                model=deployment,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        extra: Dict[str, Any] = {"size": size, "quality": resolved_quality}
        if revised_prompt:
            extra["revised_prompt"] = revised_prompt

        return success_response(
            image=image_ref,
            model=deployment,
            prompt=prompt,
            aspect_ratio=aspect,
            provider=self.name,
            extra=extra,
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — register AzureFoundryImageGenProvider."""
    ctx.register_image_gen_provider(AzureFoundryImageGenProvider())
