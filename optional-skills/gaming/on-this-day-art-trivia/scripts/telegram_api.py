"""Tiny Telegram Bot API client.

Used as a fallback when Hermes' built-in send mechanism cannot deliver an
image with caption. The token is read once from the environment via
:func:`get_token` — never logged, never printed.

Public surface:

* :func:`send_photo(chat_id, photo, caption, reply_to_message_id=None)` —
  upload a local photo file with a caption. Returns the message_id of the
  sent message, or ``None`` if delivery failed.
* :func:`send_message(chat_id, text, reply_to_message_id=None)` — plain
  text reply.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"
HTTP_TIMEOUT = 30.0


def get_token() -> Optional[str]:
    """Return the bot token from $TELEGRAM_BOT_TOKEN, or None if unset.

    Token is intentionally never echoed to logs. Callers MUST treat its
    presence/absence as a quiet signal — never print the value.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TG_BOT_TOKEN")
    return token if token else None


def _build_multipart(fields: Dict[str, str], files: Dict[str, Tuple[str, bytes, str]]) -> Tuple[bytes, str]:
    """Build a minimal multipart/form-data body. Returns (body, content_type)."""
    boundary = "----HermesOTDAT" + secrets.token_hex(16)
    sep = f"--{boundary}".encode()
    end = f"--{boundary}--".encode()
    crlf = b"\r\n"
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(sep)
        parts.append(crlf)
        parts.append(f'Content-Disposition: form-data; name="{name}"'.encode())
        parts.append(crlf + crlf)
        parts.append(value.encode("utf-8"))
        parts.append(crlf)
    for name, (filename, data, mime) in files.items():
        parts.append(sep)
        parts.append(crlf)
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode()
        )
        parts.append(crlf)
        parts.append(f"Content-Type: {mime}".encode())
        parts.append(crlf + crlf)
        parts.append(data)
        parts.append(crlf)
    parts.append(end)
    parts.append(crlf)
    body = b"".join(parts)
    return body, f"multipart/form-data; boundary={boundary}"


def _api_request(method: str, fields: Dict[str, Any], files: Optional[Dict[str, Path]] = None) -> Optional[Dict[str, Any]]:
    token = get_token()
    if not token:
        logger.debug("Telegram token not set; skipping API call to %s", method)
        return None
    url = f"{API_BASE}/bot{token}/{method}"
    str_fields = {k: str(v) for k, v in fields.items() if v is not None}

    if files:
        file_payload: Dict[str, Tuple[str, bytes, str]] = {}
        for field_name, path in files.items():
            try:
                data = path.read_bytes()
            except OSError as exc:
                logger.warning("Failed to read %s: %s", path, exc)
                return None
            mime, _ = mimetypes.guess_type(path.name)
            file_payload[field_name] = (path.name, data, mime or "application/octet-stream")
        body, content_type = _build_multipart(str_fields, file_payload)
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", content_type)
    else:
        body = urllib.parse.urlencode(str_fields).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning("Telegram %s failed: %s", method, exc)
        return None
    if not payload.get("ok"):
        logger.warning("Telegram %s returned not ok: %s", method, payload.get("description"))
        return None
    return payload.get("result")


def send_photo(
    chat_id: str,
    photo_path: Path,
    caption: str,
    *,
    reply_to_message_id: Optional[str] = None,
) -> Optional[str]:
    """Send a photo with caption. Returns the new message_id, or None on failure."""
    fields: Dict[str, Any] = {"chat_id": str(chat_id), "caption": caption}
    if reply_to_message_id:
        fields["reply_to_message_id"] = str(reply_to_message_id)
    result = _api_request("sendPhoto", fields, files={"photo": Path(photo_path)})
    if not result:
        return None
    return str(result.get("message_id")) if result.get("message_id") is not None else None


def send_message(
    chat_id: str,
    text: str,
    *,
    reply_to_message_id: Optional[str] = None,
) -> Optional[str]:
    fields: Dict[str, Any] = {"chat_id": str(chat_id), "text": text}
    if reply_to_message_id:
        fields["reply_to_message_id"] = str(reply_to_message_id)
    result = _api_request("sendMessage", fields)
    if not result:
        return None
    return str(result.get("message_id")) if result.get("message_id") is not None else None
