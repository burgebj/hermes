# Plan: Example Dashboard Plugin Discovery

## Technical Context

- Language: Python backend, TypeScript/React dashboard frontend.
- Runtime loader: `hermes_cli/web_server.py` exposes dashboard plugin manifests
  to `web/src/plugins/usePlugins.ts`.
- Test runner: `scripts/run_tests.sh`.

## Files Modified

- `hermes_cli/web_server.py`
- `plugins/example-dashboard/dashboard/manifest.json`
- `plugins/example-dashboard/dashboard/plugin_api.py`
- `tests/test_project_metadata.py`
- `tests/hermes_cli/test_web_server.py`
- `website/docs/user-guide/features/extending-the-dashboard.md`
- `specs/001-example-dashboard-plugin-discovery/micro-constitution.md`
- `specs/001-example-dashboard-plugin-discovery/problems.md`
- `specs/001-example-dashboard-plugin-discovery/spec.md`
- `specs/001-example-dashboard-plugin-discovery/research.md`
- `specs/001-example-dashboard-plugin-discovery/plan.md`
- `specs/001-example-dashboard-plugin-discovery/tasks.md`
- `specs/001-example-dashboard-plugin-discovery/checklists/requirements.md`
- `specs/001-example-dashboard-plugin-discovery/audit-trail.md`
- `specs/001-example-dashboard-plugin-discovery/scorecard.md`

## Implementation

1. Add a backend helper that verifies a dashboard manifest has a loadable
   frontend `entry` asset inside its dashboard directory.
2. Use that helper for `/api/dashboard/plugins`, plugin hub dashboard metadata,
   and rescan counts.
3. Leave internal manifest discovery unchanged for API route mounting and static
   asset serving.
4. Mark the bundled example fixture as API-only with `entry: null`.
5. Add unit coverage for API-only filtering and declared bundled asset presence.
6. Update docs to describe backend-only API fixtures.

## Risk

Third-party manifests that relied on missing frontend bundles being returned to
the loader will no longer appear until the asset exists. That is intentional;
the old behavior produced broken tabs and script 404s.
