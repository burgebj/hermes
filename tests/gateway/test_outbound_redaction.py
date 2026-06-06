"""Regression tests for #23810: outbound chat messages must be scrubbed
before delivery when ``HERMES_REDACT_SECRETS`` is on.

The gateway startup banner advertises "Secret redaction: ENABLED (tool
output, logs, and chat responses are scrubbed before delivery)", but
prior to the fix the outbound path in :class:`BasePlatformAdapter` had
no call to :func:`agent.redact.redact_sensitive_text`.  Only log records
(via ``RedactingFormatter``) and tool output (in ``gateway/run.py``)
were covered — the actual message bytes delivered to
Telegram/Discord/Slack were not.

These tests pin the contract that:

* :meth:`BasePlatformAdapter._send_with_retry` runs every outbound
  payload through :meth:`_redact_outbound` before calling
  :meth:`send`, so all retries and fallbacks inherit the scrubbed text.
* :meth:`_redact_outbound` honours the global toggle
  (``HERMES_REDACT_SECRETS`` / ``security.redact_secrets``) and is
  defensive against import / runtime errors so a redaction bug can
  never break delivery.
"""

import pytest
from unittest.mock import AsyncMock, patch

from gateway.platforms.base import BasePlatformAdapter, SendResult
from gateway.platforms.base import Platform, PlatformConfig


# ---------------------------------------------------------------------------
# Test fixture: minimal concrete adapter that records every send() call.
# Mirrors the pattern used by tests/gateway/test_send_retry.py so the two
# files exercise the same surface without duplicating wiring.
# ---------------------------------------------------------------------------


class _RecordingAdapter(BasePlatformAdapter):
    def __init__(self):
        super().__init__(PlatformConfig(), Platform.TELEGRAM)
        self._send_results: list[SendResult] = []
        self._send_calls: list[tuple[str, str]] = []

    def _next_result(self) -> SendResult:
        if self._send_results:
            return self._send_results.pop(0)
        return SendResult(success=True, message_id="ok")

    async def send(self, chat_id, content, reply_to=None, metadata=None, **kwargs) -> SendResult:
        self._send_calls.append((chat_id, content))
        return self._next_result()

    async def connect(self) -> bool:
        return True

    async def disconnect(self) -> None:
        pass

    async def send_typing(self, chat_id, metadata=None) -> None:
        pass

    async def get_chat_info(self, chat_id):
        return {"name": "test", "type": "direct", "chat_id": chat_id}


@pytest.fixture(autouse=True)
def _ensure_redaction_enabled(monkeypatch):
    """Force redaction ON for every test (and make it independent of any
    HERMES_REDACT_SECRETS that prior tests / CI may have set).

    Mirrors tests/agent/test_redact.py — clears the env var AND patches
    the module-level snapshot so import-time evaluation doesn't bleed
    through.
    """
    monkeypatch.delenv("HERMES_REDACT_SECRETS", raising=False)
    monkeypatch.setattr("agent.redact._REDACT_ENABLED", True)


# ---------------------------------------------------------------------------
# _redact_outbound — unit-level contract of the helper.
# ---------------------------------------------------------------------------


