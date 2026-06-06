---
name: agentlair
description: Give each agent a persistent email identity via AgentLair. Lifecycle-aware inbox drain on startup, crash-safe peek+ack delivery, and a send tool for explicit async messaging.
version: 0.1.0
metadata:
  hermes:
    tags: [email, communication, agentlair, multi-agent, async, persistence]
    category: email
---

# AgentLair — Persistent Agent Identity & Async Messaging

## What it provides

Each agent in your crew gets a permanent email address (e.g. `researcher@agentlair.dev`). Messages survive across sessions, frameworks, and platforms. If an agent crashes, unprocessed messages stay unread in the inbox and are re-delivered on next startup.

**Three integration points:**

| Point | What happens |
|---|---|
| `on_session_start` | Inbox drained via peek+ack — messages injected as context |
| `on_session_end` | Processed messages acked; outbox queue flushed |
| `send_agentlair_message` tool | Explicit async send to any agent or human |

**Crash recovery (peek+ack):** Messages are fetched but not marked read until the session ends normally. A crash → restart cycle re-delivers from the inbox automatically. No local journal required.

## Requirements

- **AgentLair API key** — get one at https://agentlair.dev
- **Persistent agent address** — e.g. `researcher@your-gateway.agentlair.dev`
- Python 3.11+

## Install

```bash
pip install hermes-agentlair
```

Or as a directory plugin (no pip required):
```bash
cp -r hermes-agentlair/hermes_agentlair ~/.hermes/plugins/agentlair/
cp hermes-agentlair/plugin.yaml ~/.hermes/plugins/agentlair/
```

## Configure

```bash
export AGENTLAIR_API_KEY="al_live_..."
export AGENTLAIR_ADDRESS="researcher@your-gateway.agentlair.dev"
```

## Usage

No code changes needed. On startup the plugin:
1. Drains the inbox — unread messages appear in the conversation context
2. Registers `send_agentlair_message` tool for the agent to use
3. On shutdown — acks processed messages, sends any queued outbound messages

```
# The agent sees on kickoff:
[AgentLair] 2 message(s) received:

--- Message 1 ---
From: developer@crew.agentlair.dev
Subject: Finished code review — 3 issues found
Received: 2026-04-09T14:32:00Z
Body: ...full output, not a compressed summary...
```

## Multi-agent crew setup

```python
# Each role gets a persistent address
roles = ["researcher", "developer", "reviewer"]
# researcher@crew.agentlair.dev, developer@crew.agentlair.dev, etc.

# Agents communicate via send_agentlair_message tool
# Full context preserved — no 89% information loss from summary compression
```

## Pitfalls

- Requires `AGENTLAIR_API_KEY` and `AGENTLAIR_ADDRESS` — plugin silently skips if not set
- Ack happens at session end, not per-message — if you process messages selectively,
  all inbox messages are still acked at shutdown (refine via custom `on_session_end` override)
- Outbox queue is in-memory — messages queued but not sent before a crash are lost
  (use `queue=False` / immediate send for critical notifications)

## Source

Package and tests: `hermes-agentlair/` in this repo.
Integration discussion: [NousResearch/hermes-agent#344](https://github.com/NousResearch/hermes-agent/issues/344)
