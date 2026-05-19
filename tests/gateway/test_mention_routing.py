"""Tests for the mention-routing dispatch path inside ``DiscordAdapter._handle_message``.

Vector 3 token-leak fix: every @mention in an allowed channel currently
invokes the agent regardless of whether any skill's ``mention.regex``
matches. This module verifies the new ``handle_inbound_mention`` hook
short-circuits the legacy LLM invoke under the right conditions:

1. ``inbound_routing=False`` (default)              → legacy path, no resolver
2. ``inbound_routing=True`` + skill matches         → dispatch with auto_skill set
3. ``inbound_routing=True`` + no match + explicit triggers → early-return
4. ``inbound_routing=True`` + no match + no explicit triggers → fall-through
5. ``inbound_routing=True`` + skill provider raises → fall-through (fail-safe)

These tests exercise ``DiscordInteractionsHandler.handle_inbound_mention``
plus ``has_explicit_triggers`` directly, mirroring the wiring contract in
``gateway/platforms/discord.py:3649``. A full ``_handle_message`` round-trip
would require a live ``discord.Client``; instead we model the dispatch
decision as the wiring code does (compose the same primitives).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import List
from unittest.mock import AsyncMock, MagicMock

import pytest

from gateway.platforms import discord_interactions
from gateway.platforms.discord_interactions import (
    DiscordInteractionsHandler,
    get_event_counters,
)
from gateway.skill_resolver import SkillEntry, has_explicit_triggers


def _entry(name: str, *triggers: dict) -> SkillEntry:
    return (name, {}, list(triggers))


def _mention_message(channel_name: str = "general", channel_id: int = 100) -> SimpleNamespace:
    channel = SimpleNamespace(id=channel_id, name=channel_name)
    return SimpleNamespace(channel=channel)


def _make_handler(skills: List[SkillEntry]) -> tuple[DiscordInteractionsHandler, MagicMock]:
    adapter = MagicMock()
    adapter._client = MagicMock()
    adapter._client.user = SimpleNamespace(id=1)
    adapter.handle_message = AsyncMock()
    handler = DiscordInteractionsHandler(adapter=adapter, skill_provider=lambda: skills)
    return handler, adapter


@pytest.fixture(autouse=True)
def _reset_counters():
    for k in discord_interactions._event_counters:
        discord_interactions._event_counters[k] = 0
    yield
    for k in discord_interactions._event_counters:
        discord_interactions._event_counters[k] = 0


# ── Wiring-decision simulation ──────────────────────────────────────────────


async def _simulate_dispatch_decision(
    handler: DiscordInteractionsHandler,
    *,
    inbound_routing: bool,
    is_actual_mention: bool,
    message: SimpleNamespace,
    normalized_text: str,
    skills: List[SkillEntry],
) -> dict:
    """Mirror the dispatch decision in ``_handle_message`` (line 3649+).

    Returns a dict with the observed branch:
        {"branch": "legacy" | "match" | "early_return" | "failsafe_legacy",
         "matched": Optional[list[str]]}
    """
    if not inbound_routing or not is_actual_mention:
        return {"branch": "legacy", "matched": None}

    try:
        matched = await handler.handle_inbound_mention(message, normalized_text)
    except Exception:
        return {"branch": "failsafe_legacy", "matched": None}

    if matched:
        return {"branch": "match", "matched": matched}

    # No match — early-return iff the corpus has explicit triggers configured.
    if has_explicit_triggers(skills):
        return {"branch": "early_return", "matched": None}
    return {"branch": "legacy", "matched": None}


# ── Test cases per plan §3.3 ────────────────────────────────────────────────


class TestInboundRoutingDisabled:
    """Default (inbound_routing=False) preserves legacy behavior unchanged."""

    @pytest.mark.asyncio
    async def test_disabled_falls_through_to_legacy_no_resolver_call(self):
        skills = [_entry("any", {"type": "mention", "regex": r"\b.*\b"})]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=False,
            is_actual_mention=True,
            message=_mention_message(),
            normalized_text="ping",
            skills=skills,
        )
        assert decision["branch"] == "legacy"
        # Resolver was not called → counters stay zero.
        counters = get_event_counters()
        assert counters["discord.mentions.skipped_no_match"] == 0
        assert counters["discord.mentions.invoked"] == 0


class TestInboundRoutingEnabled:
    """inbound_routing=True triggers the new short-circuit logic."""

    @pytest.mark.asyncio
    async def test_skill_match_dispatches_with_auto_skill(self):
        skills = [_entry("deployer", {"type": "mention", "regex": r"\bdeploy\b"})]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=True,
            is_actual_mention=True,
            message=_mention_message(),
            normalized_text="please deploy",
            skills=skills,
        )
        assert decision["branch"] == "match"
        assert decision["matched"] == ["deployer"]
        counters = get_event_counters()
        assert counters["discord.mentions.invoked"] == 1
        assert counters["discord.mentions.skipped_no_match"] == 0

    @pytest.mark.asyncio
    async def test_no_match_with_explicit_triggers_early_returns(self):
        skills = [_entry("deployer", {"type": "mention", "regex": r"\bdeploy\b"})]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=True,
            is_actual_mention=True,
            message=_mention_message(),
            normalized_text="hello world",
            skills=skills,
        )
        assert decision["branch"] == "early_return"
        assert decision["matched"] is None
        counters = get_event_counters()
        assert counters["discord.mentions.skipped_no_match"] == 1
        assert counters["discord.mentions.invoked"] == 0

    @pytest.mark.asyncio
    async def test_no_match_no_explicit_triggers_falls_through_to_legacy(self):
        # Skill list with NO triggers → has_explicit_triggers returns False.
        skills = [_entry("legacy_skill")]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=True,
            is_actual_mention=True,
            message=_mention_message(),
            normalized_text="any text",
            skills=skills,
        )
        assert decision["branch"] == "legacy"
        counters = get_event_counters()
        # Resolver was called and recorded a no-match before the BC fall-through.
        assert counters["discord.mentions.skipped_no_match"] == 1

    @pytest.mark.asyncio
    async def test_skill_provider_raises_falls_through_to_legacy(self):
        adapter = MagicMock()
        adapter._client = MagicMock()
        adapter._client.user = SimpleNamespace(id=1)
        adapter.handle_message = AsyncMock()

        def boom():
            raise RuntimeError("provider down")

        handler = DiscordInteractionsHandler(adapter=adapter, skill_provider=boom)

        # The handler swallows the provider failure (returns None) — caller
        # then falls through to legacy because matched is falsy.
        matched = await handler.handle_inbound_mention(
            _mention_message(), "anything"
        )
        assert matched is None
        # No counter increment on the failure path.
        counters = get_event_counters()
        assert counters["discord.mentions.skipped_no_match"] == 0
        assert counters["discord.mentions.invoked"] == 0

    @pytest.mark.asyncio
    async def test_non_mention_skips_resolver_even_when_enabled(self):
        skills = [_entry("deployer", {"type": "mention", "regex": r"\bdeploy\b"})]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=True,
            is_actual_mention=False,  # message is not a mention (DM/free channel)
            message=_mention_message(),
            normalized_text="please deploy",
            skills=skills,
        )
        # Non-mention messages take the legacy path even with the flag on.
        assert decision["branch"] == "legacy"
        counters = get_event_counters()
        assert counters["discord.mentions.invoked"] == 0
        assert counters["discord.mentions.skipped_no_match"] == 0


class TestChannelFilter:
    """Mention triggers may declare a channel_filter that limits matches."""

    @pytest.mark.asyncio
    async def test_channel_filter_match(self):
        skills = [
            _entry(
                "ops",
                {
                    "type": "mention",
                    "regex": r"\bdeploy\b",
                    "channel_filter": ["ops"],
                },
            )
        ]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=True,
            is_actual_mention=True,
            message=_mention_message(channel_name="ops"),
            normalized_text="deploy now",
            skills=skills,
        )
        assert decision["branch"] == "match"
        assert decision["matched"] == ["ops"]

    @pytest.mark.asyncio
    async def test_channel_filter_excludes_other_channels(self):
        skills = [
            _entry(
                "ops",
                {
                    "type": "mention",
                    "regex": r"\bdeploy\b",
                    "channel_filter": ["ops"],
                },
            )
        ]
        handler, _ = _make_handler(skills)
        decision = await _simulate_dispatch_decision(
            handler,
            inbound_routing=True,
            is_actual_mention=True,
            message=_mention_message(channel_name="general"),
            normalized_text="deploy now",
            skills=skills,
        )
        # Channel doesn't match → resolver returns no-match → early_return
        # because the corpus still has explicit triggers configured.
        assert decision["branch"] == "early_return"
