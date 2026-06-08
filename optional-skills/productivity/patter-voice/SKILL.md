---
name: patter-voice
description: Run a full AI voice agent over real phone calls with the Patter SDK — outbound and inbound, Twilio or Telnyx, with OpenAI Realtime, ElevenLabs ConvAI, or a custom STT/LLM/TTS pipeline. Includes live transcripts and a local dashboard.
version: 1.0.0
author: PatterAI
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [voice, telephony, calls, twilio, telnyx, openai, deepgram, elevenlabs, agent-loop, transcripts, realtime, convai, pipeline]
    related_skills: [telephony]
    category: productivity
    homepage: https://github.com/PatterAI/Patter
---

# Patter Voice — Full AI Voice Agents over Real Phone Calls

This optional skill teaches Hermes to drive [Patter](https://github.com/PatterAI/Patter), an open-source SDK that runs a complete voice agent loop on real phone calls — inbound or outbound — over Twilio or Telnyx.

Where the built-in `telephony` skill is great for *placing a call and reading back a result*, Patter is for *running an autonomous voice agent on the line* with live transcripts, barge-in, tool calls during the conversation, and a local web dashboard.

## When to use this skill vs. `telephony`

| You want to... | Use |
|---|---|
| Send/receive SMS, buy a Twilio number, place a one-shot call | `telephony` |
| Use Bland.ai / Vapi as the AI calling backend | `telephony` |
| Run an autonomous voice **agent loop** (multi-turn, real-time, with tools) | **patter-voice** |
| Use Telnyx instead of (or alongside) Twilio | **patter-voice** |
| Get live transcripts streamed during the call and persisted after | **patter-voice** |
| Use OpenAI Realtime, ElevenLabs ConvAI, or a custom STT->LLM->TTS stack | **patter-voice** |
| View calls + costs + metrics in a local dashboard | **patter-voice** |
| Trigger calls from another tool via MCP | **patter-voice** (pair with the `patter-voice` MCP) |

If both skills are installed, use `telephony` for "send a text / make a single call with a pre-canned message" and `patter-voice` for "have an AI talk to a human on the phone".

## How it works — three engine modes

Patter ships three engines. Pick one per agent.

| Mode | When | Latency | Cost |
|---|---|---|---|
| `OpenAIRealtime2` (default) | Default for everything. One key, lowest latency. | ~200 ms | $$$ |
| `ElevenLabsConvAI` | Turn-taking conversations, robust to long pauses. | ~600 ms | $$ |
| `Pipeline` (STT + LLM + TTS) | Custom stack — e.g. Deepgram + Claude + ElevenLabs voice. | ~800 ms | $-$$$$ |

Patter handles WebSocket framing, audio transcoding (mulaw 8 kHz / pcm 16 kHz), VAD, barge-in, cost tracking, the local tunnel, and the dashboard. You write the system prompt, optional tools, and the engine choice.

## Install

```bash
hermes skills install official/productivity/patter-voice
```

Then install the Python SDK in whatever environment Hermes will exec into:

```bash
pip install "getpatter>=0.6.2"
```

TypeScript users:

```bash
npm install getpatter@^0.6.2
```

## Required env vars

Set the ones you actually need. At minimum: one carrier + `OPENAI_API_KEY` for the default Realtime engine.

| Var | Required | Used for |
|---|---|---|
| `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN` / `TWILIO_PHONE_NUMBER` | yes (or Telnyx) | Twilio carrier |
| `TELNYX_API_KEY` + Telnyx number | yes (or Twilio) | Telnyx carrier |
| `OPENAI_API_KEY` | yes for `OpenAIRealtime2` | LLM + speech |
| `ELEVENLABS_API_KEY` | for `ElevenLabsConvAI` or Pipeline TTS | conversational voice |
| `DEEPGRAM_API_KEY` | for Pipeline STT | speech-to-text |

The optional `patter-voice` MCP server can be installed in parallel so other agents can trigger calls via MCP — see `hermes mcp install official/patter-voice`.

## Examples

### A. Outbound call with the default OpenAI Realtime engine (Python)

```python
import asyncio
from getpatter import Patter, Twilio, OpenAIRealtime2

async def main():
    phone = Patter(carrier=Twilio(), phone_number="+15550001234")
    agent = phone.agent(
        engine=OpenAIRealtime2(),
        system_prompt=(
            "You are Mia, the AI receptionist for Acme Plumbing. "
            "Greet the caller warmly. Help them book a service visit. "
            "Keep replies under two sentences."
        ),
        first_message="Hi, this is Mia at Acme Plumbing — how can I help?",
    )
    await phone.serve(agent, tunnel=True)

asyncio.run(main())
```

Then in another shell, dial out with the SDK CLI:

```bash
patter call "+15551234567" --to "your_running_server_url"
```

### B. Inbound agent on a Telnyx number (Python)

```python
import asyncio
from getpatter import Patter, Telnyx, OpenAIRealtime2

async def main():
    phone = Patter(carrier=Telnyx(), phone_number="+15550009876")
    agent = phone.agent(
        engine=OpenAIRealtime2(),
        system_prompt=(
            "You are the support line for Acme. Identify the caller's issue, "
            "answer if known, and offer to transfer to a human otherwise."
        ),
        first_message="Acme support, how can I help today?",
    )
    # Patter exposes a built-in `transfer_call` tool — the agent can call it
    # mid-conversation. No custom code needed for transfer.
    await phone.serve(agent, tunnel=True)

asyncio.run(main())
```

### C. Custom STT + LLM + TTS Pipeline (TypeScript)

```typescript
import {
  Patter, Twilio, Pipeline,
  Deepgram, Anthropic, ElevenLabs,
} from "getpatter";

const phone = new Patter({ carrier: new Twilio(), phoneNumber: "+15550001234" });

const agent = phone.agent({
  engine: new Pipeline({
    stt: new Deepgram(),
    llm: new Anthropic({ model: "claude-sonnet-4-5" }),
    tts: new ElevenLabs({ voiceId: "Rachel" }),
  }),
  systemPrompt:
    "You are a polite cold-caller for Acme. Ask if they want a quote on roof repair. " +
    "Stop immediately if they say no.",
  firstMessage: "Hi, this is Acme calling about your roof — do you have 30 seconds?",
});

await phone.serve(agent, { tunnel: true });
```

## Live transcripts and the dashboard

Patter persists every call (caller, callee, duration, cost, full transcript) to a local SQLite database and exposes them via a built-in dashboard:

```bash
patter dashboard
# opens http://localhost:8080
```

Inside Hermes, pull a transcript with the `patter-voice` MCP tool `get_transcript`, or read directly from the SDK in a session:

```python
from getpatter import Patter, Twilio

phone = Patter(carrier=Twilio(), phone_number="+15550001234")
for call in phone.calls.list(limit=5):
    print(call.id, call.status, call.duration_s, call.cost_usd)
    print(call.transcript)
```

## Safety rules

1. Real telephony minutes cost real money — confirm with the user before placing outbound calls.
2. Never dial emergency numbers.
3. Do not use Patter for harassment, spam, impersonation, or anything illegal.
4. Treat third-party phone numbers as sensitive operational data — do not save them to Hermes memory unless the user asks.
5. The agent's `transfer_call` tool moves a live human conversation — only enable it when transfer is a wanted outcome.
6. Some carriers and regions restrict who you can dial. Twilio trial accounts in particular have allow-list limits.

## What this skill does not do

- It is **not** a managed cloud service. Everything runs locally; you bring the carrier keys.
- It does **not** buy phone numbers — use the `telephony` skill or the Twilio / Telnyx console for provisioning.
- It does **not** send SMS — Patter is voice-only today. Use `telephony` for SMS.

## References

- Patter SDK (Python + TypeScript): https://github.com/PatterAI/Patter
- patter-mcp (Streamable HTTP MCP server): https://github.com/PatterAI/patter-mcp
- Patter skills bundle (build-voice-agent, configure-telephony, inspect-calls-and-metrics, add-tools-and-handoffs, setup-patter): https://github.com/PatterAI/skills
- Hermes integration page: https://docs.patter.com/integrations/hermes
