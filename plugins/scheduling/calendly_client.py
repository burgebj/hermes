"""Thin Calendly API client for the scheduling plugin."""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from plugins.scheduling.calcom_client import SchedulingAPIError, _strip_none
from plugins.scheduling.oauth import OAuth2Manager, OAuthError


class CalendlyClient:
    """Client for Calendly API using OAuth2 with PKCE."""

    base_url = "https://api.calendly.com"

    def __init__(self) -> None:
        self._oauth = OAuth2Manager("calendly")

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
    ) -> Any:
        """Call the Calendly API and return decoded JSON."""
        response = httpx.request(
            method,
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=_strip_none(params),
            json=_strip_none(json_body) if json_body is not None else None,
            timeout=30.0,
        )
        if response.status_code >= 400:
            raise SchedulingAPIError(
                f"Calendly API error ({response.status_code}): {response.text}",
                status_code=response.status_code,
                response_body=response.text,
            )
        if response.status_code == 204 or not response.content:
            return empty_response or {"success": True, "status_code": response.status_code, "empty": True}
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return {"success": True, "text": response.text}

    def get_current_user(self) -> Any:
        """Fetch the current Calendly user."""
        return self.request("GET", "/users/me")

    def list_event_types(self, *, user_uri: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """List Calendly event types."""
        return self.request("GET", "/event_types", params={"user": user_uri, "count": limit})

    def list_events(self, *, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """List scheduled Calendly events."""
        return self.request("GET", "/scheduled_events", params={
            "min_start_time": start_time,
            "max_start_time": end_time,
            "count": limit,
        })

    def get_event(self, event_uuid: str) -> Any:
        """Fetch event details by UUID."""
        return self.request("GET", f"/scheduled_events/{event_uuid}")

    def cancel_event(self, event_uuid: str, *, reason: Optional[str] = None) -> Any:
        """Cancel a scheduled event."""
        return self.request("POST", f"/scheduled_events/{event_uuid}/cancellations", json_body={"reason": reason})

    def check_availability(self, *, user_uri: Optional[str], event_type_uri: Optional[str], start_time: str, end_time: str) -> Any:
        """Check Calendly availability for a user and event type."""
        return self.request("GET", "/availability", params={
            "user_uri": user_uri,
            "event_type": event_type_uri,
            "start_time": start_time,
            "end_time": end_time,
        })
