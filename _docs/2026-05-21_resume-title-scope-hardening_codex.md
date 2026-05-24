# Resume Title Scope Hardening

Date: 2026-05-21
Branch: `codex/hermes-resume-title-scope-20260521`

## Summary

This change scopes gateway `/resume` title listing and title resolution to the
active gateway source and user id. The public tracking issue for #29149 refers
to a private advisory, so this note intentionally avoids reproduction details.

## Changes

- Added optional `source` and `user_id` filters to `SessionDB.get_session_by_title()`
  and `SessionDB.resolve_session_by_title()`.
- Added `user_id` filtering to `SessionDB.list_sessions_rich()`.
- Updated gateway `/resume` to pass the current platform source and user id when
  listing and resolving titled sessions.
- Updated gateway `/branch` to persist the current user id on newly branched
  sessions so those sessions remain visible to the same user's scoped `/resume`.
- Added regression tests for scoped exact title lookup, scoped lineage lookup,
  scoped rich session listing, and gateway `/resume` behavior.

## Verification

```powershell
uv run --extra dev python -m pytest -o addopts= tests/gateway/test_resume_command.py tests/test_hermes_state.py::TestTitleUniqueness tests/test_hermes_state.py::TestTitleLineage tests/test_hermes_state.py::TestListSessionsRich tests/gateway/test_session_boundary_security_state.py::test_branch_clears_session_scoped_approval_and_yolo_state tests/gateway/test_session_boundary_security_state.py::test_resume_clears_session_scoped_approval_and_yolo_state
```

Result: `47 passed in 15.66s`

```powershell
uv run --extra dev python -m compileall hermes_state.py gateway/run.py
uv run --extra dev ruff check hermes_state.py gateway/run.py tests/gateway/test_resume_command.py tests/gateway/test_session_boundary_security_state.py tests/test_hermes_state.py
git diff --check
```

Results:

- compileall passed.
- ruff passed.
- `git diff --check` passed with Windows line-ending normalization warnings only.
