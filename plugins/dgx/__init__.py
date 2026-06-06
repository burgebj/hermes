"""dgx plugin — manage NVIDIA DGX Spark inference endpoints from Hermes Agent.

CLI subcommands: setup, status, models, use, endpoint, pull, rm, ps,
                 run, push, doctor, watch, formation, nim, node

Agent tools: dgx_gpu_status, dgx_run, dgx_pull_model
"""

from __future__ import annotations

from plugins.dgx.cli import dgx_command, register_cli as _register_dgx_cli
from plugins.dgx.tools import (
    DGX_GPU_STATUS_SCHEMA,
    DGX_PULL_MODEL_SCHEMA,
    DGX_RUN_SCHEMA,
    handle_dgx_gpu_status,
    handle_dgx_pull_model,
    handle_dgx_run,
)

_TOOLS = (
    ("dgx_gpu_status",  DGX_GPU_STATUS_SCHEMA,  handle_dgx_gpu_status,  "🖥️"),
    ("dgx_run",         DGX_RUN_SCHEMA,         handle_dgx_run,         "⚡"),
    ("dgx_pull_model",  DGX_PULL_MODEL_SCHEMA,  handle_dgx_pull_model,  "📥"),
)


def register(ctx) -> None:
    ctx.register_cli_command(
        name="dgx",
        help="NVIDIA DGX Spark endpoint management",
        setup_fn=_register_dgx_cli,
        handler_fn=dgx_command,
        description=(
            "Manage local GPU inference endpoints on a DGX Spark. "
            "See: hermes dgx setup"
        ),
    )
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="dgx",
            schema=schema,
            handler=handler,
            emoji=emoji,
        )
