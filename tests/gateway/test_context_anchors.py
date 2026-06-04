from __future__ import annotations

from types import SimpleNamespace

import pytest

from gateway.config import Platform
from gateway.context_anchors import ContextAnchorStore
from gateway.platforms.base import MessageEvent, MessageType
from gateway.run import GatewayRunner
from gateway.session import SessionContext, SessionSource, build_session_context_prompt


def _source(**overrides) -> SessionSource:
    values = {
        "platform": Platform.DISCORD,
        "chat_id": "channel-1",
        "chat_type": "thread",
        "thread_id": "thread-1",
        "chat_name": "Context Anchor Thread",
        "guild_id": "guild-1",
        "parent_chat_id": "parent-1",
    }
    values.update(overrides)
    return SessionSource(**values)


def _event(text: str, **source_overrides) -> MessageEvent:
    return MessageEvent(
        text=text,
        message_type=MessageType.TEXT,
        source=_source(**source_overrides),
    )


def test_context_anchor_store_resolves_manual_thread_binding(tmp_path):
    store = ContextAnchorStore(tmp_path / "context_anchors.json")
    source = _source()

    anchor = store.bind(
        source,
        anchor_type="github",
        anchor_id="NousResearch/hermes-agent#123",
        title="Generic context anchor PR",
        url="https://github.com/NousResearch/hermes-agent/pull/123",
    )

    resolved = store.resolve_for_source(source)
    assert resolved == anchor
    assert resolved.to_dict() == {
        "type": "github",
        "id": "NousResearch/hermes-agent#123",
        "title": "Generic context anchor PR",
        "url": "https://github.com/NousResearch/hermes-agent/pull/123",
        "source": "manual",
        "metadata": {},
    }


def test_context_anchor_store_uses_title_fallback_without_manual_binding(tmp_path):
    store = ContextAnchorStore(tmp_path / "context_anchors.json")
    source = _source(chat_name="Hermes PRs [context:github:NousResearch/hermes-agent#456]")

    resolved = store.resolve_for_source(source)

    assert resolved is not None
    assert resolved.anchor_type == "github"
    assert resolved.anchor_id == "NousResearch/hermes-agent#456"
    assert resolved.source == "thread-title"


def test_session_source_serializes_context_anchor():
    source = _source(
        context_anchor={
            "type": "github",
            "id": "NousResearch/hermes-agent#123",
            "title": "Generic context anchor PR",
            "url": "https://github.com/NousResearch/hermes-agent/pull/123",
            "source": "manual",
        }
    )

    round_tripped = SessionSource.from_dict(source.to_dict())

    assert round_tripped.context_anchor == source.context_anchor


def test_session_context_prompt_includes_bound_context_anchor():
    source = _source(
        context_anchor={
            "type": "github",
            "id": "NousResearch/hermes-agent#123",
            "title": "Generic context anchor PR",
            "url": "https://github.com/NousResearch/hermes-agent/pull/123",
            "source": "manual",
        }
    )
    context = SessionContext(source=source, connected_platforms=[], home_channels={})

    prompt = build_session_context_prompt(context)

    assert "**Bound Context Anchor:**" in prompt
    assert "Type: `github`" in prompt
    assert "ID: `NousResearch/hermes-agent#123`" in prompt
    assert "Title: Generic context anchor PR" in prompt
    assert "URL: https://github.com/NousResearch/hermes-agent/pull/123" in prompt


@pytest.mark.asyncio
async def test_bind_context_command_binds_and_recovers_anchor(tmp_path):
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.context_anchors = ContextAnchorStore(tmp_path / "context_anchors.json")
    runner.config = SimpleNamespace()

    bind_response = await runner._handle_bind_context_command(
        _event("/bind-context github NousResearch/hermes-agent#123 Generic context anchor PR")
    )
    recover_response = await runner._handle_recover_command(_event("/recover"))

    assert "Bound this chat/thread to context anchor `github:NousResearch/hermes-agent#123`" in bind_response
    assert "Future turns will include this anchor" in bind_response
    assert "Context anchor: `github:NousResearch/hermes-agent#123`" in recover_response
    assert "Title: Generic context anchor PR" in recover_response


@pytest.mark.asyncio
async def test_bind_context_command_clears_manual_binding_but_reports_title_fallback(tmp_path):
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.context_anchors = ContextAnchorStore(tmp_path / "context_anchors.json")
    runner.config = SimpleNamespace()
    source = _source(chat_name="Hermes PRs [context:github:NousResearch/hermes-agent#456]")

    response = await runner._handle_bind_context_command(MessageEvent(text="/bind-context clear", source=source))

    assert "No manual context anchor was set" in response
    assert "[context:<type>:<id>]" in response


def test_source_with_context_anchor_attaches_resolved_binding(tmp_path):
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.context_anchors = ContextAnchorStore(tmp_path / "context_anchors.json")
    source = _source()
    runner.context_anchors.bind(source, anchor_type="github", anchor_id="NousResearch/hermes-agent#123")

    enriched = runner._source_with_context_anchor(source)

    assert enriched is not source
    assert enriched.context_anchor == {
        "type": "github",
        "id": "NousResearch/hermes-agent#123",
        "title": "",
        "url": "",
        "source": "manual",
        "metadata": {},
    }
