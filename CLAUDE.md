# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Hermes Agent** is a self-improving AI agent built by Nous Research. It creates skills from experience, improves them during use, and runs anywhere (local, VPS, Docker, Daytona, Modal, Singularity). It supports multiple messaging platforms (Telegram, Discord, Slack, WhatsApp, Signal, Email) via a unified gateway, and provides a full terminal TUI.

## Development Setup

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv --python 3.11
source venv/bin/activate
uv pip install -e ".[all,dev]"
```

(Use `.[termux]` on Android/Termux — avoids faster-whisper which has Android-incompatible transitive deps.)

For RL training work:
```bash
git submodule update --init tinker-atropos
uv pip install -e "./tinker-atropos"
```

## Running Tests

**Always use `scripts/run_tests.sh`** — never call pytest directly. The wrapper enforces CI-parity (credential vars unset, TZ=UTC, LANG=C.UTF-8, 4 xdist workers). Running pytest directly on a dev machine with API keys set causes local-vs-CI drift.

```bash
scripts/run_tests.sh                      # full suite
scripts/run_tests.sh tests/gateway/       # one directory
scripts/run_tests.sh tests/tools/test_x.py::test_y  # one test
scripts/run_tests.sh -v --tb=long         # pass through pytest flags
```

## Code Style

- **PEP 8** with practical exceptions (no strict line-length enforcement)
- Comments only for non-obvious intent, trade-offs, or API quirks — don't narrate obvious code
- Catch specific exceptions; use `logger.warning()`/`logger.error()` with `exc_info=True` for unexpected errors

## Architecture

### Entry Points (3 binaries)

| Binary | Entry | Purpose |
|--------|-------|---------|
| `hermes` | `hermes_cli.main:main` | Interactive CLI TUI (classic prompt_toolkit or modern Ink/React) |
| `hermes-agent` | `run_agent:main` | Standalone agent runner |
| `hermes-acp` | `acp_adapter.entry:main` | VS Code/Zed/JetBrains integration |

### Core Dependency Chain

```
tools/registry.py  (no deps — imported by all tool files)
       ↑
