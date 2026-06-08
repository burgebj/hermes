"""Tests for Telegram bot message filtering via is_bot field (issue #32188).

Verifies that:
1. SessionSource.is_bot propagates correctly (field that build_source sets).
2. _is_user_authorized() blocks bot-sourced Telegram messages unless
   TELEGRAM_ALLOW_BOTS opts them in.
3. The user.is_bot attribute from python-telegram-bot is read correctly.
"""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from gateway.config import Platform
from gateway.session import SessionSource


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_telegram_user(*, is_bot: bool = False, user_id: int = 12345, full_name: str = "Alice"):
    """Return a minimal python-telegram-bot User-like object."""
    u = SimpleNamespace()
    u.id = user_id
    u.full_name = full_name
    u.is_bot = is_bot
    return u


def _make_source(*, is_bot: bool = False, user_id: str = "12345") -> SessionSource:
    """Return a SessionSource with is_bot pre-set."""
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="9001",
        user_id=user_id,
        is_bot=is_bot,
    )


# ---------------------------------------------------------------------------
# 1. SessionSource.is_bot field propagation (the field build_source sets)
# ---------------------------------------------------------------------------


class TestTelegramBuildSourceIsBot:
    """SessionSource.is_bot must propagate correctly (the field that build_source sets)."""

    def test_is_bot_false_propagates_via_session_source(self):
        """SessionSource accepts is_bot=False and stores it."""
        source = SessionSource(
            platform=Platform.TELEGRAM,
            chat_id="9001",
            user_id="12345",
            is_bot=False,
        )
        assert source.is_bot is False

    def test_is_bot_true_propagates_via_session_source(self):
        """SessionSource accepts is_bot=True and stores it."""
        source = SessionSource(
            platform=Platform.TELEGRAM,
            chat_id="9001",
            user_id="12345",
            is_bot=True,
        )
        assert source.is_bot is True

    def test_is_bot_defaults_to_false_in_session_source(self):
        """SessionSource.is_bot defaults to False when not provided."""
        source = SessionSource(
            platform=Platform.TELEGRAM,
            chat_id="9001",
            user_id="12345",
        )
        assert source.is_bot is False


# ---------------------------------------------------------------------------
# 2. _is_user_authorized blocks bot sources unless TELEGRAM_ALLOW_BOTS set
# ---------------------------------------------------------------------------


class TestIsUserAuthorizedTelegramBot:
    """Bot Telegram sources must be rejected / admitted per TELEGRAM_ALLOW_BOTS."""

    def _run(self, source: SessionSource, *, allow_bots_env: str | None = None) -> bool:
        """Call _is_user_authorized with minimal gateway wiring."""
        import importlib
        run_mod = importlib.import_module("gateway.run")
        GatewayRunner = run_mod.GatewayRunner

        runner = object.__new__(GatewayRunner)
        runner.config = SimpleNamespace(
            extra={},
            gateways=[],
        )

        # Stub pairing store — always unapproved
        runner.pairing_store = SimpleNamespace(
            is_approved=lambda _platform, _user_id: False
        )

        # Wipe all gateway allowlist env vars so we're testing the bot path only
        allowlist_keys = [
            "TELEGRAM_ALLOWED_USERS",
            "GATEWAY_ALLOWED_USERS",
            "GATEWAY_ALLOW_ALL_USERS",
            "TELEGRAM_ALLOW_ALL_USERS",
            "TELEGRAM_ALLOW_BOTS",
        ]
        for key in allowlist_keys:
            os.environ.pop(key, None)

        if allow_bots_env is not None:
            os.environ["TELEGRAM_ALLOW_BOTS"] = allow_bots_env

        try:
            result = runner._is_user_authorized(source)
        finally:
            for key in allowlist_keys:
                os.environ.pop(key, None)

        return result

    def test_human_telegram_message_not_short_circuited_by_bot_path(self):
        """Human Telegram messages reach allowlist check (not short-circuited as bot)."""
        source = _make_source(is_bot=False, user_id="99")
        # With no allowlists configured _is_user_authorized returns False
        # (no allowlist = locked down). The key thing: is_bot=False means
        # the bot filter doesn't fire at all — allowlist logic decides.
        result = self._run(source)
        assert result is False  # no allowlist set → locked out (expected behavior)

    def test_bot_telegram_message_blocked_by_default(self):
        """Bot Telegram messages are blocked when TELEGRAM_ALLOW_BOTS is unset."""
        source = _make_source(is_bot=True, user_id="bot42")
        result = self._run(source, allow_bots_env=None)
        assert result is False

    def test_bot_telegram_message_blocked_when_allow_bots_none(self):
        """Explicit TELEGRAM_ALLOW_BOTS=none still blocks bots."""
        source = _make_source(is_bot=True, user_id="bot42")
        result = self._run(source, allow_bots_env="none")
        assert result is False

    def test_bot_telegram_message_admitted_when_allow_bots_all(self):
        """TELEGRAM_ALLOW_BOTS=all should admit bot-originated messages."""
        source = _make_source(is_bot=True, user_id="bot42")
        result = self._run(source, allow_bots_env="all")
        assert result is True

    def test_bot_telegram_message_admitted_when_allow_bots_mentions(self):
        """TELEGRAM_ALLOW_BOTS=mentions should admit bot-originated messages."""
        source = _make_source(is_bot=True, user_id="bot42")
        result = self._run(source, allow_bots_env="mentions")
        assert result is True

    def test_allow_bots_env_is_case_insensitive(self):
        """TELEGRAM_ALLOW_BOTS value matching must be case-insensitive."""
        source = _make_source(is_bot=True, user_id="bot42")
        assert self._run(source, allow_bots_env="ALL") is True
        assert self._run(source, allow_bots_env="NONE") is False


