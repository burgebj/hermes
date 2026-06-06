---
sidebar_position: 25
---

# Channel Routing

Route different chats, groups, or channels to different Hermes profiles so a single gateway can serve multiple isolated personas with their own models, credentials, memories, and identities.

## Use Cases

- **Family group** uses a family-friendly model with its own SOUL.md and warm personality
- **Work channel** routes to a developer-focused profile with technical skills enabled
- **Personal DMs** stay on the default profile with your primary assistant identity
- **Research group** uses a different model endpoint optimized for long-context reasoning

## Configuration

### Step 1: Create Profiles

Each routed chat needs a corresponding profile. Create them with:

```bash
hermes profile create family --clone
hermes profile create work --clone
hermes profile create research --clone-all
```

Customize each profile's `SOUL.md`, `memories/USER.md`, `memories/MEMORY.md`, and `config.yaml` (model, provider, base_url). Each profile can have its own `.env` with separate API keys.

### Step 2: Configure Routes

Add a `channel_routes` section to your `~/.hermes/config.yaml`:

```yaml
channel_routes:
  "group:abc123...":
    profile: personal
  "group:def456...":
    profile: work
  "group:ghi789...":
    profile: family
  "+123****7890":
    profile: personal
```

### Route Key Formats

The route key is the full `chat_id` as seen by the gateway. Common formats:

| Platform | DM / Direct | Group | Topic / Thread |
|---|---|---|---|
| Signal | `+123****7890` | `group:abc123...` | — |
| Telegram | `-1001234567890` | `-1001234567890` (same as DM) | thread_id appended |
| Discord | `channel_id` | `channel_id` | — |
| Slack | `Dxxxxx` (DM) | `Cxxxxx` (channel) | — |

Find your chat IDs in the gateway logs:

```bash
hermes logs --follow 2>&1 | grep "inbound message"
```

### Step 3: Restart Gateway

```bash
hermes gateway restart
```

## What Gets Routed

When a route matches, the following are overridden from the target profile:

| Setting | Source | Override |
|---|---|---|
| Model | Profile `config.yaml` → `model.default` or `model.model` | ✅ Replaces gateway default |
| Provider | Profile `config.yaml` → `model.provider` | ✅ Replaced |
| Base URL | Profile `config.yaml` → `model.base_url` | ✅ Replaced |
| API Key | Profile `.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) | ✅ Replaced |
| SOUL.md | Profile `SOUL.md` | ✅ Replaces global SOUL.md |
| Memories | Profile `memories/USER.md` + `memories/MEMORY.md` | ✅ Replaces global memories |
| Context files | Global `AGENTS.md`, `CLAUDE.md` | ⛔ Skipped (not loaded) |
| Skills | Bundled skills from gateway profile | ⚠️ Uses gateway's skills, not routed profile's |

## Finding Chat IDs

### Signal

```bash
# From gateway logs — look for the group ID in inbound messages:
hermes logs 2>&1 | grep "Signal.*group" | head -5

# Or from signal-cli directly:
signal-cli -u +YOUR_NUMBER listGroups
```

### Telegram

The chat_id appears in gateway logs. For groups, it's typically a negative number prefixed with `-100`.

### Discord

Channel IDs appear in your browser URL or in gateway logs as `inbound message: platform=discord ... chat=CHANNEL_ID`.

## Troubleshooting

### Route not matching

Check the gateway log for route resolution:

```bash
hermes logs 2>&1 | grep "Channel route"
```

You should see lines like:
```
Channel route: group:abc123... -> profile 'family' (model=agent, base_url=http://...)
```

If you see `Channel route resolution failed`, the profile name may be misspelled or the profile doesn't exist.

### Profile not found

Make sure the profile was created:

```bash
hermes profile list
```

The profile name in `channel_routes` must match exactly (case-insensitive).

### Model not being used

Check that the profile's `config.yaml` has a valid model configuration:

```yaml
# ~/.hermes/profiles/family/config.yaml
model:
  default: my-model.gguf
  provider: custom
  base_url: http://192.168.100.25:8000/v1
```

Or as a simple string:
```yaml
model: gpt-4o
```

### Memory not loading

The profile needs a `memories/` directory with `USER.md` and/or `MEMORY.md`:

```bash
mkdir -p ~/.hermes/profiles/family/memories
echo "User: Family members" > ~/.hermes/profiles/family/memories/USER.md
echo "Be warm and casual" > ~/.hermes/profiles/family/memories/MEMORY.md
```

## Advanced: Simple String Routes

For brevity, you can use a plain string instead of a dict when the profile name is the only setting:

```yaml
channel_routes:
  "group:abc123": family        # equivalent to {"profile": "family"}
  "+123****7890": personal      # equivalent to {"profile": "personal"}
```