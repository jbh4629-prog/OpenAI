#!/usr/bin/env bash
set -euo pipefail

LOCAL_BIN="$HOME/.local/bin"
WRAPPER_BIN="$LOCAL_BIN/codex-with-model"

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

ensure_shell_helpers() {
  local rc_file="$1"
  local marker="# added by /workspaces/OpenAI/.devcontainer/post-create.sh shell helpers"

  touch "$rc_file"
  if ! grep -Fq "$marker" "$rc_file"; then
    cat >>"$rc_file" <<'EOF'

# added by /workspaces/OpenAI/.devcontainer/post-create.sh shell helpers
ob() {
  ouroboros "$@"
}
EOF
  fi
}

export PATH="$LOCAL_BIN:$PATH"

ensure_login_path "$HOME/.bashrc"
ensure_login_path "$HOME/.profile"
ensure_shell_helpers "$HOME/.bashrc"

python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$LOCAL_BIN:$PATH"

npm install -g @openai/codex

REAL_CODEX_BIN="$(command -v codex)"

cat >"$WRAPPER_BIN" <<EOF
#!/usr/bin/env bash
set -euo pipefail

REAL_CODEX_BIN="$REAL_CODEX_BIN"
DEFAULT_MODEL="gpt-5.1-codex-max"

has_explicit_model_flag() {
  local prev=""
  for arg in "\$@"; do
    if [[ "\$prev" == "-m" || "\$prev" == "--model" ]]; then
      return 0
    fi
    case "\$arg" in
      -m|--model)
        return 0
        ;;
      --model=*)
        return 0
        ;;
    esac
    prev="\$arg"
  done
  return 1
}

pick_model_interactive() {
  local choice=""
  while true; do
    echo
    echo "Select Codex model for this Ouroboros run:"
    echo "  1) gpt-5.1-codex-max"
    echo "  2) gpt-5.1-codex-mini"
    echo "  3) custom"
    printf "Enter choice [1-3] (default: 1): " >&2
    read -r choice || true

    case "\${choice:-1}" in
      1)
        printf '%s\n' "gpt-5.1-codex-max"
        return 0
        ;;
      2)
        printf '%s\n' "gpt-5.1-codex-mini"
        return 0
        ;;
      3)
        printf "Enter custom model id: " >&2
        read -r choice
        if [[ -n "\${choice:-}" ]]; then
          printf '%s\n' "\$choice"
          return 0
        fi
        echo "Custom model id cannot be empty." >&2
        ;;
      *)
        echo "Invalid selection." >&2
        ;;
    esac
  done
}

main() {
  if has_explicit_model_flag "\$@"; then
    exec "\$REAL_CODEX_BIN" "\$@"
  fi

  local model="\${OB_CODEX_MODEL:-}"

  if [[ -z "\$model" ]]; then
    if [[ -t 0 && -t 1 ]]; then
      model="\$(pick_model_interactive)"
    else
      model="\$DEFAULT_MODEL"
    fi
  fi

  echo "[codex-with-model] using model: \$model" >&2
  exec "\$REAL_CODEX_BIN" -m "\$model" "\$@"
}

main "\$@"
EOF

chmod +x "$WRAPPER_BIN"

pipx install --force ouroboros-ai

if command -v ouroboros >/dev/null 2>&1; then
  ouroboros setup --runtime codex --non-interactive || true

  ouroboros config set orchestrator.runtime_backend codex || true
  ouroboros config set orchestrator.codex_cli_path "$WRAPPER_BIN" || true
  ouroboros config validate || true
fi

npx -y playwright@latest install --with-deps chromium

python3 --version
pipx --version
node --version
uv --version
codex --version
ouroboros --version

echo
echo "Setup complete."
echo "New Ouroboros runs will prompt for a Codex model."
echo "Open a new terminal, then run: ouroboros"
