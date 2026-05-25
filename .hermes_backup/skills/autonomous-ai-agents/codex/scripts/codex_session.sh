#!/bin/bash
# codex_session.sh — Call Codex with automatic session continuity
# First call starts a new session; subsequent calls auto-resume the same session.
# Session marker: ~/.codex/last_session_for_hermes
set -euo pipefail

MARKER="$HOME/.codex/last_session_for_hermes"
WORKDIR=""; MODEL=""; JSON_FLAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="$2"; shift 2 ;;
    --model)   MODEL="$2";   shift 2 ;;
    -j|--json) JSON_FLAG="--json"; shift ;;
    --) shift; break ;;
    *) break ;;
  esac
done

PROMPT="$*"
if [ -z "$PROMPT" ]; then
  echo "ERROR: prompt is required"
  exit 1
fi

# Resume or fresh?
if [ -f "$MARKER" ] && [ "$(cat "$MARKER" | tr -d '[:space:]')" = "active" ]; then
  echo "[Codex-Session] Resuming last session..." >&2
  # Note: codex exec resume does NOT support -C flag; cd instead
  if [ -n "$WORKDIR" ]; then cd "$WORKDIR"; fi
  codex exec resume --last ${JSON_FLAG} ${MODEL:+-m "$MODEL"} "$PROMPT"
  EC=$?
  if [ $EC -ne 0 ]; then
    echo "[Codex-Session] Resume failed (exit=$EC), will start fresh next time." >&2
    rm -f "$MARKER"
  fi
  exit $EC
fi

echo "[Codex-Session] Starting new session..." >&2
ARGS=()
[ -n "$WORKDIR" ] && ARGS=(-C "$WORKDIR")
[ -n "$MODEL" ]   && ARGS+=(-m "$MODEL")
[ -n "$JSON_FLAG" ] && ARGS+=("$JSON_FLAG")
codex exec --full-auto "${ARGS[@]}" "$PROMPT"
EC=$?
if [ $EC -eq 0 ]; then
  echo "active" > "$MARKER"
fi
exit $EC
