#!/usr/bin/env python3
"""
ScanBlitz Tool Module — QR Code & Analytics for Agents

Allows the agent to create trackable QR codes, pull scan analytics,
manage campaigns, and self-register for an API key — all via the
ScanBlitz API (Supabase Edge Functions).

Environment:
    SCANBLITZ_API_KEY  — Partner key (sbz_partner_...) or Enterprise key (sb_api_...)
    SCANBLITZ_API_URL  — Base URL (default: Supabase partner-api endpoint)

Registration works without an API key.
"""

import json
import os
import urllib.request
import urllib.error
from typing import Optional

_SUPABASE_URL = "https://kylpeyhiqtdonlqqguty.supabase.co"
_PARTNER_API_URL = os.environ.get(
    "SCANBLITZ_API_URL",
    f"{_SUPABASE_URL}/functions/v1/partner-api",
)
_REGISTER_URL = f"{_SUPABASE_URL}/functions/v1/agent-register"
_API_KEY = os.environ.get("SCANBLITZ_API_KEY", "")


def _request(method: str, url: str, body: Optional[dict] = None,
             auth: bool = True) -> dict:
    """Make an HTTP request to the ScanBlitz API."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "hermes-scanblitz/1.0",
        "X-Source-Type": "agent",
    }
    if auth and _API_KEY:
        # Support both partner keys (X-Partner-Key) and enterprise keys (Bearer)
        if _API_KEY.startswith("sbz_partner_"):
            headers["X-Partner-Key"] = _API_KEY
        else:
            headers["Authorization"] = f"Bearer {_API_KEY}"

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode() if e.fp else ""
        except Exception:
            pass
        try:
            err_data = json.loads(body_text)
            msg = err_data.get("error", body_text)
            if isinstance(msg, dict):
                msg = msg.get("message", str(msg))
        except Exception:
            msg = body_text or str(e)
        return {"error": msg, "status": e.code}
    except Exception as e:
        return {"error": str(e)}


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

def scanblitz_create_qr(args: dict, **_kw) -> str:
    """Create a trackable QR code."""
    name = args.get("name", "")
    url = args.get("destination_url", "")
    if not name or not url:
        return _err("name and destination_url are required")

    result = _request("POST", _PARTNER_API_URL, {
        "name": name,
        "destination_url": url,
        "partner_ref": f"hermes:{name.lower().replace(' ', '-')}",
    })
    return json.dumps(result, indent=2, ensure_ascii=False)


def scanblitz_list_qr(args: dict, **_kw) -> str:
    """List QR codes. Currently returns all codes via partner API."""
    # The partner API doesn't have a list endpoint, so we use a simple approach
    result = _request("GET", f"{_PARTNER_API_URL}/health")
    if "error" in result:
        return json.dumps(result, ensure_ascii=False)
    return json.dumps({
        "message": "Use scanblitz_get_analytics to check individual QR codes by short_id, or scanblitz_create_qr to create new ones.",
        "api_status": result,
    }, indent=2, ensure_ascii=False)


def scanblitz_get_analytics(args: dict, **_kw) -> str:
    """Get scan analytics for a QR code by short_id."""
    short_id = args.get("short_id")
    if not short_id:
        return _err("short_id is required (e.g. 'xK7mQ3')")

    result = _request("GET", f"{_PARTNER_API_URL}/analytics/{short_id}")
    return json.dumps(result, indent=2, ensure_ascii=False)


def scanblitz_update_qr(args: dict, **_kw) -> str:
    """Update a QR code's destination, name, or active status."""
    short_id = args.get("short_id")
    if not short_id:
        return _err("short_id is required")
    body = {}
    for k in ("name", "destination_url", "is_active"):
        v = args.get(k)
        if v is not None:
            body[k] = v
    result = _request("PUT", f"{_PARTNER_API_URL}/{short_id}", body)
    return json.dumps(result, indent=2, ensure_ascii=False)


def scanblitz_get_qr(args: dict, **_kw) -> str:
    """Get details of a QR code by short_id."""
    short_id = args.get("short_id")
    if not short_id:
        return _err("short_id is required")
    result = _request("GET", f"{_PARTNER_API_URL}/{short_id}")
    return json.dumps(result, indent=2, ensure_ascii=False)


def scanblitz_delete_qr(args: dict, **_kw) -> str:
    """Deactivate a QR code (soft delete)."""
    short_id = args.get("short_id")
    if not short_id:
        return _err("short_id is required")
    result = _request("DELETE", f"{_PARTNER_API_URL}/{short_id}")
    return json.dumps(result, indent=2, ensure_ascii=False)


