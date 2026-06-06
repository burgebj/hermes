"""Discord interactive component helpers.

This module backs the Discord adapter's generic component support for messages
sent with ``metadata['components']``.  It is intentionally small: build a
``discord.ui.View`` from the send_message component schema, track views by
message id, and turn button/select interactions back into ``MessageEvent``
objects for the gateway runner.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

try:  # pragma: no cover - exercised with real discord.py in production
    import discord
except Exception:  # pragma: no cover - tests provide a mock when needed
    discord = None  # type: ignore

from gateway.platforms.base import MessageEvent, MessageType
from gateway.session import SessionSource

logger = logging.getLogger(__name__)

CUSTOM_ID_PREFIX = "hermes:"


def _style_from_spec(value: Any) -> Any:
    """Map API/friendly button style values to discord.py ButtonStyle."""
    if discord is None:
        return value
    style = getattr(discord, "ButtonStyle", None)
    if style is None:
        return value

    # Discord API numeric styles: 1 primary, 2 secondary, 3 success, 4 danger,
    # 5 link.  The test mock and some discord.py versions expose aliases.
    mapping = {
        1: getattr(style, "primary", getattr(style, "blurple", 1)),
        2: getattr(style, "secondary", getattr(style, "grey", 2)),
        3: getattr(style, "success", getattr(style, "green", 3)),
        4: getattr(style, "danger", getattr(style, "red", 4)),
        5: getattr(style, "link", 5),
        "primary": getattr(style, "primary", getattr(style, "blurple", 1)),
        "secondary": getattr(style, "secondary", getattr(style, "grey", 2)),
        "success": getattr(style, "success", getattr(style, "green", 3)),
        "danger": getattr(style, "danger", getattr(style, "red", 4)),
        "link": getattr(style, "link", 5),
    }
    return mapping.get(value, mapping.get(str(value).lower(), mapping[2]))


def _prefixed_custom_id(custom_id: str) -> str:
    custom_id = str(custom_id or "")
    if custom_id.startswith(CUSTOM_ID_PREFIX):
        return custom_id
    return f"{CUSTOM_ID_PREFIX}{custom_id}"


def _format_interaction_text(
    kind: str,
    *,
    label: str = "",
    custom_id: str = "",
    values: Optional[list] = None,
) -> str:
    """Format a component interaction as text for the agent.

    Keep this explicit and parseable.  The agent sees the click/selection as a
    normal user message, preserving the existing gateway path.
    """
    parts = [kind]
    if label:
        parts.append(f"label={label!r}")
    if custom_id:
        parts.append(f"custom_id={custom_id!r}")
    if values:
        parts.append(f"values={values!r}")
    return " | ".join(parts)


@dataclass
class TrackedComponentView:
    message_id: str
    view: Any
    session_key: str = ""
    interaction_callback: Optional[Callable[[MessageEvent], Any]] = None
    source: Optional[MessageSource] = None
    rest_sent: bool = False
    resolved: bool = False
    chat_id: str = ""


class ComponentStore:
    """In-memory registry for Discord component views by message id."""

    def __init__(self) -> None:
        self._items: Dict[str, TrackedComponentView] = {}

    def register(
        self,
        *,
        message_id: str,
        view: Any,
        session_key: str = "",
        interaction_callback: Optional[Callable[[MessageEvent], Any]] = None,
        source: Optional[MessageSource] = None,
        rest_sent: bool = False,
        chat_id: str = "",
    ) -> TrackedComponentView:
        tracked = TrackedComponentView(
            message_id=str(message_id),
            view=view,
            session_key=session_key,
            interaction_callback=interaction_callback,
            source=source,
            rest_sent=rest_sent,
            chat_id=str(chat_id or getattr(source, "chat_id", "") or ""),
        )
        self._items[str(message_id)] = tracked
        return tracked

    def get(self, message_id: str) -> Optional[TrackedComponentView]:
        return self._items.get(str(message_id))

    def remove(self, message_id: str) -> None:
        self._items.pop(str(message_id), None)


component_store = ComponentStore()


class ComponentView(discord.ui.View if discord is not None else object):  # type: ignore[misc]
    """discord.py View built from a generic component spec."""

    def __init__(
        self,
        *,
        spec: Optional[dict],
        message_id: str = "",
        session_key: str = "",
        source: Optional[MessageSource] = None,
        interaction_callback: Optional[Callable[[MessageEvent], Any]] = None,
        timeout: Optional[float] = 900,
    ) -> None:
        if discord is not None:
            super().__init__(timeout=timeout)
        self._spec = spec or {}
        self._message_id = str(message_id or "")
        self._session_key = session_key
        self._source = source
        self._interaction_callback = interaction_callback
        self.resolved = False
        self._build_items()

    def _build_items(self) -> None:
        if discord is None:
            return
        rows = self._spec.get("action_rows") or []
        for row_index, row in enumerate(rows[:5]):
            for button in (row.get("buttons") or [])[:5]:
                self._add_button(button, row_index)
            if row.get("select"):
                self._add_select(row["select"], row_index)

    def _add_button(self, spec: dict, row: int) -> None:
        label = str(spec.get("label") or spec.get("custom_id") or "Button")[:80]
        url = spec.get("url")
        custom_id = str(spec.get("custom_id") or label)
        kwargs = {
            "label": label,
            "style": _style_from_spec(spec.get("style", 2)),
            "disabled": bool(spec.get("disabled", False)),
            "row": row,
        }
        if url:
            kwargs["url"] = str(url)
            kwargs["style"] = _style_from_spec("link")
        else:
            kwargs["custom_id"] = _prefixed_custom_id(custom_id)
        item = discord.ui.Button(**kwargs)

        async def _callback(interaction, *, _label=label, _custom_id=custom_id):
            await self._handle_interaction(
                interaction,
                kind="Button clicked",
                label=_label,
                custom_id=_custom_id,
            )

        item.callback = _callback
        self.add_item(item)

    def _add_select(self, spec: dict, row: int) -> None:
        custom_id = str(spec.get("custom_id") or "select")
        options = []
        for opt in (spec.get("options") or [])[:25]:
            if not isinstance(opt, dict):
                continue
            options.append(
                discord.SelectOption(
                    label=str(opt.get("label") or opt.get("value") or "Option")[:100],
                    value=str(opt.get("value") or opt.get("label") or "")[:100],
                    description=(
                        str(opt.get("description"))[:100]
                        if opt.get("description") is not None else None
                    ),
                )
            )
        if not options:
            return
        item = discord.ui.Select(
            placeholder=str(spec.get("placeholder") or "Select an option")[:100],
            options=options,
            custom_id=_prefixed_custom_id(custom_id),
            row=row,
        )

        async def _callback(interaction, *, _custom_id=custom_id):
            values = list(getattr(item, "values", []) or getattr(interaction, "data", {}).get("values", []) or [])
            await self._handle_interaction(
                interaction,
                kind="Select chosen",
                label=values[0] if values else "",
                custom_id=_custom_id,
                values=values,
            )

        item.callback = _callback
        self.add_item(item)

    async def _handle_interaction(
        self,
        interaction,
        *,
        kind: str,
        label: str = "",
        custom_id: str = "",
        values: Optional[list] = None,
    ) -> None:
        if self.resolved:
            try:
                await interaction.response.send_message(
                    "This component has already been used.", ephemeral=True
                )
            except Exception:
                pass
            return

        self.resolved = True
        for child in getattr(self, "children", []) or []:
            if not getattr(child, "url", None):
                try:
                    child.disabled = True
                except Exception:
                    pass

        try:
            await interaction.response.edit_message(view=self)
        except Exception:
            try:
                await interaction.response.defer()
            except Exception:
                pass

        source = self._source
        if source is None:
            channel_id = ""
            try:
                channel_id = str(interaction.channel.id)
            except Exception:
                pass
            user_id = str(getattr(getattr(interaction, "user", None), "id", "") or "")
            user_name = str(getattr(interaction, "user", "") or "")
            source = MessageSource(
                platform="discord",
                chat_id=channel_id,
                user_id=user_id,
                user_name=user_name,
            )

        message_id = self._message_id
        if not message_id:
            try:
                message_id = str(interaction.message.id)
            except Exception:
                message_id = ""

        event = MessageEvent(
            text=_format_interaction_text(kind, label=label, custom_id=custom_id, values=values),
            message_type=MessageType.TEXT,
            source=source,
            raw_message=interaction,
            message_id=message_id,
            reply_to_message_id=message_id or None,
        )
        if self._interaction_callback:
            result = self._interaction_callback(event)
            # The callback normally schedules a task and returns it; avoid
            # importing inspect on the hot path unless needed.
            if hasattr(result, "__await__"):
                await result


def build_view_from_spec(
    *,
    spec: Optional[dict],
    message_id: str = "",
    session_key: str = "",
    source: Optional[MessageSource] = None,
    interaction_callback: Optional[Callable[[MessageEvent], Any]] = None,
) -> ComponentView:
    return ComponentView(
        spec=spec,
        message_id=message_id,
        session_key=session_key,
        source=source,
        interaction_callback=interaction_callback,
    )
