"""Hermes terminal compaction plugin."""

from __future__ import annotations

import logging

from .rewrite import rewrite_command

logger = logging.getLogger(__name__)


def _pre_tool_call(tool_name, args, **kwargs):
    if tool_name != "terminal":
        return None
    if not isinstance(args, dict):
        return None

    command = args.get("command")
    if not isinstance(command, str) or not command.strip():
        return None

    if args.get("background") is True or args.get("pty") is True:
        return None

    rewritten = rewrite_command(command)
    if not rewritten or rewritten.command == command:
        return None

    logger.info("[terminal_compact] %s -> %s (%s)", command, rewritten.command, rewritten.reason)

    new_args = dict(args)
    new_args["command"] = rewritten.command
    return {
        "action": "rewrite_args",
        "args": new_args,
        "reason": rewritten.reason,
    }


def register(ctx):
    ctx.register_hook("pre_tool_call", _pre_tool_call)
