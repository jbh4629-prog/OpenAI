#!/usr/bin/env bash
set -e

curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

npm install -g @openai/codex

python3 --version
node --version
uv --version
codex --version || true
