#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIBLING_ACE="$(cd "$REPO_ROOT/.." && pwd)/ACE-Step-1.5"
API_DIR="$REPO_ROOT/apps/api"

echo "==> ACE Studio install"
echo "Repo: $REPO_ROOT"

if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

if [[ ! -d "$SIBLING_ACE" ]]; then
  echo "==> Cloning ACE-Step 1.5 to $SIBLING_ACE"
  git clone --depth 1 https://github.com/ACE-Step/ACE-Step-1.5.git "$SIBLING_ACE"
else
  echo "==> ACE-Step already present at $SIBLING_ACE"
fi

echo "==> Syncing ACE-Step (Python 3.12)"
(
  cd "$SIBLING_ACE"
  uv python install 3.12
  uv sync --python 3.12
  if [[ ! -f .env ]]; then
    cat > .env <<'EOF'
ACESTEP_CONFIG_PATH=acestep-v15-turbo
ACESTEP_LM_MODEL_PATH=acestep-5Hz-lm-0.6B
ACESTEP_LM_BACKEND=pt
ACESTEP_INIT_LLM=true
ACESTEP_API_HOST=127.0.0.1
ACESTEP_API_PORT=8001
ACESTEP_OFFLOAD_TO_CPU=true
EOF
    echo "Wrote ACE-Step .env defaults for ~8GB VRAM (edit as needed)."
  fi
)

echo "==> Syncing ACE Studio API"
(
  cd "$API_DIR"
  uv sync
)

if [[ ! -f "$REPO_ROOT/.env" ]]; then
  cp "$REPO_ROOT/.env.example" "$REPO_ROOT/.env"
  echo "Created $REPO_ROOT/.env"
fi

mkdir -p "$REPO_ROOT/data/uploads" "$REPO_ROOT/data/library" "$REPO_ROOT/data/exports" "$REPO_ROOT/data/stems"

echo
echo "Install complete."
echo "Next: ./scripts/start.sh"
echo "First generation downloads model weights (multi-GB)."
