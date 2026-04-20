#!/usr/bin/env bash
set -euo pipefail
trap 'rc=$?; echo "[post-create failed] line=$LINENO cmd=$BASH_COMMAND rc=$rc" >&2' ERR

LOCAL_BIN="$HOME/.local/bin"

upsert_managed_block() {
  local rc_file="$1"
  local begin_marker="$2"
  local end_marker="$3"
  local block_content="$4"
  local tmp_file

  touch "$rc_file"
  tmp_file="$(mktemp)"

  awk -v begin="$begin_marker" -v end="$end_marker" '
    $0 == begin { skip=1; next }
    $0 == end   { skip=0; next }
    !skip       { print }
  ' "$rc_file" >"$tmp_file"

  {
    cat "$tmp_file"
    printf '\n%s\n' "$begin_marker"
    printf '%s\n' "$block_content"
    printf '%s\n' "$end_marker"
  } >"$rc_file"

  rm -f "$tmp_file"
}

ensure_login_path() {
  local rc_file="$1"
  local begin_marker="# >>> /workspaces/OpenAI/.devcontainer/post-create.sh path >>>"
  local end_marker="# <<< /workspaces/OpenAI/.devcontainer/post-create.sh path <<<"
  local block_content

  block_content=$(cat <<EOF
if [ -d "$LOCAL_BIN" ] && [[ ":\$PATH:" != *":$LOCAL_BIN:"* ]]; then
  export PATH="$LOCAL_BIN:\$PATH"
fi
EOF
)

  upsert_managed_block "$rc_file" "$begin_marker" "$end_marker" "$block_content"
}

export PATH="$LOCAL_BIN:$PATH"

ensure_login_path "$HOME/.bashrc"
ensure_login_path "$HOME/.profile"

python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath || true

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$LOCAL_BIN:$PATH"

npm install -g @openai/codex

# Optional browser deps; do not fail Codespace creation if this step has issues.
npx -y playwright@latest install --with-deps chromium || true

python3 --version
pipx --version
node --version
uv --version
codex --version || true

echo
echo "Base Codespace setup complete."
