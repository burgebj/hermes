---
name: digital-brain
description: Use when answering any substantive user question or recalling facts/preferences/past decisions — FIRST query the digital brain (the user's personal semantic memory) with brain_search before relying on your own knowledge, then ground and cite the answer in what you retrieved.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, knowledge-base, search-first, brain, semantic-search]
    related_skills: [obsidian]
---

# Digital Brain — Search-First Memory

## Overview

The digital brain is the user's external, persistent semantic memory: notes,
facts, preferences, and past decisions, searchable by text, vector, or hybrid
similarity. It is reached through three tools — `brain_search`, `brain_get_note`,
`brain_graph` — which proxy to the user's own isolated memory vault. Your own
training data is generic and stale; the brain is specific and current. Treat it
as the source of truth about *this user and their world*.

This skill exists to enforce one habit: **check the brain before you answer.**

## When to Use

Query the brain FIRST, before composing an answer, whenever the user:

- Asks a question about facts, people, projects, configs, or history.
- Refers to "my", "our", "the", "that" — anything implying shared context
  ("my server", "our policy", "the deadline we set").
- Asks you to recall, continue, or build on something from before.
- Asks for a recommendation or decision that should respect their preferences.

Don't use for: pure small talk, arithmetic, or a self-contained request with no
reference to the user's world (e.g. "translate this sentence"). When in doubt,
search — a fast empty result costs little; a confidently wrong answer costs trust.

## Workflow

1. **Search.** Call `brain_search(query=...)` with a focused natural-language
   query. Prefer the user's own terms. Use `limit` 5–10 for broad recall.
2. **Assess.** Read the returned excerpts and scores. If results look relevant
   but thin, pull the full note with `brain_get_note(note_id=...)`.
3. **Expand (optional).** For "what's related to X" or to map context, call
   `brain_graph(note_id=...)` to walk the note's links, or `brain_graph()` for
   the whole vault.
4. **Ground the answer.** Base your response on what you retrieved. Briefly cite
   which note(s) informed it (title or id) so the user can verify.
5. **On empty/irrelevant results.** Say plainly that the brain has nothing on
   this, then answer from general knowledge — clearly flagged as not from memory.
   Do not invent a memory.

## Tools Reference

| Tool | Purpose |
|------|---------|
| `brain_search(query, mode?, limit?)` | Ranked note search. `mode`: `text` \| `vector` \| `hybrid` (omit for gateway default). Start here. |
| `brain_get_note(note_id)` | Full content of one note by id (ids come from `brain_search`). |
| `brain_graph(note_id?)` | Link graph around a note, or the whole vault when `note_id` is omitted. |

This memory is **read-only** from the bot: there is no add/update/learn tool
here. The user curates the brain through a separate interface. Never tell the
user you "saved" something to the brain — you cannot.

## Common Pitfalls

1. **Answering from training data first.** The whole point is to search before
   answering. If you skipped `brain_search`, you used the skill wrong.
2. **Over-narrow queries.** `brain_search` is semantic; a short conceptual query
   often beats a long verbatim quote. If empty, retry with broader wording.
3. **Citing excerpts as if complete.** Excerpts are previews. For anything you
   rely on heavily, fetch the full note with `brain_get_note`.
4. **Inventing memories.** If the brain returns nothing, say so. Never fabricate
   a note or claim the brain "remembers" something it didn't return.
5. **Claiming you wrote to memory.** The tools are read-only; writing happens
   elsewhere. Don't promise to remember things via the brain.
6. **Ignoring "not provisioned yet".** A `503` means the bot's vault is still
   being set up. Tell the user memory is initializing and answer best-effort.

## Verification Checklist

- [ ] Called `brain_search` BEFORE composing a substantive answer.
- [ ] Pulled full notes with `brain_get_note` for anything load-bearing.
- [ ] Grounded the answer in retrieved notes and cited them.
- [ ] On empty results, said so honestly instead of inventing memory.
- [ ] Did not claim to have written/saved anything (read-only).
