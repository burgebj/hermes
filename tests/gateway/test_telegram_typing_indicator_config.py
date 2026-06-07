import pytest

from gateway.config import PlatformConfig
from gateway.platforms.telegram import TelegramAdapter


class DummyBot:
    def __init__(self):
        self.actions = []

    async def send_chat_action(self, **kwargs):
        self.actions.append(kwargs)


@pytest.mark.asyncio
async def test_telegram_typing_indicators_can_be_disabled_by_config():
    adapter = TelegramAdapter(PlatformConfig(extra={"typing_indicators": False}))
    bot = DummyBot()
    adapter._bot = bot

    await adapter.send_typing("123", metadata={"thread_id": "131"})

    assert bot.actions == []


@pytest.mark.asyncio
async def test_telegram_typing_indicators_default_enabled():
    adapter = TelegramAdapter(PlatformConfig(extra={}))
    bot = DummyBot()
    adapter._bot = bot

    await adapter.send_typing("123", metadata={"thread_id": "131"})

    assert bot.actions == [
        {"chat_id": 123, "action": "typing", "message_thread_id": 131}
    ]