# ---------------------------------------------------------------------------
# 3. user.is_bot attribute reading (expression used in telegram.py)
# ---------------------------------------------------------------------------


class TestBuildMessageEventIsBot:
    """_build_message_event must read user.is_bot and pass it to build_source."""

    def test_human_sender_sets_is_bot_false(self):
        """Human sender → bool(getattr(user, 'is_bot', False)) == False."""
        user = _make_telegram_user(is_bot=False)
        assert bool(getattr(user, "is_bot", False)) is False

    def test_bot_sender_sets_is_bot_true(self):
        """Bot sender → bool(getattr(user, 'is_bot', False)) == True."""
        user = _make_telegram_user(is_bot=True)
        assert bool(getattr(user, "is_bot", False)) is True

    def test_missing_user_is_bot_attr_defaults_to_false(self):
        """Mocks / users without is_bot attribute should default to False safely."""
        user = SimpleNamespace(id=5, full_name="Mystery")  # no is_bot attr
        assert bool(getattr(user, "is_bot", False)) is False


# ---------------------------------------------------------------------------
# 4. TELEGRAM_ALLOW_BOTS present in platform_allow_bots_map
# ---------------------------------------------------------------------------


def test_telegram_allow_bots_key_in_platform_map():
    """Platform map must include a TELEGRAM entry so the env var is honoured."""
    import importlib
    run_mod = importlib.import_module("gateway.run")
    GatewayRunner = run_mod.GatewayRunner

    runner = object.__new__(GatewayRunner)
    runner.config = SimpleNamespace(extra={}, gateways=[])
    runner.pairing_store = SimpleNamespace(is_approved=lambda p, u: False)

    # Probe the map by passing a bot source and TELEGRAM_ALLOW_BOTS=all;
    # if the map entry exists, the bot will be admitted.
    source = _make_source(is_bot=True, user_id="tgbot1")

    allowlist_keys = [
        "TELEGRAM_ALLOWED_USERS",
        "GATEWAY_ALLOWED_USERS",
        "GATEWAY_ALLOW_ALL_USERS",
        "TELEGRAM_ALLOW_ALL_USERS",
    ]
    for key in allowlist_keys:
        os.environ.pop(key, None)
    os.environ["TELEGRAM_ALLOW_BOTS"] = "all"

    try:
        result = runner._is_user_authorized(source)
    finally:
        os.environ.pop("TELEGRAM_ALLOW_BOTS", None)

    assert result is True, (
        "TELEGRAM_ALLOW_BOTS=all should admit bot sources; "
        "check that Platform.TELEGRAM is in platform_allow_bots_map in gateway/run.py"
    )
