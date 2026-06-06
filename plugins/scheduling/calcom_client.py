"""Thin Cal.com API client for the scheduling plugin."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx

from plugins.scheduling.oauth import OAuth2Manager, OAuthError


class SchedulingAPIError(RuntimeError):
    """Structured scheduling API failure."""

    def __init__(self, message: str, *, status_code: Optional[int] = None, response_body: Optional[str] = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


def _strip_none(data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    return {k: v for k, v in (data or {}).items() if v is not None}


class CalComClient:
    """Client for Cal.com v1 API using OAuth bearer tokens or API keys."""

    base_url = "https://api.cal.com/v1"

    def __init__(self) -> None:
        self._oauth = OAuth2Manager("calcom")

    def _headers(self) -> Dict[str, str]:
        api_key = os.getenv("CALCOM_API_KEY")
        if api_key:
            return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
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
        """Call the Cal.com API and return decoded JSON."""
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
                f"Cal.com API error ({response.status_code}): {response.text}",
                status_code=response.status_code,
                response_body=response.text,
            )
        if response.status_code == 204 or not response.content:
            return empty_response or {"success": True, "status_code": response.status_code, "empty": True}
        if "application/json" in response.headers.get("content-type", ""):
            return response.json()
        return {"success": True, "text": response.text}

    def list_event_types(self) -> Any:
        """List Cal.com event types."""
        return self.request("GET", "/event-types")

    def list_bookings(self, *, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: Optional[int] = None) -> Any:
        """List bookings between optional timestamps."""
        return self.request("GET", "/bookings", params={"startTime": start_time, "endTime": end_time, "limit": limit})

    def create_booking(self, payload: Dict[str, Any]) -> Any:
        """Create a Cal.com booking."""
        return self.request("POST", "/bookings", json_body=payload)

    def get_booking(self, booking_id: str) -> Any:
        """Fetch booking details."""
        return self.request("GET", f"/bookings/{booking_id}")

    def cancel_booking(self, booking_id: str, *, reason: Optional[str] = None) -> Any:
        """Cancel a booking."""
        return self.request("DELETE", f"/bookings/{booking_id}", params={"reason": reason})

    def check_availability(self, *, event_type_id: Optional[str], start_time: str, end_time: str) -> Any:
        """Check availability for an event type."""
        return self.request("GET", "/availability", params={
            "eventTypeId": event_type_id,
            "startTime": start_time,
            "endTime": end_time,
        })
