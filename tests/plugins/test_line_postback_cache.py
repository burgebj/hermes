"""Regression tests for LINE slow-response postback cache delivery."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from plugins.platforms.line.adapter import LineAdapter


class _ReplyRecorder:
    def __init__(self) -> None:
        self.replies: list[tuple[str, list[dict[str, object]]]] = []
        self.pushes: list[tuple[str, list[dict[str, object]]]] = []

    async def reply(self, reply_token: str, messages: list[dict[str, object]]) -> None:
        self.replies.append((reply_token, messages))

    async def push(self, chat_id: str, messages: list[dict[str, object]]) -> None:
        self.pushes.append((chat_id, messages))


def _adapter() -> LineAdapter:
    return LineAdapter(SimpleNamespace(extra={}))


def _postback_event(chat_id: str, reply_token: str, request_id: str) -> dict[str, object]:
    return {
        "replyToken": reply_token,
        "source": {"type": "user", "userId": chat_id},
        "postback": {
            "data": json.dumps(
                {"action": "show_response", "request_id": request_id}
            )
        },
    }


@pytest.mark.asyncio
async def test_postback_cache_rejects_ready_entry_from_different_chat() -> None:
    adapter = _adapter()
    client = _ReplyRecorder()
    adapter._client = client

    request_id = adapter._cache.register_pending("U-chat-a")
    adapter._cache.set_ready(request_id, "cached private answer")

    await adapter._handle_postback_event(
        _postback_event("U-chat-b", "reply-token-b", request_id)
    )

    assert client.replies == []
    assert client.pushes == []
    assert adapter._cache.get(request_id).state.value == "ready"


@pytest.mark.asyncio
async def test_postback_cache_delivers_ready_entry_to_origin_chat() -> None:
    adapter = _adapter()
    client = _ReplyRecorder()
    adapter._client = client

    request_id = adapter._cache.register_pending("U-chat-a")
    adapter._cache.set_ready(request_id, "cached private answer")

    await adapter._handle_postback_event(
        _postback_event("U-chat-a", "reply-token-a", request_id)
    )

    assert client.replies == [
        ("reply-token-a", [{"type": "text", "text": "cached private answer"}])
    ]
    assert client.pushes == []
    assert adapter._cache.get(request_id).state.value == "delivered"
