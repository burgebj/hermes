"""Tests for Telegram adapter fail-closed auth fallback (#24457).

The _is_callback_user_authorized fallback must deny users by default
when TELEGRAM_ALLOWED_USERS is empty, instead of allowing everyone.
"""

import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from gateway.config import PlatformConfig, Platform
from gateway.platforms.base import MessageType


# -- Fake telegram modules (minimal stubs) --------------------------------

_fake_telegram_error = types.ModuleType("telegram.error")


class _TelegramError(Exception):
    pass


_fake_telegram_error.TelegramError = _TelegramError
_fake_telegram_error.BadRequest = type("BadRequest", (_TelegramError,), {})
_fake_telegram_error.NetworkError = type("NetworkError", (_TelegramError,), {})

_fake_telegram_constants = types.ModuleType("telegram.constants")
_fake_telegram_constants.ParseMode = SimpleNamespace(HTML="HTML")

_fake_telegram_request = types.ModuleType("telegram.request")
_fake_telegram_request.HTTPXRequest = type("HTTPXRequest", (), {"__init__": lambda *a, **kw: None})

_fake_telegram_ext = types.ModuleType("telegram.ext")
_fake_telegram_ext.ApplicationBuilder = type("ApplicationBuilder", (), {
    "token": lambda self, *a: self,
    "build": lambda self: None,
})

_fake_telegram = types.ModuleType("telegram")
_fake_telegram.error = _fake_telegram_error
_fake_telegram.constants = _fake_telegram_constants
_fake_telegram.ext = _fake_telegram_ext
_fake_telegram.request = _fake_telegram_request


@pytest.fixture(autouse=True)
def _inject_fake_telegram(monkeypatch):
    monkeypatch.setitem(sys.modules, "telegram", _fake_telegram)
    monkeypatch.setitem(sys.modules, "telegram.error", _fake_telegram_error)
    monkeypatch.setitem(sys.modules, "telegram.constants", _fake_telegram_constants)
    monkeypatch.setitem(sys.modules, "telegram.ext", _fake_telegram_ext)
    monkeypatch.setitem(sys.modules, "telegram.request", _fake_telegram_request)


def _make_adapter():
    from gateway.platforms.telegram import TelegramAdapter

    config = PlatformConfig(enabled=True, token="fake-token")
    adapter = object.__new__(TelegramAdapter)
    adapter.config = config
    adapter._config = config
    adapter._platform = Platform.TELEGRAM
    adapter._connected = True
    return adapter


class TestCallbackAuthFailClosed:
    """_is_callback_user_authorized fallback must be fail-closed."""

    def test_no_allowlist_no_allow_all_denies(self, monkeypatch):
        """No TELEGRAM_ALLOWED_USERS and no GATEWAY_ALLOW_ALL_USERS → deny."""
        monkeypatch.delenv("TELEGRAM_ALLOWED_USERS", raising=False)
        monkeypatch.delenv("GATEWAY_ALLOW_ALL_USERS", raising=False)
        adapter = _make_adapter()
        # Force the fallback path (no runner auth)
        adapter._message_handler = None
        assert adapter._is_callback_user_authorized("12345") is False

    def test_no_allowlist_with_global_allow_all_permits(self, monkeypatch):
        """No TELEGRAM_ALLOWED_USERS but GATEWAY_ALLOW_ALL_USERS=true → allow."""
        monkeypatch.delenv("TELEGRAM_ALLOWED_USERS", raising=False)
        monkeypatch.setenv("GATEWAY_ALLOW_ALL_USERS", "true")
        adapter = _make_adapter()
        adapter._message_handler = None
        assert adapter._is_callback_user_authorized("12345") is True

    def test_allowlist_with_matching_user_permits(self, monkeypatch):
        """TELEGRAM_ALLOWED_USERS contains the user → allow."""
        monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "12345,67890")
        adapter = _make_adapter()
        adapter._message_handler = None
        assert adapter._is_callback_user_authorized("12345") is True

    def test_allowlist_without_matching_user_denies(self, monkeypatch):
        """TELEGRAM_ALLOWED_USERS does not contain the user → deny."""
        monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "67890")
        adapter = _make_adapter()
        adapter._message_handler = None
        assert adapter._is_callback_user_authorized("12345") is False

    def test_allowlist_wildcard_permits(self, monkeypatch):
        """TELEGRAM_ALLOWED_USERS=* → allow everyone."""
        monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "*")
        adapter = _make_adapter()
        adapter._message_handler = None
        assert adapter._is_callback_user_authorized("12345") is True


def _make_message(
    text: str = "inject me",
    *,
    user_id: int = 12345,
    chat_id: int = 999,
    chat_type: str = "private",
    location=None,
    venue=None,
):
    return SimpleNamespace(
        text=text,
        caption=None,
        message_id=7,
        message_thread_id=None,
        chat=SimpleNamespace(
            id=chat_id,
            type=chat_type,
            title=None,
            full_name="Sender Chat",
            is_forum=False,
        ),
        from_user=SimpleNamespace(id=user_id, full_name="Sender User"),
        location=location,
        venue=venue,
        sticker=None,
        photo=None,
        video=None,
        audio=None,
        voice=None,
        document=None,
        media_group_id=None,
    )


class _Runner:
    def __init__(self, authorized: bool = True, *, raises: bool = False):
        self.authorized = authorized
        self.raises = raises

    def _is_user_authorized(self, _source):
        if self.raises:
            raise RuntimeError("auth backend unavailable")
        return self.authorized

    async def _handle_message(self, _event):
        raise AssertionError("test should not call runner directly")


