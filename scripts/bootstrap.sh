#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/bootstrap.sh [--copy] [--force] [--with-plugins] [--with-lazycodex]

Options:
  --copy            Copy files instead of creating symlinks
  --force           Replace existing install paths
  --with-plugins    Also install local plugins into ~/plugins
  --with-lazycodex  Install LazyCodex/OmO for Codex
EOF
}

mode="link"
force="false"
with_plugins="false"
with_lazycodex="${CODEX_SKILLS_WITH_LAZYCODEX:-false}"

while [ $# -gt 0 ]; do
  case "$1" in
    --copy)
      mode="copy"
      ;;
    --force)
      force="true"
      ;;
    --with-plugins)
      with_plugins="true"
      ;;
    --with-lazycodex)
      with_lazycodex="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
  shift
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/.." && pwd)"
codex_home="${CODEX_HOME:-$HOME/.codex}"
skill_src="$repo_root/skills"
skill_dest="$codex_home/skills"
plugin_src="$repo_root/plugins"
plugin_dest="$HOME/plugins"

mkdir -p "$skill_dest"

install_item() {
  local src="$1"
  local dest="$2"

  if [ -e "$dest" ] || [ -L "$dest" ]; then
    if [ "$force" = "true" ]; then
      rm -rf "$dest"
    else
      echo "skip existing: $dest"
      return 0
    fi
  fi

  if [ "$mode" = "copy" ]; then
    cp -a "$src" "$dest"
  else
    ln -s "$src" "$dest"
  fi

  echo "installed: $dest"
}

for skill in "$skill_src"/*; do
  [ -d "$skill" ] || continue
  install_item "$skill" "$skill_dest/$(basename "$skill")"
done

if [ "$with_plugins" = "true" ] && [ -d "$plugin_src" ]; then
  mkdir -p "$plugin_dest"
  for plugin in "$plugin_src"/*; do
    [ -d "$plugin" ] || continue
    if [ -f "$plugin/.codex-plugin/plugin.json" ]; then
      install_item "$plugin" "$plugin_dest/$(basename "$plugin")"
    fi
  done
fi

install_lazycodex() {
  if ! command -v node >/dev/null 2>&1; then
    echo "LazyCodex install requires node on PATH" >&2
    return 1
  fi

  if ! command -v bun >/dev/null 2>&1; then
    echo "installing Bun runtime for LazyCodex"
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
  fi

  if [ -x "$repo_root/bin/lazycodex-ai.js" ]; then
    node "$repo_root/bin/lazycodex-ai.js" install --no-tui --codex-autonomous
  else
    npx --yes lazycodex-ai install --no-tui --codex-autonomous
  fi
}

case "$with_lazycodex" in
  true|1|yes|YES|y|Y)
    install_lazycodex
    ;;
  false|0|no|NO|n|N)
    ;;
  *)
    echo "Invalid CODEX_SKILLS_WITH_LAZYCODEX: $with_lazycodex" >&2
    echo "Expected true or false" >&2
    exit 1
    ;;
esac

echo "done"
