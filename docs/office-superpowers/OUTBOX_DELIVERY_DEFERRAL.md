# Office report outbox live-delivery deferral

Status: live Telegram/gateway delivery intentionally deferred
Last verified: 2026-05-13
Owner lane for future live sender: Backend/Coder plus Reviewer/QA/Security smoke review

## Current behavior

`scripts/office_report_outbox.py` is a durable local report outbox and dry-run preview tool. It may enqueue redacted report payloads and maintain delivery state fields, but its CLI `send-due` and `retry-failed` commands do not send Telegram or gateway messages.

The CLI commands currently mean:

- `status`: inspect local JSONL outbox counts by state.
- `enqueue`: append a redacted report intent idempotently.
- `send-due`: preview due `pending` records only; no external delivery occurs.
- `retry-failed`: preview due `failed` records only; no external delivery occurs.

Any handoff, runbook, or launch claim must describe those commands as queued/dry-run only unless a future reviewed sender is wired and smoke-tested.

## Durable state fields now required on records

Each normalized outbox record includes:

- `status`: `pending`, `sent`, or `failed` (corrupt rows are counted by status reporting but not loaded as sendable records).
- `attempts`: integer delivery attempt count.
- `last_error`: redacted last failure string, or `null`.
- `next_attempt_at`: UTC timestamp for the next eligible attempt, or `null` after sent.
- `sent_at`: UTC timestamp when a sender marks the record sent, or `null`.
- `delivery_result`: redacted sender return metadata, or `null`.
- `idempotency_key`: stable key derived from board, task id, run id, report type, and payload hash.

The helper `send_due_report_outbox(..., sender=...)` implements state transitions with an injected sender for testability and future integration. It skips already-sent records, increments attempts exactly once per due attempted record, records failed-send errors with exponential retry backoff, and clears retry fields only after sender success.

## Explicit deferral rationale

Live delivery was not enabled in this task because a safe production sender needs all of the following external/operational evidence before the CLI can honestly claim Telegram delivery:

1. A reviewed gateway sender target and policy for which chat/channel receives Office status messages.
2. Credential/config presence checks that do not expose tokens, chat ids, raw user ids, or cookies.
3. A live smoke artifact proving one redacted test message was received by the intended target.
4. Alert-volume controls so current board findings do not spam Akhil.
5. Reviewer/QA/Security validation of no duplicate sends and failure/retry behavior against the live gateway path.

Until those gates exist, the product wording is: "report outbox queued/dry-run only; live Telegram delivery deferred."

## Future live sender acceptance gates

A follow-up live sender may flip the CLI from preview to delivery only after it provides:

- gateway sender implementation or adapter with a constrained target;
- tests that use the same durable outbox state machine;
- a smoke artifact path containing command, timestamp, sanitized target description, and received-message proof;
- rollback instructions to return cron/reporting to `deliver=local` or dry-run mode;
- a reviewer-approved gate scorecard.
