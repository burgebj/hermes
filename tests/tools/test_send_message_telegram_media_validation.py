"""Regression tests for standalone Telegram media delivery validation."""

import asyncio
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from tools.send_message_tool import _send_telegram


def _install_telegram_mock(monkeypatch, bot):
    parse_mode = SimpleNamespace(MARKDOWN_V2="MarkdownV2", HTML="HTML")
    constants_mod = SimpleNamespace(ParseMode=parse_mode)
    telegram_mod = SimpleNamespace(
        Bot=lambda token: bot,
        MessageEntity=lambda **kw: SimpleNamespace(**kw),
        constants=constants_mod,
    )
    monkeypatch.setitem(sys.modules, "telegram", telegram_mod)
    monkeypatch.setitem(sys.modules, "telegram.constants", constants_mod)


def test_send_telegram_skips_unsafe_media_path_before_upload(tmp_path, monkeypatch):
    secret_path = tmp_path / "secret.txt"
    secret_path.write_text("token", encoding="utf-8")

    bot = MagicMock()
    bot.send_message = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.send_video = AsyncMock()
    bot.send_voice = AsyncMock()
    bot.send_audio = AsyncMock()
    bot.send_document = AsyncMock()
    _install_telegram_mock(monkeypatch, bot)

    def deny_media_path(path):
        assert path == str(secret_path)
        return None

    monkeypatch.setattr(
        "gateway.platforms.base.validate_media_delivery_path",
        deny_media_path,
    )

    result = asyncio.run(
        _send_telegram(
            "token",
            "12345",
            "",
            media_files=[(str(secret_path), False)],
        )
    )

    assert "error" in result
    assert "No deliverable text or media remained" in result["error"]
    assert any("Skipping unsafe media path" in warning for warning in result["warnings"])
    bot.send_message.assert_not_awaited()
    bot.send_photo.assert_not_awaited()
    bot.send_video.assert_not_awaited()
    bot.send_voice.assert_not_awaited()
    bot.send_audio.assert_not_awaited()
    bot.send_document.assert_not_awaited()
