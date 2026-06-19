#!/bin/bash
# install.sh — Install all fd-coding skills
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/FindDataOfficial/coding/master/install.sh | bash
#   ./install.sh                          → install to current project's .claude/skills/
#   ./install.sh /path/to/project         → install to specified project
#   ./install.sh --global                 → install to ~/.claude/skills/

set -euo pipefail

REPO_URL="https://github.com/FindDataOfficial/coding.git"

# Resolve target directory
if [ "${1:-}" = "--global" ]; then
  TARGET="$HOME/.claude/skills"
elif [ -n "${1:-}" ]; then
  TARGET="$1/.claude/skills"
else
  TARGET="$(pwd)/.claude/skills"
fi

# Determine source: running from cloned repo, or need to clone?
if [ -d "$(dirname "$0")/.claude/skills/fd-coding-common-resources" ]; then
  # Running from a cloned repo
  SOURCE="$(cd "$(dirname "$0")" && pwd)/.claude/skills"
else
  # Running via curl pipe — clone to temp dir
  TMPDIR="$(mktemp -d)"
  echo "==> Cloning $REPO_URL ..."
  git clone --depth 1 "$REPO_URL" "$TMPDIR" 2>&1 | sed 's/^/    /'
  SOURCE="$TMPDIR/.claude/skills"
  CLEANUP_TMPDIR="$TMPDIR"
fi

echo "==> Installing fd-coding skills to: $TARGET"
mkdir -p "$TARGET"

# Copy all fd-* skill and resource directories
COUNT=0
for dir in "$SOURCE"/fd-*; do
  [ -d "$dir" ] || continue
  name="$(basename "$dir")"
  echo "    Copying $name..."
  rm -rf "$TARGET/$name"
  cp -r "$dir" "$TARGET/$name"
  COUNT=$((COUNT + 1))
done

echo ""
echo "==> Done! Installed $COUNT items:"
ls -d "$TARGET"/fd-* | while read d; do
  echo "    $(basename "$d")"
done

echo ""
echo "==> Available slash commands:"
echo "    /fd-coding-goal-clear        — Brainstorm and refine goals"
echo "    /fd-coding-diagram-creator   — Design class diagrams"
echo "    /fd-coding-schema-creator    — Generate SQLAlchemy models"
echo "    /fd-coding-plan-creator      — Plan pages and services"
echo "    /fd-coding-code-creator      — Generate implementations"
echo "    /fd-coding-project-builder   — TDD project builder"

# Cleanup temp dir if we cloned
if [ -n "${CLEANUP_TMPDIR:-}" ]; then
  rm -rf "$CLEANUP_TMPDIR"
fi
