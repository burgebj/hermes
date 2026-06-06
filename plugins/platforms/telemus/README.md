# Telemus platform plugin

Hermes gateway adapter for Telemus / VR AI Chat headless devtools.

## Telemus side

Start Telemus headless with the JSONL socket enabled:

```bash
cd /home/ubuntu/vr-ai-chat
vrai_headless --socket 8765
# or: scripts/run_headless_devtools.sh
```

The adapter prefers stable channel/event devtools methods when present:

- `Devtools.getInfo` for health/capability probe
- `Channels.status` for channel protocol state
- `Channels.sendMessage` for outbound Hermes messages into Telemus
- `Channels.pollEvents` for inbound events with monotonic `eventId`
- `Channels.ack` to prune delivered events

It falls back to legacy methods when the channel API is unavailable:

- `AI.sendMessage`
- `AI.getTranscript`

## Hermes config

Either set environment variables in `~/.hermes/.env`:

```bash
TELEMUS_DEVTOOLS_HOST=127.0.0.1
TELEMUS_DEVTOOLS_PORT=8765
TELEMUS_AGENT_INDEX=-1
TELEMUS_HOME_CHANNEL=agent:-1
```

or use `gateway.platforms.telemus.extra`:

```yaml
gateway:
  platforms:
    telemus:
      enabled: true
      extra:
        host: 127.0.0.1
        port: 8765
        agent_index: -1
        poll_interval_seconds: 1.0
        inbound_speakers: [User, Human, You]
        prefer_channels: true
```

## Notes

- `agent:-1` means Telemus' selected/default agent. `agent:0` targets a concrete agent slot.
- Channel-event polling acknowledges delivered event ids and avoids transcript inference when supported by Telemus.
- Transcript fallback de-duplicates entries by agent, transcript index, speaker, and text.
- This connector assumes the devtools endpoint is local/trusted; do not expose it publicly without an auth layer and command allowlist.
