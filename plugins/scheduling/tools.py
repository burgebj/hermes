"""Native scheduling tools for Hermes (registered via plugins/scheduling)."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from hermes_constants import get_hermes_home
from plugins.scheduling.calcom_client import CalComClient, SchedulingAPIError
from plugins.scheduling.calendly_client import CalendlyClient
from plugins.scheduling.google_calendar_client import GoogleCalendarClient
from plugins.scheduling.oauth import OAuth2Manager, OAuthError
from tools.registry import tool_error, tool_result

PROVIDERS = {"calcom", "calendly", "google_calendar"}
COMMON_STRING = {"type": "string"}
PROVIDER_SCHEMA = {"type": "string", "enum": sorted(PROVIDERS)}


def _check_scheduling_available() -> bool:
    """Return True when at least one scheduling provider can authenticate."""
    try:
        if os.getenv("CALCOM_API_KEY"):
            return True
        if os.getenv("CALCOM_CLIENT_ID") or os.getenv("CALENDLY_CLIENT_ID"):
            return True
        home = get_hermes_home()
        if (home / "google_token.json").exists():
            return True
        tokens_dir = home / "scheduling_tokens"
        return (tokens_dir / "calcom.json").exists() or (tokens_dir / "calendly.json").exists()
    except Exception:
        return False


def _provider(args: Dict[str, Any]) -> str:
    provider = str(args.get("provider") or "").strip().lower()
    if provider not in PROVIDERS:
        raise ValueError(f"provider must be one of: {', '.join(sorted(PROVIDERS))}")
    return provider


def _coerce_limit(raw: Any, *, default: int = 20, minimum: int = 1, maximum: int = 100) -> int:
    try:
        value = int(raw)
    except Exception:
        value = default
    return max(minimum, min(maximum, value))


def _as_list(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]
    return [str(raw).strip()] if str(raw).strip() else []


def _calendar_id(args: Dict[str, Any]) -> str:
    return str(args.get("calendar_id") or "primary").strip() or "primary"


def _tool_failure(exc: Exception) -> str:
    if isinstance(exc, SchedulingAPIError):
        return tool_error(str(exc), status_code=exc.status_code)
    if isinstance(exc, (OAuthError, ValueError)):
        return tool_error(str(exc))
    return tool_error(f"Scheduling tool failed: {type(exc).__name__}: {exc}")


def _google_event_payload(args: Dict[str, Any]) -> Dict[str, Any]:
    attendees = [{"email": email} for email in _as_list(args.get("attendees"))]
    return {
        "summary": args.get("title"),
        "description": args.get("description"),
        "location": args.get("location"),
        "start": {"dateTime": args.get("start_time")},
        "end": {"dateTime": args.get("end_time")},
        "attendees": attendees or None,
    }


def _calcom_booking_payload(args: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "eventTypeId": args.get("event_type_id"),
        "title": args.get("title"),
        "start": args.get("start_time"),
        "end": args.get("end_time"),
        "description": args.get("description"),
        "location": args.get("location"),
        "attendees": _as_list(args.get("attendees")) or None,
        "responses": args.get("responses"),
        "metadata": args.get("metadata"),
    }


def _handle_scheduling_list_events(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        limit = _coerce_limit(args.get("limit"), default=20)
        if provider == "calcom":
            result = CalComClient().list_bookings(
                start_time=args.get("start_date"),
                end_time=args.get("end_date"),
                limit=limit,
            )
        elif provider == "calendly":
            result = CalendlyClient().list_events(
                start_time=args.get("start_date"),
                end_time=args.get("end_date"),
                limit=limit,
            )
        else:
            result = GoogleCalendarClient(calendar_id=_calendar_id(args)).list_events(
                start_time=args.get("start_date"),
                end_time=args.get("end_date"),
                limit=limit,
            )
        return tool_result({"success": True, "provider": provider, "result": result})
    except Exception as exc:
        return _tool_failure(exc)


def _handle_scheduling_create_event(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        if not args.get("title"):
            return tool_error("title is required")
        if not args.get("start_time") or not args.get("end_time"):
            return tool_error("start_time and end_time are required")
        if provider == "calcom":
            result = CalComClient().create_booking(_calcom_booking_payload(args))
        elif provider == "calendly":
            return tool_error("Calendly API does not support creating scheduled events directly; create a booking through a scheduling link.")
        else:
            result = GoogleCalendarClient(calendar_id=_calendar_id(args)).create_event(_google_event_payload(args))
        return tool_result({"success": True, "provider": provider, "result": result})
    except Exception as exc:
        return _tool_failure(exc)


def _handle_scheduling_get_event(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        event_id = str(args.get("event_id") or "").strip()
        if not event_id:
            return tool_error("event_id is required")
        if provider == "calcom":
            result = CalComClient().get_booking(event_id)
        elif provider == "calendly":
            result = CalendlyClient().get_event(event_id)
        else:
            result = GoogleCalendarClient(calendar_id=_calendar_id(args)).get_event(event_id)
        return tool_result({"success": True, "provider": provider, "result": result})
    except Exception as exc:
        return _tool_failure(exc)


def _handle_scheduling_cancel_event(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        event_id = str(args.get("event_id") or "").strip()
        if not event_id:
            return tool_error("event_id is required")
        reason = args.get("reason")
        if provider == "calcom":
            result = CalComClient().cancel_booking(event_id, reason=reason)
        elif provider == "calendly":
            result = CalendlyClient().cancel_event(event_id, reason=reason)
        else:
            result = GoogleCalendarClient(calendar_id=_calendar_id(args)).delete_event(event_id)
        return tool_result({"success": True, "provider": provider, "result": result})
    except Exception as exc:
        return _tool_failure(exc)


def _handle_scheduling_check_availability(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        start_date = args.get("start_date")
        end_date = args.get("end_date")
        if not start_date or not end_date:
            return tool_error("start_date and end_date are required")
        if provider == "calcom":
            result = CalComClient().check_availability(
                event_type_id=args.get("event_type_id"),
                start_time=start_date,
                end_time=end_date,
            )
        elif provider == "calendly":
            result = CalendlyClient().check_availability(
                user_uri=args.get("user_uri"),
                event_type_uri=args.get("event_type_uri"),
                start_time=start_date,
                end_time=end_date,
            )
        else:
            result = GoogleCalendarClient(calendar_id=_calendar_id(args)).free_busy(
                start_time=start_date,
                end_time=end_date,
                calendar_ids=_as_list(args.get("calendar_ids")) or None,
            )
        return tool_result({"success": True, "provider": provider, "result": result})
    except Exception as exc:
        return _tool_failure(exc)


def _handle_scheduling_list_calendars(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        if provider != "google_calendar":
            return tool_error("scheduling_list_calendars only supports provider='google_calendar'")
        return tool_result({"success": True, "provider": provider, "result": GoogleCalendarClient().list_calendars()})
    except Exception as exc:
        return _tool_failure(exc)


def _handle_scheduling_oauth(args: Dict[str, Any], **_kw: Any) -> str:
    try:
        provider = _provider(args)
        action = str(args.get("action") or "check").strip().lower()
        manager = OAuth2Manager(provider)
        if action == "check":
            return tool_result(manager.check())
        if action == "auth_url":
            return tool_result(manager.authorization_url())
        if action == "auth_code":
            code = str(args.get("code") or "").strip()
            if not code:
                return tool_error("code is required for action='auth_code'")
            return tool_result(manager.exchange_code(code))
        if action == "revoke":
            return tool_result(manager.revoke())
        return tool_error("action must be one of: check, auth_url, auth_code, revoke")
    except Exception as exc:
        return _tool_failure(exc)


SCHEDULING_LIST_EVENTS_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_list_events",
    "description": "List scheduling events or bookings from Cal.com, Calendly, or Google Calendar.",
    "parameters": {
        "type": "object",
        "properties": {
            "provider": PROVIDER_SCHEMA,
            "start_date": COMMON_STRING,
            "end_date": COMMON_STRING,
            "limit": {"type": "integer"},
            "calendar_id": COMMON_STRING,
        },
        "required": ["provider"],
    },
}

SCHEDULING_CREATE_EVENT_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_create_event",
    "description": "Create a Cal.com booking or Google Calendar event. Calendly event creation is not supported by Calendly's public API.",
    "parameters": {
        "type": "object",
        "properties": {
            "provider": PROVIDER_SCHEMA,
            "title": COMMON_STRING,
            "start_time": COMMON_STRING,
            "end_time": COMMON_STRING,
            "description": COMMON_STRING,
            "attendees": {"type": "array", "items": COMMON_STRING},
            "location": COMMON_STRING,
            "calendar_id": COMMON_STRING,
            "event_type_id": COMMON_STRING,
            "responses": {"type": "object"},
            "metadata": {"type": "object"},
        },
        "required": ["provider", "title", "start_time", "end_time"],
    },
}

SCHEDULING_GET_EVENT_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_get_event",
    "description": "Get one scheduling event or booking by provider-specific event id.",
    "parameters": {
        "type": "object",
        "properties": {
            "provider": PROVIDER_SCHEMA,
            "event_id": COMMON_STRING,
            "calendar_id": COMMON_STRING,
        },
        "required": ["provider", "event_id"],
    },
}

SCHEDULING_CANCEL_EVENT_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_cancel_event",
    "description": "Cancel or delete one scheduling event by provider-specific event id.",
    "parameters": {
        "type": "object",
        "properties": {
            "provider": PROVIDER_SCHEMA,
            "event_id": COMMON_STRING,
            "reason": COMMON_STRING,
            "calendar_id": COMMON_STRING,
        },
        "required": ["provider", "event_id"],
    },
}

SCHEDULING_CHECK_AVAILABILITY_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_check_availability",
    "description": "Check provider availability between two timestamps.",
    "parameters": {
        "type": "object",
        "properties": {
            "provider": PROVIDER_SCHEMA,
            "start_date": COMMON_STRING,
            "end_date": COMMON_STRING,
            "event_type_id": COMMON_STRING,
            "event_type_uri": COMMON_STRING,
            "user_uri": COMMON_STRING,
            "calendar_id": COMMON_STRING,
            "calendar_ids": {"type": "array", "items": COMMON_STRING},
        },
        "required": ["provider", "start_date", "end_date"],
    },
}

SCHEDULING_LIST_CALENDARS_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_list_calendars",
    "description": "List calendars for Google Calendar.",
    "parameters": {
        "type": "object",
        "properties": {"provider": PROVIDER_SCHEMA},
        "required": ["provider"],
    },
}

SCHEDULING_OAUTH_SCHEMA: Dict[str, Any] = {
    "name": "scheduling_oauth",
    "description": "Manage scheduling OAuth status, authorization URLs, code exchange, and local token revocation.",
    "parameters": {
        "type": "object",
        "properties": {
            "provider": PROVIDER_SCHEMA,
            "action": {"type": "string", "enum": ["check", "auth_url", "auth_code", "revoke"]},
            "code": COMMON_STRING,
        },
        "required": ["provider", "action"],
    },
}
