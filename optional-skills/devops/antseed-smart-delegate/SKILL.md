---
name: antseed-smart-delegate
description: "Use when delegating LLM calls through AntSeed P2P network. Auto peer selection by task type, cost-aware routing, fallback on failure. Requires funded wallet + buyer proxy."
version: 2.1.0
author: "Hermes Agent"
license: MIT
platforms: [linux, macos, windows]
required_environment_variables:
  - name: ANTSEED_IDENTITY_HEX
    prompt: AntSeed buyer identity (64 hex chars, no 0x prefix)
    help: "Run: antseed buyer wallet create  →  cat ~/.antseed/identity.key"
    required_for: opening payment channels
prerequisites:
  commands: [antseed]
metadata:
  hermes:
    tags: [antseed, p2p, delegation, smart-routing, peer-selection, fallback]
    related_skills: []
    requires_toolsets: [terminal]
---

# AntSeed Smart Delegate

> **Prerequisite:** Funded AntSeed wallet + running buyer proxy. See `references/setup.md`.

## When to Use

- User asks to delegate via AntSeed
- Previous AntSeed delegation failed (502/timeout/402)
- User wants best peer+model for a specific task type

**Don't use for:** Direct LLM calls through OpenAI/Anthropic. Tasks not needing model inference.

## Quick Reference

| Command | When |
|---------|------|
| `bash ${HERMES_SKILL_DIR}/scripts/discover.sh models` | List all live models grouped by category |
| `bash ${HERMES_SKILL_DIR}/scripts/discover.sh models --json` | Same as JSON |
| `bash ${HERMES_SKILL_DIR}/scripts/discover.sh best <task>` | Best peer+model for task |
| `delegate_task(provider="antseed", model="<result>", goal="...")` | Delegate |

`<task>`: `code` | `research` | `vision` | `chat` | `cheap` | `any`

## Procedure

1. **Check proxy** — `curl -sf http://127.0.0.1:8377/v1/models | head`. If down → `antseed buyer start`
2. **Find best peer** — `bash ${HERMES_SKILL_DIR}/scripts/discover.sh best <task>`. Read `recommended.model` and `recommended.peer_id`.
3. **Pin peer** — `antseed buyer connection set --peer <peer_id>`
4. **Delegate** — `delegate_task(provider="antseed", model="<model>", goal="...")`
5. **On failure** — Use `fallback_chain` from output. Max 3 retries, then alert user.

## Error Handling

| Error | Fix |
|-------|-----|
| proxy down | `antseed buyer start` |
| no peer pinned | `discover.sh best <task>` → pick → pin |
| no funds | `antseed buyer deposit 1` |
| 502/timeout | Next peer in fallback chain |
| 400 model not found | Re-run `discover.sh` (catalog drift) |
| 402 | Alert user — needs more funds |

## Pitfalls

- **Unicode tables:** AntSeed CLI uses `│` (U+2502). Script uses Python for parsing.
- **openai-responses protocol** requires streaming. `discover.sh` prefers `chat_completions`.
- **Reserve ceiling ≠ price:** Peer may require $1 reserve even for cheap models.
- **No real data in examples:** Placeholders only.

## Verification

- [ ] `bash ${HERMES_SKILL_DIR}/scripts/test.sh` passes
- [ ] `antseed buyer balance` shows deposits
- [ ] Proxy returns models: `curl -sf http://127.0.0.1:8377/v1/models`

## References

- `references/setup.md` — CLI install, wallet, config wiring
