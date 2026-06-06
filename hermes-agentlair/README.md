# hermes-agentlair

AgentLair integration for [Hermes Agent](https://github.com/NousResearch/hermes-agent). Gives your Hermes agent a persistent identity, async email-based messaging, and lifecycle-aware inbox management.

## Design

**Lifecycle-first, crash-safe:**

1. **`on_session_start`** — Drains inbox using peek+ack pattern. Messages are fetched and injected as context, but NOT marked as read until the session ends normally.
2. **`on_session_end`** — Acks processed messages and flushes any queued outbound messages.
3. **`send_agentlair_message` tool** — Send messages explicitly during a session (immediate or queued for session-end).

If the agent crashes mid-session, unprocessed messages remain unread in the inbox and will be re-fetched on next startup. No local persistence required.

## Install

```bash
pip install hermes-agentlair
```

Or as a directory plugin:
```bash
cp -r hermes_agentlair ~/.hermes/plugins/agentlair/
cp plugin.yaml ~/.hermes/plugins/agentlair/
```

## Configure

```bash
export AGENTLAIR_API_KEY="al_live_..."
export AGENTLAIR_ADDRESS="your-agent@agentlair.dev"
```

## Usage

The plugin auto-registers with Hermes Agent. On startup, any unread AgentLair messages are injected into the conversation context. The `send_agentlair_message` tool is available for the agent to send messages.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Related

- [AgentLair](https://agentlair.dev) — Agent identity and communication infrastructure
- [NousResearch/hermes-agent#344](https://github.com/NousResearch/hermes-agent/issues/344) — Integration discussion
