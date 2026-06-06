"""Regression coverage for #29005 — platform adapters silently stop
when their internal reconnect ladder exhausts, leaving the gateway
process alive but the bot permanently dead.

The fix has two halves:

* **QQBot (P0)** — three ``MAX_RECONNECT_ATTEMPTS`` exit paths in
  ``QQAdapter._listen_loop`` swapped ``_mark_disconnected()`` for
  ``_set_fatal_error(..., retryable=True)`` + ``await
  _notify_fatal_error()``, so the gateway's
  ``_platform_reconnect_watcher`` actually re-queues the platform
  for background reconnection.

* **Telegram (P1)** — ``_handle_polling_network_error`` now writes
  ``platform_state="retrying"`` to the runtime status file before
  each back-off sleep (was: status stayed ``connected`` for the
  full ~55-min retry window) and ``"connected"`` again on
  successful reconnect.

These tests exercise each half at the adapter level — no real
network, no real WebSocket — so they're hermetic and stay under a
couple of seconds.
"""
from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Shared scaffolding
# ---------------------------------------------------------------------------


def _ensure_telegram_mock():
    """Telegram's PTB dependency is optional; stub the surface we touch
    so import doesn't pull the real package on minimal test installs."""
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return

    telegram_mod = MagicMock()
    telegram_mod.ext.ContextTypes.DEFAULT_TYPE = type(None)
    telegram_mod.constants.ParseMode.MARKDOWN_V2 = "MarkdownV2"
    telegram_mod.constants.ChatType.GROUP = "group"
    telegram_mod.constants.ChatType.SUPERGROUP = "supergroup"
    telegram_mod.constants.ChatType.CHANNEL = "channel"
    telegram_mod.constants.ChatType.PRIVATE = "private"
    for name in ("telegram", "telegram.ext", "telegram.constants", "telegram.request"):
        sys.modules.setdefault(name, telegram_mod)


_ensure_telegram_mock()


# ===========================================================================
# QQBot — reconnect exhaustion must notify the gateway watcher
# ===========================================================================


class TestQQBotReconnectExhaustionNotifies:
    """All three ``MAX_RECONNECT_ATTEMPTS`` exits in ``_listen_loop``
    must fire ``_notify_fatal_error`` so ``_platform_reconnect_watcher``
    can re-queue the platform.  A bare ``_mark_disconnected()`` (the
    pre-fix behaviour) lets the listener task die in silence.

    Rather than driving the full ``_listen_loop`` (which would need a
    fake WebSocket + heartbeat plumbing), we set up the same end-state
    each branch reaches — ``backoff_idx >= MAX_RECONNECT_ATTEMPTS`` —
    and assert the helper that runs at that point routes through the
    fatal-error escalation.
    """

    def _make_adapter(self):
        from gateway.config import PlatformConfig
        from gateway.platforms.qqbot import QQAdapter

        adapter = QQAdapter(PlatformConfig(enabled=True, extra={
            "app_id": "test-app",
            "client_secret": "test-secret",
        }))
        # Replace status-file write with a no-op recorder so we can
        # assert without touching the real ~/.hermes status dir.
        adapter._write_runtime_status_safe = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_set_fatal_error_runs_handler_with_retryable(self):
        """``_set_fatal_error(retryable=True)`` + ``_notify_fatal_error``
        must invoke the gateway-registered handler with the same
        ``retryable`` flag the watcher branches on."""
        adapter = self._make_adapter()
        handler = AsyncMock()
        adapter.set_fatal_error_handler(handler)

        adapter._set_fatal_error(
            "qq_reconnect_exhausted",
            "WebSocket reconnect exhausted after 100 attempts",
            retryable=True,
        )
        await adapter._notify_fatal_error()

        handler.assert_awaited_once()
        called_with = handler.await_args.args[0]
        assert called_with is adapter
        assert adapter.fatal_error_code == "qq_reconnect_exhausted"
        assert adapter.fatal_error_retryable is True
        assert "100 attempts" in (adapter.fatal_error_message or "")

    def test_exhaustion_paths_use_set_fatal_error_not_mark_disconnected(self):
        """Static guard: the three ``MAX_RECONNECT_ATTEMPTS`` exit
        sites in ``_listen_loop`` must invoke ``_set_fatal_error`` and
        ``_notify_fatal_error``.  A future refactor that drops one of
        the escalations and falls back to ``_mark_disconnected()`` —
        the pre-#29005 behaviour — would re-open the bug.
        """
        import inspect

        from gateway.platforms.qqbot import adapter as qq_adapter_mod

        src = inspect.getsource(qq_adapter_mod.QQAdapter._listen_loop)
        # Three exhaustion sites → at least three fatal-error
        # escalations, each paired with a notify.
        assert src.count("_set_fatal_error(") >= 3, (
            "Expected at least 3 _set_fatal_error() calls in "
            "_listen_loop (rate-limit, QQCloseError, generic Exception); "
            "found only %d.  Reverting any exhaustion site to "
            "_mark_disconnected() re-opens #29005." % src.count("_set_fatal_error(")
        )
        assert src.count("_notify_fatal_error()") >= 3, (
            "Every fatal-error escalation on the exhaustion path must "
            "be followed by `await self._notify_fatal_error()` so the "
            "gateway watcher actually picks the platform up (#29005)."
        )
        # The exhaustion error code is shared across the three sites
        # for easy log greps.
        assert "qq_reconnect_exhausted" in src

    @pytest.mark.asyncio
    async def test_notify_fatal_error_noop_without_handler(self):
        """Adapters started outside a GatewayRunner (CLI smoke tests,
        local debug) must not crash when no handler is registered."""
        adapter = self._make_adapter()
        # No handler set; should silently return.
        adapter._set_fatal_error("qq_reconnect_exhausted", "x", retryable=True)
        await adapter._notify_fatal_error()  # must not raise


