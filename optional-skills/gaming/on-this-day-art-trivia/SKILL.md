---
name: on-this-day-art-trivia
description: |
  Use when the user asks for an "on this day" history guessing game with an
  AI-generated image of the scene 30 seconds before a historic event. Drives
  Telegram-native interactive play through a companion plugin and hook.
version: 0.1.1
author: Hermes Agent contributors
license: MIT
metadata:
  hermes:
    tags: [game, history, telegram, image-gen, interactive]
    surfaces: [telegram, cli]
    state_db: ~/.hermes/data/on-this-day-art-trivia/trivia.db
    companion_plugin: on_this_day_art_trivia
    companion_hook: on-this-day-art-trivia
---

# On This Day — Art Trivia

A Telegram-native history guessing game. The bot picks a historically
important event for today's date, generates an image of the **scene 30
seconds before** the event happened, and sends it with a caption that
contains *only the date (including the year) and the location*. The user
replies with a guess. Streaks, hints, achievements, and daily subscriptions
are tracked locally.

Image generation is delegated to the Hermes built-in image engine via the
`gpt-image-2` bridge skill (which uses whatever provider is configured in
the host environment). No direct API credentials are required in the skill
or the game package itself.

## When this skill applies

The skill is invoked through the `/on-this-day-art-trivia` slash command
(handled by the companion **hook** at `~/.hermes/hooks/on-this-day-art-trivia/`)
and through inbound Telegram replies (intercepted by the companion **plugin**
at `~/.hermes/plugins/on_this_day_art_trivia/`). The skill itself is the
core engine — sources, scoring, prompt construction, persistence, matching,
achievements, and the optional Telegram client used as a fallback when
Hermes' built-in send mechanism cannot deliver an image with caption.

## Subcommands

| Subcommand                                                | Effect                                                                      |
|-----------------------------------------------------------|-----------------------------------------------------------------------------|
| `/on-this-day-art-trivia`                                 | Start a new challenge for today's date.                                     |
| `/on-this-day-art-trivia guess <answer>`                  | Submit a guess explicitly (also works in groups).                           |
| `/on-this-day-art-trivia hint`                            | Reveal the next hint (decade → country → initial).                          |
| `/on-this-day-art-trivia reveal`                          | Reveal the answer; resets streak.                                           |
| `/on-this-day-art-trivia stats`                           | Personal stats — correct, attempts, streak, longest, countries.             |
| `/on-this-day-art-trivia achievements`                    | List unlocked achievements.                                                 |
| `/on-this-day-art-trivia subscribe`                       | Receive a daily challenge in this chat.                                     |
| `/on-this-day-art-trivia unsubscribe`                     | Stop daily delivery in this chat.                                           |
| `/on-this-day-art-trivia leaderboard`                     | Top players by total correct.                                               |
| `/on-this-day-art-trivia help`                            | Print this list.                                                            |

## Interaction rules

- **DM mode** — while a challenge is active, plain text in the DM is
  treated as a guess. Only commands (anything starting with `/`) escape.
- **Group mode** — only direct replies to the challenge image, or explicit
  `/on-this-day-art-trivia guess <answer>`, are scored.
- The bot **never** reveals the answer in the initial caption — caption is
  exactly two lines: the full date (including the year) and the location.
- After 3 wrong attempts (default), the streak resets and the answer is
  revealed.

## Source pipeline

1. Britannica `/on-this-day` (editorial).
2. Wikimedia REST `/feed/v1/wikipedia/en/onthisday/all/<MM>/<DD>` (structured).
3. onthisday.com (HTML fallback).
4. Cached fixtures under `scripts/fixtures/MM-DD.json` for fully-offline use.

Each candidate is run through the scoring rubric in `scripts/scoring.py`.
Disqualifying topics (graphic violence, sexual abuse, mass-casualty visuals,
child harm) are hard-rejected — never selected.

## Image generation contract

The skill builds a spoiler-safe prompt in `scripts/prompt_builder.py`. Proper
nouns from the canonical answer are scrubbed; sensitive trigger words are
removed; defence-in-depth blocklist is applied. The prompt asks for the
scene **before** the event, with no central protagonist, no readable text,
no labels, no weapons, no violence.

The resulting prompt is passed to the Hermes built-in image engine through
the `gpt-image-2` bridge skill. The bridge handles provider selection,
authentication, and model routing internally — no API credentials are
needed in this skill package. If the bridge is unavailable, the challenge
still goes out as a text-only message with the same surface caption.

## Persistence

SQLite at `~/.hermes/data/on-this-day-art-trivia/trivia.db`. Schema is
migrated on first use. Tables: `users`, `challenges`, `acceptable_answers`,
`guesses`, `achievements`, `subscriptions`, `schema_version`.

## Daily subscriptions

`python -m scripts.challenge daily` (run from the skill directory) walks
every active subscription and starts a fresh challenge in each chat. Wire
this into Hermes cron with the entry shown in `README.md`.

## Files

- `scripts/challenge.py` — orchestrator + CLI entry point.
- `scripts/sources.py` — Britannica, Wikimedia, onthisday adapters.
- `scripts/scoring.py` — event-scoring rubric.
- `scripts/prompt_builder.py` — spoiler-safe image prompt.
- `scripts/state.py` — SQLite layer.
- `scripts/guess_matcher.py` — exact + fuzzy + anchor-token matching.
- `scripts/achievements.py` — achievement engine.
- `scripts/telegram_api.py` — fallback Telegram Bot API client.
