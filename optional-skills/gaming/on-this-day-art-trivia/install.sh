#!/usr/bin/env bash
# install.sh — install on-this-day-art-trivia into ~/.hermes
#
# Symlinks (or copies) the bundled skill, hook, and plugin into the
# locations Hermes scans on startup. Idempotent: running it twice does
# nothing destructive.
#
# Usage:
#   ./install.sh                 # symlink into ~/.hermes
#   ./install.sh --copy          # copy instead of symlink
#   ./install.sh --uninstall     # remove the installed entries

set -euo pipefail

PKG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"

SKILL_SRC="$PKG_DIR/skill/on-this-day-art-trivia"
HOOK_SRC="$PKG_DIR/hook/on-this-day-art-trivia"
PLUGIN_SRC="$PKG_DIR/plugin/on_this_day_art_trivia"

SKILL_DST="$HERMES_HOME/skills/on-this-day-art-trivia"
HOOK_DST="$HERMES_HOME/hooks/on-this-day-art-trivia"
PLUGIN_DST="$HERMES_HOME/plugins/on_this_day_art_trivia"

mode="symlink"
do_uninstall=0
for arg in "$@"; do
  case "$arg" in
    --copy) mode="copy" ;;
    --uninstall) do_uninstall=1 ;;
    -h|--help)
      sed -n '1,18p' "$0"
      exit 0
      ;;
    *) echo "Unknown option: $arg" >&2; exit 2 ;;
  esac
done

uninstall_one() {
  local target="$1"
  if [[ -L "$target" || -e "$target" ]]; then
    rm -rf "$target"
    echo "  removed $target"
  fi
}

install_one() {
  local src="$1"
  local dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [[ -L "$dst" || -e "$dst" ]]; then
    if [[ -L "$dst" && "$(readlink "$dst")" == "$src" ]]; then
      echo "  ok   $dst (already linked)"
      return 0
    fi
    echo "  warn $dst already exists; leaving in place" >&2
    return 0
  fi
  if [[ "$mode" == "copy" ]]; then
    cp -r "$src" "$dst"
    echo "  copied $src -> $dst"
  else
    ln -s "$src" "$dst"
    echo "  linked $src -> $dst"
  fi
}

if [[ $do_uninstall -eq 1 ]]; then
  echo "Uninstalling on-this-day-art-trivia from $HERMES_HOME ..."
  uninstall_one "$SKILL_DST"
  uninstall_one "$HOOK_DST"
  uninstall_one "$PLUGIN_DST"
  echo "Done. The SQLite database at $HERMES_HOME/data/on-this-day-art-trivia/ was left in place."
  echo "Remove it manually if you want a clean slate."
  exit 0
fi

echo "Installing on-this-day-art-trivia into $HERMES_HOME ($mode mode) ..."
install_one "$SKILL_SRC"  "$SKILL_DST"
install_one "$HOOK_SRC"   "$HOOK_DST"
install_one "$PLUGIN_SRC" "$PLUGIN_DST"

# Ensure data directory exists with the right permissions.
mkdir -p "$HERMES_HOME/data/on-this-day-art-trivia"

# Smoke-test: import the skill scripts.
PYTHONPATH="$SKILL_DST" python3 -c "
from scripts import state, sources, scoring, prompt_builder, guess_matcher, achievements, telegram_api, challenge
state.migrate()
print('on-this-day-art-trivia: skill imports OK; schema migrated.')
"

echo
echo "Next steps:"
echo "  1. Restart the Hermes gateway so it discovers the hook and plugin:"
echo "       hermes restart   (or kill \$(< $HERMES_HOME/gateway.pid) && hermes start)"
echo "  2. Send /on-this-day-art-trivia in Telegram to start your first challenge."
echo "  3. (Optional) wire daily delivery into Hermes cron — see README.md."
