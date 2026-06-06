# AR-1 M3 Audit Rule Engine Prototype

- Added `hermes_cli/safe_refactor_audit.py` as a small, diff-driven TDB-3 audit prototype.
- Enforces file-scope warnings, hard rejection for uninstall TTY/confirmation downgrade patterns, and warnings for high-risk delete/write plus shell/PATH touches.
- Adds a contract-consistency warning when uninstall help/arg text changes without matching control-flow changes.
- Coverage is intentionally heuristic and minimal for diff-first review.
