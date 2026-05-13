# Browser, Dashboard, and Log Access Checks

## Boundary

Office diagnostics may list local dashboard/log paths and safe route checks. They must not print cookies, browser profiles, authorization headers, raw session IDs, or platform user identifiers.

## Doctor checks

`scripts/office_doctor.py` reports:
- runtime and Hermes home;
- gateway pid if detectable;
- messaging config presence without credential values;
- Kanban board status/counts;
- Office profile presence;
- evidence gate policy;
- log paths;
- browser/dashboard policy and recommended checks.

Use `--include-log-tail` only when needed; tails are redacted before printing.

## Manual safe smoke examples

```bash
python3 scripts/office_doctor.py --json
python3 scripts/office_watchdog.py --dry-run --json
python3 scripts/office_report_outbox.py status --json
```

Do not scrape dashboard pages that require a human browser profile unless the task explicitly allows it and the evidence can be redacted.
