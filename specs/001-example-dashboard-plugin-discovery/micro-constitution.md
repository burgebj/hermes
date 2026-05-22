# Micro-Constitution: 001-example-dashboard-plugin-discovery

- Spec ID: 001
- Feature Name: example-dashboard-plugin-discovery
- Target Repository: /Users/shawnowen/dev/sandbox/hermes-codex-example-dashboard-fix
- Branch: codex/fix-example-dashboard-plugin
- Autonomy Level: HIGH
- Deploy Target: none
- Score Threshold: 10

## Problem Statement

Hermes dashboard Sessions page QA stopped on the first browser issue at
http://127.0.0.1:5173/sessions. The bundled Example dashboard plugin is
discovered in the dashboard sidebar/plugin loader and its manifest declares
entry "dist/index.js", but plugins/example-dashboard/dashboard/dist/index.js is
missing. The browser console reports "[plugins] Failed to load example from
/dashboard-plugins/example/dist/index.js?..." and direct requests to both the
Vite proxy URL and backend URL return HTTP 404 File not found. Determine
whether the Example dashboard plugin should ship a built dist bundle or be
excluded/hidden from runtime dashboard discovery because it is test-only.
Implement the governed fix, add regression coverage, update docs/tests as
needed, and preserve unrelated dirty files.

Evidence folder:
/Users/shawnowen/dev/sandbox/hermes/handoffs/sessions-ui-qa-2026-05-20T0425Z

## Success Criteria

- SC-001: `/api/dashboard/plugins` does not return the backend-only `example`
  fixture unless it has a real frontend entry asset.
- SC-002: `/api/plugins/example/hello` remains mounted for auth middleware
  regression coverage.
- SC-003: Bundled dashboard manifests that declare `entry` or `css` assets are
  covered by a metadata regression test.
- SC-004: Dashboard plugin documentation explains backend-only API fixtures and
  loadable frontend asset requirements.
- SC-005: Unrelated dirty files in the original checkout remain untouched.
