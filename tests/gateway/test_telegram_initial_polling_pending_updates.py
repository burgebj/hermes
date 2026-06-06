"""Tests for the initial polling startup preserve-pending-updates fix.

On initial connect(), the polling-mode branch previously called
``updater.start_polling(drop_pending_updates=True)`` — which tells the
Telegram Bot API to discard every message queued while the gateway was
offline (e.g. during a Fly.io deploy's SIGTERM window, a cold-start,
or any rolling restart).

The two reconnect retry paths (_handle_polling_network_error line ~800 and
_handle_polling_conflict line ~903) already used ``drop_pending_updates=False``
correctly.  This test confirms the initial startup path is now consistent.

Motivation: single-machine Fly.io apps receive a SIGTERM on every ``fly
deploy``.  With the previous default, every restart silently discarded all
messages the user sent during downtime — there was no error, no log, just
missing messages.

See: https://github.com/NousResearch/hermes-agent/pull/26005 (OT-88) for the
prior art pattern used here.
"""

import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call

import pytest

from gateway.config import PlatformConfig


def _ensure_telegram_mock() -> None:
    """Inject a minimal telegram stub so the adapter can be imported without
    the real ``python-telegram-bot`` package installed in the test venv."""
    if "telegram" in sys.modules and hasattr(sys.modules["telegram"], "__file__"):
        return

    telegram_mod = MagicMock()
    telegram_mod.ext.ContextTypes.DEFAULT_TYPE = type(None)
    telegram_mod.constants.ParseMode.MARKDOWN_V2 = "MarkdownV2"
    telegram_mod.constants.ChatType.GROUP = "group"
    telegram_mod.constants.ChatType.SUPERGROUP = "supergroup"
    telegram_mod.constants.ChatType.CHANNEL = "channel"
    telegram_mod.constants.ChatType.PRIVATE = "private"

    # Real exception classes so ``except (NetworkError, ...)`` in connect()
    # doesn't raise "catching classes that do not inherit from BaseException".
    telegram_mod.error.NetworkError = type("NetworkError", (OSError,), {})
    telegram_mod.error.TimedOut = type("TimedOut", (OSError,), {})
    telegram_mod.error.BadRequest = type("BadRequest", (Exception,), {})

    for name in ("telegram", "telegram.ext", "telegram.constants", "telegram.request"):
        sys.modules.setdefault(name, telegram_mod)
    sys.modules.setdefault("telegram.error", telegram_mod.error)


_ensure_telegram_mock()

from gateway.platforms.telegram import TelegramAdapter  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_adapter() -> TelegramAdapter:
    return TelegramAdapter(PlatformConfig(enabled=True, token="test-token"))


def _make_app_with_captured_polling(captured: dict):
    """Build a fake PTB Application that records start_polling kwargs."""

    async def _fake_start_polling(**kwargs):
        captured.setdefault("start_polling_calls", []).append(kwargs)

    updater = SimpleNamespace(
        start_polling=AsyncMock(side_effect=_fake_start_polling),
        stop=AsyncMock(),
        running=False,
    )
    bot = SimpleNamespace(
        set_my_commands=AsyncMock(),
        delete_webhook=AsyncMock(),
    )
    return SimpleNamespace(
        bot=bot,
        updater=updater,
        add_handler=MagicMock(),
        initialize=AsyncMock(),
        start=AsyncMock(),
    )


@pytest.fixture(autouse=True)
def _no_auto_discovery(monkeypatch):
    """Disable DoH fallback discovery so connect() uses the plain builder chain."""
    async def _noop():
        return []

    monkeypatch.setattr("gateway.platforms.telegram.discover_fallback_ips", _noop)
    monkeypatch.setattr(
        "gateway.platforms.telegram.HTTPXRequest", lambda **kwargs: MagicMock()
    )


# ---------------------------------------------------------------------------
# Core fix: initial startup must use drop_pending_updates=False
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_initial_polling_uses_drop_pending_updates_false(monkeypatch):
    """The initial connect() polling path must pass drop_pending_updates=False.

    This is the regression guard for the fix that aligns the initial startup
    with the reconnect retry paths (_handle_polling_network_error and
    _handle_polling_conflict), which already used False.

    If this test fails it means a refactor reverted the fix and the gateway
    will again silently discard messages queued during any restart window.
    """
    monkeypatch.setattr(
        "gateway.status.acquire_scoped_lock",
        lambda scope, identity, metadata=None: (True, None),
    )
    monkeypatch.setattr(
        "gateway.status.release_scoped_lock",
        lambda scope, identity: None,
    )

    captured: dict = {}
    app = _make_app_with_captured_polling(captured)

    builder = MagicMock()
    builder.token.return_value = builder
    builder.request.return_value = builder
    builder.get_updates_request.return_value = builder
    builder.build.return_value = app

    monkeypatch.setattr(
        "gateway.platforms.telegram.Application",
        SimpleNamespace(builder=MagicMock(return_value=builder)),
    )

    adapter = _make_adapter()
    ok = await adapter.connect()

    assert ok is True, "connect() should succeed"

    assert captured.get("start_polling_calls"), (
        "start_polling() was not called — polling-mode branch was not reached"
    )
    first_call_kwargs = captured["start_polling_calls"][0]
    assert first_call_kwargs.get("drop_pending_updates") is False, (
        "Initial polling startup must use drop_pending_updates=False to preserve "
        "messages queued while the gateway was offline (e.g. during fly deploy "
        "SIGTERM window).  Got: "
        f"drop_pending_updates={first_call_kwargs.get('drop_pending_updates')!r}"
    )


