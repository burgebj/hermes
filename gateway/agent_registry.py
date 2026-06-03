"""Agent roster registry for multi-agent Telegram workspace operation.

Operator-authored config under ``workspace.agent_registry.agents`` maps agent
aliases to display names, capabilities, route targets, and invocation guidance.
The registry is used by /agents, /agent_status, /summon, /swarm, /route, /guide
and by @mention parsing in the gateway message dispatch loop.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AgentEntry:
    alias: str
    display_name: str
    description: str = ""
    capabilities: tuple[str, ...] = field(default_factory=tuple)
    route_target: str = ""          # delivery ref, e.g. telegram:-100123:708
    topic_lane: str = ""            # workspace alias, e.g. "agent-workbench"
    cost_risk: str = "low"          # low | medium | high
    invocation_examples: tuple[str, ...] = field(default_factory=tuple)
    notes: str = ""
    enabled: bool = True

    # Compatibility shim so frozen dataclass works with tuple field defaults
    def __init__(self, alias: str, display_name: str, **kw: Any) -> None:  # noqa: D107
        object.__setattr__(self, "alias", alias)
        object.__setattr__(self, "display_name", display_name)
        object.__setattr__(self, "description", str(kw.get("description") or ""))
        caps = kw.get("capabilities") or ()
        object.__setattr__(self, "capabilities", tuple(caps))
        object.__setattr__(self, "route_target", str(kw.get("route_target") or ""))
        object.__setattr__(self, "topic_lane", str(kw.get("topic_lane") or ""))
        object.__setattr__(self, "cost_risk", str(kw.get("cost_risk") or "low"))
        examples = kw.get("invocation_examples") or ()
        object.__setattr__(self, "invocation_examples", tuple(examples))
        object.__setattr__(self, "notes", str(kw.get("notes") or ""))
        object.__setattr__(self, "enabled", bool(kw.get("enabled", True)))


# ---------------------------------------------------------------------------
# Built-in agent definitions (operator can override or extend via config)
# ---------------------------------------------------------------------------

BUILTIN_AGENTS: dict[str, AgentEntry] = {
    "hermes": AgentEntry(
        alias="hermes",
        display_name="Hermes",
        description="Primary AI agent — coding, research, automation, Telegram orchestration.",
        capabilities=["coding", "research", "shell", "web", "memory", "delegation"],
        route_target="telegram:-1003932124823:708",
        topic_lane="agent-workbench",
        cost_risk="medium",
        invocation_examples=["@hermes run the test suite", "@hermes summarise yesterday's alerts"],
        notes="Default agent. Handles all tasks unless routed to a specialist.",
        enabled=True,
    ),
    "codex": AgentEntry(
        alias="codex",
        display_name="Codex",
        description="OpenAI Codex CLI — agentic code generation and PR-level changes.",
        capabilities=["coding", "git", "pr-generation", "refactoring"],
        route_target="telegram:-1003932124823:708",
        topic_lane="agent-workbench",
        cost_risk="medium",
        invocation_examples=["@codex add pagination to the users API", "@codex fix the failing test in auth.py"],
        notes="Spawned via `hermes codex` or Kanban. Best for isolated code tasks.",
        enabled=True,
    ),
    "glm": AgentEntry(
        alias="glm",
        display_name="GLM / Z.AI",
        description="Z.AI GLM coding agent — cost-efficient code generation.",
        capabilities=["coding", "git"],
        route_target="telegram:-1003932124823:708",
        topic_lane="agent-workbench",
        cost_risk="low",
        invocation_examples=["@glm refactor the data pipeline", "@glm write unit tests for utils.py"],
        notes="Use for high-volume or cost-sensitive coding tasks.",
        enabled=True,
    ),
    "blazemind": AgentEntry(
        alias="blazemind",
        display_name="BlazeMind",
        description="Parallel AI swarm orchestrator — fan-out multi-agent workloads.",
        capabilities=["orchestration", "swarm", "parallel-agents"],
        route_target="telegram:-1003932124823:823",
        topic_lane="blazemind",
        cost_risk="high",
        invocation_examples=["@blazemind run a 5-agent sweep of the auth module", "@blazemind spec: build.yaml"],
        notes="High token usage. Use for complex multi-agent workflows with a spec.",
        enabled=True,
    ),
    "nexus": AgentEntry(
        alias="nexus",
        display_name="Nexus",
        description="GitNexus code knowledge graph — architecture queries and blast-radius analysis.",
        capabilities=["code-search", "architecture", "blast-radius"],
        route_target="telegram:-1003932124823:708",
        topic_lane="agent-workbench",
        cost_risk="low",
        invocation_examples=["@nexus who calls process_payment?", "@nexus blast radius of auth.py"],
        notes="Read-only knowledge graph. No code changes, fast answers.",
        enabled=True,
    ),
    "voice": AgentEntry(
        alias="voice",
        display_name="Voice / TTS",
        description="Voice input transcription and TTS reply routing.",
        capabilities=["voice", "tts", "transcription"],
        route_target="telegram:-1003932124823:1",
        topic_lane="general",
        cost_risk="low",
        invocation_examples=["@voice read out the latest alert", "/voice on"],
        notes="Use /voice on to enable voice mode. Voice messages auto-transcribe via Whisper.",
        enabled=True,
    ),
}

_ALL_ALIASES = {"all", "everyone", "broadcast"}


# ---------------------------------------------------------------------------
# Loading and lookup
# ---------------------------------------------------------------------------

def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def load_agent_registry(config: Mapping[str, Any] | None = None) -> dict[str, AgentEntry]:
    """Return merged agent registry: builtins + operator overrides from config.

    Config path: ``workspace.agent_registry.agents``.  Each key is the agent
    alias; values follow the AgentEntry field names.  Operator entries with
    ``enabled: false`` are included but marked disabled.  Builtins suppressed
    by setting the alias to ``null`` or ``{enabled: false}`` remain in the
    registry as disabled — they are never silently removed.
    """
    from hermes_cli.config import load_config  # lazy to avoid circular imports

    cfg = _as_mapping(config if config is not None else load_config())
    workspace = _as_mapping(cfg.get("workspace"))
    agent_reg = _as_mapping(workspace.get("agent_registry"))
    raw_agents = _as_mapping(agent_reg.get("agents"))

    # Start with builtins, then apply operator overrides
    result: dict[str, AgentEntry] = {k: v for k, v in BUILTIN_AGENTS.items()}

    for alias, raw in raw_agents.items():
        alias = str(alias).strip().lower()
        if not alias:
            continue
        if not isinstance(raw, Mapping):
            # e.g. alias: null → disable builtin
            if alias in result:
                entry = result[alias]
                object.__setattr__(entry, "enabled", False)
            continue
        # Merge over builtin if present, otherwise create fresh
        base = BUILTIN_AGENTS.get(alias)
        entry = AgentEntry(
            alias=alias,
            display_name=str(raw.get("display_name") or (base.display_name if base else alias.title())),
            description=str(raw.get("description") or (base.description if base else "")),
            capabilities=list(raw.get("capabilities") or (base.capabilities if base else [])),
            route_target=str(raw.get("route_target") or (base.route_target if base else "")),
            topic_lane=str(raw.get("topic_lane") or (base.topic_lane if base else "")),
            cost_risk=str(raw.get("cost_risk") or (base.cost_risk if base else "low")),
            invocation_examples=list(raw.get("invocation_examples") or (base.invocation_examples if base else [])),
            notes=str(raw.get("notes") or (base.notes if base else "")),
            enabled=bool(raw.get("enabled", True)),
        )
        result[alias] = entry

    return result


def lookup_agent(alias: str, config: Mapping[str, Any] | None = None) -> AgentEntry | None:
    """Look up a single agent by alias (case-insensitive). Returns None if not found."""
    registry = load_agent_registry(config)
    return registry.get(alias.strip().lower())


def parse_agent_mentions(
    text: str,
    config: Mapping[str, Any] | None = None,
) -> list[tuple[str, AgentEntry | None]]:
    """Parse @alias mentions from message text.

    Returns a list of ``(alias, entry_or_none)`` tuples for every ``@word``
    found in the text.  The entry is ``None`` if the alias is not in the
    registry.  ``@all`` / ``@everyone`` / ``@broadcast`` are returned with
    entry=None and alias='all'.
    """
    registry = load_agent_registry(config)
    found: list[tuple[str, AgentEntry | None]] = []
    seen: set[str] = set()
    for match in re.finditer(r"@([A-Za-z][A-Za-z0-9_-]*)", text):
        raw_alias = match.group(1).lower()
        if raw_alias in seen:
            continue
        seen.add(raw_alias)
        if raw_alias in _ALL_ALIASES:
            found.append(("all", None))
        else:
            entry = registry.get(raw_alias)
            if entry is not None or raw_alias in registry:
                found.append((raw_alias, entry))
    return found


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def render_agent_roster(config: Mapping[str, Any] | None = None) -> str:
    """Return a human-readable agent roster for /agent_status and /guide."""
    registry = load_agent_registry(config)
    enabled = [e for e in registry.values() if e.enabled]
    disabled = [e for e in registry.values() if not e.enabled]

    lines = ["**Agent Roster**", ""]
    for entry in sorted(enabled, key=lambda e: e.alias):
        caps = ", ".join(entry.capabilities) if entry.capabilities else "general"
        risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(entry.cost_risk, "⚪")
        lane = f" → #{entry.topic_lane}" if entry.topic_lane else ""
        lines.append(f"**@{entry.alias}** — {entry.display_name} {risk_icon}{lane}")
        lines.append(f"  {entry.description}")
        lines.append(f"  Caps: {caps}")
        if entry.invocation_examples:
            lines.append(f"  e.g. `{entry.invocation_examples[0]}`")
        lines.append("")

    if disabled:
        lines.append("*Disabled:* " + ", ".join(f"@{e.alias}" for e in disabled))
        lines.append("")

    lines.append("Use `/summon @agent task` to invoke, `/swarm @a @b task` for multi-agent.")
    return "\n".join(lines)


def render_summon_help(alias: str, config: Mapping[str, Any] | None = None) -> str:
    """Return invocation guidance for a specific agent."""
    entry = lookup_agent(alias, config)
    if entry is None:
        registry = load_agent_registry(config)
        known = ", ".join(f"@{a}" for a in sorted(registry))
        return f"Unknown agent @{alias}. Known agents: {known}"

    if not entry.enabled:
        return f"Agent @{alias} ({entry.display_name}) is currently disabled."

    lines = [f"**@{alias}** — {entry.display_name}"]
    if entry.description:
        lines.append(entry.description)
    lines.append("")
    caps = ", ".join(entry.capabilities) if entry.capabilities else "general"
    lines.append(f"Capabilities: {caps}")
    risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(entry.cost_risk, "⚪")
    lines.append(f"Cost risk: {risk_icon} {entry.cost_risk}")
    if entry.topic_lane:
        lines.append(f"Topic lane: #{entry.topic_lane}")
    if entry.route_target:
        lines.append(f"Route target: `{entry.route_target}`")
    if entry.invocation_examples:
        lines.append("")
        lines.append("Examples:")
        for ex in entry.invocation_examples:
            lines.append(f"  • `{ex}`")
    if entry.notes:
        lines.append("")
        lines.append(f"Notes: {entry.notes}")
    return "\n".join(lines)


def render_route_guidance(
    alias: str,
    task: str = "",
    config: Mapping[str, Any] | None = None,
) -> str:
    """Return routing guidance for directing a task to a specific agent."""
    entry = lookup_agent(alias, config)
    if entry is None:
        registry = load_agent_registry(config)
        known = ", ".join(f"@{a}" for a in sorted(registry))
        return f"Unknown agent @{alias}. Known agents: {known}"

    lines = [f"Routing to **@{alias}** ({entry.display_name})"]
    if entry.route_target:
        lines.append(f"Delivery target: `{entry.route_target}`")
    if entry.topic_lane:
        lines.append(f"Topic: #{entry.topic_lane}")
    if task:
        lines.append(f"Task: {task}")
        if entry.invocation_examples:
            lines.append(f"Tip: try `@{alias} {task}`")
    lines.append("")
    lines.append(
        "Note: To truly delegate to a separate bot/agent, that agent must be "
        "present in the Telegram group and respond to @mentions or in its own topic."
    )
    return "\n".join(lines)


def render_swarm_guidance(
    aliases: list[str],
    task: str = "",
    config: Mapping[str, Any] | None = None,
) -> str:
    """Return multi-agent swarm dispatch guidance."""
    registry = load_agent_registry(config)
    resolved: list[tuple[str, AgentEntry | None]] = []
    broadcast = False
    for alias in aliases:
        a = alias.strip().lower()
        if a in _ALL_ALIASES:
            broadcast = True
            resolved = [(a2, e) for a2, e in registry.items() if e.enabled]
            break
        entry = registry.get(a)
        resolved.append((a, entry))

    if not resolved:
        return "No agents specified. Usage: `/swarm @codex @glm <task>`"

    lines = ["**Swarm dispatch**" + (" (broadcast)" if broadcast else "")]
    lines.append(f"Task: {task or '(not specified)'}")
    lines.append("")
    for alias, entry in resolved:
        if entry is None:
            lines.append(f"• @{alias} — ⚠️ unknown agent")
        elif not entry.enabled:
            lines.append(f"• @{alias} — ⏸ disabled")
        else:
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(entry.cost_risk, "⚪")
            lane = f" (#{entry.topic_lane})" if entry.topic_lane else ""
            lines.append(f"• @{alias} — {entry.display_name} {risk_icon}{lane}")

    lines.append("")
    lines.append(
        "To run a BlazeMind swarm: `@blazemind` then describe your spec, or use "
        "`hermes blazemind` in the CLI. Each agent runs in its own worktree."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pinned guide generation
# ---------------------------------------------------------------------------

def generate_pinned_guide(config: Mapping[str, Any] | None = None) -> str:
    """Generate a pinned-message-ready multi-agent workspace guide."""
    from hermes_cli.config import load_config  # lazy import

    cfg = _as_mapping(config if config is not None else load_config())
    registry = load_agent_registry(cfg)
    enabled = sorted((e for e in registry.values() if e.enabled), key=lambda e: e.alias)

    lines = [
        "**Eternal — Multi-Agent Workspace Guide**",
        "",
        "**Available Agents**",
    ]
    for entry in enabled:
        risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(entry.cost_risk, "⚪")
        lines.append(f"• @{entry.alias} {risk_icon} — {entry.display_name}: {entry.description[:80]}")
    lines.extend([
        "",
        "**Quick Commands**",
        "• `/agents` — active sessions & processes",
        "• `/agent_status` — registered agent roster",
        "• `/guide` — this guide",
        "• `/whereami` — topic routing diagnostics",
        "• `/summon @agent task` — invoke an agent",
        "• `/swarm @a @b task` — multi-agent dispatch",
        "• `/route @agent task` — routing guidance",
        "• `/status` — session info",
        "• `/help` — all commands",
        "",
        "**Topic Lanes**",
    ])

    # Import topic registry for topic listing
    try:
        from gateway.topic_registry import load_topic_registry
        topics = sorted(load_topic_registry(cfg).values(), key=lambda e: e.display_name)
        if topics:
            for t in topics:
                purpose = f" — {t.purpose}" if t.purpose else ""
                lines.append(f"• #{t.alias}: {t.display_name}{purpose}")
        else:
            lines.append("• No topics registered (run `hermes workspace eternal-example --apply`)")
    except Exception:
        lines.append("• Run `hermes workspace list` to see registered topics")

    lines.extend([
        "",
        "**Mention Syntax**",
        "• `@hermes <task>` — invoke Hermes directly",
        "• `@codex <task>` — code generation",
        "• `@glm <task>` — cost-efficient coding",
        "• `@blazemind <spec>` — parallel swarm",
        "• `@all <task>` — broadcast to all agents",
        "",
        "**Adding a New Agent**",
        "• See: `hermes workspace guide` for the compatibility contract",
        "• The agent must be in the Telegram group with appropriate permissions",
        "• Add it to `workspace.agent_registry.agents` in config.yaml",
        "",
        "**Diagnostics**",
        "• `hermes workspace drift` — check config consistency",
        "• `hermes workspace ops-index` — full ops index",
        "• `/whereami` in any topic — verify routing",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Feature readiness diagnostics
# ---------------------------------------------------------------------------

def inline_mode_diagnostics() -> str:
    """Return a BotFather inline-mode readiness checklist."""
    return """\
