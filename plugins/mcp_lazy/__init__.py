"""mcp_lazy — lazy MCP tool schema loading.

Phase 1: stub MCP tool schemas at request time and promote selected
MCP tools on demand via the ``load_mcp_tools`` meta-tool. Each session
keeps its own promoted-tool set so promoted MCP tools stay full for the
rest of that conversation only.

Activation: opt-in via ``hermes plugins enable mcp_lazy`` and
``mcp.lazy_loading: true`` in ``config.yaml``.
"""
from __future__ import annotations

import logging

from . import hook_impl
from . import meta_tool

logger = logging.getLogger(__name__)


def register(ctx) -> None:  # noqa: ANN001
    """Register the Phase 1 meta-tool + request-time hook surface."""
    ctx.register_tool(
        name="load_mcp_tools",
        toolset="mcp_lazy",
        schema=meta_tool.SCHEMA,
        handler=meta_tool.handler,
        check_fn=meta_tool.check,
        is_async=True,
        description=meta_tool.SCHEMA.get("description", ""),
        emoji="📦",
    )
    ctx.register_hook("transform_tools", hook_impl.transform_tools)
    ctx.register_hook("on_session_reset", hook_impl.on_session_reset)
    logger.info("mcp_lazy: registered Phase 1 hooks and load_mcp_tools meta-tool")
