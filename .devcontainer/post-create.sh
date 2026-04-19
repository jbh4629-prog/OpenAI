#!/usr/bin/env bash
set -euo pipefail

LOCAL_BIN="$HOME/.local/bin"
WRAPPER_BIN="$LOCAL_BIN/codex-with-model"

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

ensure_shell_helpers() {
  local rc_file="$1"
  local begin_marker="# >>> /workspaces/OpenAI/.devcontainer/post-create.sh shell helpers >>>"
  local end_marker="# <<< /workspaces/OpenAI/.devcontainer/post-create.sh shell helpers <<<"
  local block_content

  block_content=$(cat <<'EOF'
select_ouroboros_codex_model() {
  local choice=""
  local default_model="gpt-5.1-codex-max"

  echo
  echo "Codex CLI model presets:"
  echo "  1) gpt-5.1-codex-max"
  echo "  2) gpt-5.1-codex-mini"
  echo "  c) other supported / legacy model id"
  printf "Codex model [%s]: " "$default_model" >&2

  read -r choice || true
  choice="${choice:-$default_model}"

  case "$choice" in
    1|max|gpt-5.1-codex-max)
      printf '%s\n' "gpt-5.1-codex-max"
      ;;
    2|mini|gpt-5.1-codex-mini)
      printf '%s\n' "gpt-5.1-codex-mini"
      ;;
    c|C|custom|other)
      printf "Enter exact Codex model id: " >&2
      read -r choice
      if [[ -z "${choice:-}" ]]; then
        echo "Model id cannot be empty." >&2
        return 1
      fi
      printf '%s\n' "$choice"
      ;;
    *)
      printf '%s\n' "$choice"
      ;;
  esac
}

ouroboros() {
  if [[ -z "${OB_CODEX_MODEL:-}" && -t 0 && -t 1 ]]; then
    export OB_CODEX_MODEL
    OB_CODEX_MODEL="$(select_ouroboros_codex_model)"
  fi

  command ouroboros "$@"
}

ob() {
  ouroboros "$@"
}
EOF
)

  upsert_managed_block "$rc_file" "$begin_marker" "$end_marker" "$block_content"
}

export PATH="$LOCAL_BIN:$PATH"

ensure_login_path "$HOME/.bashrc"
ensure_login_path "$HOME/.profile"
ensure_shell_helpers "$HOME/.bashrc"

python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath || true

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

main() {
  if has_explicit_model_flag "\$@"; then
    exec "\$REAL_CODEX_BIN" "\$@"
  fi

  local model="\${OB_CODEX_MODEL:-}"

  if [[ -z "\$model" ]]; then
    model="\$DEFAULT_MODEL"
  fi

  echo "[codex-with-model] using model: \$model" >&2
  exec "\$REAL_CODEX_BIN" -m "\$model" "\$@"
}

main "\$@"
EOF

chmod +x "$WRAPPER_BIN"

pipx install --force ouroboros-ai

if command -v ouroboros >/dev/null 2>&1; then
  REAL_OUROBOROS_BIN="$(command -v ouroboros)"

  ouroboros setup --runtime codex --non-interactive || true
  "$REAL_OUROBOROS_BIN" config set orchestrator.runtime_backend codex || true
  "$REAL_OUROBOROS_BIN" config set orchestrator.codex_cli_path "$WRAPPER_BIN" || true
  "$REAL_OUROBOROS_BIN" config validate || true
fi

npx -y playwright@latest install --with-deps chromium || true

python3 --version
pipx --version
node --version
uv --version
codex --version
command -v ouroboros
ouroboros --version

echo
echo "Setup complete."
echo "Open a new terminal, then run: ouroboros"
echo "You will be prompted to select a Codex model before Ouroboros runs."
