"""Hermes-tools-as-MCP server for the codex_app_server runtime.

When the user runs `openai/*` turns through the codex app-server, codex
owns the loop and builds its own tool list. By default, that means
Hermes' richer tool surface — web search, browser automation,
delegate_task subagents, vision analysis, persistent memory, skills,
cross-session search, image generation, TTS — is unreachable.

This module exposes a curated subset of those Hermes tools to the
spawned codex subprocess via stdio MCP. Codex registers it as a normal
MCP server (per `~/.codex/config.toml [mcp_servers.hermes-tools]`) and
the user gets full Hermes capability inside a Codex turn.

Scope (what we expose):
  - web_search, web_extract              — Firecrawl, no codex equivalent
  - browser_navigate / _click / _type /  — Camofox/Browserbase automation
    _snapshot / _scroll / _back / _press /
    _get_images / _console / _vision
  - vision_analyze                       — image inspection by vision model
  - image_generate                       — image generation
  - skill_view, skills_list              — Hermes' skill library
  - text_to_speech                       — TTS
  - active memory-provider tools         — e.g. memos_search/memos_skill_list
  - kanban_* (complete/block/comment/    — kanban worker + orchestrator
    heartbeat/show/list/create/            handoff (stateless: read env var,
    unblock/link)                          write ~/.hermes/kanban.db)

What we DO NOT expose:
  - terminal / shell                     — codex's own shell tool
  - read_file / write_file / patch       — codex's apply_patch + shell
  - search_files / process               — codex's shell
  - clarify                              — codex's own UX
  - delegate_task / builtin memory /     — `_AGENT_LOOP_TOOLS` in Hermes
    session_search / todo                  (model_tools.py). They require
                                           the running AIAgent context to
                                           dispatch (mid-loop state), so a
                                           stateless MCP callback can't
                                           drive them. See the inline
                                           comment on EXPOSED_TOOLS below.

Run with: python -m agent.transports.hermes_tools_mcp_server
Spawned by: CodexAppServerSession.ensure_started() when the runtime is
            active and config opts in.
"""

from __future__ import annotations

import atexit
import inspect
import json
import keyword
import logging
import os
import sys
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def _current_session_id() -> str:
    """Return the Hermes session id visible to the MCP subprocess."""
    return (
        os.environ.get("HERMES_SESSION_ID")
        or os.environ.get("HERMES_CODEX_SESSION_ID")
        or "codex_app_server_mcp"
    )


def _env_toolset_list(env_name: str) -> Optional[list[str]]:
    """Parse an exported toolset filter.

    ``None`` means the parent did not apply a filter.  An empty string is a real
    empty filter (for example ``enabled_toolsets=[]``), so return ``[]`` rather
    than falling back to "all".
    """
    raw = os.environ.get(env_name)
    if raw is None:
        return None
    return [item.strip() for item in raw.split(",") if item.strip()]


