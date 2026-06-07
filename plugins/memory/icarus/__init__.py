"""Icarus memory provider — wraps the Icarus plugin as a MemoryProvider.

Discovers the user-installed Icarus plugin (from ``$HERMES_HOME/plugins/icarus/``)
at runtime and delegates all 16 fabric_* tool schemas and handlers to it.
Also exposes config for ``FABRIC_DIR``, ``ICARUS_ENDPOINT``, and
``ICARUS_EXTRACTION_MODEL``, and provides context prefetch via ``fabric_recall``.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Icarus plugin discovery — called once at provider init
# ---------------------------------------------------------------------------

_ICARUS_SCHEMAS: Optional[list] = None
_ICARUS_HANDLERS: Optional[dict] = None
_ICARUS_HOOKS_MODULE = None
_ICARUS_FOUND = False


def _discover_icarus() -> bool:
    """Discover and import the Icarus plugin at runtime.

    Returns True if the Icarus plugin was found and its schemas/tools
    were successfully imported.  Checks ``$HERMES_HOME/plugins/icarus/``
    first, then falls back to a bundled ``plugins/icarus/`` next to the
    memory plugins directory.
    """
    global _ICARUS_SCHEMAS, _ICARUS_HANDLERS, _ICARUS_HOOKS_MODULE, _ICARUS_FOUND

    if _ICARUS_FOUND:
        return True

    # 1. Find the icarus plugin directory
    from hermes_constants import get_hermes_home

    icarus_dir = get_hermes_home() / "plugins" / "icarus"
    if not icarus_dir.is_dir() or not (icarus_dir / "__init__.py").exists():
        # Fallback: bundled plugins/icarus/ next to plugins/memory/
        bundled = Path(__file__).parent.parent.parent / "plugins" / "icarus"
        if bundled.is_dir() and (bundled / "__init__.py").exists():
            icarus_dir = bundled
        else:
            logger.debug("Icarus plugin not found at %s or %s", icarus_dir, bundled)
            return False

    # 2. Ensure the parent dir is on sys.path so import icarus.xxx resolves
    parent = str(icarus_dir.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)

    # 3. Import the schemas, tools, and hooks modules
    try:
        # Import schemas module first (pure data, no side effects)
        import icarus.schemas  # type: ignore[import-untyped]
        import icarus.tools  # type: ignore[import-untyped]
        import icarus.hooks  # type: ignore[import-untyped]
    except ImportError as exc:
        logger.debug("Failed to import Icarus modules from %s: %s", icarus_dir, exc)
        return False

    # 4. Collect all 16 tool schemas
    schema_names = [
        "FABRIC_RECALL", "FABRIC_WRITE", "FABRIC_SEARCH", "FABRIC_PENDING",
        "FABRIC_CURATE", "FABRIC_EXPORT", "FABRIC_TRAIN", "FABRIC_TRAIN_STATUS",
        "FABRIC_MODELS", "FABRIC_EVAL", "FABRIC_SWITCH_MODEL", "FABRIC_ROLLBACK_MODEL",
        "FABRIC_BRIEF", "FABRIC_TELEMETRY", "FABRIC_INIT_OBSIDIAN", "FABRIC_REPORT",
    ]
    schemas = []
    for name in schema_names:
        schema = getattr(icarus.schemas, name, None)
        if schema is not None:
            schemas.append(schema)
    _ICARUS_SCHEMAS = schemas

    # 5. Build tool name -> handler function mapping
    tool_names = [s["name"] for s in schemas]
    handlers = {}
    for tname in tool_names:
        handler = getattr(icarus.tools, tname, None)
        if handler is not None:
            handlers[tname] = handler
        else:
            logger.warning("Icarus tool %s has no handler in icarus.tools", tname)
    _ICARUS_HANDLERS = handlers
    _ICARUS_HOOKS_MODULE = icarus.hooks
    _ICARUS_FOUND = True

    logger.info(
        "Icarus memory provider discovered: %d schemas, %d handlers from %s",
        len(schemas), len(handlers), icarus_dir,
    )
    return True


def _reload_icarus() -> None:
    """Force re-discovery on next access (for testing / config changes)."""
    global _ICARUS_SCHEMAS, _ICARUS_HANDLERS, _ICARUS_HOOKS_MODULE, _ICARUS_FOUND
    _ICARUS_SCHEMAS = None
    _ICARUS_HANDLERS = None
    _ICARUS_HOOKS_MODULE = None
    _ICARUS_FOUND = False

    # Also unload from sys.modules so next import gets fresh copies
    for mod_name in list(sys.modules):
        if mod_name.startswith("icarus.") or mod_name == "icarus":
            sys.modules.pop(mod_name, None)

    # Remove the icarus path from sys.path if present
    from hermes_constants import get_hermes_home
    candidates = [
        str(get_hermes_home() / "plugins"),
        str(Path(__file__).parent.parent.parent / "plugins"),
    ]
    for c in candidates:
        while c in sys.path:
            sys.path.remove(c)


# ---------------------------------------------------------------------------
# MemoryProvider implementation
# ---------------------------------------------------------------------------

ALL_TOOL_SCHEMAS: list = []


class IcarusMemoryProvider(MemoryProvider):
    """Icarus fabric memory — cross-session memory provider.

    Wraps the installed Icarus plugin (``$HERMES_HOME/plugins/icarus/``) and
    exposes its 16 fabric_* tools through the MemoryProvider interface.
    """

    def __init__(self):
        self._initialized = False
        self._session_id = ""
        self._hooks = None  # reference to icarus.hooks module

    # -- Core properties ----------------------------------------------------

    @property
    def name(self) -> str:
        return "icarus"

    def is_available(self) -> bool:
        """Check if Icarus plugin is discoverable and FABRIC_DIR exists.

        Does NOT make network calls — just checks filesystem and env vars.
        """
        # Check FABRIC_DIR env var
        fabric_dir = os.environ.get("FABRIC_DIR", "")
        if not fabric_dir:
            fabric_dir = str(Path.home() / "fabric")
        if not Path(fabric_dir).is_dir():
            logger.debug("Icarus unavailable: FABRIC_DIR=%s not found", fabric_dir)
            return False

        # Check Icarus plugin discoverability
        return _discover_icarus()

    # -- Config -------------------------------------------------------------

    def get_config_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": "FABRIC_DIR",
                "description": "Path to the fabric directory for ephemeral memory storage. Defaults to ~/fabric",
                "env_var": "FABRIC_DIR",
                "required": False,
            },
            {
                "key": "ICARUS_ENDPOINT",
                "description": "Custom LLM endpoint URL for Icarus extraction (default: auto-detected from DEEPSEEK_API_KEY or OPENROUTER_API_KEY)",
                "env_var": "ICARUS_ENDPOINT",
                "required": False,
            },
            {
                "key": "ICARUS_EXTRACTION_MODEL",
                "description": "Model override for session extraction (default: deepseek/deepseek-v4-flash)",
                "env_var": "ICARUS_EXTRACTION_MODEL",
                "required": False,
            },
            {
                "key": "ICARUS_EXTRACTION_MAX_TOKENS",
                "description": "Max tokens for extraction (default: 1024)",
                "env_var": "ICARUS_EXTRACTION_MAX_TOKENS",
                "required": False,
            },
        ]

    # -- Lifecycle ----------------------------------------------------------

    def initialize(self, session_id: str, **kwargs) -> None:
        """Initialize the Icarus provider for a session.

        Discovers the Icarus plugin at runtime and captures its tool schemas
        and handlers.  If Icarus is not installed, logs a warning and marks
        the provider as unavailable.
        """
        self._session_id = session_id

        if not _discover_icarus():
            logger.warning(
                "Icarus plugin not found — provider will be inactive. "
                "Install it at $HERMES_HOME/plugins/icarus/ or via the plugin manager."
            )
            return

        self._hooks = _ICARUS_HOOKS_MODULE

        # Warm the Icarus plugin state by calling on_session_start if available
        if self._hooks and hasattr(self._hooks, "on_session_start"):
            try:
                self._hooks.on_session_start(
                    session_id=session_id,
                    platform=kwargs.get("platform", ""),
                )
            except Exception as exc:
                logger.debug("Icarus on_session_start hook failed: %s", exc)

        self._initialized = True
        logger.info("Icarus memory provider initialized for session %s", session_id)

    def shutdown(self) -> None:
        """Clean shutdown — release references."""
        self._initialized = False
        self._hooks = None

    # -- System prompt ------------------------------------------------------

    def system_prompt_block(self) -> str:
        """Return the static system prompt for fabric memory awareness."""
        if not self._initialized:
            return ""
        return (
            "# Fabric Memory (Icarus)\n"
            "You have access to a shared fabric memory system across all agents and platforms.\n"
            "Use fabric_recall to retrieve past work, decisions, and context.\n"
            "Use fabric_write to persist important outcomes, decisions, and task completions.\n"
            "Use fabric_brief at session start to see pending items and recent activity.\n"
            "Use fabric_curate to tag entries for training quality.\n"
            "For complete details, see the fabric_* tool descriptions."
        )

    # -- Prefetch (context injection on each turn) --------------------------

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        """Recall relevant fabric memories for the upcoming turn.

        Delegates to the Icarus plugin's ``fabric_recall`` handler to retrieve
        ranked entries matching the query, then formats them as a compact
        context block for injection.
        """
        if not self._initialized or not query or not _ICARUS_HANDLERS:
            return ""

        # Use the recall handler directly with the user query
        recall_fn = _ICARUS_HANDLERS.get("fabric_recall")
        if not recall_fn:
            return ""

        try:
            result_str = recall_fn({"query": query, "max_results": 5})
            result = json.loads(result_str)
        except Exception as exc:
            logger.debug("Icarus prefetch recall failed: %s", exc)
            return ""

        entries = result.get("entries", [])
        if not entries:
            return ""

        lines = ["## Fabric Memory Context"]
        for entry in entries[:3]:
            summary = entry.get("summary", "")
            agent = entry.get("agent", "")
            score = entry.get("score", "")
            lines.append(f"- [{score:.2f}] ({agent}) {summary}")
        return "\n".join(lines)

    def queue_prefetch(self, query: str, *, session_id: str = "") -> None:
        """Compatibility stub — prefetch is synchronous for now."""
        pass

    # -- Turn sync ----------------------------------------------------------

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Per-turn sync is handled by Icarus hooks — no-op here."""
        pass

    # -- Tools --------------------------------------------------------------

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Return all 16 fabric_* tool schemas from the Icarus plugin."""
        if _ICARUS_SCHEMAS is not None:
            return _ICARUS_SCHEMAS
        # If not yet discovered, try now
        _discover_icarus()
        return _ICARUS_SCHEMAS or []

    def handle_tool_call(self, tool_name: str, args: Dict[str, Any], **kwargs) -> str:
        """Delegate tool calls to the Icarus plugin's handler functions.

        Each Icarus handler takes ``(args: dict, **kwargs) -> str`` and
        returns a JSON string.  We call it directly.
        """
        if _ICARUS_HANDLERS is None:
            _discover_icarus()
        handler = _ICARUS_HANDLERS.get(tool_name) if _ICARUS_HANDLERS else None
        if handler:
            try:
                return handler(args, **kwargs)
            except Exception as exc:
                logger.exception("Icarus tool %s failed", tool_name)
                return tool_error(f"{tool_name} failed: {exc}")
        return tool_error(f"Unknown Icarus tool: {tool_name}")

    # -- Optional hooks -----------------------------------------------------

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        """Delegate end-of-session extraction to the Icarus plugin's hook.

        Icarus's ``on_session_end`` hook scores the session, extracts training
        entries, and persists memory state.
        """
        if not self._initialized or not self._hooks:
            return
        on_session_end_hook = getattr(self._hooks, "on_session_end", None)
        if on_session_end_hook:
            try:
                on_session_end_hook(
                    session_id=self._session_id,
                    platform="hermes",
                    completed=True,
                )
            except Exception as exc:
                logger.debug("Icarus on_session_end hook failed: %s", exc)

    def on_turn_start(self, turn_number: int, message: str, **kwargs) -> None:
        """Delegate to Icarus pre_llm_call hook context injection.

        Passes the user message so Icarus can detect topic changes and
        inject relevant memories via its ``pre_llm_call`` hook.
        """
        if not self._initialized or not self._hooks:
            return
        pre_llm_call = getattr(self._hooks, "pre_llm_call", None)
        if pre_llm_call:
            try:
                pre_llm_call(
                    session_id=self._session_id,
                    user_message=message,
                    is_first_turn=(turn_number == 1),
                )
            except Exception as exc:
                logger.debug("Icarus pre_llm_call hook failed: %s", exc)


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------

def register(ctx) -> None:
    """Register the Icarus memory provider with the plugin system."""
    provider = IcarusMemoryProvider()
    ctx.register_memory_provider(provider)
