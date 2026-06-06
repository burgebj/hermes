#!/usr/bin/env bash
# test.sh — Integrity checks for antseed-smart-delegate skill
set -uo pipefail

SDIR="$(cd "$(dirname "$0")/.." && pwd)"
P=0; F=0; T=0

ok() { T=$((T+1)); P=$((P+1)); echo "  ✅ $1"; }
no() { T=$((T+1)); F=$((F+1)); echo "  ❌ $1 — $2"; }

echo "🧪 antseed-smart-delegate"

# Structure
for f in SKILL.md references/setup.md scripts/discover.sh; do
  [[ -f "$SDIR/$f" ]] && ok "$f" || no "$f" "missing"
done
[[ ! -f "$SDIR/references/model-catalog.md" ]] && ok "no static catalog" || no "model-catalog.md" "should be removed"
[[ ! -f "$SDIR/scripts/models.sh" ]] && ok "no old models.sh" || no "models.sh" "superseded by discover.sh"
[[ ! -f "$SDIR/scripts/best-peer.sh" ]] && ok "no old best-peer.sh" || no "best-peer.sh" "superseded by discover.sh"

# Permissions
[[ -x "$SDIR/scripts/discover.sh" ]] && ok "discover.sh executable" || no "discover.sh" "not executable"

# No hardcoded paths
if grep -q '/home/' "$SDIR/scripts/discover.sh" 2>/dev/null; then
  no "no hardcoded paths" "found /home/ in discover.sh"
else
  ok "no hardcoded paths"
fi

# No hardcoded model names
if grep -qE '(deepseek|claude-opus|claude-sonnet|gpt-[0-9]|minimax|qwen3|llama-|gemini-)' "$SDIR/scripts/discover.sh" 2>/dev/null; then
  no "no hardcoded models" "found specific model names in discover.sh"
else
  ok "no hardcoded models"
fi

# Tag-driven design
grep -q 'TASK_TAGS' "$SDIR/scripts/discover.sh" && ok "tag-driven scoring" || no "tag-driven" "no TASK_TAGS"
grep -q 'TAG_CATEGORIES' "$SDIR/scripts/discover.sh" && ok "tag-based categories" || no "categories" "no TAG_CATEGORIES"

# Live network queries
grep -q 'network.*browse' "$SDIR/scripts/discover.sh" && ok "queries network" || no "network browse" "missing"
grep -q 'network.*peer' "$SDIR/scripts/discover.sh" && ok "fetches peer details" || no "network peer" "missing"
grep -q 'v1/models' "$SDIR/scripts/discover.sh" && ok "proxy fallback" || no "proxy fallback" "missing"

# SKILL.md references discover.sh, not old scripts
grep -q 'discover.sh' "$SDIR/SKILL.md" && ok "SKILL.md refs discover.sh" || no "discover.sh ref" "missing"
if grep -q 'models.sh\|best-peer.sh' "$SDIR/SKILL.md"; then
  no "no old script refs" "SKILL.md still references models.sh or best-peer.sh"
else
  ok "no old script refs in SKILL.md"
fi

# Frontmatter
for field in name description version prerequisites; do
  grep -q "^${field}:" "$SDIR/SKILL.md" && ok "frontmatter: $field" || no "frontmatter: $field" "missing"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━"
echo "$P/$T passed"
[[ $F -eq 0 ]] && exit 0 || exit 1
