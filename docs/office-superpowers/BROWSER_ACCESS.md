# Browser, Dashboard, and Log Access Guide

Status: current boundary guide
Last verified: 2026-05-13T01:12:55Z
Audience: Akhil/default profile, Office workers, reviewers, DevOps, QA

## Purpose

This guide explains what Hermes Office workers may do with browser, dashboard, and log access when diagnosing Office superpowers. It prevents a common overclaim: browser automation is useful, but it is not unrestricted access to Akhil's logged-in Chrome profile, cookies, private sessions, or production dashboards.

## Current boundary

Keep these three access modes separate:

| Access mode | Current status | What it proves / does not prove |
|---|---|---|
| Remote browser tool session | Available only when the browser tool is enabled for the worker | Can inspect public/available pages, console output, screenshots, and local URLs reachable from the tool session. It does not imply access to Akhil's personal Chrome profile. |
| Local dashboard HTTP/API route | Available only when the local service is running and reachable from the worker environment | Can prove a specific route/status check responded. It does not prove a production dashboard or private authenticated view is healthy. |
| Logged-in Chrome profile / cookies / private session | Not available by default | Requires explicit human setup/approval and remains a `human_login_or_browser_profile_required` blocker when essential. Never extract or persist cookies/session tokens. |

Allowed when tools are available and the task requires it:

- open public or locally served pages;
- click, type, scroll, and use keyboard actions in the controlled browser session;
- inspect accessibility snapshots;
- inspect page console output and JavaScript errors;
- capture screenshots and use vision analysis;
- fetch safe local dashboard/API routes;
- read safe log files or redacted excerpts;
- report path, status code, title, and non-secret error summaries.

Not allowed without explicit setup or approval:

- accessing Akhil's personal logged-in Chrome profile;
- extracting, printing, storing, or reusing cookies/session tokens;
- bypassing CAPTCHA, 2FA, paywalls, or account controls;
- using private dashboards that require a human login unless the human has provided access for that task;
- persisting raw PII, user ids, chat ids, tokens, or private browser data in docs, logs, Kanban, or Telegram;
- claiming a dashboard is healthy unless a route/status check actually passed.

## When to block

Block or create a `SCOPE_CHANGE_REQUEST` only when access is essential and unavailable:

- human login, 2FA, CAPTCHA, or a specific browser profile is required;
- paid/cloud/admin permissions are required;
- private dashboard access cannot be verified from available routes;
- requested evidence depends on browser state that cannot be reproduced safely;
- logs or screenshots contain secrets/raw PII that require Security handling.

Routine page inspection, local API checks, and public docs browsing should not require blocking.

## Dashboard and API inspection checklist

Before claiming a dashboard/API behavior:

1. Identify the exact route or command.
2. Run the route/command.
3. Capture status code, exit code, or console error summary.
4. Record any artifact path, such as JSON output or screenshot.
5. Redact sensitive values.
6. State caveats: local-only, unauthenticated route, mocked route, dry-run, or unavailable.

Example safe evidence record:

```json
{
  "gate": "Dashboard route reachable",
  "command_or_check": "curl -sS -o /tmp/dashboard_health.json -w '%{http_code}' http://127.0.0.1:8000/health",
  "exit_code_or_artifact": "exit 0; http 200; /tmp/dashboard_health.json",
  "artifact_paths": ["/tmp/dashboard_health.json"],
  "verdict": "PASS",
  "rationale": "The local unauthenticated health route returned 200 and saved a redacted JSON artifact."
}
```

If the route is not actually checked, say `unverified` rather than `healthy`.

## Log access checklist

Safe log references:

- file path;
- timestamp range;
- severity counts;
- task id or run id;
- redacted exception class and short message;
- line numbers if safe.

Unsafe log content:

- tokens, cookies, private keys, passwords, API keys;
- raw user ids, chat ids, phone numbers, emails, private messages;
- raw headers or full request bodies;
- private browser profile paths with sensitive context;
- complete stack traces containing secrets.

Recommended command shape for humans/operators:

```bash
python3 scripts/office_doctor.py --json > /tmp/office_doctor.json
python3 scripts/office_watchdog.py --dry-run --json > /tmp/office_watchdog.json
```

Doctor lists safe log paths and can include redacted tails when requested by implementation. Do not paste raw tails into durable Kanban comments unless they are redacted.

## Browser automation checklist

Use browser automation when it materially improves evidence, such as testing a local UI, public docs page, or visible bug.

Record:

- URL;
- action sequence;
- observed text/console/screenshot artifact;
- whether the session was authenticated or unauthenticated;
- limitations.

Do not claim:

- that a private account flow works if no logged-in session was available;
- that a production dashboard is healthy based on a mock/local page;
- that browser state can be reused across tasks unless explicitly configured.

## Screenshots and vision

Screenshots are useful for UI evidence, but they can leak sensitive content. Before attaching or referencing them:

- ensure no tokens, chats, private messages, emails, or personal data are visible;
- crop or redact if needed;
- prefer text/JSON artifacts for machine verification;
- describe screenshots as visual evidence, not as proof of backend correctness by themselves.

## Office Doctor/browser section

The current Doctor builder includes a `browser_dashboard` section that states browser/dashboard access is operator-bounded and not probed destructively. It lists route categories and cookie policy without printing credentials.

Relevant implementation path:

- `hermes_cli/office_superpowers.py`, `build_doctor_report()`.

Run:

```bash
python3 scripts/office_doctor.py --json
```

Expected section id:

```json
{
  "id": "browser_dashboard",
  "status": "warn",
  "summary": "Browser/dashboard access is documented as operator-bounded and not probed destructively"
}
```

The `warn` status is intentional boundary visibility, not proof of failure.

## Escalation

- Need human login/profile/2FA: block for Akhil.
- Need credential or token: block; never ask the worker to paste secrets into Kanban/docs.
- Need dashboard route or service start: route DevOps/tooling if outside docs authority.
- Need UI bug reproduction: route QA/frontend worker with exact URL and safe artifacts.
- Need privacy/security review: route Security/reviewer.

## Related files

- `docs/office-superpowers/references/BROWSER_DASHBOARD_LOG_ACCESS.md`
- `docs/office-superpowers/OPERATOR_RUNBOOK.md`
- `docs/office-superpowers/DEPLOYMENT.md`
- `docs/office-superpowers/README.md`