tools/*.py  (each calls registry.register() at import time; auto-discovered)
       ↑
model_tools.py  (imports tools/registry, exposes get_tool_definitions, handle_function_call)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

### Agent Loop (`run_agent.py`)

`AIAgent.run_conversation()` is synchronous. It loops calling the LLM with tool schemas until the model returns a plain text response (no tool_calls). Messages are OpenAI-format dicts: `{"role": "system/user/assistant/tool", ...}`. Reasoning content lives in `assistant_msg["reasoning"]`.

Agent-level tools (todo, memory) are intercepted in `run_agent.py` before dispatching to `handle_function_call()` — see `todo_tool.py` for the pattern.

### Tool System (`tools/`)

Every tool file calls `registry.register()` at module level. **Auto-discovery** — no manual import list is needed in `model_tools.py`. Each tool specifies: schema, handler, toolset, check_fn (env var/API key availability), and requires_env. All handlers MUST return a JSON string.

### CLI Architecture (`hermes_cli/`)

- All slash commands are defined in a single `COMMAND_REGISTRY` list of `CommandDef` objects in `hermes_cli/commands.py`. This feeds CLI dispatch, autocomplete, Telegram bot menu, Slack subcommands, and gateway help all from one source.
- Adding an alias to a `CommandDef`'s `aliases` tuple automatically propagates to all consumers.
- The skin engine (`hermes_cli/skin_engine.py`) provides data-driven CLI theming — new skins are YAML data, no code changes.

### TUI Architecture (`ui-tui/` + `tui_gateway/`)

The TUI (`hermes --tui` or `HERMES_TUI=1`) is a full Ink/React terminal UI. TypeScript owns the screen; Python owns sessions, tools, and model calls. They communicate via newline-delimited JSON-RPC over stdio:

```
hermes --tui
  └─ Node (Ink)  ──stdio JSON-RPC──  Python (tui_gateway)
       │                                  └─ AIAgent + tools + sessions
       └─ renders transcript, composer, prompts, activity
```

Built-in TUI commands (`/help`, `/quit`, `/clear`, etc.) are handled locally in TypeScript. Everything else goes to the Python `_SlashWorker` subprocess.

### Gateway (`gateway/`)

A long-running process that bridges messaging platforms to the agent. Platform adapters live in `gateway/platforms/` (telegram, discord, slack, whatsapp, signal, homeassistant, qqbot). The gateway runs its own event loop and translates platform events into agent turns. Config is loaded via direct YAML (not the CLI config loader).

### Profiles (Multi-Instance)

`_apply_profile_override()` in `hermes_cli/main.py` sets `HERMES_HOME` before all module imports. All 119+ references to `get_hermes_home()` from `hermes_constants` automatically scope to the active profile.

### State Store (`hermes_state.py`)

`SessionDB` is a SQLite store (WAL mode, FTS5 full-text search) for session metadata and message history. Replaces the old per-session JSONL approach. Not used for batch runner or RL trajectories (separate systems).

### Plugins (`plugins/`)

Optional extensions discoverable at runtime. Plugins can contribute skills via the skills system.

## Key Constraints

### Prompt Caching

**Do not** change toolsets, reload memories, or rebuild system prompts mid-conversation. Cache validity is maintained throughout the session. The only sanctioned mid-conversation mutation is context compression.

### Path Safety

- All state paths MUST use `get_hermes_home()` from `hermes_constants` — never `Path.home() / ".hermes"`. This was the source of 5 bugs fixed in PR #3575.
- For user-facing messages, use `display_hermes_home()` which shows `~/`-relative paths.
- Tests must redirect `HERMES_HOME` to a temp dir via the `_isolate_hermes_home` autouse fixture — never write to `~/.hermes/`.

### UI Constraints

- Do NOT use `\033[K` (ANSI erase-to-EOL) in spinner/display code — it leaks as literal `?[K` text under prompt_toolkit. Use space-padding instead.
- Do NOT use `simple-term-menu` for interactive menus — rendering bugs in tmux/iTerm2. Use `curses` (stdlib) instead.

### Tool Schema Constraints

- Do not hardcode cross-tool references in schema descriptions (e.g. `browser_navigate` should not say "use web_search"). Those tools may be disabled or unavailable. If a cross-reference is needed, add it dynamically in `get_tool_definitions()` in `model_tools.py`.
- For schema descriptions with file paths, use `display_hermes_home()` to make them profile-aware, since schema is generated at import time (after `_apply_profile_override()` sets `HERMES_HOME`).

### Background Processes

`_last_resolved_tool_names` in `model_tools.py` is process-global. `_run_single_child()` in `delegate_tool.py` saves and restores it around subagent execution. New code that reads this global will see a stale value during child agent runs.

### Cross-Platform Compatibility

- **`termios` and `fcntl` are Unix-only** — always catch both `ImportError` and `NotImplementedError`
- **File encoding** — Windows may save `.env` in `cp1252`; always handle `UnicodeDecodeError`
- **Process management** — `os.setsid()`, `os.killpg()`, signal handling differ on Windows; use `platform.system() != "Windows"` checks
- **Path separators** — use `pathlib.Path` instead of string concatenation

## Config System

Config lives in `~/.hermes/config.yaml` and `~/.hermes/.env` (API keys). See `hermes_cli/config.py` for `DEFAULT_CONFIG` and `OPTIONAL_ENV_VARS`.

There are two separate config loaders:
- `load_cli_config()` — used by CLI mode (`cli.py`)
- `load_config()` — used by `hermes tools`, `hermes setup` (`hermes_cli/config.py`)
- Direct YAML load — used by gateway (`gateway/run.py`)

When adding a new config option, bump `_config_version` to trigger migration for existing users.

## Slash Commands

All commands are in `hermes_cli/commands.py`. To add a new command:

1. Add `CommandDef` to `COMMAND_REGISTRY`
2. Add handler in `HermesCLI.process_command()` (`cli.py`)
3. If gateway-available, add handler in `gateway/run.py`
4. For persistent settings use `save_config_value()`

## Skills System

Skills live in `~/.hermes/skills/`. Skill slash commands are scanned at startup and injected as **user messages** (not system prompt) to preserve prompt caching — see `agent/skill_commands.py`. The skills hub at `agentskills.io` is the open standard registry.

**Should it be a Skill or a Tool?** Almost always a skill. Make it a tool only when it requires end-to-end API key/auth integration, custom binary/streaming data handling, or precise execution that can't be handled via terminal/CLI commands. See `CONTRIBUTING.md` for the full decision guide.

## Commit Convention

Use [Conventional Commits](https://www.conventionalcommits.org):
```
<type>(<scope>): <description>
```
Types: `fix`, `feat`, `docs`, `test`, `refactor`, `chore`. Scopes: `cli`, `gateway`, `tools`, `skills`, `agent`, `install`, `whatsapp`, `security`, etc.