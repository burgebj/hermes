# Default-profile Office Operator Policy

The default Office mode is YOLO/hands-free unless Akhil explicitly requests approval mode with phrases such as `keep me in the loop`, `ask me`, `take my permission`, `approval required`, or `do not yolo`.

## Allowed hands-free actions inside `/Users/akhilkinnera/Documents/My Workspace`

- Create, edit, test, and build task-scoped files.
- Create Kanban child tasks for the correct specialist profile.
- Produce local scripts, docs, test fixtures, smoke checks, and evidence artifacts.
- Run non-destructive Python/shell checks that do not install npm packages.
- Write redacted Office report outbox records.

## Blockers requiring human approval or specialist handoff

- credentials or human login;
- paid/cloud permission, including paid Colab/GPU;
- destructive irreversible action outside safe workspace boundaries;
- legal/license ambiguity;
- missing runtime/hardware;
- unverifiable external claim;
- explicit approval mode;
- unsafe secret/PII exposure;
- human browser profile/CAPTCHA/2FA requirement.

Routine reviewer/QA/security pipeline work is not a human blocker by itself. Complete with evidence and set handoff metadata so downstream profiles can continue.

## Evidence rule

Every meaningful run must produce a gate scorecard with commands/checks, exit codes or artifact results, safe artifact paths, verdicts, and rationale. Benchmark/performance/release/deploy claims require real artifacts, not prose.

## No-npm rule

Do not run `npm install`, `pnpm install`, `yarn install`, `npx`, or add JavaScript packages for Office work unless Akhil explicitly approves.