**Inline Mode Readiness Checklist**

Inline mode lets users type `@huntingtonjeff_bot query` in any chat to
get results without adding the bot to that chat.

**BotFather Steps (manual — cannot be done via API):**
☐ Open @BotFather → /mybots → huntingtonjeff_bot → Bot Settings → Inline Mode
☐ Toggle Inline Mode ON
☐ Optionally set an inline placeholder: "Type a command or query..."
☐ If you want inline results in groups: enable "Allow Groups" inline setting

**Code-side status:**
• The bot currently reports `supports_inline_queries: false`
• python-telegram-bot will begin receiving InlineQuery updates once BotFather
  enables inline mode — no additional code changes are required to start
  receiving them
• To handle them: add an InlineQueryHandler in the Telegram platform adapter

**Current limitation:**
`can_connect_to_business: false` — Business messaging requires a Telegram
Premium subscription and manual BotFather configuration.

**Verification:**
After enabling inline mode in BotFather:
  hermes doctor   # Check bot config status
  # Or: curl https://api.telegram.org/bot<TOKEN>/getMe | jq .result.supports_inline_queries
"""


def bot_compat_contract() -> str:
    """Return the compatibility contract for adding a new external agent/bot."""
    return """\
**Agent Compatibility Contract**

To add a new external AI agent/bot to the Eternal workspace:

