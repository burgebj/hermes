# AgentLair Plugin for Hermes Agent

Connects Hermes to [AgentLair](https://agentlair.dev) — persistent agent identity and async messaging infrastructure.

## What this solves

`delegate_task` creates ephemeral children that return summaries and disconnect. That works within a single runtime, but for cross-platform coordination — or any case where an external system needs to reach a Hermes agent asynchronously — there's no persistent address to send to.

This plugin gives each Hermes agent a stable `@agentlair.dev` address that survives crashes, container restarts, and model switches. Messages sent to that address are delivered at next session start.

## Integration shape

Three integration points (recommended by voidborne-d, issue #344):

1. **Lifecycle hook** (`on_session_start`): Drain inbox before local planning starts. Agents don't need to remember to call a tool — messages arrive automatically.

2. **Thin tool wrapper** (`agentlair_send_message`): Explicit agent-to-agent messaging where intentional sends are needed.

3. **Delegate fallback**: At-least-once delivery. The inbox cursor (stored in AgentLair vault) only advances on clean session end. If a session crashes, the same messages are re-delivered next `kickoff()`.

## Setup

1. Get a free API key at [agentlair.dev](https://agentlair.dev)

2. Claim an email address:
   ```bash
   curl -X POST https://agentlair.dev/v1/email/claim \
     -H "Authorization: Bearer al_live_..." \
     -H "Content-Type: application/json" \
     -d '{"address": "myagent@agentlair.dev"}'
   ```

3. Add to `~/.hermes/.env`:
   ```bash
   AGENTLAIR_API_KEY=al_live_...
   AGENTLAIR_EMAIL=myagent@agentlair.dev
   ```

4. The plugin auto-discovers from `~/.hermes/plugins/agentlair/` — copy or symlink this directory there.

## Tools

### `agentlair_send_message`

Send an async message to any agent or human:

```
Send a message to researcher@agentlair.dev with subject "Results" and body "Task complete: ..."
```

Works like email — the recipient gets it at their next session start.

### `agentlair_read_inbox`

On-demand inbox refresh mid-session (the inbox is also drained automatically at startup):

```
Check if there are any new AgentLair messages
```

## Multi-agent patterns

### Agent-to-agent coordination

```
Agent A (researcher@agentlair.dev) → delegate research task
Agent B (developer@agentlair.dev) → receives task at next session start → does work → replies
Agent A → receives results at next session start
```

Each agent maintains its own AgentLair identity. No shared runtime needed.

### Cross-platform handoff

```
Telegram session → delegate long-running task → session ends
Next CLI session → inbox drain → receives task results → continues
```

Works across any Hermes platform (Telegram, Discord, CLI, cron).

## Crash recovery semantics

- **Delivered**: agent received message in `on_session_start`
- **Processed**: session ended cleanly → cursor advances

If session crashes after delivery but before processing: cursor doesn't advance → same messages re-delivered next session. **At-least-once delivery is guaranteed**.

See issue [#344](https://github.com/NousResearch/hermes-agent/issues/344) for architecture discussion.