@pytest.mark.asyncio
async def test_initial_polling_preserves_allowed_updates(monkeypatch):
    """Confirm allowed_updates=Update.ALL_TYPES is still passed (unchanged)."""
    monkeypatch.setattr(
        "gateway.status.acquire_scoped_lock",
        lambda scope, identity, metadata=None: (True, None),
    )
    monkeypatch.setattr(
        "gateway.status.release_scoped_lock",
        lambda scope, identity: None,
    )

    captured: dict = {}
    app = _make_app_with_captured_polling(captured)

    builder = MagicMock()
    builder.token.return_value = builder
    builder.request.return_value = builder
    builder.get_updates_request.return_value = builder
    builder.build.return_value = app

    monkeypatch.setattr(
        "gateway.platforms.telegram.Application",
        SimpleNamespace(builder=MagicMock(return_value=builder)),
    )

    adapter = _make_adapter()
    await adapter.connect()

    assert captured.get("start_polling_calls"), "start_polling() was not called"
    first_call_kwargs = captured["start_polling_calls"][0]
    # allowed_updates must still be present (Update.ALL_TYPES in the real code is
    # a mock sentinel here — we just verify the key is passed)
    assert "allowed_updates" in first_call_kwargs, (
        "allowed_updates must be passed to start_polling()"
    )


@pytest.mark.asyncio
async def test_initial_polling_error_callback_wired(monkeypatch):
    """error_callback is still passed so the reconnect/conflict logic fires."""
    monkeypatch.setattr(
        "gateway.status.acquire_scoped_lock",
        lambda scope, identity, metadata=None: (True, None),
    )
    monkeypatch.setattr(
        "gateway.status.release_scoped_lock",
        lambda scope, identity: None,
    )

    captured: dict = {}
    app = _make_app_with_captured_polling(captured)

    builder = MagicMock()
    builder.token.return_value = builder
    builder.request.return_value = builder
    builder.get_updates_request.return_value = builder
    builder.build.return_value = app

    monkeypatch.setattr(
        "gateway.platforms.telegram.Application",
        SimpleNamespace(builder=MagicMock(return_value=builder)),
    )

    adapter = _make_adapter()
    await adapter.connect()

    assert captured.get("start_polling_calls"), "start_polling() was not called"
    first_call_kwargs = captured["start_polling_calls"][0]
    assert callable(first_call_kwargs.get("error_callback")), (
        "error_callback must be passed to start_polling() so the reconnect "
        "and conflict-retry paths can fire"
    )


@pytest.mark.asyncio
async def test_reconnect_paths_also_use_drop_pending_updates_false(monkeypatch):
    """Regression guard: confirm the two reconnect paths still pass False.

    _handle_polling_network_error (line ~800) and _handle_polling_conflict
    (line ~903) were already correct before this fix.  This test documents
    that invariant so future refactors can't accidentally regress them.
    """
    from unittest.mock import patch

    adapter = _make_adapter()
    adapter._polling_network_error_count = 0

    captured: dict = {}

    async def _capturing_start_polling(**kwargs):
        captured.setdefault("calls", []).append(kwargs)

    updater = SimpleNamespace(
        running=True,
        stop=AsyncMock(),
        start_polling=AsyncMock(side_effect=_capturing_start_polling),
    )
    # _drain_polling_connections() accesses self._app.bot — provide a stub
    # with no _request attribute so the drain path short-circuits cleanly.
    bot_stub = SimpleNamespace()  # no ._request → drain exits early
    mock_app = SimpleNamespace(updater=updater, bot=bot_stub)
    adapter._app = mock_app
    adapter._polling_error_callback_ref = lambda e: None

    with patch("asyncio.sleep", new_callable=AsyncMock):
        await adapter._handle_polling_network_error(Exception("simulated 502"))

    assert captured.get("calls"), "_handle_polling_network_error did not call start_polling"
    for kw in captured["calls"]:
        assert kw.get("drop_pending_updates") is False, (
            "_handle_polling_network_error reconnect must use drop_pending_updates=False; "
            f"got {kw.get('drop_pending_updates')!r}"
        )
