# Live Documentation Sources

A structured reference for fetching current information about Hermes Agent itself. Use this when you are uncertain about your own capabilities, when cached knowledge seems incorrect, or when the user asks about features not covered in your active context.

## When to Check

- User asks about a Hermes feature you can't confidently describe
- Cached knowledge of a capability seems stale or incomplete
- User reports behavior that contradicts what you expect from a feature
- You need to verify whether a feature exists before telling the user it doesn't
- User asks about configuration keys, env vars, or tool semantics

## How to Check (in order)

1. **This reference** — find the topic below, try the docs URL first via WebFetch
2. **Source code** — find the source path below and read the relevant file directly. Source is ground truth.
3. **Verification command** — run the listed command to check live system state

---

## Topic Reference

### Configuration & Setup

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Config schema | `https://hermes-agent.nousresearch.com/docs/user-guide/configuration` | `~/.hermes/hermes-agent/hermes_cli/config.py` (search for DEFAULT_CONFIG) | `hermes config` |
| Environment variables | `https://hermes-agent.nousresearch.com/docs/reference/environment-variables` | `~/.hermes/hermes-agent/hermes_cli/config.py` (env var definitions) | `hermes config env-path` |
| .env file | — | `~/.hermes/.env` | `hermes doctor` |
| Profiles | `https://hermes-agent.nousresearch.com/docs/user-guide/profiles` | `~/.hermes/hermes-agent/hermes_cli/main.py` (profile subcommands) | `hermes profile list` |
| Provider setup | `https://hermes-agent.nousresearch.com/docs/integrations/providers` | `~/.hermes/hermes-agent/hermes_cli/main.py` (provider resolution) | `hermes model` |

### CLI & Commands

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| CLI reference | `https://hermes-agent.nousresearch.com/docs/reference/cli-commands` | `~/.hermes/hermes-agent/hermes_cli/main.py` (argparse) | `hermes --help` |
| Slash commands | `https://hermes-agent.nousresearch.com/docs/reference/slash-commands` | `~/.hermes/hermes-agent/hermes_cli/commands.py` (COMMAND_REGISTRY) | `/help` |
| Session management | — | `~/.hermes/hermes-agent/hermes_state.py` (SessionDB) | `hermes sessions list` |

### Tools

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Tool reference | `https://hermes-agent.nousresearch.com/docs/reference/tools-reference` | `~/.hermes/hermes-agent/tools/` (one file per tool) | `hermes tools list` |
| Tool registry | — | `~/.hermes/hermes-agent/tools/registry.py` | — |
| Toolset definitions | — | `~/.hermes/hermes-agent/toolsets.py` (_HERMES_CORE_TOOLS) | `hermes toolsets` |
| Tool discovery | — | `~/.hermes/hermes-agent/model_tools.py` (discover_builtin_tools) | — |

### MCP

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| MCP guide | `https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp` | — | `hermes mcp list` |
| MCP client | — | `~/.hermes/hermes-agent/tools/mcp_tool.py` | `hermes mcp test <name>` |
| MCP OAuth bridge | — | See hermes-agent skill `references/mcp-oauth-bridge.md` | — |

### Gateway & Platforms

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Messaging guide | `https://hermes-agent.nousresearch.com/docs/user-guide/messaging/` | `~/.hermes/hermes-agent/gateway/` | `hermes gateway status` |
| Platform adapters | — | `~/.hermes/hermes-agent/gateway/platforms/<platform>.py` | `/platforms` |
| Gateway runner | — | `~/.hermes/hermes-agent/gateway/run.py` | — |
| Platform registry | — | `~/.hermes/hermes-agent/gateway/platform_registry.py` | — |

### Agent Loop & System Prompt

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| AIAgent core loop | — | `~/.hermes/hermes-agent/run_agent.py` (AIAgent.run_conversation) | — |
| System prompt builder | — | `~/.hermes/hermes-agent/agent/prompt_builder.py` | — |
| Context files (SOUL.md, AGENTS.md) | — | `~/.hermes/hermes-agent/agent/prompt_builder.py` (load_soul_md, build_context_files_prompt) | — |
| Skills index injection | — | `~/.hermes/hermes-agent/agent/prompt_builder.py` (build_skills_system_prompt) | — |
| Memory manager | — | `~/.hermes/hermes-agent/agent/memory_manager.py` | `hermes memory status` |
| Auxiliary client | — | `~/.hermes/hermes-agent/agent/auxiliary_client.py` | — |

### Skills System

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Skills catalog | `https://hermes-agent.nousresearch.com/docs/reference/skills-catalog` | `~/.hermes/hermes-agent/agent/skill_utils.py` | `hermes skills list` |
| Skills hub | — | `~/.hermes/hermes-agent/tools/skills_hub.py` | `hermes skills browse` |
| Skill indexing | — | `~/.hermes/hermes-agent/agent/prompt_builder.py` (build_skills_system_prompt) | — |

### Cron & Scheduling

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Cron guide | `https://hermes-agent.nousresearch.com/docs/user-guide/features/cron` | `~/.hermes/hermes-agent/cron/` | `hermes cron list` |
| Scheduler | — | `~/.hermes/hermes-agent/cron/scheduler.py` | — |
| Job model | — | `~/.hermes/hermes-agent/cron/jobs.py` | — |

### Plugins

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Plugin management | — | `~/.hermes/hermes-agent/hermes_cli/plugins.py` | `hermes plugins list` |
| Memory provider plugins | — | `~/.hermes/hermes-agent/plugins/memory/` | — |
| Plugin loading | — | `~/.hermes/hermes-agent/plugins/` | — |

### Memory & Persistence

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Memory guide | `https://hermes-agent.nousresearch.com/docs/user-guide/features/memory` | `~/.hermes/hermes-agent/agent/memory_provider.py` | `hermes memory status` |
| Built-in memory store | — | `~/.hermes/hermes-agent/agent/memory_manager.py` | — |
| User profile | — | `~/.hermes/hermes-agent/agent/memory_manager.py` | — |

### Kanban System

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Kanban DB | — | `~/.hermes/hermes-agent/hermes_cli/kanban_db.py` | `/kanban list` |
| Kanban CLI | — | `~/.hermes/hermes-agent/hermes_cli/kanban_cli.py` | `hermes kanban` |

### TUI & Skins

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| TUI (Ink/React) | — | `~/.hermes/hermes-agent/ui-tui/src/` | `hermes --tui` |
| Skin engine | — | `~/.hermes/hermes-agent/hermes_cli/skin_engine.py` | `/skin` |

### Voice & STT/TTS

| Topic | Docs URL | Source Path | Verification |
|-------|----------|-------------|--------------|
| Voice config | — | See hermes-agent skill section on Voice & Transcription | `/voice status` |

### Agent Loop Internals

| Topic | Source Path |
|-------|-------------|
| Prompt caching | `~/.hermes/hermes-agent/agent/prompt_caching.py` |
| Context compression | `~/.hermes/hermes-agent/agent/context_engine.py` |
| Credential pools | `~/.hermes/hermes-agent/agent/credential_sources.py` |
| Shell hooks | `~/.hermes/hermes-agent/agent/shell_hooks.py` |
| File safety scanner | `~/.hermes/hermes-agent/agent/file_safety.py` |
| Goal/judge system | `~/.hermes/hermes-agent/hermes_cli/goals.py` |