def scanblitz_register(args: dict, **_kw) -> str:
    """Register for a ScanBlitz account. Sends a verification code to email."""
    email = args.get("email")
    if not email:
        return _err("email is required")
    result = _request("POST", _REGISTER_URL, {
        "email": email,
        "agent_name": args.get("agent_name", "Hermes"),
    }, auth=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


def scanblitz_verify(args: dict, **_kw) -> str:
    """Complete registration with the 6-digit code from email."""
    email = args.get("email")
    code = args.get("code")
    if not email or not code:
        return _err("email and code are required")
    result = _request("POST", f"{_REGISTER_URL}/verify", {
        "email": email,
        "code": code,
    }, auth=False)
    return json.dumps(result, indent=2, ensure_ascii=False)


def _err(msg: str) -> str:
    return json.dumps({"error": msg}, ensure_ascii=False)


def check_scanblitz() -> bool:
    """ScanBlitz tool is always available (registration works without a key)."""
    return True


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

SCANBLITZ_CREATE_QR_SCHEMA = {
    "name": "scanblitz_create_qr",
    "description": (
        "Create a trackable QR code via ScanBlitz. Returns a short_id, "
        "scan_url, and a receipt confirming who created it and when. "
        "Every scan is tracked with device, location, and referrer data. "
        "Save the short_id to check analytics or update the destination later."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Display name for the QR code",
            },
            "destination_url": {
                "type": "string",
                "description": "URL the QR code points to",
            },
        },
        "required": ["name", "destination_url"],
    },
}

SCANBLITZ_GET_QR_SCHEMA = {
    "name": "scanblitz_get_qr",
    "description": "Get details of a QR code by its short_id.",
    "parameters": {
        "type": "object",
        "properties": {
            "short_id": {
                "type": "string",
                "description": "The short ID of the QR code (e.g. 'xK7mQ3')",
            },
        },
        "required": ["short_id"],
    },
}

SCANBLITZ_GET_ANALYTICS_SCHEMA = {
    "name": "scanblitz_get_analytics",
    "description": (
        "Get scan analytics for a QR code: total scans, device breakdown, "
        "country distribution, daily scan counts, and the last scan event. "
        "Includes a receipt confirming retrieval."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "short_id": {
                "type": "string",
                "description": "The short ID of the QR code",
            },
        },
        "required": ["short_id"],
    },
}

SCANBLITZ_UPDATE_QR_SCHEMA = {
    "name": "scanblitz_update_qr",
    "description": "Update a QR code's destination URL, name, or active status.",
    "parameters": {
        "type": "object",
        "properties": {
            "short_id": {
                "type": "string",
                "description": "The short ID of the QR code",
            },
            "name": {"type": "string", "description": "New name"},
            "destination_url": {"type": "string", "description": "New destination URL"},
            "is_active": {"type": "boolean", "description": "Enable or disable"},
        },
        "required": ["short_id"],
    },
}

SCANBLITZ_DELETE_QR_SCHEMA = {
    "name": "scanblitz_delete_qr",
    "description": "Deactivate a QR code (soft delete). The QR code will stop redirecting.",
    "parameters": {
        "type": "object",
        "properties": {
            "short_id": {
                "type": "string",
                "description": "The short ID of the QR code",
            },
        },
        "required": ["short_id"],
    },
}

SCANBLITZ_REGISTER_SCHEMA = {
    "name": "scanblitz_register",
    "description": (
        "Register for a ScanBlitz API key. Sends a 6-digit verification code "
        "to the email address. Use scanblitz_verify with the code to complete "
        "registration and get your API key. No existing API key needed."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "Email address"},
            "agent_name": {"type": "string", "description": "Name of this agent"},
        },
        "required": ["email"],
    },
}

SCANBLITZ_VERIFY_SCHEMA = {
    "name": "scanblitz_verify",
    "description": (
        "Complete ScanBlitz registration with the 6-digit code sent to your "
        "email. Returns the API key — store it securely."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "Email used during registration"},
            "code": {"type": "string", "description": "6-digit verification code"},
        },
        "required": ["email", "code"],
    },
}


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

from tools.registry import registry

TOOLSET = "scanblitz"

registry.register(
    name="scanblitz_create_qr",
    toolset=TOOLSET,
    schema=SCANBLITZ_CREATE_QR_SCHEMA,
    handler=scanblitz_create_qr,
    check_fn=check_scanblitz,
    emoji="\U0001f4f1",
)

registry.register(
    name="scanblitz_get_qr",
    toolset=TOOLSET,
    schema=SCANBLITZ_GET_QR_SCHEMA,
    handler=scanblitz_get_qr,
    check_fn=check_scanblitz,
    emoji="\U0001f50d",
)

registry.register(
    name="scanblitz_get_analytics",
    toolset=TOOLSET,
    schema=SCANBLITZ_GET_ANALYTICS_SCHEMA,
    handler=scanblitz_get_analytics,
    check_fn=check_scanblitz,
    emoji="\U0001f4ca",
)

registry.register(
    name="scanblitz_update_qr",
    toolset=TOOLSET,
    schema=SCANBLITZ_UPDATE_QR_SCHEMA,
    handler=scanblitz_update_qr,
    check_fn=check_scanblitz,
    emoji="\u270f\ufe0f",
)

registry.register(
    name="scanblitz_delete_qr",
    toolset=TOOLSET,
    schema=SCANBLITZ_DELETE_QR_SCHEMA,
    handler=scanblitz_delete_qr,
    check_fn=check_scanblitz,
    emoji="\U0001f5d1",
)

registry.register(
    name="scanblitz_register",
    toolset=TOOLSET,
    schema=SCANBLITZ_REGISTER_SCHEMA,
    handler=scanblitz_register,
    check_fn=check_scanblitz,
    emoji="\U0001f511",
)

registry.register(
    name="scanblitz_verify",
    toolset=TOOLSET,
    schema=SCANBLITZ_VERIFY_SCHEMA,
    handler=scanblitz_verify,
    check_fn=check_scanblitz,
    emoji="\u2705",
)
