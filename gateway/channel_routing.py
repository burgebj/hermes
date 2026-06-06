"""
Channel routing — load a different profile's model, credentials, persona, and
memory per chat_id so a single gateway can serve multiple isolated profiles.

This enables scenarios like:
  - A "family" Signal group uses a family-friendly model with its own SOUL.md
  - A "work" Telegram chat routes to a developer-focused profile
  - A personal DM stays on the default profile

Config example in config.yaml:

    channel_routes:
      \"group:abc123...\":
        profile: personal
      \"group:def456...\":
        profile: work
      \"+123****7890\":
        profile: family

Each routed profile must exist (created via ``hermes profile create``).
The profile's config.yaml provides model/provider/base_url, its .env provides
API keys, and its SOUL.md + memories/ provide identity and context.

When a route matches:
  - The routed profile's model overrides the gateway default
  - The routed profile's credentials are used for API calls
  - The routed profile's SOUL.md replaces the global one
  - The routed profile's memories replace global memories
  - skip_context_files and skip_memory prevent double-loading
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProfileContext:
    """Resolved profile overrides for a routed channel."""

    profile_name: str
    profile_dir: Path
    model: str
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    provider: Optional[str] = None
    soul_content: Optional[str] = None
    memory_block: Optional[str] = None
    dotenv_overrides: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_profile_config(profile_dir: Path) -> dict:
    """Load config.yaml from a profile directory."""
    config_path = profile_dir / "config.yaml"
    if not config_path.exists():
        return {}
    try:
        import yaml

        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.warning("channel_routing: failed to load %s: %s", config_path, e)
        return {}


def _load_profile_dotenv(profile_dir: Path) -> dict:
    """Parse .env from profile directory without modifying os.environ."""
    env_path = profile_dir / ".env"
    if not env_path.exists():
        return {}
    try:
        from dotenv import dotenv_values

        return dict(dotenv_values(env_path, encoding="utf-8"))
    except Exception:
        try:
            from dotenv import dotenv_values

            return dict(dotenv_values(env_path, encoding="latin-1"))
        except Exception as e:
            logger.warning("channel_routing: failed to parse %s: %s", env_path, e)
            return {}


def _read_file_safe(path: Path) -> Optional[str]:
    """Read a text file, returning None on missing/error."""
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def _build_memory_block(profile_dir: Path) -> Optional[str]:
    """Build a memory injection block from a profile's memories directory.

    Reads USER.md and MEMORY.md and combines them into a formatted block
    suitable for injecting into the ephemeral system prompt.
    """
    mem_dir = profile_dir / "memories"
    if not mem_dir.is_dir():
        return None

    parts: List[str] = []
    user_md = _read_file_safe(mem_dir / "USER.md")
    if user_md:
        parts.append(f"## User profile\n{user_md}")

    memory_md = _read_file_safe(mem_dir / "MEMORY.md")
    if memory_md:
        parts.append(f"## Persistent memory\n{memory_md}")

    return "\n\n".join(parts) if parts else None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_channel_route(
    chat_id: str,
    channel_routes: dict,
) -> Optional[ProfileContext]:
    """Resolve a chat_id to a ProfileContext if a route is configured.

    Returns None if no route matches (use default profile).

    Args:
        chat_id: The full chat identifier (e.g. "group:abc123...").
        channel_routes: The ``channel_routes`` dict from config.yaml.
    """
    if not channel_routes or not chat_id:
        return None

    route = channel_routes.get(chat_id)
    if not route:
        return None

    profile_name = route if isinstance(route, str) else route.get("profile")
    if not profile_name:
        return None

    # Resolve profile directory
    try:
        from hermes_cli.profiles import get_profile_dir, profile_exists
    except ImportError:
        logger.warning("channel_routing: hermes_cli.profiles not available")
        return None

    if not profile_exists(profile_name):
        logger.warning("channel_routing: profile '%s' does not exist", profile_name)
        return None

    profile_dir = get_profile_dir(profile_name)

    # Load config.yaml — extract model settings
    cfg = _load_profile_config(profile_dir)
    model_cfg = cfg.get("model", {})
    if isinstance(model_cfg, str):
        model = model_cfg
        base_url: Optional[str] = None
        provider: Optional[str] = None
    elif isinstance(model_cfg, dict):
        model = model_cfg.get("default") or model_cfg.get("model") or ""
        base_url = model_cfg.get("base_url")
        provider = model_cfg.get("provider")
    else:
        model = ""
        base_url = None
        provider = None

    # Load .env for credentials
    dotenv = _load_profile_dotenv(profile_dir)
    api_key = (
        dotenv.get("OPENROUTER_API_KEY")
        or dotenv.get("ANTHROPIC_API_KEY")
        or dotenv.get("OPENAI_API_KEY")
    )

    # For custom providers with no-key or empty key, use the base_url from config
    if provider == "custom" and not api_key:
        api_key = dotenv.get("LLM_API_KEY") or "no-key"

    # Load SOUL.md — profile-specific identity/persona
    soul_content = _read_file_safe(profile_dir / "SOUL.md")

    # Load memory block (USER.md + MEMORY.md)
    memory_block = _build_memory_block(profile_dir)

    ctx = ProfileContext(
        profile_name=profile_name,
        profile_dir=profile_dir,
        model=model,
        base_url=base_url,
        api_key=api_key,
        provider=provider,
        soul_content=soul_content,
        memory_block=memory_block,
        dotenv_overrides=dotenv,
    )

    logger.info(
        "Channel route: %s -> profile '%s' (model=%s, base_url=%s)",
        chat_id[:24] + "..." if len(chat_id) > 24 else chat_id,
        profile_name,
        model,
        base_url or "(default)",
    )
    return ctx


def build_routed_runtime_kwargs(ctx: ProfileContext) -> dict:
    """Build runtime agent kwargs from a ProfileContext.

    This is analogous to _resolve_runtime_agent_kwargs() but uses the
    routed profile's credentials instead of the current environment.
    """
    return {
        "api_key": ctx.api_key,
        "base_url": ctx.base_url,
        "provider": ctx.provider,
        "api_mode": None,
        "command": None,
        "args": [],
        "credential_pool": None,
    }


def build_routed_ephemeral_prompt(
    ctx: ProfileContext,
    platform_context: str = "",
) -> str:
    """Build combined ephemeral system prompt for a routed profile.

    Layers (in order):
    1. Profile SOUL.md (identity/persona)
    2. Profile memory block (persistent memory + user profile)
    3. Platform context (channel info, session context from gateway)

    Args:
        ctx: The resolved ProfileContext.
        platform_context: The platform-specific context prompt from the gateway.

    Returns:
        Combined prompt string, or empty string if nothing to inject.
    """
    parts: List[str] = []
    if ctx.soul_content:
        parts.append(ctx.soul_content)
    if ctx.memory_block:
        parts.append(ctx.memory_block)
    if platform_context:
        parts.append(platform_context)
    return "\n\n".join(p for p in parts if p)