class TestRedactOutboundHelper:
    """The helper used by every outbound path must be safe to call on any input."""

    def test_none_passes_through(self):
        adapter = _RecordingAdapter()
        assert adapter._redact_outbound(None) is None

    def test_empty_passes_through(self):
        adapter = _RecordingAdapter()
        assert adapter._redact_outbound("") == ""

    def test_non_string_passes_through(self):
        # _send_with_retry only feeds strings, but defensive: a bogus int
        # must not raise — silent passthrough keeps delivery working
        # even if a caller upstream regresses.
        adapter = _RecordingAdapter()
        assert adapter._redact_outbound(12345) == 12345  # type: ignore[arg-type]

    def test_clean_text_unchanged(self):
        adapter = _RecordingAdapter()
        assert adapter._redact_outbound("hello world") == "hello world"

    def test_sk_token_is_masked(self):
        adapter = _RecordingAdapter()
        result = adapter._redact_outbound("api: sk-proj-abc123def456ghi789jkl012")
        assert "abc123def456" not in result
        assert "sk-pro" in result  # masking keeps the prefix for diagnostics

    def test_telegram_bot_token_is_masked(self):
        adapter = _RecordingAdapter()
        result = adapter._redact_outbound(
            "Your token is bot1234567890:AAH-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        )
        assert "AAH-xxxxxxxx" not in result
        assert ":***" in result

    def test_github_pat_is_masked(self):
        adapter = _RecordingAdapter()
        result = adapter._redact_outbound("see ghp_abc123def456ghi789jkl in audit log")
        assert "abc123def456" not in result

    def test_import_failure_returns_input(self):
        """If agent.redact ever fails to import (broken venv, partial
        install, etc.) the gateway must still deliver — silent
        passthrough is the correct fallback for a security helper that
        is OPT-IN ON by default, never load-bearing for delivery."""
        adapter = _RecordingAdapter()
        secret_text = "key sk-proj-abc123def456"
        with patch.dict("sys.modules", {"agent.redact": None}):
            # ImportError surfaces; helper must catch and passthrough.
            assert adapter._redact_outbound(secret_text) == secret_text

    def test_redaction_disabled_via_env(self, monkeypatch):
        """When the operator opts out via security.redact_secrets: false
        (bridged to HERMES_REDACT_SECRETS=false), outbound delivery
        passes through unchanged.  Honours the same toggle as logs and
        tool output so the security posture is consistent end-to-end."""
        monkeypatch.setattr("agent.redact._REDACT_ENABLED", False)
        adapter = _RecordingAdapter()
        text = "OPENAI_API_KEY=sk-proj-abc123def456ghi789jkl012"
        assert adapter._redact_outbound(text) == text


# ---------------------------------------------------------------------------
# _send_with_retry — end-to-end: secrets must be scrubbed before send().
# This is the actual bug from #23810: bot replied with token bodies verbatim.
# ---------------------------------------------------------------------------


class TestSendWithRetryRedactsBeforeDelivery:
    @pytest.mark.asyncio
    async def test_sk_token_scrubbed_on_first_send(self):
        """The bug repro from the issue body — an LLM-echoed sk- key
        must not reach :meth:`send` verbatim."""
        adapter = _RecordingAdapter()
        leaky = (
            "Here is the key you asked about: sk-proj-abc123def456ghi789jkl012"
        )

        await adapter._send_with_retry(chat_id="123", content=leaky)

        assert len(adapter._send_calls) == 1
        _, delivered = adapter._send_calls[0]
        assert "abc123def456" not in delivered
        assert "sk-pro" in delivered  # masked but identifiable

    @pytest.mark.asyncio
    async def test_telegram_bot_token_scrubbed(self):
        adapter = _RecordingAdapter()
        leaky = "bot1234567890:AAH-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx ready"

        await adapter._send_with_retry(chat_id="123", content=leaky)

        _, delivered = adapter._send_calls[0]
        assert "AAH-xxxxxxxx" not in delivered

    @pytest.mark.asyncio
    async def test_clean_text_unchanged_through_retry(self):
        """No false positives: a normal agent reply round-trips byte-
        for-byte."""
        adapter = _RecordingAdapter()
        clean = "All good — your file has been saved to /tmp/report.md."

        await adapter._send_with_retry(chat_id="123", content=clean)

        _, delivered = adapter._send_calls[0]
        assert delivered == clean

    @pytest.mark.asyncio
    async def test_redaction_happens_once_not_per_retry(self):
        """Retries must reuse the already-scrubbed payload — re-running
        the redactor per attempt would be redundant work and, more
        importantly, would mask the contract that scrubbing is a
        single canonical step at the top of the delivery pipeline.

        Verified by counting calls to ``redact_sensitive_text`` via
        the helper: one network failure + retry = one redaction."""
        adapter = _RecordingAdapter()
        # First attempt: retryable network failure.
        # Second attempt: success.
        adapter._send_results = [
            SendResult(success=False, error="httpx.ConnectError: dropped", retryable=True),
            SendResult(success=True, message_id="ok"),
        ]

        with patch.object(
            adapter, "_redact_outbound", wraps=adapter._redact_outbound
        ) as wrapped:
            # Tight backoff so the test runs fast — the retry path
            # would otherwise sleep 2s+jitter between attempts.
            await adapter._send_with_retry(
                chat_id="123",
                content="sk-proj-abc123def456ghi789jkl012",
                base_delay=0.001,
            )

        assert wrapped.call_count == 1, (
            "Redaction must run exactly once at the top of _send_with_retry, "
            "not per attempt"
        )
        # Both attempts saw the SAME (already-redacted) content.
        assert len(adapter._send_calls) == 2
        first = adapter._send_calls[0][1]
        second = adapter._send_calls[1][1]
        assert first == second
        assert "abc123def456" not in first

    @pytest.mark.asyncio
    async def test_plain_text_fallback_uses_redacted_content(self):
        """When the first send fails with a non-retryable formatting
        error, ``_send_with_retry`` re-sends a plain-text fallback
        prefixed with a "(Response formatting failed, plain text:)"
        notice.  That fallback wraps the SAME ``content`` variable that
        the top-of-function redaction already scrubbed, so the secret
        must not reappear in the fallback body."""
        adapter = _RecordingAdapter()
        adapter._send_results = [
            SendResult(success=False, error="Bad Request: can't parse entities", retryable=False),
            SendResult(success=True, message_id="ok"),
        ]
        leaky = "Markdown failed sk-proj-abc123def456ghi789jkl012 here."

        result = await adapter._send_with_retry(chat_id="123", content=leaky)

        assert result.success
        assert len(adapter._send_calls) == 2
        first = adapter._send_calls[0][1]
        fallback = adapter._send_calls[1][1]
        assert "abc123def456" not in first
        assert "abc123def456" not in fallback
        assert "plain text" in fallback.lower()

    @pytest.mark.asyncio
    async def test_disabled_redaction_lets_secrets_through(self, monkeypatch):
        """Defence in depth shouldn't gate user intent: an operator
        who explicitly opts out via ``security.redact_secrets: false``
        (e.g. an internal Slack DM that ships raw provider responses
        for debugging) must still see verbatim text downstream.

        This is the same end-to-end contract that ``tool output`` and
        ``logs`` already honour — the three surfaces share one toggle."""
        monkeypatch.setattr("agent.redact._REDACT_ENABLED", False)
        adapter = _RecordingAdapter()
        leaky = "sk-proj-abc123def456ghi789jkl012"

        await adapter._send_with_retry(chat_id="123", content=leaky)

        _, delivered = adapter._send_calls[0]
        assert delivered == leaky

    @pytest.mark.asyncio
    async def test_delivery_failure_notice_does_not_leak_original(self):
        """When all retries are exhausted the adapter sends a separate
        "delivery failed" notice via :meth:`send`.  That notice is
        composed by the adapter itself and must not include any
        scrubbed-but-still-reflected echo of the leaky body — verified
        by checking that the notice text contains the canonical
        delivery-failure string and no token fragment."""
        adapter = _RecordingAdapter()
        # First attempt + max_retries=2 retries: all retryable network failures.
        retryable = SendResult(success=False, error="ConnectError: nope", retryable=True)
        adapter._send_results = [retryable, retryable, retryable, SendResult(success=True, message_id="notice")]
        leaky = "key sk-proj-abc123def456ghi789jkl012"

        result = await adapter._send_with_retry(
            chat_id="123", content=leaky, base_delay=0.001
        )

        # Final result is the LAST failed retry, not the notice.
        assert not result.success
        # The notice is the final send call.
        assert len(adapter._send_calls) == 4
        notice = adapter._send_calls[-1][1]
        assert "delivery failed" in notice.lower()
        assert "abc123def456" not in notice
