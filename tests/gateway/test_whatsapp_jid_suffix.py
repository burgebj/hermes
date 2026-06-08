"""Tests for WhatsApp bare-phone-number → JID normalization.

Regression tests for #41660: ``send_message(target="whatsapp:15551234567")``
crashed the Baileys bridge because the Python adapter passed the bare
phone number through without appending ``@s.whatsapp.net``.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from gateway.platforms.whatsapp import WhatsAppAdapter


# ---------------------------------------------------------------------------
# _ensure_jid_suffix — static method, no adapter state needed
# ---------------------------------------------------------------------------

class TestEnsureJidSuffix:
    """Unit tests for ``WhatsAppAdapter._ensure_jid_suffix``."""

    def test_bare_number_gets_suffix(self):
        assert WhatsAppAdapter._ensure_jid_suffix("15551234567") == "15551234567@s.whatsapp.net"

    def test_already_has_swhatsapp_net(self):
        jid = "15551234567@s.whatsapp.net"
        assert WhatsAppAdapter._ensure_jid_suffix(jid) == jid

    def test_lid_jid_unchanged(self):
        jid = "12345@lid"
        assert WhatsAppAdapter._ensure_jid_suffix(jid) == jid

    def test_group_jid_unchanged(self):
        jid = "120363012345678@g.us"
        assert WhatsAppAdapter._ensure_jid_suffix(jid) == jid

    def test_empty_string_passthrough(self):
        assert WhatsAppAdapter._ensure_jid_suffix("") == ""

    def test_none_passthrough(self):
        # _ensure_jid_suffix checks ``not chat_id`` which covers None
        assert WhatsAppAdapter._ensure_jid_suffix(None) is None

    def test_number_with_plus_prefix(self):
        # E.164 format like "+15551234567" — contains no @, should get suffix
        assert WhatsAppAdapter._ensure_jid_suffix("+15551234567") == "+15551234567@s.whatsapp.net"


# ---------------------------------------------------------------------------
# send() — integration: bare number is normalised before bridge POST
# ---------------------------------------------------------------------------

class _FakeResp:
    """Minimal async context manager for ``aiohttp.ClientSession.post``."""

    def __init__(self, status=200, body=None):
        self.status = status
        self._body = body or {"messageId": "msg-1"}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def json(self):
        return self._body

    async def text(self):
        return str(self._body)


def _make_adapter_for_send():
    """Create a minimal adapter ready for ``send()``."""
    from gateway.platforms.whatsapp import WhatsAppAdapter

    adapter = WhatsAppAdapter.__new__(WhatsAppAdapter)
    adapter._running = True
    adapter._http_session = MagicMock()
    adapter._bridge_port = 19876
    adapter._outgoing_chunk_limit = MagicMock(return_value=4096)
    adapter.format_message = MagicMock(side_effect=lambda c: c)
    adapter.truncate_message = MagicMock(side_effect=lambda c, lim: [c])
    adapter._check_managed_bridge_exit = AsyncMock(return_value=None)
    return adapter


@pytest.mark.asyncio
async def test_send_bare_number_gets_jid_suffix():
    """send() must normalise a bare phone number before posting to bridge."""
    adapter = _make_adapter_for_send()

    captured_payloads = []

    def _capture_post(url, json=None, **kw):
        captured_payloads.append(json)
        return _FakeResp(200)

    adapter._http_session.post = MagicMock(side_effect=_capture_post)

    await adapter.send("15551234567", "hello")

    assert len(captured_payloads) == 1
    assert captured_payloads[0]["chatId"] == "15551234567@s.whatsapp.net"


@pytest.mark.asyncio
async def test_send_already_jid_unchanged():
    """send() must not double-append suffix to an already-formatted JID."""
    adapter = _make_adapter_for_send()

    captured_payloads = []

    def _capture_post(url, json=None, **kw):
        captured_payloads.append(json)
        return _FakeResp(200)

    adapter._http_session.post = MagicMock(side_effect=_capture_post)

    await adapter.send("15551234567@s.whatsapp.net", "hello")

    assert captured_payloads[0]["chatId"] == "15551234567@s.whatsapp.net"


@pytest.mark.asyncio
async def test_send_group_jid_unchanged():
    """Group JIDs must not be normalised."""
    adapter = _make_adapter_for_send()

    captured_payloads = []

    def _capture_post(url, json=None, **kw):
        captured_payloads.append(json)
        return _FakeResp(200)

    adapter._http_session.post = MagicMock(side_effect=_capture_post)

    await adapter.send("120363012345678@g.us", "hello")

    assert captured_payloads[0]["chatId"] == "120363012345678@g.us"
