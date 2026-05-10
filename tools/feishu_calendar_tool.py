"""Feishu Calendar Tool -- calendar event and freebusy operations via Feishu/Lark API.

Provides four tools for managing calendar events as the signed-in user (UAT):
  - ``feishu_calendar_list_events``   -- list events in a time range (instance_view)
  - ``feishu_calendar_get_event``     -- fetch a single event by ID
  - ``feishu_calendar_create_event``  -- create a new calendar event with optional attendees
  - ``feishu_calendar_freebusy``      -- batch-query free/busy status for 1-10 users

All tools use ``FeishuClient.for_user()`` (UAT) and the ``do_request`` helper on the
FeishuClient instance.  Error codes 99991672 and 99991679 are surfaced as semantic
auth exceptions via ``raise_for_feishu_errcode``.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

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

_CALENDAR_SCOPE = "calendar:calendar"
_CALENDAR_READONLY_SCOPE = "calendar:calendar:readonly"

# ---------------------------------------------------------------------------
# Helper: resolve primary calendar ID
# ---------------------------------------------------------------------------

_PRIMARY_CALENDAR_URI = "/open-apis/calendar/v4/calendars/primary"


def _get_primary_calendar_id(fc: FeishuClient) -> str:
    """Resolve the user's primary calendar ID via the primary() API.

    Args:
        fc: A FeishuClient instance configured for UAT.

    Returns:
        The primary calendar_id string.

    Raises:
        RuntimeError: If the primary calendar cannot be resolved.
    """
    code, msg, data = fc.do_request(
        "POST",
        _PRIMARY_CALENDAR_URI,
        queries=[("user_id_type", "open_id")],
        body={},
        use_uat=True,
    )
    if code != 0:
        raise_for_feishu_errcode(
            code, msg, api_name="calendar_primary", user_open_id=fc.user_open_id
        )
        raise RuntimeError(f"primary calendar failed: code={code} msg={msg}")

    calendars = data.get("calendars", [])
    if not calendars:
        raise RuntimeError("No primary calendar returned by Feishu API")

    # First entry: {"calendar": {"calendar_id": "..."}, ...}
    first = calendars[0]
    cal_obj = first if isinstance(first, dict) and "calendar_id" in first else first.get("calendar", {})
    cid = cal_obj.get("calendar_id", "")
    if not cid:
        raise RuntimeError(f"primary calendar_id missing in response: {data}")

    logger.info("Resolved primary calendar_id=%s", cid)
    return cid


def _resolve_calendar_id(fc: FeishuClient, calendar_id: str) -> str:
    """Return calendar_id if provided, else resolve primary.

    Args:
        fc: FeishuClient with UAT.
        calendar_id: Caller-supplied calendar ID (may be empty).

    Returns:
        A non-empty calendar ID string.
    """
    if calendar_id:
        return calendar_id
    return _get_primary_calendar_id(fc)


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


def _normalize_instance_time(value) -> str:
    """Return Feishu instance_view time as Unix epoch seconds."""
    text = str(value or "").strip()
    if not text:
        return ""
    if text.isdigit():
        return text

    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            "time must be Unix epoch seconds or ISO 8601/RFC3339 with timezone"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(
            "ISO 8601/RFC3339 time must include timezone, e.g. +08:00 or Z"
        )
    return str(int(parsed.timestamp()))


def _event_time_payload(value) -> dict:
    return {"timestamp": _normalize_instance_time(value)}


def _default_rfc3339_window(hours: int = 1) -> tuple[str, str]:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    end = now + timedelta(hours=hours)
    return now.isoformat(), end.isoformat()


# ---------------------------------------------------------------------------
# feishu_calendar_list_events
# ---------------------------------------------------------------------------

_LIST_EVENTS_URI = "/open-apis/calendar/v4/calendars/:calendar_id/events/instance_view"

FEISHU_CALENDAR_LIST_EVENTS_SCHEMA = {
    "name": "feishu_calendar_list_events",
    "description": (
        "List calendar events in a time range as the signed-in user. "
        "Uses the instance_view endpoint which auto-expands recurring events. "
        "The time range must be under 40 days. "
        "Times should be Unix epoch seconds; ISO 8601 / RFC 3339 with timezone is also accepted."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "start_time": {
                "type": "string",
                "description": (
                    "Range start time as Unix epoch seconds, e.g. '1704038400'. "
                    "ISO 8601 / RFC 3339 with timezone is accepted and converted. "
                    "Range must be under 40 days."
                ),
            },
            "end_time": {
                "type": "string",
                "description": (
                    "Range end time as Unix epoch seconds, e.g. '1704124799'. "
                    "ISO 8601 / RFC 3339 with timezone is accepted and converted. "
                    "Range must be under 40 days."
                ),
            },
            "calendar_id": {
                "type": "string",
                "description": "Calendar ID (optional; primary calendar used if omitted).",
            },
        },
        "required": ["start_time", "end_time"],
    },
}


def _handle_calendar_list_events(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_list_events.

    Args:
        args: Tool arguments containing start_time, end_time, and optional calendar_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    try:
        start_time = _normalize_instance_time(args.get("start_time"))
        end_time = _normalize_instance_time(args.get("end_time"))
    except ValueError as exc:
        return tool_error(str(exc))

    if not start_time or not end_time:
        return tool_error("start_time and end_time are required")

    calendar_id = (args.get("calendar_id") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    try:
        cid = _resolve_calendar_id(fc, calendar_id)
    except (RuntimeError, AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError)) else str(exc))

    logger.info(
        "list_events: calendar_id=%s start_time=%s end_time=%s", cid, start_time, end_time
    )

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    builder = (
        BaseRequest.builder()
        .http_method(HttpMethod.GET)
        .uri(_LIST_EVENTS_URI)
        .token_types({AccessTokenType.USER})
        .paths({"calendar_id": cid})
        .queries([
            ("start_time", start_time),
            ("end_time", end_time),
            ("user_id_type", "open_id"),
        ])
    )
    request = builder.build()
    opt = (
        RequestOption.builder()
        .user_access_token(fc.access_token)
        .build()
    )
    response = fc.sdk.request(request, opt)

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")

    data: dict = {}
    raw = getattr(response, "raw", None)
    if raw and hasattr(raw, "content"):
        try:
            body_json = json.loads(raw.content)
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
            data = body_json.get("data", {})
        except (json.JSONDecodeError, AttributeError):
            pass
    if not data:
        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict):
            data = resp_data
        elif resp_data and hasattr(resp_data, "__dict__"):
            data = vars(resp_data)

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_list_events",
                user_open_id=fc.user_open_id
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"List events failed: code={code} msg={msg}")

    items = data.get("items", [])
    logger.info("list_events: returned %d event instances", len(items))
    return tool_result({
        "events": items,
        "has_more": data.get("has_more", False),
        "page_token": data.get("page_token"),
    })


# ---------------------------------------------------------------------------
# feishu_calendar_get_event
# ---------------------------------------------------------------------------

_GET_EVENT_URI = "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id"

FEISHU_CALENDAR_GET_EVENT_SCHEMA = {
    "name": "feishu_calendar_get_event",
    "description": (
        "Fetch a single calendar event by event_id as the signed-in user. "
        "Returns full event details including attendees and recurrence info."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "The event ID to retrieve.",
            },
            "calendar_id": {
                "type": "string",
                "description": "Calendar ID (optional; primary calendar used if omitted).",
            },
        },
        "required": ["event_id"],
    },
}


def _handle_calendar_get_event(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_get_event.

    Args:
        args: Tool arguments containing event_id and optional calendar_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    event_id = (args.get("event_id") or "").strip()
    if not event_id:
        return tool_error("event_id is required")

    calendar_id = (args.get("calendar_id") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    try:
        cid = _resolve_calendar_id(fc, calendar_id)
    except (RuntimeError, AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError)) else str(exc))

    logger.info("get_event: calendar_id=%s event_id=%s", cid, event_id)

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    request = (
        BaseRequest.builder()
        .http_method(HttpMethod.GET)
        .uri(_GET_EVENT_URI)
        .token_types({AccessTokenType.USER})
        .paths({"calendar_id": cid, "event_id": event_id})
        .queries([("user_id_type", "open_id")])
        .build()
    )
    opt = (
        RequestOption.builder()
        .user_access_token(fc.access_token)
        .build()
    )
    response = fc.sdk.request(request, opt)

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")

    data: dict = {}
    raw = getattr(response, "raw", None)
    if raw and hasattr(raw, "content"):
        try:
            body_json = json.loads(raw.content)
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
            data = body_json.get("data", {})
        except (json.JSONDecodeError, AttributeError):
            pass
    if not data:
        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict):
            data = resp_data
        elif resp_data and hasattr(resp_data, "__dict__"):
            data = vars(resp_data)

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_get_event",
                user_open_id=fc.user_open_id
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Get event failed: code={code} msg={msg}")

    logger.info("get_event: retrieved event %s", event_id)
    return tool_result({"event": data.get("event", data)})


# ---------------------------------------------------------------------------
# feishu_calendar_create_event
# ---------------------------------------------------------------------------

_CREATE_EVENT_URI = "/open-apis/calendar/v4/calendars/:calendar_id/events"
_CREATE_ATTENDEE_URI = (
    "/open-apis/calendar/v4/calendars/:calendar_id/events/:event_id/attendees"
)

FEISHU_CALENDAR_CREATE_EVENT_SCHEMA = {
    "name": "feishu_calendar_create_event",
    "description": (
        "Create a new calendar event as the signed-in user. "
        "Optionally adds attendees in a follow-up call. "
        "Times must be ISO 8601 / RFC 3339 with timezone, e.g. '2024-01-01T09:00:00+08:00'. "
        "Pass the current user's open_id in attendees so the event appears in their calendar."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "start_time": {
                "type": "string",
                "description": (
                    "Event start time in ISO 8601 / RFC 3339 format with timezone, "
                    "e.g. '2024-01-01T09:00:00+08:00'."
                ),
            },
            "end_time": {
                "type": "string",
                "description": (
                    "Event end time in ISO 8601 / RFC 3339 format with timezone, "
                    "e.g. '2024-01-01T10:00:00+08:00'. Defaults to 1 hour after start_time."
                ),
            },
            "summary": {
                "type": "string",
                "description": "Event title / summary (strongly recommended).",
            },
            "description": {
                "type": "string",
                "description": "Event description / notes (optional).",
            },
            "attendees": {
                "type": "array",
                "description": (
                    "List of attendees. Each item must have 'type' and 'id'. "
                    "type='user' with id=open_id (ou_xxx); "
                    "type='third_party' with id=email address. "
                    "Include the requesting user's open_id so the event appears in their calendar."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "type": "string",
                            "description": "Attendee type: 'user', 'chat', 'resource', or 'third_party'.",
                        },
                        "id": {
                            "type": "string",
                            "description": "Attendee ID: open_id for user, chat_id for chat, resource_id, or email for third_party.",
                        },
                    },
                    "required": ["type", "id"],
                },
            },
            "calendar_id": {
                "type": "string",
                "description": "Calendar ID (optional; primary calendar used if omitted).",
            },
        },
        "required": ["start_time", "end_time"],
    },
}


def _handle_calendar_create_event(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_create_event.

    Args:
        args: Tool arguments with start_time, end_time, summary, description,
              attendees list, and optional calendar_id.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    start_time = (args.get("start_time") or "").strip()
    end_time = (args.get("end_time") or "").strip()
    if not start_time or not end_time:
        return tool_error("start_time and end_time are required")

    summary = (args.get("summary") or "").strip()
    description = (args.get("description") or "").strip()
    attendees = args.get("attendees") or []
    calendar_id = (args.get("calendar_id") or "").strip()

    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    try:
        cid = _resolve_calendar_id(fc, calendar_id)
    except (RuntimeError, AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
        return tool_error(_auth_error_message(exc) if isinstance(exc, (NeedAuthorizationError, AppScopeMissingError, UserAuthRequiredError)) else str(exc))

    logger.info(
        "create_event: calendar_id=%s summary=%r start=%s end=%s attendees=%d",
        cid, summary, start_time, end_time, len(attendees),
    )

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    # Build event body
    try:
        start_payload = _event_time_payload(start_time)
        end_payload = _event_time_payload(end_time)
    except ValueError as exc:
        return tool_error(str(exc))

    event_body: dict = {
        "start_time": start_payload,
        "end_time": end_payload,
        "attendee_ability": "can_modify_event",
        "need_notification": True,
    }
    if summary:
        event_body["summary"] = summary
    if description:
        event_body["description"] = description

    def _make_opt() -> object:
        return (
            RequestOption.builder()
            .user_access_token(fc.access_token)
            .build()
        )

    # Create event
    create_request = (
        BaseRequest.builder()
        .http_method(HttpMethod.POST)
        .uri(_CREATE_EVENT_URI)
        .token_types({AccessTokenType.USER})
        .paths({"calendar_id": cid})
        .queries([("user_id_type", "open_id")])
        .body(event_body)
        .build()
    )
    response = fc.sdk.request(create_request, _make_opt())

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")
    data: dict = {}
    raw = getattr(response, "raw", None)
    if raw and hasattr(raw, "content"):
        try:
            body_json = json.loads(raw.content)
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
            data = body_json.get("data", {})
        except (json.JSONDecodeError, AttributeError):
            pass
    if not data:
        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict):
            data = resp_data
        elif resp_data and hasattr(resp_data, "__dict__"):
            data = vars(resp_data)

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_create_event",
                user_open_id=fc.user_open_id
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Create event failed: code={code} msg={msg}")

    event_obj = data.get("event", data)
    event_id = event_obj.get("event_id", "") if isinstance(event_obj, dict) else ""
    logger.info("create_event: created event_id=%s", event_id)

    # Add attendees if provided
    attendee_warning = None
    if attendees and event_id:
        attendee_data = []
        for a in attendees:
            a_type = a.get("type", "user")
            a_id = a.get("id", "")
            entry: dict = {"type": a_type}
            if a_type == "user":
                entry["user_id"] = a_id
            elif a_type == "chat":
                entry["chat_id"] = a_id
            elif a_type == "resource":
                entry["room_id"] = a_id
            elif a_type == "third_party":
                entry["third_party_email"] = a_id
            attendee_data.append(entry)

        attendee_request = (
            BaseRequest.builder()
            .http_method(HttpMethod.POST)
            .uri(_CREATE_ATTENDEE_URI)
            .token_types({AccessTokenType.USER})
            .paths({"calendar_id": cid, "event_id": event_id})
            .queries([("user_id_type", "open_id")])
            .body({
                "attendees": attendee_data,
                "need_notification": True,
            })
            .build()
        )
        att_response = fc.sdk.request(attendee_request, _make_opt())
        att_code = getattr(att_response, "code", None)
        att_msg = getattr(att_response, "msg", "")
        att_raw = getattr(att_response, "raw", None)
        if att_raw and hasattr(att_raw, "content"):
            try:
                att_json = json.loads(att_raw.content)
                if att_code is None:
                    att_code = att_json.get("code", -1)
                if not att_msg:
                    att_msg = att_json.get("msg", "")
            except (json.JSONDecodeError, AttributeError):
                pass

        if att_code != 0:
            attendee_warning = f"Event created but attendee add failed: code={att_code} msg={att_msg}"
            logger.warning("create_event: %s", attendee_warning)
        else:
            logger.info("create_event: added %d attendees to %s", len(attendees), event_id)

    result: dict = {"event": event_obj, "calendar_id": cid}
    if attendee_warning:
        result["warning"] = attendee_warning
    elif attendees and event_id:
        result["note"] = f"Successfully added {len(attendees)} attendee(s)."

    return tool_result(success=True, data=result)


# ---------------------------------------------------------------------------
# feishu_calendar_freebusy
# ---------------------------------------------------------------------------

_FREEBUSY_URI = "/open-apis/calendar/v4/freebusy/batch"

FEISHU_CALENDAR_FREEBUSY_SCHEMA = {
    "name": "feishu_calendar_freebusy",
    "description": (
        "Query free/busy status for 1-10 users as the signed-in user. "
        "Returns busy time blocks per user within the given time range. "
        "Use this when the user asks whether they are busy/free now or asks for 忙闲. "
        "If user_ids/start/end are omitted, queries the signed-in user for the next hour. "
        "Times must be ISO 8601 / RFC 3339 with timezone, e.g. '2024-01-01T09:00:00+08:00'."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_ids": {
                "type": "array",
                "description": (
                    "List of user open_ids (ou_xxx) to query (1-10 users). "
                    "Optional; defaults to the signed-in user."
                ),
                "items": {"type": "string"},
            },
            "start": {
                "type": "string",
                "description": (
                    "Query start time in ISO 8601 / RFC 3339 format with timezone, "
                    "e.g. '2024-01-01T09:00:00+08:00'. Optional; defaults to now."
                ),
            },
            "end": {
                "type": "string",
                "description": (
                    "Query end time in ISO 8601 / RFC 3339 format with timezone, "
                    "e.g. '2024-01-01T18:00:00+08:00'. Optional; defaults to one hour after start."
                ),
            },
        },
        "required": [],
    },
}


def _handle_calendar_freebusy(args: dict, **kwargs) -> str:
    """Handler for feishu_calendar_freebusy.

    Args:
        args: Tool arguments containing user_ids list, start, and end times.
        **kwargs: Additional keyword arguments (unused).

    Returns:
        JSON string via tool_result or tool_error.
    """
    try:
        fc = FeishuClient.for_user()
    except NeedAuthorizationError as exc:
        return tool_error(_auth_error_message(exc))
    except ValueError as exc:
        return tool_error(f"Feishu configuration error: {exc}")

    user_ids = args.get("user_ids") or []
    if isinstance(user_ids, str):
        user_ids = [user_ids]
    user_ids = [str(user_id).strip() for user_id in user_ids if str(user_id).strip()]
    if not user_ids and fc.user_open_id:
        user_ids = [fc.user_open_id]

    start = (args.get("start") or "").strip()
    end = (args.get("end") or "").strip()
    if not start or not end:
        default_start, default_end = _default_rfc3339_window()
        start = start or default_start
        end = end or default_end

    if not user_ids:
        return tool_error("user_ids is required (list of 1-10 open_ids)")
    if len(user_ids) > 10:
        return tool_error(
            f"user_ids count exceeds limit: maximum 10 users (got {len(user_ids)})"
        )

    logger.info(
        "freebusy: user_ids=%d start=%s end=%s", len(user_ids), start, end
    )

    try:
        from lark_oapi import AccessTokenType, RequestOption
        from lark_oapi.core.enum import HttpMethod
        from lark_oapi.core.model.base_request import BaseRequest
    except ImportError:
        return tool_error("lark_oapi not installed")

    request = (
        BaseRequest.builder()
        .http_method(HttpMethod.POST)
        .uri(_FREEBUSY_URI)
        .token_types({AccessTokenType.USER})
        .queries([("user_id_type", "open_id")])
        .body({
            "time_min": start,
            "time_max": end,
            "user_ids": user_ids,
            "include_external_calendar": True,
            "only_busy": True,
        })
        .build()
    )
    opt = (
        RequestOption.builder()
        .user_access_token(fc.access_token)
        .build()
    )
    response = fc.sdk.request(request, opt)

    code = getattr(response, "code", None)
    msg = getattr(response, "msg", "")
    data: dict = {}
    raw = getattr(response, "raw", None)
    if raw and hasattr(raw, "content"):
        try:
            body_json = json.loads(raw.content)
            if code is None:
                code = body_json.get("code", -1)
            if not msg:
                msg = body_json.get("msg", "")
            data = body_json.get("data", {})
        except (json.JSONDecodeError, AttributeError):
            pass
    if not data:
        resp_data = getattr(response, "data", None)
        if isinstance(resp_data, dict):
            data = resp_data
        elif resp_data and hasattr(resp_data, "__dict__"):
            data = vars(resp_data)

    if code != 0:
        try:
            raise_for_feishu_errcode(
                code, msg, api_name="feishu_calendar_freebusy",
                user_open_id=fc.user_open_id
            )
        except (AppScopeMissingError, UserAuthRequiredError, NeedAuthorizationError) as exc:
            return tool_error(_auth_error_message(exc))
        return tool_error(f"Freebusy query failed: code={code} msg={msg}")

    freebusy_lists = data.get("freebusy_lists", [])
    logger.info("freebusy: returned data for %d user(s)", len(freebusy_lists))
    return tool_result({
        "freebusy_lists": freebusy_lists,
    })


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

registry.register(
    name="feishu_calendar_list_events",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_LIST_EVENTS_SCHEMA,
    handler=_handle_calendar_list_events,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="List calendar events in a time range (instance_view, expands recurring)",
    emoji="\U0001f4c5",
)

registry.register(
    name="feishu_calendar_get_event",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_GET_EVENT_SCHEMA,
    handler=_handle_calendar_get_event,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Get a single calendar event by event_id",
    emoji="\U0001f4c5",
)

registry.register(
    name="feishu_calendar_create_event",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_CREATE_EVENT_SCHEMA,
    handler=_handle_calendar_create_event,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Create a calendar event with optional attendees",
    emoji="\U0001f4c5",
)

registry.register(
    name="feishu_calendar_freebusy",
    toolset="feishu_calendar",
    schema=FEISHU_CALENDAR_FREEBUSY_SCHEMA,
    handler=_handle_calendar_freebusy,
    check_fn=_check_feishu,
    requires_env=[],
    is_async=False,
    description="Query free/busy status for 1-10 users",
    emoji="\U0001f4c5",
)

# Register tool metadata (scopes + identity) in the shared registry
TOOLS_METADATA.update({
    "feishu_calendar_list_events": {
        "scopes": [_CALENDAR_READONLY_SCOPE, _CALENDAR_SCOPE],
        "identity": "user",
    },
    "feishu_calendar_get_event": {
        "scopes": [_CALENDAR_READONLY_SCOPE, _CALENDAR_SCOPE],
        "identity": "user",
    },
    "feishu_calendar_create_event": {
        "scopes": [_CALENDAR_SCOPE],
        "identity": "user",
    },
    "feishu_calendar_freebusy": {
        "scopes": [_CALENDAR_READONLY_SCOPE, _CALENDAR_SCOPE],
        "identity": "user",
    },
})