def _memory_enabled(config: dict[str, Any]) -> bool:
    memory_cfg = config.get("memory") if isinstance(config, dict) else {}
    if not isinstance(memory_cfg, dict):
        return False
    if os.environ.get("HERMES_SKIP_MEMORY", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        return False
    enabled_toolsets = _env_toolset_list("HERMES_ENABLED_TOOLSETS")
    if enabled_toolsets is not None:
        enabled = set(enabled_toolsets)
        if not enabled.intersection({"memory", "all", "*"}):
            return False
    disabled_toolsets = _env_toolset_list("HERMES_DISABLED_TOOLSETS")
    if disabled_toolsets is not None:
        disabled = set(disabled_toolsets)
        if disabled.intersection({"memory", "all", "*"}):
            return False
    if memory_cfg.get("enabled") is False:
        return False
    if memory_cfg.get("memory_enabled") is False:
        return False
    return bool(str(memory_cfg.get("provider") or "").strip())


def _build_memory_manager_for_mcp() -> Any:
    """Initialize the active MemoryProvider for codex's hermes-tools MCP bridge.

    Memory provider tools are dynamic: they are not registered in
    model_tools.get_tool_definitions(), because the normal AIAgent path injects
    them after reading the user's memory.provider config. The codex app-server
    runtime bypasses that path, so the MCP callback has to repeat the provider
    bootstrap locally.
    """
    try:
        from agent.memory_manager import MemoryManager
        from hermes_cli.config import load_config
        from hermes_constants import get_hermes_home
        from plugins.memory import load_memory_provider
    except Exception as exc:
        logger.debug("memory provider MCP bootstrap unavailable: %s", exc)
        return None

    try:
        config = load_config()
    except Exception as exc:
        logger.debug("memory provider MCP config load failed: %s", exc)
        return None

    memory_cfg = config.get("memory") if isinstance(config, dict) else {}
    if not isinstance(memory_cfg, dict) or not _memory_enabled(config):
        return None

    provider_name = str(memory_cfg.get("provider") or "").strip()
    try:
        provider = load_memory_provider(provider_name)
        if not provider or not provider.is_available():
            logger.debug("memory provider %r unavailable for MCP bridge", provider_name)
            return None
        manager = MemoryManager()
        manager.add_provider(provider)
        init_kwargs: dict[str, Any] = {
            "hermes_home": str(get_hermes_home()),
            "platform": os.environ.get("HERMES_PLATFORM") or "cli",
            "agent_context": os.environ.get("HERMES_AGENT_CONTEXT") or "primary",
        }
        # Preserve identity/scoping metadata when the parent agent exported it.
        optional_env = {
            "user_id": "HERMES_USER_ID",
            "user_name": "HERMES_USER_NAME",
            "chat_id": "HERMES_CHAT_ID",
            "chat_name": "HERMES_CHAT_NAME",
            "chat_type": "HERMES_CHAT_TYPE",
            "thread_id": "HERMES_THREAD_ID",
            "gateway_session_key": "HERMES_GATEWAY_SESSION_KEY",
            "session_title": "HERMES_SESSION_TITLE",
            "agent_identity": "HERMES_AGENT_IDENTITY",
            "agent_workspace": "HERMES_AGENT_WORKSPACE",
        }
        for key, env_name in optional_env.items():
            value = os.environ.get(env_name)
            if value:
                init_kwargs[key] = value
        if "agent_workspace" not in init_kwargs:
            init_kwargs["agent_workspace"] = "hermes"
        manager.initialize_all(_current_session_id(), **init_kwargs)
        return manager
    except Exception as exc:
        logger.warning("memory provider %r MCP bootstrap failed: %s", provider_name, exc)
        return None


def _memory_tool_specs(memory_manager: Any) -> dict[str, dict[str, Any]]:
    """Return OpenAI-style function specs for active memory provider tools."""
    if memory_manager is None:
        return {}
    try:
        schemas = memory_manager.get_all_tool_schemas() or []
    except Exception as exc:
        logger.warning("memory provider MCP get_tool_schemas failed: %s", exc)
        return {}
    specs: dict[str, dict[str, Any]] = {}
    for schema in schemas:
        if not isinstance(schema, dict):
            continue
        name = str(schema.get("name") or "").strip()
        if not name:
            continue
        specs[name] = {
            "name": name,
            "description": schema.get("description") or f"Hermes memory {name} tool",
            "parameters": schema.get("parameters")
            or {"type": "object", "properties": {}},
        }
    return specs


def _annotation_for_json_schema(schema: dict[str, Any]) -> Any:
    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        schema_type = next((item for item in schema_type if item != "null"), None)
    return {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }.get(schema_type, Any)


def _signature_from_json_schema(parameters_schema: dict[str, Any]) -> inspect.Signature:
    properties = parameters_schema.get("properties") or {}
    if not isinstance(properties, dict):
        properties = {}
    required = parameters_schema.get("required") or []
    if not isinstance(required, list):
        required = []
    required_names = [str(name) for name in required]
    property_names = [
        name for name in required_names if name in properties
    ] + [
        name for name in properties if name not in required_names
    ]

    params: list[inspect.Parameter] = []
    for name in property_names:
        if not name.isidentifier() or keyword.iskeyword(name):
            logger.debug("skipping non-identifier MCP parameter %r", name)
            continue
        prop_schema = properties.get(name) or {}
        if not isinstance(prop_schema, dict):
            prop_schema = {}
        default = (
            inspect.Parameter.empty
            if name in required_names
            else prop_schema.get("default", None)
        )
        params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=default,
                annotation=_annotation_for_json_schema(prop_schema),
            )
        )
    return inspect.Signature(params)


