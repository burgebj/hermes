#!/usr/bin/env bash
# Canonical test runner for hermes-agent. Run this instead of calling
# `pytest` directly to guarantee your local run matches CI behavior.
#
# What this script enforces:
#   * Per-file isolation via scripts/run_tests_parallel.py — each test
#     file runs in its own freshly-spawned `python -m pytest <file>`
#     subprocess. No xdist, no shared workers, no module-level leakage
#     between files.
#   * TZ=UTC, LANG=C.UTF-8, PYTHONHASHSEED=0 (deterministic)
#   * Env vars blanked (conftest.py also does this, but this
#     is belt-and-suspenders for anyone running pytest outside our
#     conftest path — e.g. on a single file)
#   * Proper venv interpreter detection (probes .venv, venv, then shared
#     Hermes installs; supports both POSIX ``bin/python`` and Windows
#     ``Scripts/python.exe`` layouts)
#
# Usage:
#   scripts/run_tests.sh                            # full suite
#   scripts/run_tests.sh -j 4                       # cap parallelism
#   scripts/run_tests.sh tests/agent/               # discover only here
#   scripts/run_tests.sh tests/agent/ tests/acp/    # multiple roots
#   scripts/run_tests.sh tests/foo.py               # single file
#   scripts/run_tests.sh tests/foo.py -- --tb=long  # path + pytest args
#   scripts/run_tests.sh -- -v --tb=long            # pytest args only
#
# Everything after a literal '--' is passed through to each per-file
# pytest invocation. Positional path arguments before '--' override
# the default discovery root (tests/).

set -euo pipefail

# ── Locate repo root ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ── Activate venv ───────────────────────────────────────────────────────────
VENV=""
PYTHON=""
candidates=(
  "$REPO_ROOT/.venv"
  "$REPO_ROOT/venv"
  "$HOME/.hermes/hermes-agent/venv"
)

if [ -n "${HERMES_HOME:-}" ]; then
  candidates+=("$HERMES_HOME/hermes-agent/venv")
fi

if [ -n "${LOCALAPPDATA:-}" ]; then
  candidates+=("$LOCALAPPDATA/hermes/hermes-agent/venv")
fi

for candidate in "${candidates[@]}"; do
  if [ -f "$candidate/bin/python" ]; then
    VENV="$candidate"
    PYTHON="$candidate/bin/python"
    break
  fi
  if [ -f "$candidate/Scripts/python.exe" ]; then
    VENV="$candidate"
    PYTHON="$candidate/Scripts/python.exe"
    break
  fi
  if [ -f "$candidate/Scripts/python" ]; then
    VENV="$candidate"
    PYTHON="$candidate/Scripts/python"
    break
  fi
done

if [ -z "$VENV" ]; then
  echo "error: no virtualenv found in $REPO_ROOT/.venv or $REPO_ROOT/venv" >&2
  exit 1
fi

# ── Live-gateway plugin (computed before we drop env) ───────────────────────
EXTRA_PYTHONPATH=""
EXTRA_PYTEST_PLUGINS=""
if [ -f "$HOME/.hermes/pytest_live_guard.py" ]; then
  EXTRA_PYTHONPATH="$HOME/.hermes"
  EXTRA_PYTEST_PLUGINS="pytest_live_guard"
fi


# ── Run in hermetic env ──────────────────────────────────────────────────────
# env -i: start with empty environment, opt-in only what we need.
# No credential var can leak — you'd have to explicitly add it here.
echo "▶ running per-file parallel test suite via run_tests_parallel.py"
echo "  (TZ=UTC LANG=C.UTF-8 PYTHONHASHSEED=0; clean env)"

cd "$REPO_ROOT"

env_args=(
  "PATH=$PATH"
  "HOME=$HOME"
  "TZ=UTC"
  "LANG=C.UTF-8"
  "LC_ALL=C.UTF-8"
  "PYTHONHASHSEED=0"
  "PYTHONUTF8=1"
  "PYTHONIOENCODING=utf-8"
)

if [ -n "${EXTRA_PYTHONPATH:-}" ]; then
  env_args+=("PYTHONPATH=$EXTRA_PYTHONPATH")
fi

if [ -n "${EXTRA_PYTEST_PLUGINS:-}" ]; then
  env_args+=("PYTEST_PLUGINS=$EXTRA_PYTEST_PLUGINS")
fi

# Windows-native Python uses USERPROFILE / HOMEDRIVE / HOMEPATH to resolve
# Path.home(), and Hermes itself defaults to LOCALAPPDATA for HERMES_HOME.
# Preserve just the non-secret environment pieces that keep the hermetic
# subprocess behaving like a real Windows login shell.
for name in USERPROFILE LOCALAPPDATA APPDATA TEMP TMP HOMEDRIVE HOMEPATH SYSTEMROOT WINDIR COMSPEC PATHEXT; do
  if [ -n "${!name:-}" ]; then
    env_args+=("$name=${!name}")
  fi
done

exec env -i "${env_args[@]}" \
  "$PYTHON" "$SCRIPT_DIR/run_tests_parallel.py" "$@"
