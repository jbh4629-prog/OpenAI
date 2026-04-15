#!/usr/bin/env bash
set -euo pipefail

UPSTREAM_REPO="https://github.com/getcompanion-ai/feynman.git"
TARGET_DIR="${1:-feynman}"

if [ -e "$TARGET_DIR" ]; then
  echo "[create-feynman-project] Target '$TARGET_DIR' already exists."
  echo "[create-feynman-project] Choose another directory: bash scripts/create-feynman-project.sh my-feynman"
  exit 1
fi

echo "[create-feynman-project] Cloning $UPSTREAM_REPO -> $TARGET_DIR"
git clone "$UPSTREAM_REPO" "$TARGET_DIR"

cd "$TARGET_DIR"

if [ -f package-lock.json ]; then
  echo "[create-feynman-project] Installing dependencies with npm ci"
  npm ci
else
  echo "[create-feynman-project] Installing dependencies with npm install"
  npm install
fi

echo
echo "[create-feynman-project] Done."
echo "[create-feynman-project] Next steps:"
echo "  cd $TARGET_DIR"
echo "  npm run build"
echo "  npm test"
