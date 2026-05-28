"""Regression guard for #32188: Telegram bot messages must honor TELEGRAM_ALLOW_BOTS.

The bug had two halves that combined to silently bypass the bot filter:

  Half 1 — gateway/platforms/telegram.py never passed PTB's
  ``message.from_user.is_bot`` into ``build_source(...)``, so the resulting
  ``SessionSource.is_bot`` was always ``False`` even when the sender was
  another bot. The ``_is_user_authorized`` bot-bypass branch keys off
  ``source.is_bot``, so the policy was never evaluated.

  Half 2 — ``platform_allow_bots_map`` in gateway/run.py only had entries
  for Discord and Feishu. Even with ``is_bot`` correctly set, Telegram had
  no env var wired up, so operators had no way to admit or exclude bot
  traffic.

These tests pin both halves: the adapter now propagates ``is_bot`` from
PTB, and ``_is_user_authorized`` consults ``TELEGRAM_ALLOW_BOTS`` for
Telegram sources the same way it consults ``DISCORD_ALLOW_BOTS``.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from gateway.session import Platform, SessionSource


@pytest.fixture(autouse=True)
def _isolate_telegram_env(monkeypatch):
    """Make every test start with a clean Telegram env so prior tests (or
    CI setups) can't leak env vars and silently flip the auth result.
    """
    for var in (
        "TELEGRAM_ALLOW_BOTS",
        "TELEGRAM_ALLOWED_USERS",
        "TELEGRAM_ALLOW_ALL_USERS",
        "TELEGRAM_GROUP_ALLOWED_USERS",
        "TELEGRAM_GROUP_ALLOWED_CHATS",
        "GATEWAY_ALLOW_ALL_USERS",
        "GATEWAY_ALLOWED_USERS",
    ):
        monkeypatch.delenv(var, raising=False)


# -----------------------------------------------------------------------------
# Gate: _is_user_authorized honors TELEGRAM_ALLOW_BOTS for Telegram bot sources
# -----------------------------------------------------------------------------


def _make_bare_runner():
    """Build a GatewayRunner skeleton with just enough wiring for the auth test.

    Mirrors the pattern from test_discord_bot_auth_bypass.py (and AGENTS.md
    pitfall #17): ``object.__new__`` skips the heavy __init__.
    """
    from gateway.run import GatewayRunner
    runner = object.__new__(GatewayRunner)
    runner.pairing_store = SimpleNamespace(is_approved=lambda *_a, **_kw: False)
    return runner


def _make_telegram_bot_source(bot_id: str = "999888777"):
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="123",
        chat_type="dm",
        user_id=bot_id,
        user_name="OtherProfileBot",
        is_bot=True,
    )


def _make_telegram_human_source(user_id: str = "100200300"):
    return SessionSource(
        platform=Platform.TELEGRAM,
        chat_id="123",
        chat_type="dm",
        user_id=user_id,
        user_name="SomeHuman",
        is_bot=False,
    )


def test_telegram_bot_authorized_when_allow_bots_mentions(monkeypatch):
    """TELEGRAM_ALLOW_BOTS=mentions must authorize a bot sender even when
    TELEGRAM_ALLOWED_USERS is set and the bot's ID is NOT in it.
    """
    runner = _make_bare_runner()

    monkeypatch.setenv("TELEGRAM_ALLOW_BOTS", "mentions")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "100200300")

    source = _make_telegram_bot_source(bot_id="999888777")
    assert runner._is_user_authorized(source) is True


def test_telegram_bot_authorized_when_allow_bots_all(monkeypatch):
    """TELEGRAM_ALLOW_BOTS=all is a superset of =mentions — should also bypass."""
    runner = _make_bare_runner()

    monkeypatch.setenv("TELEGRAM_ALLOW_BOTS", "all")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "100200300")

    source = _make_telegram_bot_source()
    assert runner._is_user_authorized(source) is True


def test_telegram_bot_NOT_authorized_when_allow_bots_unset(monkeypatch):
    """Unset TELEGRAM_ALLOW_BOTS (the default) must reject bot senders even
    though no human allowlist is configured.  This is the exact #32188
    scenario — two Hermes profiles on the same account, no env tuning,
    one bot's outbound message echoes through the other gateway.
    """
    runner = _make_bare_runner()

    monkeypatch.delenv("TELEGRAM_ALLOW_BOTS", raising=False)
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "100200300")

    source = _make_telegram_bot_source(bot_id="999888777")
    assert runner._is_user_authorized(source) is False


def test_telegram_bot_NOT_authorized_when_allow_bots_none(monkeypatch):
    """TELEGRAM_ALLOW_BOTS=none must still reject bots that aren't in
    TELEGRAM_ALLOWED_USERS — preserves the secure default behavior.
    """
    runner = _make_bare_runner()

    monkeypatch.setenv("TELEGRAM_ALLOW_BOTS", "none")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "100200300")

    source = _make_telegram_bot_source(bot_id="999888777")
    assert runner._is_user_authorized(source) is False


def test_telegram_human_still_checked_against_allowlist_when_bot_policy_set(monkeypatch):
    """TELEGRAM_ALLOW_BOTS=all must NOT open the gate for humans — they
    still need to be in TELEGRAM_ALLOWED_USERS (or a pairing approval).
    """
    runner = _make_bare_runner()

    monkeypatch.setenv("TELEGRAM_ALLOW_BOTS", "all")
    monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", "100200300")

    source = _make_telegram_human_source(user_id="999999999")
    assert runner._is_user_authorized(source) is False

    source_allowed = _make_telegram_human_source(user_id="100200300")
    assert runner._is_user_authorized(source_allowed) is True


# -----------------------------------------------------------------------------
# Gate: telegram adapter actually propagates PTB's user.is_bot to SessionSource
# -----------------------------------------------------------------------------


def _import_telegram_adapter():
    """Import TelegramAdapter without running its heavy module-level import
    chain. The adapter module imports a fair amount of code, but it's safe
    to import at test collection time on systems that already import
    ``gateway.run`` (which gateway tests rely on anyway).
    """
    from gateway.platforms.telegram import TelegramAdapter  # noqa: WPS433
    return TelegramAdapter


def _build_telegram_message(*, is_bot: bool):
    """Construct a python-telegram-bot-shaped Update.message mock.

    Only the attributes touched by ``_build_message_event_from_message``
    matter; everything else is left as a default MagicMock so any new
    accesses won't blow up.
    """
    user = SimpleNamespace(
        id=999888777 if is_bot else 100200300,
        full_name="OtherProfileBot" if is_bot else "Alice",
        first_name="OtherProfileBot" if is_bot else "Alice",
        is_bot=is_bot,
    )
    chat = SimpleNamespace(
        id=-100123,
        type="private",
        title=None,
        full_name="Alice",
        is_forum=False,
    )
    message = MagicMock()
    message.from_user = user
    message.chat = chat
    message.message_id = 4242
    message.message_thread_id = None
    message.is_topic_message = False
    message.forum_topic_created = None
    return message


def test_telegram_adapter_propagates_is_bot_true(monkeypatch):
    """The adapter must thread PTB's ``user.is_bot=True`` into SessionSource
    so ``_is_user_authorized`` sees the bot-origin signal.  Without this,
    the auth path in run.py is dead code on Telegram.
    """
    TelegramAdapter = _import_telegram_adapter()
    adapter = object.__new__(TelegramAdapter)
    adapter.platform = Platform.TELEGRAM
    adapter.config = SimpleNamespace(extra={})

    message = _build_telegram_message(is_bot=True)

    # _build_message_event_from_message does a lot of work; we only need
    # build_source to be invoked with is_bot=True.
    captured: dict = {}

    def fake_build_source(**kwargs):
        captured.update(kwargs)
        return SessionSource(
            platform=Platform.TELEGRAM,
            chat_id=str(kwargs.get("chat_id") or ""),
            chat_type=kwargs.get("chat_type") or "dm",
            user_id=kwargs.get("user_id"),
            is_bot=kwargs.get("is_bot", False),
        )

    with patch.object(adapter, "build_source", side_effect=fake_build_source):
        # Stop the rest of the method from doing too much: pass in just
        # enough to reach build_source. Reply/quote/forward extraction
        # runs after build_source but reads attributes off ``message`` —
        # MagicMock's defaults are tolerant enough for that path.
        try:
            from gateway.platforms.base import MessageType
            adapter._build_message_event(message, MessageType.TEXT, update_id=1)
        except Exception:
            # The method continues past build_source into media/reply
            # handling that needs real PTB types. We only care that
            # build_source was called with the right is_bot flag.
            pass

    assert captured.get("is_bot") is True, (
        "Telegram adapter must forward PTB's user.is_bot=True to "
        "build_source() so the gateway auth filter can act on it."
    )


def test_telegram_adapter_propagates_is_bot_false(monkeypatch):
    """The adapter must also pass is_bot=False through for human senders."""
    TelegramAdapter = _import_telegram_adapter()
    adapter = object.__new__(TelegramAdapter)
    adapter.platform = Platform.TELEGRAM
    adapter.config = SimpleNamespace(extra={})

    message = _build_telegram_message(is_bot=False)

    captured: dict = {}

    def fake_build_source(**kwargs):
        captured.update(kwargs)
        return SessionSource(
            platform=Platform.TELEGRAM,
            chat_id=str(kwargs.get("chat_id") or ""),
            chat_type=kwargs.get("chat_type") or "dm",
            user_id=kwargs.get("user_id"),
            is_bot=kwargs.get("is_bot", False),
        )

    with patch.object(adapter, "build_source", side_effect=fake_build_source):
        try:
            from gateway.platforms.base import MessageType
            adapter._build_message_event(message, MessageType.TEXT, update_id=1)
        except Exception:
            pass

    assert captured.get("is_bot") is False
