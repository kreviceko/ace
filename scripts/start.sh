#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SIBLING_ACE="$(cd "$REPO_ROOT/.." && pwd)/ACE-Step-1.5"
API_DIR="$REPO_ROOT/apps/api"
LOG_DIR="${TMPDIR:-/tmp}/ace-studio-logs"
mkdir -p "$LOG_DIR"

if [[ ! -d "$SIBLING_ACE" ]]; then
  echo "ACE-Step not found at $SIBLING_ACE. Run ./scripts/install.sh first." >&2
  exit 1
fi

port_open() {
  local port="$1"
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
  else
    (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

echo "==> Starting ACE-Step API on :8001"
if port_open 8001; then
  echo "Port 8001 already in use — assuming ACE-Step API is running."
else
  ACE_LOG="$LOG_DIR/acestep-api.log"
  (
    cd "$SIBLING_ACE"
    nohup uv run acestep-api >"$ACE_LOG" 2>&1 &
    echo $! >"$LOG_DIR/acestep-api.pid"
  )
  echo "ACE-Step API starting (log: $ACE_LOG)"
fi

echo "==> Waiting for ACE-Step /health ..."
healthy=0
for _ in $(seq 1 600); do
  if curl -fsS "http://127.0.0.1:8001/health" >/dev/null 2>&1; then
    healthy=1
    break
  fi
  sleep 3
done
if [[ "$healthy" -ne 1 ]]; then
  echo "Warning: ACE-Step /health not ready yet (models may still be downloading). Studio will still start." >&2
else
  echo "ACE-Step API is healthy."
fi

echo "==> Starting ACE Studio UI on :8787"
cd "$API_DIR"
exec uv run ace-studio
