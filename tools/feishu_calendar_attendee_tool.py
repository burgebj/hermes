"""Feishu Calendar Attendee Tool -- attendee management and calendar listing via Feishu/Lark API.

Provides four tools for managing calendar event attendees and listing calendars as the
signed-in user (UAT):
  - ``feishu_calendar_event_attendee_create`` -- add attendees to an event
  - ``feishu_calendar_event_attendee_list``   -- list attendees of an event
  - ``feishu_calendar_event_attendee_delete`` -- batch-delete attendees from an event
  - ``feishu_calendar_list_calendars``        -- list accessible calendars

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper on the
FeishuClient instance.  Error codes 99991672 and 99991679 are surfaced as semantic
auth exceptions via ``raise_for_feishu_errcode``.
"""

import logging

from tools.feishu_oapi_client import (
    AppScopeMissingError,
    FeishuClient,
    NeedAuthorizationError,
    TOOLS_METADATA,
    UserAuthRequiredError,
    raise_for_feishu_errcode,
)
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scopes
# ---------------------------------------------------------------------------

_ATTENDEE_SCOPE = "calendar:calendar.event_attendee"
_ATTENDEE_READONLY_SCOPE = "calendar:calendar.event_attendee:readonly"
_CALENDAR_READONLY_SCOPE = "calendar:calendar:readonly"

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _check_feishu():
    """Check if lark_oapi is available."""
    try:
        import lark_oapi  # noqa: F401
        return True
    except ImportError:
        return False


def _auth_error_message(exc: Exception) -> str:
    """Format semantic auth exceptions as tool_error strings."""
    if isinstance(exc, NeedAuthorizationError):
        return f"Need Feishu authorization: {exc}. Run 'hermes feishu-uat' to authorize."
    if isinstance(exc, AppScopeMissingError):
        return f"App scope missing: {exc}"
    if isinstance(exc, UserAuthRequiredError):
        return f"User authorization required: {exc}"
    return str(exc)


_AUTH_EXC = (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError)

# ---------------------------------------------------------------------------
# feishu_calendar_event_attendee_create
# ---------------------------------------------------------------------------

_ATTENDEE_CREATE_URI = (
    "/open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees"
)

FEISHU_CALENDAR_EVENT_ATTENDEE_CREATE_SCHEMA = {
    "name": "feishu_calendar_event_attendee_create",
    "description": (
        "Add one or more attendees to a calendar event as the signed-in user. "
        "Each attendee entry must have a 'user_id' (open_id). "
        "Requires scope: calendar:calendar.event_attendee."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "calendar_id": {
                "type": "string",
                "description": "The calendar ID that owns the event.",
            },
            "event_id": {
                "type": "string",
                "description": "The event ID to add attendees to.",
            },
            "attendees": {
                "type": "array",
                "description": (
                    "List of attendee objects. Each must include 'user_id' (open_id). "
                    "Example: [{'type': 'user', 'user_id': 'ou_xxx'}]"
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Attendee type, e.g. 'user'.",
                        },
                        "user_id": {
                            "type": "string",
                            "description": "The user open_id of the attendee.",
                        },
                    },
                    "required": ["user_id"],
                },
            },
        },
        "required": ["calendar_id", "event_id", "attendees"],
    },
}


def _handle_attendee_create(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_event_attendee_create.

    Args:
        args: Tool arguments containing calendar_id, event_id, and attendees list.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    calendar_id = (args.get("calendar_id") or "").strip()
    event_id = (args.get("event_id") or "").strip()
    attendees = args.get("attendees") or []

    if not calendar_id:
        return tool_error("calendar_id is required")
    if not event_id:
        return tool_error("event_id is required")
    if not attendees:
        return tool_error("attendees list is required and must not be empty")

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info(
        "attendee_create: calendar_id=%s event_id=%s count=%d",
        calendar_id, event_id, len(attendees),
    )

    uri = _ATTENDEE_CREATE_URI.format(calendar_id=calendar_id, event_id=event_id)
    try:
        code, msg, data = fc.do_request(
            "POST",
            uri,
            queries=[("user_id_type", "open_id")],
            body={"attendees": attendees},
            use_uat=True,
        )
    except _AUTH_EXC as exc:
        return tool_error(_auth_error_message(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_event_attendee_create",
                user_open_id=fc.user_open_id,
            )
        except _AUTH_EXC as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Add attendees failed: code={code} msg={msg}")

    logger.info("attendee_create: success, event_id=%s", event_id)
    return tool_result({"attendees": data.get("attendees", []), "event_id": event_id})


# ---------------------------------------------------------------------------
# feishu_calendar_event_attendee_list
# ---------------------------------------------------------------------------

_ATTENDEE_LIST_URI = (
    "/open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees"
)

FEISHU_CALENDAR_EVENT_ATTENDEE_LIST_SCHEMA = {
    "name": "feishu_calendar_event_attendee_list",
    "description": (
        "List attendees of a calendar event as the signed-in user. "
        "Requires scope: calendar:calendar.event_attendee:readonly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "calendar_id": {
                "type": "string",
                "description": "The calendar ID that owns the event.",
            },
            "event_id": {
                "type": "string",
                "description": "The event ID whose attendees to list.",
            },
            "page_size": {
                "type": "integer",
                "description": "Number of attendees to return per page (default 20, max 100).",
            },
        },
        "required": ["calendar_id", "event_id"],
    },
}


