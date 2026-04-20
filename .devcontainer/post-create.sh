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
  local model=""

  while true; do
    echo
    echo "Select Codex CLI model:"
    echo "  1) gpt-5.1-codex-max"
    echo "  2) gpt-5.1-codex-mini"
    echo "  3) other supported / legacy model id"
    echo "  4) cancel"
    printf "Choose [1-4] (default: 1): " >&2

    read -r choice || true
    choice="${choice:-1}"

    case "$choice" in
      1)
        printf '%s\n' "gpt-5.1-codex-max"
        return 0
        ;;
      2)
        printf '%s\n' "gpt-5.1-codex-mini"
        return 0
        ;;
      3)
        printf "Enter exact Codex model id: " >&2
        read -r model || true
        if [[ -n "${model:-}" ]]; then
          printf '%s\n' "$model"
          return 0
        fi
        echo "Model id cannot be empty." >&2
        ;;
      4)
        echo "Cancelled." >&2
        return 1
        ;;
      *)
        echo "Invalid selection." >&2
        ;;
    esac
  done
}

ouroboros() {
  local real_ouroboros_bin
  real_ouroboros_bin="$(type -P ouroboros)"

  if [[ -z "${OB_CODEX_MODEL:-}" && -t 0 && -t 1 ]]; then
    export OB_CODEX_MODEL
    OB_CODEX_MODEL="$(select_ouroboros_codex_model)" || return 1
  fi

  command "$real_ouroboros_bin" "$@"
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

# Install Ouroboros with LiteLLM extra so init won't die if any path still imports it.
pipx install --force "ouroboros-ai[litellm]"

if command -v ouroboros >/dev/null 2>&1; then
  REAL_OUROBOROS_BIN="$(command -v ouroboros)"
  CONFIG_PATH="$HOME/.ouroboros/config.yaml"

  ouroboros setup --runtime codex --non-interactive || true

  python3 - <<PY
from pathlib import Path
import re

config_path = Path("$CONFIG_PATH")
text = config_path.read_text() if config_path.exists() else ""

def upsert_top_level(text: str, key: str, value: str) -> str:
    pattern = rf'(?m)^{re.escape(key)}:.*$'
    line = f"{key}: {value}"
    if re.search(pattern, text):
        return re.sub(pattern, line, text)
    if text and not text.endswith("\n"):
        text += "\n"
    return text + line + "\n"

def upsert_orchestrator_key(text: str, key: str, value: str) -> str:
    block_pat = r'(?ms)^orchestrator:\n(?P<body>(?:^[ \t].*\n?)*)'
    m = re.search(block_pat, text)
    new_line = f"  {key}: {value}"
    if m:
        body = m.group("body") or ""
        key_pat = rf'(?m)^[ \t]+{re.escape(key)}:.*$'
        if re.search(key_pat, body):
            body = re.sub(key_pat, new_line, body)
        else:
            if body and not body.endswith("\n"):
                body += "\n"
            body += new_line + "\n"
        return text[:m.start()] + "orchestrator:\n" + body + text[m.end():]
    if text and not text.endswith("\n"):
        text += "\n"
    return text + "orchestrator:\n" + new_line + "\n"

text = upsert_top_level(text, "llm_backend", "codex")
text = upsert_orchestrator_key(text, "runtime_backend", "codex")
text = upsert_orchestrator_key(text, "codex_cli_path", '"' + "$WRAPPER_BIN" + '"')

config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(text)
print(config_path)
PY

  cat "$CONFIG_PATH" || true
  "$REAL_OUROBOROS_BIN" config validate || true
  "$REAL_OUROBOROS_BIN" config show || true
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