def _make_mcp_handler(
    *,
    tool_name: str,
    description: str,
    parameters_schema: dict[str, Any],
    dispatcher: Callable[[dict[str, Any]], str],
) -> Callable[..., str]:
    """Build a FastMCP handler whose signature matches the JSON schema.

    FastMCP derives tool argument validation from inspect.signature(). A plain
    ``def handler(**kwargs)`` becomes a schema with one required ``kwargs``
    field, so clients cannot call ``memos_search(query="...")``. Setting an
    explicit keyword-only signature preserves the Hermes/OpenAI tool schema at
    the MCP boundary while still dispatching through one generic function.
    """
    def _dispatch(**kwargs: Any) -> str:
        try:
            return dispatcher(kwargs or {})
        except Exception as exc:
            logger.exception("tool %s raised", tool_name)
            return json.dumps({"error": str(exc), "tool": tool_name})

    _dispatch.__name__ = tool_name
    _dispatch.__doc__ = description
    _dispatch.__signature__ = _signature_from_json_schema(  # type: ignore[attr-defined]
        parameters_schema
    )
    return _dispatch


# Tools we expose. Each name MUST match a registered Hermes tool that
# `model_tools.handle_function_call()` can dispatch.
#
# What we deliberately DO NOT expose:
#   - terminal / shell / read_file / write_file / patch / search_files /
#     process — codex's built-ins cover these and approval routes through
#     codex's own UI.
#   - delegate_task / builtin memory / session_search / todo — these are
#     `_AGENT_LOOP_TOOLS` in Hermes (model_tools.py:493). They require
#     the running AIAgent context to dispatch (mid-loop state), so a
#     stateless MCP callback can't drive them. Hermes' default runtime
#     keeps these working; the codex_app_server runtime cannot.
EXPOSED_TOOLS: tuple[str, ...] = (
    "web_search",
    "web_extract",
    "browser_navigate",
    "browser_click",
    "browser_type",
    "browser_press",
    "browser_snapshot",
    "browser_scroll",
    "browser_back",
    "browser_get_images",
    "browser_console",
    "browser_vision",
    "vision_analyze",
    "image_generate",
    "skill_view",
    "skills_list",
    "text_to_speech",
    # Kanban worker handoff tools — gated on HERMES_KANBAN_TASK env var
    # (set by the kanban dispatcher when spawning a worker). Without these
    # in the callback, a worker spawned with openai_runtime=codex_app_server
    # could do the work but couldn't report completion back to the kernel,
    # making it hang until timeout. Stateless dispatch — they just read
    # the env var and write to ~/.hermes/kanban.db.
    "kanban_complete",
    "kanban_block",
    "kanban_comment",
    "kanban_heartbeat",
    "kanban_show",
    "kanban_list",
    # NOTE: kanban_create / kanban_unblock / kanban_link are orchestrator-
    # only — the kanban tool gates them on HERMES_KANBAN_TASK being unset.
    # They're exposed here for orchestrator agents running on the codex
    # runtime that need to dispatch new tasks.
    "kanban_create",
    "kanban_unblock",
    "kanban_link",
)


