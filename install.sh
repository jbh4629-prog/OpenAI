#!/usr/bin/env bash
set -euo pipefail

# Codespaces dotfiles entrypoint for installing Codex skills from this repo.
# GitHub Codespaces runs this file automatically when this repository is
# configured as the user's dotfiles repository.

SKILLS_REPO_URL="${CODEX_SKILLS_REPO_URL:-https://github.com/jbh4629-prog/OpenAI.git}"
SKILLS_REPO_DIR="${CODEX_SKILLS_REPO_DIR:-$HOME/codex-skills/OpenAI}"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
INSTALL_MODE="${CODEX_SKILLS_INSTALL_MODE:-copy}"
WITH_PLUGINS="${CODEX_SKILLS_WITH_PLUGINS:-false}"
WITH_LAZYCODEX="${CODEX_SKILLS_WITH_LAZYCODEX:-false}"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -d "$script_dir/skills" ] && [ -f "$script_dir/scripts/bootstrap.sh" ]; then
  skills_source_dir="$script_dir"
else
  mkdir -p "$(dirname "$SKILLS_REPO_DIR")"

  if [ ! -d "$SKILLS_REPO_DIR/.git" ]; then
    echo "[codex-skills] cloning $SKILLS_REPO_URL to $SKILLS_REPO_DIR"
    git clone "$SKILLS_REPO_URL" "$SKILLS_REPO_DIR"
  else
    echo "[codex-skills] updating $SKILLS_REPO_DIR"
    git -C "$SKILLS_REPO_DIR" pull --ff-only || true
  fi

  skills_source_dir="$SKILLS_REPO_DIR"
fi

mkdir -p "$CODEX_HOME_DIR/skills"

bootstrap_args=(--force)
case "$INSTALL_MODE" in
  copy)
    bootstrap_args+=(--copy)
    ;;
  link|symlink)
    ;;
  *)
    echo "[codex-skills] invalid CODEX_SKILLS_INSTALL_MODE: $INSTALL_MODE" >&2
    echo "[codex-skills] expected one of: copy, link, symlink" >&2
    exit 1
    ;;
esac

case "$WITH_PLUGINS" in
  true|1|yes|YES|y|Y)
    bootstrap_args+=(--with-plugins)
    ;;
  false|0|no|NO|n|N)
    ;;
  *)
    echo "[codex-skills] invalid CODEX_SKILLS_WITH_PLUGINS: $WITH_PLUGINS" >&2
    echo "[codex-skills] expected true or false" >&2
    exit 1
    ;;
esac

case "$WITH_LAZYCODEX" in
  true|1|yes|YES|y|Y)
    bootstrap_args+=(--with-lazycodex)
    ;;
  false|0|no|NO|n|N)
    ;;
  *)
    echo "[codex-skills] invalid CODEX_SKILLS_WITH_LAZYCODEX: $WITH_LAZYCODEX" >&2
    echo "[codex-skills] expected true or false" >&2
    exit 1
    ;;
esac

echo "[codex-skills] source: $skills_source_dir"
echo "[codex-skills] CODEX_HOME: $CODEX_HOME_DIR"
echo "[codex-skills] install mode: $INSTALL_MODE"
echo "[codex-skills] with LazyCodex: $WITH_LAZYCODEX"

CODEX_HOME="$CODEX_HOME_DIR" bash "$skills_source_dir/scripts/bootstrap.sh" "${bootstrap_args[@]}"

echo "[codex-skills] installed skills:"
find "$CODEX_HOME_DIR/skills" -maxdepth 2 -name SKILL.md -print | sort || true