def _event(text: str = "event text", message_type=None):
    return SimpleNamespace(
        text=text,
        message_type=message_type,
        media_urls=[],
        media_types=[],
    )


class TestMessageAuthBeforeEventConstruction:
    """Telegram messages from unauthorized users must be dropped at intake."""

    @pytest.mark.asyncio
    async def test_text_message_rejects_before_trigger_gating_event_building_and_batching(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=False)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._build_message_event = Mock()
        adapter._enqueue_text_event = Mock()

        update = SimpleNamespace(
            update_id=42,
            message=_make_message(),
            effective_message=None,
        )

        await adapter._handle_text_message(update, SimpleNamespace())

        adapter._should_process_message.assert_not_called()
        adapter._build_message_event.assert_not_called()
        adapter._enqueue_text_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_command_message_rejects_before_event_building(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=False)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._ensure_forum_commands = AsyncMock()
        adapter._build_message_event = Mock()

        update = SimpleNamespace(
            update_id=43,
            message=_make_message("/new"),
            effective_message=None,
        )

        await adapter._handle_command(update, SimpleNamespace())

        adapter._should_process_message.assert_not_called()
        adapter._ensure_forum_commands.assert_not_awaited()
        adapter._build_message_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_location_message_rejects_before_event_building(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=False)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._build_message_event = Mock()

        update = SimpleNamespace(
            update_id=44,
            message=_make_message(location=SimpleNamespace(latitude=1.0, longitude=2.0)),
            effective_message=None,
        )

        await adapter._handle_location_message(update, SimpleNamespace())

        adapter._should_process_message.assert_not_called()
        adapter._build_message_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_media_message_rejects_before_event_building(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=False)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._build_message_event = Mock()

        await adapter._handle_media_message(
            SimpleNamespace(update_id=45, message=_make_message()),
            SimpleNamespace(),
        )

        adapter._should_process_message.assert_not_called()
        adapter._build_message_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_auth_exception_fails_closed_before_event_building(self):
        adapter = _make_adapter()
        runner = _Runner(raises=True)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._build_message_event = Mock()

        await adapter._handle_text_message(
            SimpleNamespace(update_id=46, message=_make_message(), effective_message=None),
            SimpleNamespace(),
        )

        adapter._should_process_message.assert_not_called()
        adapter._build_message_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_unauthorized_unmentioned_group_message_is_not_observed(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=False)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=False)
        adapter._should_observe_unmentioned_group_message = Mock(return_value=True)
        adapter._observe_unmentioned_group_message = Mock()

        update = SimpleNamespace(
            update_id=47,
            message=_make_message(
                "side chatter",
                chat_id=-100,
                chat_type="supergroup",
            ),
            effective_message=None,
        )

        await adapter._handle_text_message(update, SimpleNamespace())

        adapter._should_process_message.assert_not_called()
        adapter._should_observe_unmentioned_group_message.assert_not_called()
        adapter._observe_unmentioned_group_message.assert_not_called()

    @pytest.mark.asyncio
    async def test_authorized_text_message_reaches_batching(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=True)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._ensure_forum_commands = AsyncMock()
        adapter._build_message_event = Mock(return_value=_event("hello"))
        adapter._clean_bot_trigger_text = Mock(return_value="hello")
        adapter._apply_telegram_group_observe_attribution = Mock(side_effect=lambda event: event)
        adapter._enqueue_text_event = Mock()

        await adapter._handle_text_message(
            SimpleNamespace(update_id=48, message=_make_message("hello"), effective_message=None),
            SimpleNamespace(),
        )

        adapter._should_process_message.assert_called_once()
        adapter._build_message_event.assert_called_once()
        adapter._enqueue_text_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_authorized_command_message_reaches_dispatch(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=True)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._ensure_forum_commands = AsyncMock()
        adapter._build_message_event = Mock(return_value=_event("/new"))
        adapter._clean_bot_trigger_text = Mock(return_value="/new")
        adapter._apply_telegram_group_observe_attribution = Mock(side_effect=lambda event: event)
        adapter.handle_message = AsyncMock()

        await adapter._handle_command(
            SimpleNamespace(update_id=49, message=_make_message("/new"), effective_message=None),
            SimpleNamespace(),
        )

        adapter._should_process_message.assert_called_once()
        adapter._ensure_forum_commands.assert_awaited_once()
        adapter._build_message_event.assert_called_once()
        adapter.handle_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_authorized_location_message_reaches_dispatch(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=True)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._build_message_event = Mock(return_value=_event(""))
        adapter._apply_telegram_group_observe_attribution = Mock(side_effect=lambda event: event)
        adapter.handle_message = AsyncMock()

        await adapter._handle_location_message(
            SimpleNamespace(
                update_id=50,
                message=_make_message(location=SimpleNamespace(latitude=1.0, longitude=2.0)),
                effective_message=None,
            ),
            SimpleNamespace(),
        )

        adapter._should_process_message.assert_called_once()
        adapter._build_message_event.assert_called_once()
        adapter.handle_message.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_authorized_media_message_reaches_dispatch(self):
        adapter = _make_adapter()
        runner = _Runner(authorized=True)
        adapter._message_handler = runner._handle_message
        adapter._should_process_message = Mock(return_value=True)
        adapter._build_message_event = Mock(return_value=_event("", MessageType.DOCUMENT))
        adapter.handle_message = AsyncMock()

        await adapter._handle_media_message(
            SimpleNamespace(update_id=51, message=_make_message()),
            SimpleNamespace(),
        )

        adapter._should_process_message.assert_called_once()
        adapter._build_message_event.assert_called_once()
        adapter.handle_message.assert_awaited_once()