def _build_server() -> Any:
    """Create the FastMCP server with Hermes tools attached. Lazy imports
    so the module can be imported without the mcp package installed
    (we degrade to a clear error only when actually run)."""
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover - install hint
        raise ImportError(
            f"hermes-tools MCP server requires the 'mcp' package: {exc}"
        ) from exc

    # Discover Hermes tools so dispatch works.
    from model_tools import (
        get_tool_definitions,
        handle_function_call,
    )

    mcp = FastMCP(
        "hermes-tools",
        instructions=(
            "Hermes Agent's tool surface, exposed for use inside a Codex "
            "session. Use these for capabilities Codex's built-in toolset "
            "doesn't cover: web search/extract, browser automation, "
            "subagent delegation, vision, image generation, persistent "
            "memory, skills, and cross-session search."
        ),
    )

    # Pull authoritative Hermes tool schemas for the static tools we expose,
    # so MCP clients see the same parameter docs Hermes gives the model.
    enabled_toolsets = _env_toolset_list("HERMES_ENABLED_TOOLSETS")
    disabled_toolsets = _env_toolset_list("HERMES_DISABLED_TOOLSETS")
    all_defs: dict[str, dict[str, Any]] = {
        td["function"]["name"]: td["function"]
        for td in (
            get_tool_definitions(
                enabled_toolsets=enabled_toolsets,
                disabled_toolsets=disabled_toolsets,
                quiet_mode=True,
            )
            or []
        )
        if isinstance(td, dict) and td.get("type") == "function"
    }

    # Memory provider tools are injected dynamically in the normal AIAgent
    # path and therefore are absent from get_tool_definitions(). Bootstrap the
    # active provider here so codex_app_server can see memos_search,
    # memos_skill_list, honcho_search, etc. through the hermes-tools MCP
    # callback.
    memory_manager = _build_memory_manager_for_mcp()
    memory_defs = _memory_tool_specs(memory_manager)
    if memory_manager is not None:
        atexit.register(memory_manager.shutdown_all)

    dispatchers: dict[str, Callable[[dict[str, Any]], str]] = {}

    exposed_count = 0

    for name in EXPOSED_TOOLS:
        spec = all_defs.get(name)
        if spec is None:
            logger.debug(
                "skipping %s — not registered in this Hermes process", name
            )
            continue
        dispatchers[name] = (
            lambda kwargs, tool_name=name: handle_function_call(
                tool_name, kwargs or {}
            )
        )
        exposed_count += 1

    for name, spec in memory_defs.items():
        if name in all_defs:
            logger.debug("skipping memory tool %s — static tool already exists", name)
            continue
        if memory_manager is None:
            continue
        all_defs[name] = spec
        dispatchers[name] = (
            lambda kwargs, tool_name=name: memory_manager.handle_tool_call(
                tool_name, kwargs or {}
            )
        )
        exposed_count += 1

    for name, spec in all_defs.items():
        if name not in dispatchers:
            continue
        description = spec.get("description") or f"Hermes {name} tool"
        params_schema = spec.get("parameters") or {
            "type": "object",
            "properties": {},
        }

        handler = _make_mcp_handler(
            tool_name=name,
            description=description,
            parameters_schema=params_schema,
            dispatcher=dispatchers[name],
        )

        try:
            mcp.add_tool(
                handler,
                name=name,
                description=description,
            )
        except TypeError:
            # Older mcp SDK signature — fall back to decorator-style.
            handler = mcp.tool(name=name, description=description)(handler)

    logger.info(
        "hermes-tools MCP server registered %d tools (%d static candidates, %d memory tools)",
        exposed_count,
        len(EXPOSED_TOOLS),
        len(memory_defs),
    )
    return mcp


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for `python -m agent.transports.hermes_tools_mcp_server`."""
    argv = argv or sys.argv[1:]
    verbose = "--verbose" in argv or "-v" in argv

    log_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=log_level,
        stream=sys.stderr,  # MCP uses stdio for protocol — logs MUST go to stderr
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Quiet mode: keep Hermes' own banners off stdout (which is the MCP wire).
    os.environ.setdefault("HERMES_QUIET", "1")
    os.environ.setdefault("HERMES_REDACT_SECRETS", "true")

    try:
        server = _build_server()
    except ImportError as exc:
        sys.stderr.write(f"hermes-tools MCP server cannot start: {exc}\n")
        return 2

    # FastMCP runs with stdio transport by default when launched as a
    # subprocess.
    try:
        server.run()
    except KeyboardInterrupt:
        return 0
    except Exception as exc:
        logger.exception("hermes-tools MCP server crashed")
        sys.stderr.write(f"hermes-tools MCP server error: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