# ===========================================================================
# Telegram — retry window must surface as platform_state=retrying
# ===========================================================================


class TestTelegramPollingRetryStatus:
    """``_handle_polling_network_error`` must mark the runtime status
    ``retrying`` *during* the back-off window (not just at the final
    fatal-error step) so external monitors can detect degraded
    connectivity earlier.  On successful reconnect it must flip back
    to ``connected``.
    """

    def _make_adapter(self):
        from gateway.config import PlatformConfig
        from gateway.platforms.telegram import TelegramAdapter

        adapter = TelegramAdapter(PlatformConfig(enabled=True, token="test-token"))
        # Record every status write so we can assert ordering.
        adapter._write_runtime_status_safe = MagicMock()
        return adapter

    @pytest.mark.asyncio
    async def test_retry_window_writes_retrying_state(self):
        """Any non-final attempt (1..MAX_NETWORK_RETRIES) must emit a
        ``platform_state=retrying`` write before sleeping — that's the
        window external monitors were blind to (#29005)."""
        adapter = self._make_adapter()
        adapter._polling_network_error_count = 0  # → attempt 1 after increment

        mock_updater = MagicMock()
        mock_updater.running = True
        mock_updater.stop = AsyncMock()
        mock_updater.start_polling = AsyncMock()  # success path
        mock_app = MagicMock()
        mock_app.updater = mock_updater
        mock_app.bot.get_me = AsyncMock()
        adapter._app = mock_app

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await adapter._handle_polling_network_error(RuntimeError("connection reset"))

        writes = [call.kwargs for call in adapter._write_runtime_status_safe.call_args_list]
        states = [w.get("platform_state") for w in writes]
        assert "retrying" in states, (
            "Expected platform_state=retrying during the back-off window; "
            "got writes: %r" % writes
        )

    @pytest.mark.asyncio
    async def test_retrying_write_carries_diagnostic_message(self):
        """The retrying write must include the attempt counter so
        operators can tell *which* attempt is in flight from the
        runtime status payload alone."""
        adapter = self._make_adapter()
        adapter._polling_network_error_count = 2  # → attempt 3 after increment

        mock_updater = MagicMock()
        mock_updater.running = True
        mock_updater.stop = AsyncMock()
        mock_updater.start_polling = AsyncMock(side_effect=Exception("still bad"))
        mock_app = MagicMock()
        mock_app.updater = mock_updater
        adapter._app = mock_app

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await adapter._handle_polling_network_error(RuntimeError("dns failed"))

        retrying_writes = [
            call.kwargs
            for call in adapter._write_runtime_status_safe.call_args_list
            if call.kwargs.get("platform_state") == "retrying"
        ]
        assert retrying_writes, "expected at least one retrying write"
        msg = retrying_writes[0].get("error_message", "")
        assert "3/10" in msg, (
            f"expected attempt counter '3/10' in error_message; got {msg!r}"
        )
        assert retrying_writes[0].get("error_code") == "telegram_network_error"

        # Clean up the self-rescheduled retry task to keep pytest tidy.
        for t in list(adapter._background_tasks):
            t.cancel()

    @pytest.mark.asyncio
    async def test_successful_reconnect_flips_state_back_to_connected(self):
        """When start_polling succeeds, the next status write must
        clear the retrying state so external monitors stop alerting."""
        adapter = self._make_adapter()
        adapter._polling_network_error_count = 0

        mock_updater = MagicMock()
        mock_updater.running = True
        mock_updater.stop = AsyncMock()
        mock_updater.start_polling = AsyncMock()  # success
        mock_app = MagicMock()
        mock_app.updater = mock_updater
        mock_app.bot.get_me = AsyncMock()
        adapter._app = mock_app

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await adapter._handle_polling_network_error(RuntimeError("blip"))

        states = [
            call.kwargs.get("platform_state")
            for call in adapter._write_runtime_status_safe.call_args_list
        ]
        # Both transitions must be present, retrying BEFORE connected.
        assert "retrying" in states
        assert "connected" in states
        assert states.index("retrying") < states.index("connected"), (
            "retrying state must be written before the connected state "
            f"on a successful reconnect; got {states!r}"
        )

        # Background heartbeat probe gets scheduled — cancel so it
        # doesn't run after the test.
        for t in list(adapter._background_tasks):
            t.cancel()

    @pytest.mark.asyncio
    async def test_final_attempt_still_escalates_to_fatal(self):
        """The new retrying-status writes must not change the existing
        contract that attempt MAX_NETWORK_RETRIES+1 calls
        ``_set_fatal_error`` + ``_notify_fatal_error`` so the gateway
        watcher takes over.  No regression for #3173."""
        adapter = self._make_adapter()
        # MAX_NETWORK_RETRIES is 10; pushing the counter to 10 makes
        # the next increment → 11 → escalation branch.
        adapter._polling_network_error_count = 10
        handler = AsyncMock()
        adapter.set_fatal_error_handler(handler)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await adapter._handle_polling_network_error(RuntimeError("final"))

        assert adapter.fatal_error_code == "telegram_network_error"
        assert adapter.fatal_error_retryable is True
        handler.assert_awaited_once()
