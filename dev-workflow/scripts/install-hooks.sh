#!/usr/bin/env bash
# Installs the dev-workflow git hooks (pre-commit + pre-push) into the current repository.
#
# Usage: bash scripts/install-hooks.sh
#
# Safe to re-run — it just overwrites .githooks/ with the current versions of the hooks.
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "Not inside a git repository — cd into the target project first." >&2
  exit 1
}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="$REPO_ROOT/.githooks"

mkdir -p "$TARGET_DIR"
cp "$SCRIPT_DIR/check_staged.py" "$TARGET_DIR/check_staged.py"
cp "$SCRIPT_DIR/hooks/pre-commit" "$TARGET_DIR/pre-commit"
cp "$SCRIPT_DIR/hooks/pre-push" "$TARGET_DIR/pre-push"
chmod +x "$TARGET_DIR/check_staged.py" "$TARGET_DIR/pre-commit" "$TARGET_DIR/pre-push"

git -C "$REPO_ROOT" config core.hooksPath .githooks

echo "[dev-workflow] Installed git hooks into $TARGET_DIR and set core.hooksPath."
echo "[dev-workflow] Commit .githooks/ so it ships with the repo. Each teammate's clone still"
echo "[dev-workflow] needs to run this script once — core.hooksPath is a local git config, not"
echo "[dev-workflow] something version control carries."

if ! command -v trufflehog >/dev/null 2>&1; then
  echo
  echo "[dev-workflow] NOTE: trufflehog not found on PATH — the hooks will fall back to"
  echo "[dev-workflow] pattern-based secret scanning only (still blocks on its own)."
  echo "[dev-workflow] Install trufflehog for deeper scanning: https://github.com/trufflesecurity/trufflehog#install"
fi
