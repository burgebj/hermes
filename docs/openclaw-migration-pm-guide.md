# Migrating from OpenClaw to Hermes: A PM's Real-World Guide

> Written from firsthand experience by a Product Manager who built a personal AI assistant with OpenClaw and migrated to Hermes.

---

## Who This Guide Is For

You're a Product Manager (or a non-engineer who built something with OpenClaw) and you're considering Hermes. You want to know what actually transfers, what breaks, and what gets meaningfully better — without the marketing copy.

This guide is the one I wish existed when I made the switch.

---

## What You'll Keep (And What Changes)

### Your SOUL.md Persona — Fully Transferable

Your `SOUL.md` file — the system prompt that shapes your agent's personality and working style — migrates directly to Hermes.

Hermes imports it automatically during setup:

```bash
hermes claw migrate  # Detects ~/.openclaw/SOUL.md and imports it
```

Or manually:

```bash
cp ~/.openclaw/SOUL.md ~/.hermes/SOUL.md
```

**PM tip:** Your SOUL.md is the most valuable thing you've built. Don't lose it. It encodes how you think, how you want your assistant to respond, and your communication preferences. Back it up.

---

### Your Memories — Imported With One Command

OpenClaw stores memories in `MEMORY.md` and `USER.md`. Hermes imports both:

```bash
hermes claw migrate --preset user-data
```

This brings over:
- Everything in your `MEMORY.md`
- User profile notes from `USER.md`
- Your command allowlist (what the agent is allowed to do without asking)

**What changes:** Hermes has a richer memory system. After migration, your memories are searchable across sessions using FTS5 full-text search. You can ask "what did we decide about X last month?" and get an actual answer.

---

### Your Skills — Preserved as OpenClaw Imports

Any skills you created in OpenClaw land in:

```
~/.hermes/skills/openclaw-imports/
```

They'll still work. Hermes skills are procedural memory — step-by-step procedures the agent learned to do. OpenClaw skills carry over because both systems use a similar format.

**What gets better:** In Hermes, skills *self-improve*. If you run a skill and the agent finds a faster path, it updates the skill automatically. Your OpenClaw skills become a starting point, not a ceiling.

---

### API Keys — Migrated Automatically (With Your Approval)

Hermes asks before importing secrets:

```bash
hermes claw migrate  # Will prompt: "Import API keys from OpenClaw? [y/N]"
```

Keys it can import: Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs.

---

## The Real Differences (From a PM Perspective)

### 1. Multi-Platform Messaging: You're No Longer Laptop-Bound

The biggest practical difference: Hermes runs a gateway process that connects to Telegram, Discord, Slack, WhatsApp, Signal, and others — all from a single configuration.

With OpenClaw, I could only interact through the local terminal. With Hermes, I send tasks from my phone while commuting and get results before I arrive.

**Setup:**
```bash
hermes gateway setup   # Configure your messaging platforms
hermes gateway start   # Start the gateway
```

Then just message your bot on Telegram as you would a colleague.

---

### 2. Cross-Session Memory: It Actually Remembers

OpenClaw's memory is file-based. Hermes has a learning loop: it creates memories during conversations, summarizes sessions, and builds a model of who you are over time.

The difference in practice: after a few weeks, Hermes knows your preferred output format, the projects you're tracking, and your communication preferences — without you re-explaining them.

---

### 3. The Model Isn't Locked In

One of the pain points with OpenClaw was model switching — it required config file edits. Hermes makes this a one-liner:

```bash
hermes model   # Interactive picker
# or
hermes model openai:gpt-4o
hermes model anthropic:claude-3-5-sonnet
hermes model google:gemini-2.0-flash
```

As a PM evaluating models, this is genuinely useful. You can A/B test model responses on the same task without changing your setup.

---

### 4. Onboarding Is Still the Hard Part

Honest note: Hermes has better onboarding than OpenClaw, but it's still technical. If OpenClaw's setup took you 2 hours, budget 90 minutes for Hermes — slightly faster, but not zero friction.

The `hermes setup` wizard handles most of it:

```bash
hermes setup  # Walks you through everything, detects OpenClaw automatically
```

If your machine isn't developer-ready (no Python, no Node.js), you'll hit walls. The installer handles this, but be patient with it.

---

## Migration Checklist for PMs

Before you run `hermes claw migrate`, do this:

- [ ] Back up `~/.openclaw/SOUL.md` — this is irreplaceable if you've customized it
- [ ] Run `hermes claw migrate --dry-run` first — see what would be imported without touching anything
- [ ] Review your MEMORY.md before importing — clean out anything outdated or incorrect
- [ ] Decide which API keys to migrate — you can skip secrets and add them manually later
- [ ] Note your current OpenClaw command allowlist — review it in Hermes after migration

---

## The One Thing to Do First After Migrating

Open a conversation and say:

```
Here's what I built with OpenClaw and how I used it: [brief description].
Here's what I want to be able to do with you: [your goals].
Here's my working style: [how you think and communicate].
```

This seeds Hermes's user model faster than any migration script. The agent learns from conversation, so the first conversation matters.

---

## Resources

- [Hermes Migration Docs](https://hermes-agent.nousresearch.com/docs) — official reference
- `hermes claw migrate --help` — full CLI options
- [OpenClaw PM Workflow](https://github.com/Jgupta14051994/openclaw-pm-workflow) — example SOUL.md and prompt templates from a real PM setup

---

*Contributed by a PM who actually did this migration. If something here is wrong or out of date, please open an issue or PR.*
