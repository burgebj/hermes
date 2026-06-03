"""Tests for gateway.agent_registry — agent roster, mentions, guide, diagnostics."""

from __future__ import annotations

import pytest
from gateway.agent_registry import (
    AgentEntry,
    BUILTIN_AGENTS,
    bot_compat_contract,
    generate_pinned_guide,
    inline_mode_diagnostics,
    load_agent_registry,
    lookup_agent,
    parse_agent_mentions,
    render_agent_roster,
    render_route_guidance,
    render_summon_help,
    render_swarm_guidance,
)


# ---------------------------------------------------------------------------
# load_agent_registry
# ---------------------------------------------------------------------------

def test_load_agent_registry_returns_builtins_by_default():
    registry = load_agent_registry({})
    assert "hermes" in registry
    assert "codex" in registry
    assert "glm" in registry
    assert "blazemind" in registry
    assert "nexus" in registry
    assert "voice" in registry


def test_load_agent_registry_operator_override_merges_fields():
    cfg = {
        "workspace": {
            "agent_registry": {
                "agents": {
                    "codex": {
                        "display_name": "Codex Pro",
                        "cost_risk": "high",
                    }
                }
            }
        }
    }
    registry = load_agent_registry(cfg)
    entry = registry["codex"]
    assert entry.display_name == "Codex Pro"
    assert entry.cost_risk == "high"
    # Other builtin fields preserved
    assert entry.alias == "codex"
    assert entry.enabled is True


def test_load_agent_registry_custom_agent_added():
    cfg = {
        "workspace": {
            "agent_registry": {
                "agents": {
                    "my-agent": {
                        "display_name": "My Agent",
                        "description": "A custom test agent.",
                        "capabilities": ["testing"],
                        "enabled": True,
                    }
                }
            }
        }
    }
    registry = load_agent_registry(cfg)
    assert "my-agent" in registry
    entry = registry["my-agent"]
    assert entry.display_name == "My Agent"
    assert "testing" in entry.capabilities


def test_load_agent_registry_disabled_builtin():
    cfg = {
        "workspace": {
            "agent_registry": {
                "agents": {
                    "voice": {"enabled": False}
                }
            }
        }
    }
    registry = load_agent_registry(cfg)
    assert "voice" in registry
    assert registry["voice"].enabled is False


def test_load_agent_registry_empty_config():
    registry = load_agent_registry({})
    assert all(isinstance(e, AgentEntry) for e in registry.values())


# ---------------------------------------------------------------------------
# lookup_agent
# ---------------------------------------------------------------------------

def test_lookup_agent_returns_entry_for_known_alias():
    entry = lookup_agent("hermes", {})
    assert entry is not None
    assert entry.alias == "hermes"


def test_lookup_agent_case_insensitive():
    entry = lookup_agent("CODEX", {})
    assert entry is not None
    assert entry.alias == "codex"


def test_lookup_agent_returns_none_for_unknown():
    assert lookup_agent("unknown-bot-xyz", {}) is None


# ---------------------------------------------------------------------------
# parse_agent_mentions
# ---------------------------------------------------------------------------

def test_parse_agent_mentions_single_known():
    mentions = parse_agent_mentions("@hermes please run the tests", {})
    aliases = [a for a, _ in mentions]
    assert "hermes" in aliases


def test_parse_agent_mentions_multiple():
    mentions = parse_agent_mentions("@codex and @glm please refactor this", {})
    aliases = [a for a, _ in mentions]
    assert "codex" in aliases
    assert "glm" in aliases


def test_parse_agent_mentions_all_alias():
    mentions = parse_agent_mentions("@all please check status", {})
    assert any(a == "all" for a, _ in mentions)


def test_parse_agent_mentions_unknown_alias_not_returned():
    mentions = parse_agent_mentions("@totally-unknown-bot hello", {})
    # Unknown aliases not in registry are not returned
    assert all(a != "totally-unknown-bot" for a, _ in mentions)


def test_parse_agent_mentions_deduplicates():
    mentions = parse_agent_mentions("@codex do this, @codex and that", {})
    aliases = [a for a, _ in mentions]
    assert aliases.count("codex") == 1


def test_parse_agent_mentions_empty_text():
    assert parse_agent_mentions("", {}) == []


def test_parse_agent_mentions_no_mentions():
    assert parse_agent_mentions("just a normal message", {}) == []


