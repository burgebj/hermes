# Prometheus Avatar Plugin

Avatar assets, voice, and chat for Hermes. Live2D engine today, 3D engine on the roadmap.

This plugin is the "deep integration" path. If you want the lightweight documentation-only
path, see the companion skill at `optional-skills/creative/prometheus-avatar/` (PR #9754).

## Status

**v0.1 MVP ships stub handlers** that return deterministic demo data so reviewers can load
the plugin on any Hermes install without extra configuration.

Wiring the live Prometheus service arrives in **v0.2**. The service exposes avatar assets
(skins, voices, personas, effects), a voice-clone pipeline, and a real-time chat channel.
Configuration will flow through environment variables documented here once the service is
publicly reachable.

## Installation

### Automatic (once the Hermes plugin registry includes this plugin)

```bash
hermes plugins install jc-myths/hermes-agent
# Then copy only the plugin dir to your ~/.hermes/plugins/
```

### Manual

```bash
# Drop the plugin into the user plugins directory.
mkdir -p ~/.hermes/plugins
cp -r plugins/prometheus_avatar ~/.hermes/plugins/

# Restart Hermes. The plugin auto-discovers on next launch.
hermes plugins list   # you should see prometheus_avatar listed with Source=local
```

Hermes supports three discovery paths: `~/.hermes/plugins/`, project-local `./.hermes/plugins/`,
and pip entry-points under the `hermes_agent.plugins` group.

## Tools

| Tool | Purpose |
|------|---------|
| `avatar_list_assets` | List demo assets for a category: `skins`, `voices`, `personas`, or `effects`. |
| `avatar_describe` | Return metadata for a single asset ID returned by `avatar_list_assets`. |
| `avatar_status` | Report plugin version and current mode (`stub` in v0.1). |

### `avatar_list_assets`

Input:
```json
{ "category": "skins" }
```

Output:
```json
{
  "category": "skins",
  "mode": "stub",
  "assets": [
    { "id": "prometheus_avatar:skin/demo-neon", "name": "Neon Demo", "rarity": "common" },
    { "id": "prometheus_avatar:skin/demo-koi",  "name": "Koi Demo",  "rarity": "rare" }
  ]
}
```

### `avatar_describe`

Input:
```json
{ "asset_id": "prometheus_avatar:skin/demo-neon" }
```

Output:
```json
{
  "id": "prometheus_avatar:skin/demo-neon",
  "name": "Neon Demo",
  "category": "skins",
  "rarity": "common",
  "preview_url": null,
  "description": "Demo skin used by the v0.1 stub. Returns deterministic metadata only.",
  "mode": "stub"
}
```

### `avatar_status`

Input: `{}`

Output:
```json
{
  "service": "ok",
  "plugin": "prometheus_avatar",
  "version": "0.1.0",
  "mode": "stub",
  "note": "v0.1 returns demo data. v0.2 calls the live Prometheus service configured via environment variables (see README)."
}
```

## Positioning

Avatar engine: **Live2D today, 3D engine on the roadmap**. The plugin surface and tool
schemas are engine-agnostic. Consumers talk to `prometheus_avatar:*` identifiers, not
to a specific renderer, so a future 3D engine can ship without breaking tool callers.

## Companion skill

The skill path (`optional-skills/creative/prometheus-avatar/`) is a docs-only capability
module that loads with `hermes skills list` and `hermes skills inspect`. The skill covers
the same capability surface without registering tools in the tool registry.

Pick the skill when you want a human or agent to read a capability description. Pick this
plugin when you want the agent to call avatar-related tools directly during a turn.

## Roadmap

- **v0.2** wires the three tools to the live Prometheus service. Reads configuration
  from `PROMETHEUS_AVATAR_ENDPOINT` and an auth token env var (name TBD).
- **v0.3** adds `on_session_start` and `on_session_end` hooks for preloading avatar
  state and flushing per-session telemetry.
- **v0.4** opens a streaming voice channel and an image-preview tool.

## License

Apache 2.0. Same license as Hermes Agent itself.
