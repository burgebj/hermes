---
title: Telegram Workspace — Multi-Agent Setup
description: Topic registry, agent roster, multi-agent commands, @mention routing, and workspace diagnostics.
---

Hermes supports a multi-agent Telegram workspace where Hermes orchestrates
multiple AI agents (Codex, GLM, BlazeMind, Nexus, and custom bots) through
named forum topics with friendly aliases.

## Topic Registry

Operator-authored registry under `workspace.topic_registry.topics`. Maps
delivery refs like `telegram:-1001234567890:15` to stable aliases, names, and
purposes. Used by `send_message`, `/whereami`, workspace guides, drift checks,
and ops indexes.

```yaml
workspace:
  topic_registry:
    topics:
      dev-logs:
        target: telegram:-1001234567890:15
        name: "Eternal / #dev-logs"
        purpose: builds/CI/errors

telegram:
  channel_prompts:
    "-1001234567890:15": "This topic is for builds, CI, and error reports."
```

## Agent Registry

Operator-authored agent roster under `workspace.agent_registry.agents`.
Built-in agents (hermes, codex, glm, blazemind, nexus, voice) are always
present. Add custom agents or override built-ins here.

```yaml
workspace:
  agent_registry:
    agents:
      my-agent:
        display_name: "My Agent"
        description: "A custom agent for my workflow."
        capabilities: ["coding", "research"]
        route_target: "telegram:-1003932124823:708"
        topic_lane: "agent-workbench"
        cost_risk: "low"          # low | medium | high
        invocation_examples:
          - "@my-agent do the thing"
        notes: "Deployed on Unraid via launchd."
        enabled: true
```

To disable a built-in agent, set `enabled: false`:

```yaml
workspace:
  agent_registry:
    agents:
      voice:
        enabled: false
```

## Telegram Commands

| Command | Description |
|---------|-------------|
| `/guide` | Multi-agent workspace guide (suitable for pinning) |
| `/agent_status` | Registered agent roster with capabilities and cost |
| `/summon @agent [task]` | Show agent details with inline buttons to dispatch, route, checklist, or cancel |
| `/swarm @a @b [task]` | Multi-agent fanout with confirmation buttons; results route to Multi-Agent Room |
| `/route @agent [task]` | Routing guidance — which topic/target, plus quick action buttons |
| `/checklist [title]` | Create a persistent emulated checklist with toggle buttons |
| `/say <text>` / `/tts <text>` | Generate and send a Telegram voice/TTS reply when a TTS backend is configured |
| `/voice_status` | Show Telegram voice/TTS mode with quick controls |
| `/whereami` | Current topic routing diagnostics |
| `/agents` | Active sessions, processes, async jobs |
| `/status` | Session info |

## CLI Commands

```bash
hermes workspace list           # List registered topics
hermes workspace guide          # Show workspace + agent guide
hermes workspace ops-index      # Full ops index with env/cron/services
hermes workspace drift          # Check config consistency
hermes workspace eternal-example          # Dry run for Eternal group
hermes workspace eternal-example --apply  # Apply Eternal example config
```

## Mention Syntax

Use `@alias` in any Telegram message to invoke a specific agent:

```
@hermes run the test suite
@codex add pagination to the users API
@glm refactor the data pipeline
@blazemind spec: build.yaml
@nexus who calls process_payment?
@all check status
```

Hermes parses leading `@mentions` in incoming Telegram messages before the
normal LLM conversation loop. Known aliases are routed to the workspace router:

- Single-agent messages (`@codex fix tests`) dispatch that agent and deliver the
  result to the agent's configured topic lane.
- Multi-agent messages (`@codex @glm review this`) fan out and deliver results
  to the Multi-Agent Room topic.
- `@all status` expands to every enabled registered agent.
- Unknown Telegram usernames are ignored and fall through as normal chat.

