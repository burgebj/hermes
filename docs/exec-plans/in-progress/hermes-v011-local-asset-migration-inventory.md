# Hermes v0.11 Local Asset Migration Inventory

source_evidence: `/Users/beiming/.hermes/upgrade-evidence/hermes_upgrade_evidence_20260428_021819`
target_worktree: `/Users/beiming/HermesUpgradeLab/hermes-agent-v011-test`
base: official `v2026.4.23` / `bf196a3fc0fd1f79353369e8732051db275c6276`

## A. Already migrated as untracked local assets

These were copied from `untracked_files.tar.gz` into the v0.11 test worktree and passed syntax/focused tests where applicable:

- `docs/agents/` — 北冥法典/Agent map/governance docs.
- `docs/exec-plans/` — task contracts, ledgers, verification chains, acceptance reports.
- `hermes_cli/gate_controller.py` — local human gate controller support.
- `hermes_cli/human_gate_controller.py` — local human gate controller support.
- `hermes_cli/review_orchestrator.py` — local review orchestration.
- `hermes_cli/safe_refactor_audit.py` — safe-refactor audit support.
- `hermes_cli/safe_refactor_audit_report.md` — audit report artifact.
- `hermes_cli/safe_refactor_runtime.py` — safe-refactor runtime support.
- `tests/hermes_cli/test_human_gate_controller.py` — passed in focused test run.
- `tests/hermes_cli/test_review_orchestrator.py` — passed in focused test run.
- `tests/hermes_cli/test_safe_refactor_audit.py` — passed in focused test run.
- `tests/hermes_cli/test_safe_refactor_runtime.py` — passed in focused test run.

## B. Do not directly apply old tracked patch

`git apply --check` failed for both broad and focused patches, so these require manual review:

- `AGENTS.md` — official v0.11 has a new AGENTS.md; local governance map must be reconciled manually.
- `cli.py` — likely high-conflict due TUI/CLI evolution; manual diff only.
- `gateway/platforms/api_server.py` — official gateway changed; manual review.
- `hermes_cli/config.py` — official config changed; manual review.
- `hermes_cli/model_switch.py` — old patch appears largely upstreamed/reimplemented; keep official unless specific regression found.
- `hermes_cli/profiles.py` — manual review.
- `hermes_cli/uninstall.py` — official API changed; local test fails on removed/renamed `cleanup_gateway_service`.
- `scripts/whatsapp-bridge/package-lock.json` — likely dependency lock conflict; defer unless WhatsApp bridge is in scope.
- `tools/browser_tool.py` — must manually compare visible-window/DISPLAY behavior.
- `tools/image_generation_tool.py` — must manually compare with v0.11 plugin/image-gen architecture.
- `uv.lock` — do not transplant old lock wholesale into v0.11.

## C. First decisions from inspection

- custom_providers multi-model picker: official v0.11 has grouped custom provider support and reads both `model` and `models` dict/list. Synthetic check passed. Old local `model_switch.py` patch is probably no longer needed.
- safe-refactor/harness local modules: imported into worktree and focused tests passed except uninstall compatibility.
- uninstall local test/patch: needs adaptation to official v0.11 names/semantics, not direct carry-over.

## D. Next manual migration queue

1. Browser visible-window behavior: inspect old `tools/browser_tool.py` diff and v0.11 browser implementation; port only missing DISPLAY/headed logic if absent.
2. Image generation: inspect old Google/image proxy patch and v0.11 plugin image_gen support; port only missing provider behavior.
3. API server/gateway: inspect local `gateway/platforms/api_server.py` diff against official v0.11; port only required normalization/security fixes.
4. Config/profiles/uninstall: adapt tests to v0.11 APIs, then port minimal required behavior.
5. AGENTS/docs integration: reconcile official AGENTS.md with 北冥法典 docs without overwriting official development guide.
