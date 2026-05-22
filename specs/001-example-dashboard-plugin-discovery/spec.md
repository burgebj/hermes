# Spec 001: Example Dashboard Plugin Discovery

Status: Implemented

## User Story

As a Hermes dashboard user, I need backend-only dashboard plugin fixtures to stay
out of frontend plugin discovery so the dashboard does not load missing bundles
or render broken plugin tabs.

## Functional Requirements

- FR-001: Preserve internal discovery of all dashboard manifests so plugin API
  routes can still mount.
- FR-002: Return only frontend-loadable dashboard plugins from
  `/api/dashboard/plugins`.
- FR-003: Treat a non-string, empty, or missing frontend `entry` as not
  frontend-loadable.
- FR-004: Verify the declared `entry` path resolves inside the plugin
  `dashboard/` directory and points to an existing file before returning it to
  the frontend loader.
- FR-005: Keep `/api/plugins/example/hello` available for authenticated route
  coverage.
- FR-006: Add regression coverage for missing declared dashboard assets.
- FR-007: Document backend-only API fixture behavior.

## Acceptance Criteria

- AC-001: The internal discovery list still includes `example` with `has_api`.
- AC-002: The frontend discovery list excludes `example`.
- AC-003: The frontend discovery list includes bundled plugins with real
  `dist/index.js` assets, including `kanban` and `hermes-achievements`.
- AC-004: The metadata test fails if a bundled manifest declares a missing
  `entry` or `css` asset.
- AC-005: Dashboard plugin docs explain `entry: null` for backend-only API
  fixtures.

## Out of Scope

- Shipping a real Example dashboard UI bundle.
- Reworking the frontend plugin SDK or registration lifecycle.
- Changing plugin API auth semantics.
