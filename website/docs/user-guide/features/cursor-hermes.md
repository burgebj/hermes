---
sidebar_position: 5
title: "Cursor & Hermes"
description: "Connect Cursor to Hermes MCP — skills/context mode vs live gateway mode, path overrides, and source-of-truth hierarchy"
---

# Cursor & Hermes

Hermes exposes a stdio MCP server so Cursor (and Claude Code, Codex, etc.) can read fleet context and optionally control a running gateway. This page separates **what works without a gateway** from **live operational control**, and documents **which layer is authoritative** when documents disagree.

## Quick setup

1. Copy the example config and edit paths for your machine:

```bash
cp .cursor/mcp.json.example .cursor/mcp.json
```

2. Ensure the launcher is executable and the venv exists:

```bash
chmod +x hermes-mcp-serve
./setup-hermes.sh   # or: pip install -e ".[mcp,dev]"
```

3. In Cursor: enable the **hermes** MCP server (Settings -> MCP). Restart the IDE if tools do not appear.

4. Optional: run `hermes doctor --mcp` or `hermes mcp doctor` to check launcher, Cursor config, tool registration, and gateway reachability.

### Recommended `mcp.json` environment

| Variable | Purpose |
|----------|---------|
| `HERMES_REPO` | Hermes platform checkout (this repo) |
| `HERMES_HOME` | Profile directory (`~/.hermes` or `~/.hermes/profiles/<name>`) |
| `HERMES_AGENTS_DIR` | **Runtime** fleet agents directory (SOUL.md, HEARTBEAT.md) |

Resolution order for agent documents: **`HERMES_AGENTS_DIR`** -> `HERMES_REPO/agents/` -> `HERMES_HOME/hermes-agent/agents/`.

For multi-repo fleets, point `HERMES_AGENTS_DIR` at the operational repo (e.g. `your-product/agents/`) and keep `hermes-agent/agents/AGENT_REGISTRY.json` as **index only** (no duplicate SOUL trees).

Do **not** commit machine-specific paths in the shared `.cursor/mcp.json`; use `.cursor/mcp.json.example` as the template and keep local overrides in your clone or gitignored copy.

## Two MCP modes

Hermes MCP is really two products behind one server:

### Skills / context mode (no gateway)

**Works offline** from disk: custom agents, registry, learnings, knowledge layer, artifacts.

| Tool | Purpose |
|------|---------|
| `fleet_context_snapshot` | One-call bounded fleet bootstrap for IDEs |
| `agent_health_summary` | Compact actionable health anomalies without the full registry dump |
| `town_brief` | Human-facing Town/Cursor status, source-of-truth paths, and next MCP calls |
| `skills_list` | Agent SOUL.md dirs + repo `skills/` catalog |
| `skills_read` | Read SOUL.md or skill files |
| `agents_list` | Registry + optional heartbeat files |
| `agents_get` | Registry entry + SOUL + files for one agent |
| `knowledge_read` | `latest_state`, held specs, operator brief, etc. |
| `knowledge_query` | Bounded deterministic keyword query over knowledge graph artifacts |
| `learnings_read` | `.learnings/memory.md` and namespaces |
| `artifacts_list` | Browse `artifacts/` tree |

Use this mode for: editing agents, pipeline code, audits, PRs, and Cursor Cloud sessions that only need fleet cognition.

For a concise session start, call `town_brief()` first. Use
`fleet_context_snapshot(summary=True)` when the agent needs structured
bootstrap data without text blobs, and use the full snapshot only when a task
needs learnings or latest-state excerpts.

### Live ops / gateway mode

**Requires** `hermes gateway` (or an already-running gateway) and populated `HERMES_HOME/sessions/`.

Messaging tools: `conversations_list`, `messages_read`, `messages_send`, `events_poll`, `events_wait`, bridge-observed approvals, `channels_list`, etc. Approval responses are best-effort for approvals observed by the MCP bridge; they are not a durable gateway approval API.

Use this mode for: steering live Telegram/Discord/Slack sessions, approvals, and operational messaging.

If messaging tools fail with session/DB errors, the gateway is probably not running -- that does **not** mean skills tools are broken.

## Source of truth hierarchy

When layers disagree, use this precedence (highest first):

| Priority | Layer | Authority |
|----------|--------|-----------|
| 1 | Runtime wrappers, cron, production scripts | **Execution truth** -- what actually runs |
| 2 | `HERMES_AGENTS_DIR/<agent>/SOUL.md`, `IDENTITY.md`, `HEARTBEAT.md` | **Behavioral truth** -- how the agent must act |
| 3 | `AGENT_REGISTRY.json` | **Index / discovery** -- names, lanes, metadata; not a substitute for SOUL |
| 4 | Knowledge layer (`artifacts/ops/knowledge_layer/`, ledgers) | **Operational state** -- production status, holds |
| 5 | `.learnings/` | **Memory / reference** -- operator notes, HOT memory |
| 6 | `CLAUDE.md`, `.cursor/rules/` | **IDE workflow** -- session rituals, not runtime overrides |

**Anti-pattern:** Treating registry JSON or synthesized summaries as behavioral truth while runtime SOUL.md says something else. That causes identity drift (e.g. audit wrappers vs live SOUL).

## Session bootstrap

Use `fleet_context_snapshot` for a single-call bounded bootstrap that returns registry summary, HOT learnings excerpt, `latest_state` digest, and held-spec flags. For finer control, call the individual tools per the checklist in `.cursor/rules/hermes-fleet.mdc` or `CLAUDE.md`.

For Cursor Cloud agents, `.cursor/mcp.cloud.json.example` is a portable
template that keeps `HERMES_REPO` tied to `${workspaceFolder}` and leaves
`HERMES_AGENTS_DIR` empty for local override. Copy it to `.cursor/mcp.json`
inside the cloud workspace when you want a clean cloud-only MCP setup.

## Read-only fleet tools (by design)

Skills/knowledge MCP tools are **read-only**. That is intentional for governed fleets (auditability, no silent SOUL mutation from the IDE).

Writable surfaces (e.g. append-only `learnings_append`) require provenance and governance specs before they ship. Do not bypass this with ad-hoc file edits that skip review.

## Multi-repo topology

A common mature layout:

| Repo / path | Role |
|-------------|------|
| `hermes-agent` | Platform: CLI, gateway, MCP transport, `AGENT_REGISTRY.json` index |
| `your-product` | Operational truth: `agents/<name>/SOUL.md`, pipelines, artifacts |
| MCP | Federation layer: Cursor reads product agents via `HERMES_AGENTS_DIR` |

## Related docs

- [MCP (Model Context Protocol)](./mcp.md) -- Hermes as MCP *client* to external servers
- [ACP](./acp.md) -- VS Code / Zed / JetBrains adapter
- `CLAUDE.md` -- session checklist for Claude Code/Cursor agents in this repo

## Roadmap (high leverage)

| Item | Benefit |
|------|---------|
| Spec-aware edit guards | Prevents governed edits without held-spec and contradiction context |
| Agent dependency graph | Shows Lane A/B/C, pipeline dependencies, and stale heartbeat impact |