# ---------------------------------------------------------------------------
# render_agent_roster
# ---------------------------------------------------------------------------

def test_render_agent_roster_includes_all_builtins():
    roster = render_agent_roster({})
    for alias in BUILTIN_AGENTS:
        assert f"@{alias}" in roster


def test_render_agent_roster_includes_risk_icons():
    roster = render_agent_roster({})
    # At least one of the known icons should appear
    assert any(icon in roster for icon in ("🟢", "🟡", "🔴"))


def test_render_agent_roster_includes_summon_hint():
    roster = render_agent_roster({})
    assert "/summon" in roster


# ---------------------------------------------------------------------------
# render_summon_help
# ---------------------------------------------------------------------------

def test_render_summon_help_known_agent():
    text = render_summon_help("codex", {})
    assert "Codex" in text
    assert "capabilities" in text.lower() or "Capabilities" in text


def test_render_summon_help_unknown_agent():
    text = render_summon_help("ghost-bot", {})
    assert "Unknown agent" in text
    assert "ghost-bot" in text


def test_render_summon_help_disabled_agent():
    cfg = {
        "workspace": {
            "agent_registry": {
                "agents": {"voice": {"enabled": False}}
            }
        }
    }
    text = render_summon_help("voice", cfg)
    assert "disabled" in text.lower()


def test_render_summon_help_includes_examples():
    text = render_summon_help("blazemind", {})
    assert "@blazemind" in text


# ---------------------------------------------------------------------------
# render_route_guidance
# ---------------------------------------------------------------------------

def test_render_route_guidance_known_agent():
    text = render_route_guidance("hermes", "run tests", {})
    assert "hermes" in text.lower()
    assert "run tests" in text


def test_render_route_guidance_unknown_agent():
    text = render_route_guidance("ghost", "", {})
    assert "Unknown agent" in text


# ---------------------------------------------------------------------------
# render_swarm_guidance
# ---------------------------------------------------------------------------

def test_render_swarm_guidance_two_agents():
    text = render_swarm_guidance(["codex", "glm"], "refactor auth", {})
    assert "@codex" in text
    assert "@glm" in text
    assert "refactor auth" in text


def test_render_swarm_guidance_all_broadcast():
    text = render_swarm_guidance(["all"], "check status", {})
    # Should include multiple known agents
    assert "broadcast" in text.lower() or "all" in text.lower()


def test_render_swarm_guidance_empty_list():
    text = render_swarm_guidance([], "task", {})
    assert "No agents" in text


def test_render_swarm_guidance_unknown_agent_flagged():
    text = render_swarm_guidance(["ghost-9000"], "task", {})
    assert "unknown" in text.lower()


# ---------------------------------------------------------------------------
# generate_pinned_guide
# ---------------------------------------------------------------------------

def test_generate_pinned_guide_includes_commands():
    guide = generate_pinned_guide({})
    assert "/agents" in guide
    assert "/guide" in guide
    assert "/summon" in guide
    assert "/swarm" in guide
    assert "/agent_status" in guide


def test_generate_pinned_guide_includes_agents():
    guide = generate_pinned_guide({})
    assert "@hermes" in guide
    assert "@codex" in guide
    assert "@blazemind" in guide


def test_generate_pinned_guide_includes_mention_syntax():
    guide = generate_pinned_guide({})
    assert "@all" in guide


# ---------------------------------------------------------------------------
# inline_mode_diagnostics
# ---------------------------------------------------------------------------

def test_inline_mode_diagnostics_includes_botfather_steps():
    text = inline_mode_diagnostics()
    assert "BotFather" in text
    assert "Inline Mode" in text


def test_inline_mode_diagnostics_includes_verification_step():
    text = inline_mode_diagnostics()
    assert "getMe" in text or "doctor" in text


# ---------------------------------------------------------------------------
# bot_compat_contract
# ---------------------------------------------------------------------------

def test_bot_compat_contract_includes_config_schema():
    text = bot_compat_contract()
    assert "agent_registry" in text
    assert "route_target" in text


def test_bot_compat_contract_includes_verification_commands():
    text = bot_compat_contract()
    assert "hermes workspace list" in text
    assert "hermes workspace drift" in text


def test_bot_compat_contract_includes_telegram_setup():
    text = bot_compat_contract()
    assert "Telegram" in text
    assert "group" in text.lower()
