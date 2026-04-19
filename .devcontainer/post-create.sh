#!/usr/bin/env bash
set -euo pipefail

LOCAL_BIN="$HOME/.local/bin"

ensure_login_path() {
  local rc_file="$1"
  local marker="# added by /workspaces/OpenAI/.devcontainer/post-create.sh"

  touch "$rc_file"
  if ! grep -Fq "$marker" "$rc_file"; then
    cat >>"$rc_file" <<EOF

$marker
if [ -d "$LOCAL_BIN" ] && [[ ":\$PATH:" != *":$LOCAL_BIN:"* ]]; then
  export PATH="$LOCAL_BIN:\$PATH"
fi
EOF
  fi
}

export PATH="$LOCAL_BIN:$PATH"

ensure_login_path "$HOME/.bashrc"
ensure_login_path "$HOME/.profile"

python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$LOCAL_BIN:$PATH"

npm install -g @openai/codex

pipx install --force ouroboros-ai

if command -v ouroboros >/dev/null 2>&1; then
  ouroboros setup --runtime codex --non-interactive || true
fi

npx -y playwright@latest install --with-deps chromium

python3 --version
pipx --version
node --version
uv --version
codex --version
ouroboros --version
