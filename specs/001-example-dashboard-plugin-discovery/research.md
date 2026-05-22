# Research: Example Dashboard Plugin Discovery

## Findings

- `plugins/example-dashboard/dashboard/plugin_api.py` states the fixture exists
  so the test suite has a stable side-effect-free GET endpoint for auth
  coverage.
- `plugins/example-dashboard/dashboard/manifest.json` declared
  `entry: "dist/index.js"` even though no `dist/` directory exists.
- `hermes_cli/web_server.py` used one manifest list for frontend discovery,
  static asset serving, plugin hub metadata, and API route mounting.
- `web/src/plugins/usePlugins.ts` constructs
  `/dashboard-plugins/<name>/<entry>` for every returned manifest.
- Existing docs describe a separate reference Example plugin in
  `hermes-example-plugins`, so the bundled fixture is not the intended user
  facing demo.

## Decision

Keep the bundled `example` plugin as a backend-only fixture and exclude it from
frontend runtime discovery unless it has a real entry asset. This preserves the
auth regression route and removes the broken sidebar/plugin loader surface.

## Alternatives

- Ship a minimal `dist/index.js`: rejected because it would turn a test fixture
  into a visible or globally loaded runtime plugin.
- Remove the manifest: rejected because API route mounting uses the manifest's
  `api` declaration.
