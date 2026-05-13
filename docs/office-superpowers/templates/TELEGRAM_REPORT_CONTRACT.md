# Telegram Reporting Contract for YOLO Office Goals

Status: MVP contract implemented by `hermes_cli.office_superpowers.build_report_payload()` and `scripts/office_report_outbox.py`. Live Telegram delivery is explicitly deferred; the MVP script is queued/dry-run only.

## Payload shape

```json
{
  "schema_version": 1,
  "policy_version": "office-superpowers-v1",
  "report_type": "started|blocked|completed|qa_failed|scope_change|watchdog_digest|doctor_summary",
  "task_id": "t_xxx",
  "title": "safe title",
  "state": "started|blocked|done|qa_failed|scope_change",
  "assignee": "profile",
  "evidence_summary": "short safe summary",
  "artifact_paths": ["safe/path.json"],
  "next_owner_or_action": "profile or next action",
  "blocker_type": null,
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "redaction_status": "checked|redacted"
}
```

## Redaction and privacy

Before writing to the outbox, secret-like values are redacted as `[REDACTED]`. Durable reports must not contain raw tokens, cookies, private keys, passwords, emails, phone numbers, or raw platform user identifiers.

## Outbox behavior

`office_report_outbox.py enqueue` computes an idempotency key from board, task id, run id, report type, and payload hash. Duplicate enqueue attempts return the same key without appending another line. Outbox records carry durable sender-state fields: `status` (`pending|sent|failed`), `attempts`, `last_error`, `next_attempt_at`, and `sent_at`. `status` reports counts and oldest timestamp without dumping payloads. `send-due` and `retry-failed` are safe queued/dry-run previews only until a reviewed gateway sender and live smoke artifact exist.
