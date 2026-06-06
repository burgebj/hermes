"""Scheduling integration plugin — bundled, auto-loaded.

Registers tools for Cal.com, Calendly, and Google Calendar into the
``scheduling`` toolset. Runtime auth is handled by ``plugins.scheduling.oauth``:
Cal.com supports either an API key or OAuth token, Calendly uses OAuth with
PKCE, and Google Calendar reuses the existing Hermes Google token.
"""

from __future__ import annotations

from plugins.scheduling.tools import (
    SCHEDULING_CANCEL_EVENT_SCHEMA,
    SCHEDULING_CHECK_AVAILABILITY_SCHEMA,
    SCHEDULING_CREATE_EVENT_SCHEMA,
    SCHEDULING_GET_EVENT_SCHEMA,
    SCHEDULING_LIST_CALENDARS_SCHEMA,
    SCHEDULING_LIST_EVENTS_SCHEMA,
    SCHEDULING_OAUTH_SCHEMA,
    _check_scheduling_available,
    _handle_scheduling_cancel_event,
    _handle_scheduling_check_availability,
    _handle_scheduling_create_event,
    _handle_scheduling_get_event,
    _handle_scheduling_list_calendars,
    _handle_scheduling_list_events,
    _handle_scheduling_oauth,
)

_TOOLS = (
    ("scheduling_list_events", SCHEDULING_LIST_EVENTS_SCHEMA, _handle_scheduling_list_events, "📅"),
    ("scheduling_create_event", SCHEDULING_CREATE_EVENT_SCHEMA, _handle_scheduling_create_event, "➕"),
    ("scheduling_get_event", SCHEDULING_GET_EVENT_SCHEMA, _handle_scheduling_get_event, "🔎"),
    ("scheduling_cancel_event", SCHEDULING_CANCEL_EVENT_SCHEMA, _handle_scheduling_cancel_event, "🗑️"),
    ("scheduling_check_availability", SCHEDULING_CHECK_AVAILABILITY_SCHEMA, _handle_scheduling_check_availability, "🕒"),
    ("scheduling_list_calendars", SCHEDULING_LIST_CALENDARS_SCHEMA, _handle_scheduling_list_calendars, "🗓️"),
    ("scheduling_oauth", SCHEDULING_OAUTH_SCHEMA, _handle_scheduling_oauth, "🔐"),
)


def register(ctx) -> None:
    """Register all scheduling tools. Called once by the plugin loader."""
    for name, schema, handler, emoji in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="scheduling",
            schema=schema,
            handler=handler,
            check_fn=_check_scheduling_available,
            emoji=emoji,
        )