def _handle_attendee_list(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_event_attendee_list.

    Args:
        args: Tool arguments containing calendar_id, event_id, and optional page_size.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    calendar_id = (args.get("calendar_id") or "").strip()
    event_id = (args.get("event_id") or "").strip()
    page_size = args.get("page_size") or 20

    if not calendar_id:
        return tool_error("calendar_id is required")
    if not event_id:
        return tool_error("event_id is required")

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info("attendee_list: calendar_id=%s event_id=%s", calendar_id, event_id)

    uri = _ATTENDEE_LIST_URI.format(calendar_id=calendar_id, event_id=event_id)
    try:
        code, msg, data = fc.do_request(
            "GET",
            uri,
            queries=[("page_size", str(page_size)), ("user_id_type", "open_id")],
            use_uat=True,
        )
    except _AUTH_EXC as exc:
        return tool_error(_auth_error_message(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_event_attendee_list",
                user_open_id=fc.user_open_id,
            )
        except _AUTH_EXC as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"List attendees failed: code={code} msg={msg}")

    items = data.get("items", [])
    logger.info("attendee_list: returned %d attendee(s)", len(items))
    return tool_result({
        "attendees": items,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# feishu_calendar_event_attendee_delete
# ---------------------------------------------------------------------------

_ATTENDEE_DELETE_URI = (
    "/open-apis/calendar/v4/calendars/{calendar_id}/events/{event_id}/attendees/batch_delete"
)

FEISHU_CALENDAR_EVENT_ATTENDEE_DELETE_SCHEMA = {
    "name": "feishu_calendar_event_attendee_delete",
    "description": (
        "Batch-delete attendees from a calendar event as the signed-in user. "
        "Requires scope: calendar:calendar.event_attendee."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "calendar_id": {
                "type": "string",
                "description": "The calendar ID that owns the event.",
            },
            "event_id": {
                "type": "string",
                "description": "The event ID to remove attendees from.",
            },
            "attendee_ids": {
                "type": "array",
                "description": "List of attendee IDs to delete. User open_ids are also accepted and resolved via attendee list.",
                "items": {"type": "string"},
            },
        },
        "required": ["calendar_id", "event_id", "attendee_ids"],
    },
}


def _handle_attendee_delete(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_event_attendee_delete.

    Args:
        args: Tool arguments containing calendar_id, event_id, and attendee_ids list.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    calendar_id = (args.get("calendar_id") or "").strip()
    event_id = (args.get("event_id") or "").strip()
    attendee_ids = args.get("attendee_ids") or []

    if not calendar_id:
        return tool_error("calendar_id is required")
    if not event_id:
        return tool_error("event_id is required")
    if not attendee_ids:
        return tool_error("attendee_ids list is required and must not be empty")

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info(
        "attendee_delete: calendar_id=%s event_id=%s count=%d",
        calendar_id, event_id, len(attendee_ids),
    )

    resolved_attendee_ids = list(attendee_ids)
    open_ids = [value for value in resolved_attendee_ids if isinstance(value, str) and value.startswith("ou_")]
    if open_ids:
        list_uri = _ATTENDEE_LIST_URI.format(calendar_id=calendar_id, event_id=event_id)
        try:
            list_code, list_msg, list_data = fc.do_request(
                "GET",
                list_uri,
                queries=[("page_size", "100"), ("user_id_type", "open_id")],
                use_uat=True,
            )
        except _AUTH_EXC as exc:
            return tool_error(_auth_error_message(exc))
        if list_code != 0:
            try:
                raise_for_feishu_errcode(
                    list_code,
                    list_msg,
                    api_name="feishu_calendar_event_attendee_list",
                    user_open_id=fc.user_open_id,
                )
            except _AUTH_EXC as exc:
                return tool_error(_auth_error_message(exc))
            return tool_error(f"List attendees for delete failed: code={list_code} msg={list_msg}")

        open_id_to_attendee_id = {
            item.get("user_id"): item.get("attendee_id")
            for item in list_data.get("items", [])
            if item.get("type") == "user" and item.get("user_id") and item.get("attendee_id")
        }
        missing = [open_id for open_id in open_ids if open_id not in open_id_to_attendee_id]
        if missing:
            return tool_error(f"Could not resolve attendee open_id(s): {', '.join(missing)}")
        resolved_attendee_ids = [
            open_id_to_attendee_id.get(value, value) for value in resolved_attendee_ids
        ]

    uri = _ATTENDEE_DELETE_URI.format(calendar_id=calendar_id, event_id=event_id)
    try:
        code, msg, data = fc.do_request(
            "POST",
            uri,
            body={"attendee_ids": resolved_attendee_ids},
            use_uat=True,
        )
    except _AUTH_EXC as exc:
        return tool_error(_auth_error_message(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_event_attendee_delete",
                user_open_id=fc.user_open_id,
            )
        except _AUTH_EXC as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Delete attendees failed: code={code} msg={msg}")

    logger.info("attendee_delete: deleted %d attendee(s) from event_id=%s", len(resolved_attendee_ids), event_id)
    return tool_result({"deleted_count": len(resolved_attendee_ids), "event_id": event_id})


# ---------------------------------------------------------------------------
# feishu_calendar_list_calendars
# ---------------------------------------------------------------------------

_LIST_CALENDARS_URI = "/open-apis/calendar/v4/calendars"

FEISHU_CALENDAR_LIST_CALENDARS_SCHEMA = {
    "name": "feishu_calendar_list_calendars",
    "description": (
        "List calendars accessible to the signed-in user. "
        "Requires scope: calendar:calendar:readonly."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "page_size": {
                "type": "integer",
                "description": "Number of calendars to return per page (default 10, max 50).",
            },
        },
        "required": [],
    },
}


def _handle_list_calendars(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_list_calendars.

    Args:
        args: Tool arguments with optional page_size.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    try:
        page_size = int(args.get("page_size") or 50)
    except (TypeError, ValueError):
        page_size = 50
    # Feishu calendar list rejects smaller page sizes with 99992402.
    page_size = 50 if page_size < 50 else min(page_size, 50)

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    logger.info("list_calendars: page_size=%s", page_size)

    try:
        code, msg, data = fc.do_request(
            "GET",
            _LIST_CALENDARS_URI,
            queries=[("page_size", str(page_size))],
            use_uat=True,
        )
    except _AUTH_EXC as exc:
        return tool_error(_auth_error_message(exc))

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_list_calendars",
                user_open_id=fc.user_open_id,
            )
        except _AUTH_EXC as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"List calendars failed: code={code} msg={msg}")

    calendars = data.get("calendar_list", data.get("calendars", []))
    logger.info("list_calendars: returned %d calendar(s)", len(calendars))
    return tool_result({
        "calendars": calendars,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_calendar_event_attendee_create",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_EVENT_ATTENDEE_CREATE_SCHEMA,
    handler=_handle_attendee_create,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Add attendees to a calendar event",
    emoji="\U0001f4c5",
)

registry.register(
    name="feishu_calendar_event_attendee_list",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_EVENT_ATTENDEE_LIST_SCHEMA,
    handler=_handle_attendee_list,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List attendees of a calendar event",
    emoji="\U0001f4c5",
)

registry.register(
    name="feishu_calendar_event_attendee_delete",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_EVENT_ATTENDEE_DELETE_SCHEMA,
    handler=_handle_attendee_delete,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Batch-delete attendees from a calendar event",
    emoji="\U0001f4c5",
)

registry.register(
    name="feishu_calendar_list_calendars",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_LIST_CALENDARS_SCHEMA,
    handler=_handle_list_calendars,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List calendars accessible to the signed-in user",
    emoji="\U0001f4c5",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_calendar_event_attendee_create": {
        "scopes": [_ATTENDEE_SCOPE],
        "identity": "user",
    },
    "feishu_calendar_event_attendee_list": {
        "scopes": [_ATTENDEE_READONLY_SCOPE, _ATTENDEE_SCOPE],
        "identity": "user",
    },
    "feishu_calendar_event_attendee_delete": {
        "scopes": [_ATTENDEE_SCOPE],
        "identity": "user",
    },
    "feishu_calendar_list_calendars": {
        "scopes": [_CALENDAR_READONLY_SCOPE],
        "identity": "user",
    },
})
