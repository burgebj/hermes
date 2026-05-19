"""Backward-compatibility tests for the Feishu reaction routing fork.

The unified trigger framework changes how Feishu's `_handle_reaction_event`
dispatches matched skills. The BC contract:

  - If the resolver matches at least one skill → dispatch with auto_skill set
    (NEW behavior, performant routing).
  - If the resolver returns [] AND no skill in the corpus has explicit
    `triggers:` frontmatter → fall through to broadcast (EXISTING BEHAVIOR
    for skills that pre-date the schema; preserved by design).
  - If the resolver returns [] AND some skill has explicit triggers → skip.
    The corpus is opt-in to the new schema; broadcasting would resurface old
    behavior that the opt-in user just stepped away from.

These tests focus on the BC fork logic in isolation. The full
`_handle_reaction_event` pipeline reaches into Feishu SDK objects that are
heavyweight to mock; instead we exercise the resolver-side decision tree
directly via the shared `gateway.skill_resolver` API and assert the policy
outcomes match the documented contract.
"""

from __future__ import annotations

from typing import List, Tuple

from gateway.skill_resolver import (
    SkillEntry,
    has_explicit_triggers,
    resolve_event_skills,
)


def _entry(name: str, *triggers: dict) -> SkillEntry:
    return (name, {}, list(triggers))


# ── BC fork policy: matched → dispatch with auto_skill ────────────────────


def test_bc_matched_corpus_dispatches_only_matched() -> None:
    skills: List[SkillEntry] = [
        _entry("approver", {"type": "reaction", "emoji": "✅"}),
        _entry("noisy", {"type": "reaction", "emoji": "👀"}),
        _entry("legacy_no_triggers"),  # no triggers field
    ]
    payload = {"emoji": "✅"}
    matched = resolve_event_skills("reaction", payload, skills)
    assert matched == ["approver"]
    # legacy_no_triggers is NOT in matched — that is the new behavior.


# ── BC fork policy: no matches AND legacy-only corpus → broadcast ─────────


def test_bc_legacy_only_corpus_falls_back_to_broadcast() -> None:
    """When NO skill in the corpus uses explicit triggers, an unmatched
    reaction must fall through to the legacy broadcast routing path.
    The Feishu adapter implements this fallback via ``has_explicit_triggers``;
    we verify the signal here."""
    skills = [_entry("legacy_a"), _entry("legacy_b"), _entry("legacy_c")]
    payload = {"emoji": "✅"}
    matched = resolve_event_skills("reaction", payload, skills)
    assert matched == []
    assert has_explicit_triggers(skills) is False
    # Adapter contract: matched=[] AND has_explicit_triggers=False → broadcast.


# ── BC fork policy: no matches AND opt-in corpus → skip ──────────────────


def test_bc_opt_in_corpus_skips_unmatched_reactions() -> None:
    """When at least one skill uses explicit triggers, an unmatched reaction
    is SKIPPED (not broadcast). This is the opt-in semantics the new schema
    promises: 'I declared what I want; please don't surprise me.'"""
    skills = [
        _entry("legacy_a"),
        _entry("opt_in", {"type": "reaction", "emoji": "🎯"}),  # different emoji
    ]
    payload = {"emoji": "✅"}  # not matching any explicit trigger
    matched = resolve_event_skills("reaction", payload, skills)
    assert matched == []
    assert has_explicit_triggers(skills) is True
    # Adapter contract: matched=[] AND has_explicit_triggers=True → skip.


# ── BC fork policy: matched corpus AND mixed legacy+opt-in ───────────────


def test_bc_mixed_corpus_dispatches_only_matched_not_legacy() -> None:
    """Critical BC nuance: in a corpus with both legacy and opt-in skills,
    a matched reaction must NOT also broadcast to legacy skills. The opt-in
    skill is the canonical responder; legacy skills opted out of reactions
    by NOT declaring triggers."""
    skills = [
        _entry("legacy_a"),
        _entry("legacy_b"),
        _entry("opt_in", {"type": "reaction", "emoji": "✅"}),
    ]
    payload = {"emoji": "✅"}
    matched = resolve_event_skills("reaction", payload, skills)
    assert matched == ["opt_in"]


# ── BC fork policy: ACK emoji filter is upstream ──────────────────────────


def test_bc_ack_emoji_filter_is_upstream_of_resolver() -> None:
    """The Feishu adapter's existing `_FEISHU_ACK_EMOJI` skip lives upstream
    of the resolver call (in `_on_reaction_event` and bot/app sender filter).
    The resolver itself is emoji-agnostic — it relies on the adapter to have
    already filtered out the bot's own ACK reactions and bot-sender events.
    This test documents that the resolver does NOT re-filter."""
    # The resolver matches a reaction even if it's "👀" (the ACK emoji used
    # internally for processing-feedback). The adapter is responsible for not
    # invoking the resolver with such payloads.
    skills = [_entry("watcher", {"type": "reaction", "emoji": "👀"})]
    payload = {"emoji": "👀"}
    matched = resolve_event_skills("reaction", payload, skills)
    assert matched == ["watcher"]  # resolver does not know about ACK semantics


# ── BC fork policy: empty corpus → broadcast (vacuous case) ──────────────


def test_bc_empty_corpus_falls_back_to_broadcast() -> None:
    """When the skills directory is empty (or hasn't loaded yet), the
    contract is broadcast — preserves pre-framework Feishu behavior."""
    skills: List[SkillEntry] = []
    matched = resolve_event_skills("reaction", {"emoji": "✅"}, skills)
    assert matched == []
    assert has_explicit_triggers(skills) is False
    # Adapter contract: matched=[] AND has_explicit_triggers=False → broadcast.