The router currently invokes local CLIs when available (`codex`, `glm`, `bm
quick`). If a CLI is missing, Telegram receives an explicit unsupported/needs
setup response instead of a fake result.

## Per-Topic Safety Controls

Each topic gets a `channel_prompts` entry that shapes Hermes's behavior:

```yaml
telegram:
  channel_prompts:
    "-1003932124823:14":  "Alerts topic — respond tersely, no lengthy output."
    "-1003932124823:15":  "Dev-logs — summarize failures and next commands."
    "-1003932124823:16":  "Media topic — accept images/documents, describe them."
    "-1003932124823:17":  "Decisions — log changes in compact durable records."
    "-1003932124823:707": "Briefings — concise summaries, action-oriented."
    "-1003932124823:708": "Agent Workbench — full agent/workspace admin mode."
```

Run `hermes workspace drift` to verify prompts and registry are in sync.

## Voice & TTS

Voice messages from Telegram are auto-transcribed when `stt.enabled: true`:

```yaml
stt:
  enabled: true
  provider: local   # local (faster-whisper), groq, openai, mistral
```

Use `/voice on` in Telegram to enable voice input. Use `/voice tts` to have
replies spoken. Use `/say <text>` or `/tts <text>` for one-shot spoken replies.
`/voice_status` shows the current mode and adds quick inline buttons. The
`voice` agent alias routes voice-specific tasks.

## Image & Document Ingestion

Images and documents sent to the **#media** topic (thread 16), and dev
artifacts sent to **#dev-logs** (thread 15), are handled by Hermes's media
message handler. The gateway now adds lane-aware inline buttons in those topics
for Analyze, OCR/Summarize, Route to dev-logs, and Add to checklist actions.
The channel prompt still shapes the underlying agent response:

```yaml
telegram:
  channel_prompts:
    "-1003932124823:16": "Media topic — describe images, extract text from docs, summarize files."
```

For dev artifacts (logs, diffs, screenshots), use **#dev-logs** (thread 15).

## Checklist Buttons

Native Telegram Bot API checklists are currently business-account gated, so
Hermes emulates checklists with ordinary messages plus inline keyboard buttons.
Checklist JSON is persisted under `$HERMES_HOME/checklists/`, scoped by
chat/thread/user metadata, and survives gateway restarts. Buttons toggle items
between done/undone and update the original Telegram message.

## Inline Mode

Inline mode lets users type `@huntingtonjeff_bot query` from any chat.
This requires a **manual BotFather step** — it cannot be enabled via API:

1. Open @BotFather → `/mybots` → `huntingtonjeff_bot`
2. Bot Settings → Inline Mode → Enable
3. Run diagnostics to verify:

```bash
python scripts/telegram-multiagent-diagnostics.py
```

## Adding a New External Agent

See the full compatibility contract via:

```bash
# In CLI
python -c "from gateway.agent_registry import bot_compat_contract; print(bot_compat_contract())"

# In Telegram
/guide
```

Summary:
1. Add the bot to the Eternal Telegram group
2. Create a forum topic (note the thread_id)
3. Add `workspace.agent_registry.agents.<alias>` to config.yaml
4. Add a `telegram.channel_prompts` entry for the topic
5. Run `hermes workspace drift` — should report no issues
6. Verify with `/agent_status` in Telegram

## Diagnostics

```bash
python scripts/telegram-multiagent-diagnostics.py  # Full diagnostic run
hermes workspace drift                              # Config consistency
hermes workspace ops-index                          # Env/cron/services overview
/whereami                                           # Topic routing (in Telegram)
/agent_status                                       # Agent roster (in Telegram)
```

## Eternal Group Quick-Start

For Blaze's Eternal group (`-1003932124823`), apply the example config:

```bash
hermes workspace eternal-example           # Dry run
hermes workspace eternal-example --apply   # Apply with backup
```

This adds registry entries and channel prompts for all known topics (14, 15, 16,
17, 707, 708, 823) and merges cleanly with any existing config.
