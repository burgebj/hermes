"""Prometheus Avatar plugin for Hermes Agent.

Exposes three tools that let a Hermes agent browse and describe avatar
assets (skins, voices, personas, effects) and check the plugin's own
status.

Version 0.1 ships deterministic stub handlers so reviewers can load the
plugin on any Hermes install without extra config. Version 0.2 wires these
handlers to the live Prometheus service described in README.md.

Companion fast-path skill: optional-skills/creative/prometheus-avatar/
(PR #9754 to NousResearch/hermes-agent).
"""

from __future__ import annotations

import json
from typing import Any

__version__ = "0.1.0"

TOOLSET = "avatar"

# ---------------------------------------------------------------------------
# Demo catalog used by the v0.1 stub handlers.
# ---------------------------------------------------------------------------

_DEMO_CATALOG: dict[str, list[dict[str, Any]]] = {
    "skins": [
        {"id": "prometheus_avatar:skin/demo-neon", "name": "Neon Demo",
         "rarity": "common"},
        {"id": "prometheus_avatar:skin/demo-koi", "name": "Koi Demo",
         "rarity": "rare"},
    ],
    "voices": [
        {"id": "prometheus_avatar:voice/demo-calm", "name": "Calm Demo",
         "rarity": "common"},
        {"id": "prometheus_avatar:voice/demo-warm", "name": "Warm Demo",
         "rarity": "common"},
    ],
    "personas": [
        {"id": "prometheus_avatar:persona/demo-companion",
         "name": "Companion Demo", "rarity": "common"},
    ],
    "effects": [
        {"id": "prometheus_avatar:effect/demo-sparkle",
         "name": "Sparkle Demo", "rarity": "common"},
    ],
}

_VALID_CATEGORIES = tuple(_DEMO_CATALOG.keys())


def _error(message: str) -> str:
    return json.dumps({"error": message})


# ---------------------------------------------------------------------------
# Tool handlers. Each accepts ``args: dict`` and returns a JSON string.
# ---------------------------------------------------------------------------

def _list_assets_handler(args: dict, **_: Any) -> str:
    category = (args or {}).get("category")
    if category not in _VALID_CATEGORIES:
        return _error(
            f"Unknown category {category!r}. "
            f"Expected one of: {', '.join(_VALID_CATEGORIES)}."
        )
    payload = {
        "category": category,
        "mode": "stub",
        "assets": _DEMO_CATALOG[category],
    }
    return json.dumps(payload)


def _describe_handler(args: dict, **_: Any) -> str:
    asset_id = (args or {}).get("asset_id")
    if not asset_id or not isinstance(asset_id, str):
        return _error("Missing required string argument 'asset_id'.")

    for category, assets in _DEMO_CATALOG.items():
        for asset in assets:
            if asset["id"] == asset_id:
                payload = {
                    "id": asset["id"],
                    "name": asset["name"],
                    "category": category,
                    "rarity": asset["rarity"],
                    "preview_url": None,
                    "description": (
                        f"Demo {category[:-1]} used by the v0.1 stub. "
                        "Returns deterministic metadata only."
                    ),
                    "mode": "stub",
                }
                return json.dumps(payload)

    return _error(f"Unknown asset_id {asset_id!r}.")


def _status_handler(_args: dict, **_: Any) -> str:
    payload = {
        "service": "ok",
        "plugin": "prometheus_avatar",
        "version": __version__,
        "mode": "stub",
        "note": (
            "v0.1 returns demo data. v0.2 calls the live Prometheus "
            "service configured via environment variables (see README)."
        ),
    }
    return json.dumps(payload)


# ---------------------------------------------------------------------------
# OpenAI-format tool schemas.
# ---------------------------------------------------------------------------

_LIST_ASSETS_SCHEMA = {
    "description": (
        "List available avatar assets from the Prometheus marketplace. "
        "v0.1 returns a demo catalog; v0.2 calls the live service."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "enum": list(_VALID_CATEGORIES),
                "description": "Asset category to list.",
            },
        },
        "required": ["category"],
    },
}

_DESCRIBE_SCHEMA = {
    "description": (
        "Return metadata for a single avatar asset by its identifier. "
        "v0.1 accepts demo IDs from avatar_list_assets only."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "asset_id": {
                "type": "string",
                "description": (
                    "Fully-qualified asset ID, e.g. "
                    "'prometheus_avatar:skin/demo-neon'."
                ),
            },
        },
        "required": ["asset_id"],
    },
}

_STATUS_SCHEMA = {
    "description": (
        "Report the plugin's current mode and version. Useful as a smoke "
        "check that the plugin loaded correctly."
    ),
    "parameters": {
        "type": "object",
        "properties": {},
    },
}


# ---------------------------------------------------------------------------
# Registration entry point.
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register the three v0.1 stub tools with Hermes."""
    ctx.register_tool(
        name="avatar_list_assets",
        toolset=TOOLSET,
        schema=_LIST_ASSETS_SCHEMA,
        handler=_list_assets_handler,
        description=_LIST_ASSETS_SCHEMA["description"],
        emoji="🎭",
    )
    ctx.register_tool(
        name="avatar_describe",
        toolset=TOOLSET,
        schema=_DESCRIBE_SCHEMA,
        handler=_describe_handler,
        description=_DESCRIBE_SCHEMA["description"],
        emoji="🔍",
    )
    ctx.register_tool(
        name="avatar_status",
        toolset=TOOLSET,
        schema=_STATUS_SCHEMA,
        handler=_status_handler,
        description=_STATUS_SCHEMA["description"],
        emoji="📡",
    )
