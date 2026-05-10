# Obsidian Memory Provider

Long-term memory for Hermes, persisted as plain markdown notes inside an
Obsidian vault. Every fact the agent stores becomes a `.md` file you can
read, edit, link, sync and back up like any other Obsidian note.

## Why pick this provider

* **Human-readable storage** — open the vault, see what the agent remembers.
* **No vendor lock-in** — uninstall Hermes and the memory is still yours.
* **Hand-editable** — fix a wrong fact in the editor; the agent will see the change.
* **Zero deps** — Python stdlib + filesystem. No API keys, no servers.

## Requirements

* An Obsidian vault on disk.
* Either:
  * `OBSIDIAN_VAULT_PATH` set in `~/.hermes/.env` (already used by the bundled
    `note-taking/obsidian` skill), **or**
  * `plugins.obsidian.vault_path` in `~/.hermes/config.yaml`.

## Setup

```bash
hermes memory setup     # select "obsidian"
```

Or activate manually after editing config.yaml:

```bash
hermes config set memory.provider obsidian
```

## Config

Under `plugins.obsidian` in `~/.hermes/config.yaml`:

| Key              | Default                              | Description                                                  |
|------------------|--------------------------------------|--------------------------------------------------------------|
| `vault_path`     | `$OBSIDIAN_VAULT_PATH`               | Absolute path to the vault used as memory store.             |
| `memory_folder`  | `Memory`                             | Subfolder of the vault where memory notes live.              |
| `mirror_builtin` | `true`                               | Mirror MEMORY.md / USER.md additions into the vault.         |
| `sync_turns`     | `false`                              | Append every turn to a daily session log under `sessions/`.  |
| `prefetch_limit` | `5`                                  | Max recall snippets injected into context per turn.          |

## Storage layout

```
<vault>/
  Memory/
    README.md                          # auto-created on first run
    facts/
      2026-05-02-171523-ab12cd-the-user-prefers-tabs-over-spaces.md
      …
    sessions/
      2026-05-02.md                    # only when sync_turns is true
```

Each fact note has YAML frontmatter:

```markdown
---
id: ab12cd34ef56
created: 2026-05-02T17:15:23
session: <session_id>
tags: [example]
category: user_pref
source: tool
---

The user prefers tabs over spaces in Python.
```

## Tools exposed

| Tool           | Action enum                                            |
|----------------|--------------------------------------------------------|
| `vault_memory` | `add`, `search`, `recall`, `list`, `update`, `remove`  |

## Recall behaviour

Token-overlap keyword search across fact bodies, tags and category. Top
matches (capped by `prefetch_limit`) are injected into the system prompt
each turn under a `## Obsidian Memory recall` heading.

This is deliberately simple — it stays dependency-free and predictable.
If you need semantic search later, layer it on top (or pair this provider
with another one in a future multi-provider setup).