**1. Telegram Setup**
• Add the bot to the Eternal group
• Grant appropriate permissions (can_send_messages at minimum)
• If the agent needs its own topic lane: create a forum topic and note the thread_id

**2. Config Entry** (workspace.agent_registry.agents in config.yaml)
```yaml
workspace:
  agent_registry:
    agents:
      my-agent:
        display_name: "My Agent"
        description: "Brief description of what this agent does."
        capabilities: ["coding", "research"]
        route_target: "telegram:-1003932124823:<thread_id>"
        topic_lane: "<topic-alias>"
        cost_risk: "low"   # low | medium | high
        invocation_examples:
          - "@my-agent do the thing"
        notes: "Any operational notes."
        enabled: true
```

**3. Channel Prompt** (optional but recommended)
Add a channel prompt so Hermes knows the topic context:
```yaml
telegram:
  channel_prompts:
    "-1003932124823:<thread_id>": "This topic is for <agent-name> tasks."
```

**4. Verification**
```bash
hermes workspace list      # Agent appears in registry
hermes workspace drift     # No config inconsistencies
hermes workspace guide     # Agent in guide output
# In Telegram: /agent_status  → roster includes new agent
# In Telegram: /guide         → new agent listed
```

**5. Multi-agent Routing**
• Hermes can @mention the bot in Telegram to delegate tasks
• The external bot must respond to @mentions or specific commands
• For bot-to-bot: the agent must be a Telegram bot with its own token
• For Hermes orchestration: use `delegate_task` or a cron job

**6. Constraints**
• `can_read_all_group_messages: false` on this bot — only messages that
  explicitly mention the bot or use slash commands will trigger it
• Bot-to-bot interaction is possible via Telegram @mentions in group topics
• Hermes cannot programmatically create bots — use BotFather
"""
