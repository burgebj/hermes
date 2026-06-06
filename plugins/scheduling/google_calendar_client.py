"""Thin Google Calendar API client for the scheduling plugin."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

from plugins.scheduling.calcom_client import SchedulingAPIError, _strip_none
from plugins.scheduling.oauth import OAuth2Manager, OAuthError


class GoogleCalendarClient:
    """Client for Google Calendar API using the existing Hermes Google token."""

    base_url = "https://www.googleapis.com/calendar/v3"

    def __init__(self, calendar_id: str = "primary") -> None:
        self.calendar_id = calendar_id or "primary"
        self._oauth = OAuth2Manager("google_calendar")

    def _headers(self) -> Dict[str, str]:
        try:
            token = self._oauth.access_token()
        except OAuthError as exc:
            raise SchedulingAPIError(str(exc)) from exc
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        empty_response: Optional[Dict[str, Any]] = None,
        allow_retry_on_401: bool = True,
    ) -> Any:
        """Call Google Calendar and refresh once on 401."""
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=_strip_none(params),
            json=_strip_none(json_body) if json_body is not None else None,
            timeout=30.0,
        )
        if response.status_code == 401 and allow_retry_on_401:
            self._oauth.refresh_token()
            return self.request(
                method,
                path,
                params=params,
                json_body=json_body,
                empty_response=empty_response,
                allow_retry_on_401=False,
            )
        if response.status_code >= 400:
            raise SchedulingAPIError(
                f"Google Calendar API error ({response.status_code}): {response.text}",
                status_code=response.status_code,
                response_body=response.text,
            )
        if response.status_code == 204 or not response.content:
            return empty_response or {"success": True, "status_code": response.status_code, "empty": True}
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return {"success": True, "text": response.text}

    def list_calendars(self) -> Any:
        """List Google calendars."""
        return self.request("GET", "/users/me/calendarList")

    def list_events(self, *, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """List events on the configured calendar."""
        return self.request("GET", f"/calendars/{self.calendar_id}/events", params={
            "timeMin": start_time,
            "timeMax": end_time,
            "maxResults": limit,
            "singleEvents": True,
            "orderBy": "startTime",
        })

    def create_event(self, payload: Dict[str, Any]) -> Any:
        """Create an event on the configured calendar."""
        return self.request("POST", f"/calendars/{self.calendar_id}/events", json_body=payload)

    def get_event(self, event_id: str) -> Any:
        """Fetch one event."""
        return self.request("GET", f"/calendars/{self.calendar_id}/events/{event_id}")

    def update_event(self, event_id: str, payload: Dict[str, Any]) -> Any:
        """Update one event."""
        return self.request("PUT", f"/calendars/{self.calendar_id}/events/{event_id}", json_body=payload)

    def delete_event(self, event_id: str) -> Any:
        """Delete one event."""
        return self.request("DELETE", f"/calendars/{self.calendar_id}/events/{event_id}")

    def free_busy(self, *, start_time: str, end_time: str, calendar_ids: Optional[List[str]] = None) -> Any:
        """Check free/busy for one or more calendars."""
        ids = calendar_ids or [self.calendar_id]
        return self.request("POST", "/freeBusy", json_body={
            "timeMin": start_time,
            "timeMax": end_time,
            "items": [{"id": calendar_id} for calendar_id in ids],
        })
