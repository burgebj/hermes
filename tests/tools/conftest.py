"""Shared discord mock setup for tests/tools/.

pytest collects ``conftest.py`` before any test module in the same
directory, so calling ``_ensure_discord_mock()`` at module top here
guarantees that ``sys.modules["discord"]`` is populated with the right
shape *before* ``test_discord_reaction_tool.py`` (and any other future
Discord-related tool test) imports its target tool module.

Behaviour:

* If real ``discord.py`` is installed (the module has a ``__file__``),
  the helper is a no-op.
* Otherwise it ensures ``Forbidden``, ``HTTPException``, and ``NotFound``
  exist as real ``Exception`` subclasses (so ``isinstance`` checks in
  the production code work) and that ``ui.View`` / ``ButtonStyle`` are
  proper stubs (not ``MagicMock`` auto-attrs that yield empty
  ``children`` lists when ``View`` subclasses them).

Idempotent and order-independent: if ``tests/gateway/conftest.py``
already populated the mock for a different test ordering, this helper
preserves whatever real types it finds and only fills in the missing
pieces. ``tests/gateway/conftest.py`` (sibling) sets the same three
exception classes for the same reason, so the two conftests cooperate
regardless of xdist worker collection order.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock


def _ensure_discord_mock() -> None:
    real_discord = sys.modules.get("discord")
    if real_discord is not None and hasattr(real_discord, "__file__"):
        return  # real discord.py installed — leave it alone

    discord_mod = real_discord if real_discord is not None else MagicMock()

    def _is_real_exception(obj: Any) -> bool:
        return isinstance(obj, type) and issubclass(obj, BaseException)

    if not _is_real_exception(getattr(discord_mod, "Forbidden", None)):
        discord_mod.Forbidden = type("Forbidden", (Exception,), {})
    if not _is_real_exception(getattr(discord_mod, "HTTPException", None)):
        discord_mod.HTTPException = type("HTTPException", (Exception,), {})
    if not _is_real_exception(getattr(discord_mod, "NotFound", None)):
        discord_mod.NotFound = type("NotFound", (Exception,), {})

    # NOTE: bare `MagicMock()` returns truthy auto-attrs for any name, so
    # `hasattr(mm, "ui")` is always True. Use stricter type checks to detect
    # whether a previous test (or the real discord.py) actually set the field.
    if not isinstance(getattr(discord_mod, "DMChannel", None), type):
        discord_mod.DMChannel = type("DMChannel", (), {})
    if not isinstance(getattr(discord_mod, "Thread", None), type):
        discord_mod.Thread = type("Thread", (), {})
    if not isinstance(getattr(discord_mod, "ForumChannel", None), type):
        discord_mod.ForumChannel = type("ForumChannel", (), {})
    if getattr(discord_mod, "Interaction", None) is not object:
        discord_mod.Interaction = object
    if not isinstance(getattr(discord_mod, "ButtonStyle", None), SimpleNamespace):
        discord_mod.ButtonStyle = SimpleNamespace(
            primary="primary",
            secondary="secondary",
            success="success",
            danger="danger",
        )

    ui_mod = getattr(discord_mod, "ui", None)
    if not (isinstance(ui_mod, SimpleNamespace) and isinstance(getattr(ui_mod, "View", None), type)):
        class _FakeView:
            def __init__(self, *, timeout: float = 180.0) -> None:
                self.timeout = timeout
                self.children: list = []

            def add_item(self, item: Any) -> None:
                self.children.append(item)

        class _FakeButton:
            def __init__(self, *, label: str, custom_id: str, style: Any = "primary") -> None:
                self.label = label
                self.custom_id = custom_id
                self.style = style
                self.callback: Any = None

        discord_mod.ui = SimpleNamespace(View=_FakeView, Button=_FakeButton)

    sys.modules["discord"] = discord_mod
    if "discord.ext" not in sys.modules:
        ext_mod = MagicMock()
        commands_mod = MagicMock()
        commands_mod.Bot = MagicMock
        ext_mod.commands = commands_mod
        sys.modules["discord.ext"] = ext_mod
        sys.modules["discord.ext.commands"] = commands_mod


_ensure_discord_mock()
