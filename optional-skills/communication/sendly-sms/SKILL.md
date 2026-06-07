---
name: sendly-sms
description: >
  Send and manage SMS, OTP/verification codes, and two-way text conversations
  through Sendly. Use when the user asks to text someone, send a one-time
  passcode, notify a phone number, check whether a message was delivered, set up
  an agent that people can text, or pick the right kind of phone number/sender.
  Covers when to use OTP vs plain SMS, how Sendly's carrier verification works,
  domestic vs international sending, and choosing a two-way-capable sender.
platforms: [linux, macos, windows]
version: 1.0.0
author: Sendly
license: MIT
category: communication
metadata:
  hermes:
    tags: [communication, sms, otp, messaging, sendly, notifications]
required_environment_variables:
  - name: SENDLY_API_KEY
    prompt: "Sendly API key"
    help: "Create one at https://sendly.live/api-keys (test key = sandbox, live key = real SMS)"
    required_for: "sending SMS and OTP through Sendly"
---

# Sendly SMS

Send text messages, one-time passcodes, and run two-way SMS conversations through
[Sendly](https://sendly.live). Sendly runs carrier verification for you, so there
is no approval gauntlet before you can send.

This skill assumes the Sendly MCP server (`@sendly/mcp`) is connected, which
exposes the tools below. If it isn't, add it first (see
https://sendly.live/docs/integrations/hermes), or call the REST API directly with
`Authorization: Bearer $SENDLY_API_KEY` against `https://sendly.live`.

## When to Use

- The user wants to **text a phone number** (a notification, reminder, reply).
- The user wants to **send a one-time passcode** and **verify** it.
- The user wants to **check delivery** of something already sent.
- The user wants people to **text the agent** (two-way) and is choosing a number.
- The user is unsure **which sender** to use (toll-free vs local vs alphanumeric).

Do NOT use for email or chat-platform messaging — only SMS/phone numbers.

## Quick Reference

| Task | Tool | Notes |
|---|---|---|
| Send one SMS | `send_sms` | `to`, `text`; `messageType` `transactional` or `marketing` |
| Send a passcode | `send_otp` | Sendly generates + delivers the code |
| Verify a passcode | `check_otp` | pass the code the user received |
| Send to many | `send_batch` | list of recipients, one body |
| Bulk campaign | `send_campaign` | larger audience, marketing |
| List conversations | `list_conversations` | inbound/outbound threads |
| Read a thread | `get_conversation` | full history for one number |
| Suggested replies | `get_suggested_replies` | AI-drafted responses |
| Save a draft | `create_draft` | human-in-the-loop approval |
| Balance / usage | account tools | credits remaining, transactions |

Phone numbers are **E.164** (`+15551234567`). Sandbox test numbers like
`+15005550000` work with a `sk_test_` key.

## Procedure

### Send a one-off SMS
Call `send_sms` with `to` (E.164) and `text`. Use `messageType: "transactional"`
for service messages (codes, alerts, confirmations) and `"marketing"` for
promotional content. SMS is **plain text** — strip markdown; the agent's
formatting will render literally.

### Send and verify a one-time passcode
Always use the OTP flow for verification codes — **never** hand-roll a code in a
plain `send_sms`. Call `send_otp` with the recipient; Sendly generates, delivers,
and tracks the code. To verify, call `check_otp` with the code the user reports.
This handles expiry and attempt limits for you.

### Check delivery
A send returns a `status` that progresses `queued → sent → delivered` (or
`failed`). Re-read the message (or `list_conversations`) to confirm. `delivered`
means it reached the handset.

### Set up two-way (people text the agent)
Two-way runs through the Sendly platform adapter (the gateway channel), not this
skill's send tools. The agent's number must be able to **receive** — see sender
choice below. Setup: https://sendly.live/docs/integrations/hermes-sms.

### Pick the right sender
- **US / Canada, two-way** → a **toll-free** number. It sends *and* receives.
  Sendly submits the required carrier verification for you.
- **International, two-way** → a local number where the country supports it.
- **One-way notifications only** → an **alphanumeric sender ID** (a brand name).
  It's send-only; recipients can't reply, so it can't drive a two-way agent.

## Pitfalls

- **Test vs live keys.** A `sk_test_` key **simulates** everything (no real SMS,
  no credits) — great for development. Switch to `sk_live_` for real delivery.
- **Unverified live account simulates.** A `sk_live_` key on an unverified
  account also simulates. Verify at https://sendly.live/verify first.
- **New US/Canada toll-free numbers** need carrier verification before real
  sends; Sendly runs it, but until it's done a send may be simulated. Don't
  assume a brand-new toll-free can deliver instantly.
- **Domestic vs international.** A US toll-free can't send *internationally* — to
  reach another country use a sender enabled for that destination, or the user's
  send may be rejected.
- **One message per segment is billed.** Long replies split into multiple
  segments; keep messages tight.
- **Two-way denies unknown senders by default.** Configure an allowlist of who
  may chat the agent.
- **No encryption.** Don't send secrets/PII over SMS beyond OTP codes.

## Verification

- A `send_sms`/`send_otp` call returns a message with a `status` — confirm it is
  `queued` (accepted) and later `delivered`.
- For OTP, `check_otp` returns whether the code was valid.
- To confirm what actually went out, `list_conversations` or re-read the message
  and check `from`, `to`, and `status`.
