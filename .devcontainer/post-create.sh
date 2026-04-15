#!/usr/bin/env bash
set -e

# pipx
python3 -m pip install --user --upgrade pipx
python3 -m pipx ensurepath
export PATH="$HOME/.local/bin:$PATH"

# uv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

npm install -g @openai/codex

python3 --version
pipx --version
node --version
uv --version
codex --version || true
