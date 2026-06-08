---
title: "GBrain / Minions HTTP Transport"
description: "Real HTTP transport adapter for Hermes queue envelopes and Minions completion callbacks"
---

# GBrain / Minions HTTP Transport

This is the real transport adapter shape after the file-spool reference worker.

It keeps the same queue protocol, but swaps the transport layer for HTTP.

Files:

- `agent/gbrain_minions_transport.py`
- `scripts/gbrain_minions_enqueue.py`
- `scripts/gbrain_minions_complete.py`
- `gateway/platforms/api_server.py` (`POST /api/minions/completions`)

## What this gives you

- Hermes can enqueue job envelopes to a remote GBrain/Minions HTTP endpoint
- Minions workers can POST completion envelopes back into Hermes
- Hermes can then deliver or reconcile those results through the existing callback path

So the loop is:

1. Hermes builds envelope
2. enqueue shim POSTs to GBrain/Minions
3. worker executes
4. completion shim POSTs back to Hermes
5. Hermes callback handler delivers or reconciles result

## Enqueue script

Hermes side:

```bash
python scripts/gbrain_minions_enqueue.py
```

It reads a queue envelope from stdin and POSTs it to:

- `HERMES_GBRAIN_ENQUEUE_URL`

Optional auth:

- `HERMES_GBRAIN_API_KEY`

Timeout:

- `HERMES_GBRAIN_TIMEOUT` (default `30`)

### Example Hermes wiring

```bash
export HERMES_BACKGROUND_BACKEND=command
export HERMES_BACKGROUND_ENQUEUE_CMD='python scripts/gbrain_minions_enqueue.py'

export HERMES_DELEGATION_BACKEND=command
export HERMES_DELEGATION_ENQUEUE_CMD='python scripts/gbrain_minions_enqueue.py'

export HERMES_CRON_BACKEND=command
export HERMES_CRON_ENQUEUE_CMD='python scripts/gbrain_minions_enqueue.py'

export HERMES_GBRAIN_ENQUEUE_URL='https://gbrain.example/api/minions/jobs'
export HERMES_GBRAIN_API_KEY='replace-me'
```

## Completion script

Worker side:

```bash
python scripts/gbrain_minions_complete.py
```

It reads a completion envelope from stdin and POSTs it to Hermes:

- `HERMES_GBRAIN_COMPLETION_URL`

Optional auth:

- `HERMES_GBRAIN_COMPLETION_KEY`
- falls back to `API_SERVER_KEY`

Timeout:

- `HERMES_GBRAIN_TIMEOUT`

## Hermes callback receiver

Hermes now exposes a receiver endpoint on the API server:

```text
POST /api/minions/completions
```

Auth behavior:

- if `API_SERVER_KEY` is set, Bearer auth is required
- if no API key is configured, the endpoint accepts requests without auth
- don’t expose that to the internet without a real key unless you enjoy pain

### Example completion URL

```bash
export API_SERVER_ENABLED=true
export API_SERVER_HOST=127.0.0.1
export API_SERVER_PORT=8086
export API_SERVER_KEY='replace-me'

export HERMES_GBRAIN_COMPLETION_URL='http://127.0.0.1:8086/api/minions/completions'
export HERMES_GBRAIN_COMPLETION_KEY='replace-me'
```

## What Minions must do

Your actual GBrain/Minions worker only needs three responsibilities:

1. accept the Hermes job envelope
2. execute based on `kind` + `payload`
3. emit a completion envelope back to Hermes

Do not mutate the envelope format per queue backend. That would be dumb.

## Suggested server endpoints on the GBrain side

This Hermes adapter assumes something roughly like:

- `POST /api/minions/jobs` -> enqueue envelope -> return ack JSON

Ack example:

```json
{
  "task_id": "bg_123",
  "backend": "gbrain-minions",
  "queue": "background",
  "message": "accepted"
}
```

Completion callback is handled on the Hermes side, not GBrain side.

## Why this is clean

Because transport and protocol are separate.

- file spool reference worker = local proof lane
- HTTP transport = real remote lane
- same envelope contract in both cases

That means you can change BullMQ, Redis, Postgres, Railway, or some cursed in-house queue later without ripping Hermes apart.
