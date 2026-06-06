#!/bin/bash
# deploy-hermes-skills.sh
# Deploys 32 Town skills to the Hermes local skill directory
# Usage: bash deploy-hermes-skills.sh [path-to-tarball]
#
# SAFE: Does not delete existing skills. Only adds/overwrites SKILL.md files.
# REVERSIBLE: Creates a backup of existing skills before deploying.

set -euo pipefail

HERMES_SKILLS="$HOME/.hermes/skills"
TARBALL="${1:-hermes-skills-bundle.tar.gz}"
BACKUP_DIR="$HOME/.hermes/skills-backup-$(date +%Y%m%d-%H%M%S)"
TEMP_DIR=$(mktemp -d)

# Validate
if [[ ! -f "$TARBALL" ]]; then
    echo "ERROR: Tarball not found: $TARBALL"
    echo "Usage: bash deploy-hermes-skills.sh [path-to-tarball]"
    exit 1
fi

echo "=== Hermes Skills Deployment ==="
echo "Source:  $TARBALL"
echo "Target:  $HERMES_SKILLS"
echo "Backup:  $BACKUP_DIR"
echo ""

# Backup existing skills
if [[ -d "$HERMES_SKILLS" ]]; then
    echo "[1/4] Backing up existing skills..."
    cp -r "$HERMES_SKILLS" "$BACKUP_DIR"
    echo "  Backup created: $BACKUP_DIR"
else
    echo "[1/4] No existing skills directory. Creating fresh."
    mkdir -p "$HERMES_SKILLS"
fi

# Extract tarball to temp
echo "[2/4] Extracting bundle..."
tar xzf "$TARBALL" -C "$TEMP_DIR"
echo "  Extracted to: $TEMP_DIR/hermes-skills/"

# Deploy: copy each category/skill/SKILL.md into target
echo "[3/4] Deploying 32 skills..."
DEPLOYED=0
SKIPPED=0
for category_dir in "$TEMP_DIR"/hermes-skills/*/; do
    category=$(basename "$category_dir")
    for skill_dir in "$category_dir"*/; do
        skill=$(basename "$skill_dir")
        src="$skill_dir/SKILL.md"
        dest_dir="$HERMES_SKILLS/$category/$skill"
        dest="$dest_dir/SKILL.md"

        if [[ ! -f "$src" ]]; then
            echo "  SKIP: $category/$skill (no SKILL.md in bundle)"
            SKIPPED=$((SKIPPED + 1))
            continue
        fi

        mkdir -p "$dest_dir"
        cp "$src" "$dest"
        echo "  OK: $category/$skill/SKILL.md ($(wc -c < "$src") bytes)"
        DEPLOYED=$((DEPLOYED + 1))
    done
done

# Verify only skills contained in the bundle (avoids false positives from existing skills)
echo "[4/4] Verification..."
VERIFIED=0
MISSING=0
for category_dir in "$TEMP_DIR"/hermes-skills/*/; do
    category=$(basename "$category_dir")
    for skill_dir in "$category_dir"*/; do
        skill=$(basename "$skill_dir")
        dest="$HERMES_SKILLS/$category/$skill/SKILL.md"
        if [[ -f "$dest" ]]; then
            VERIFIED=$((VERIFIED + 1))
        else
            echo "  MISSING: $category/$skill/SKILL.md"
            MISSING=$((MISSING + 1))
        fi
    done
done

# Cleanup temp
rm -rf "$TEMP_DIR"

echo ""
echo "=== Deployment Complete ==="
echo "Deployed: $DEPLOYED"
echo "Skipped:  $SKIPPED"
echo "Verified: $VERIFIED"
echo "Missing:  $MISSING"
echo "Backup:   $BACKUP_DIR"
echo ""
echo "To verify: hermes skills list"
echo "To rollback: rm -rf $HERMES_SKILLS && mv $BACKUP_DIR $HERMES_SKILLS"
