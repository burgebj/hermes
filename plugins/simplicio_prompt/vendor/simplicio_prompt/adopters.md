# Adopters

Projects vendoring the yool/tuple/HAMT spec.

| Project | Repo | Status | Vendored Version |
|---|---|---|---|
| SendSprint | https://github.com/wesleysimplicio/SendSprint | planning | v0.2 |
| llm-project-mapper | https://github.com/wesleysimplicio/llm-project-mapper | planning | v0.2 |

## How to vendor

1. Copy `YOOL_TUPLE_HAMT.md` into your repo as `docs/YOOL_TUPLE_HAMT.md`.
2. Pin the spec version in your repo's README (e.g., `Spec: simplicio-prompt v0.2`).
3. Implement guardrails per §11 (CPU throttle + disk GC). MANDATORY.
4. Add your project to the table above via PR.

## Update protocol

When the spec changes upstream:

1. Diff your vendored copy against the new canonical version.
2. Bump your project's vendored-version pin.
3. Run your own integration tests before merging.
4. Update the Vendored Version column here.
