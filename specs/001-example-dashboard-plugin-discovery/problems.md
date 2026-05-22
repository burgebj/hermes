# Problems: Example Dashboard Plugin Discovery

## Facts & Assumptions

- The bundled `plugins/example-dashboard/dashboard/manifest.json` identifies the
  plugin as a test-suite fixture for auth coverage.
- The fixture has `plugin_api.py` but no `dashboard/dist/index.js`.
- `hermes_cli/web_server.py` mounted plugin API routes from manifests and also
  returned those manifests to the frontend plugin loader.
- `web/src/plugins/usePlugins.ts` blindly loaded every manifest entry as a
  script.
- Assumption: backend-only dashboard plugin fixtures should not create sidebar
  tabs or frontend loader requests.

## Problem

Backend-only dashboard plugin manifests are treated as frontend plugins even
when their declared JavaScript bundle is missing. The resulting 404 blocks QA
on the first visible browser issue and creates a broken Example tab for users.

## Root Cause

Dashboard manifest discovery did not distinguish API-only manifests from
loadable frontend plugin manifests.

## Affected Surfaces

- Dashboard plugin discovery endpoint: `/api/dashboard/plugins`
- Dashboard plugin hub metadata
- Bundled `example-dashboard` fixture
- Metadata tests for bundled dashboard assets
- Dashboard plugin authoring docs

## Problem Score

10/10
