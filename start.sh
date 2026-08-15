#!/bin/bash
set -euo pipefail

# Start JioSaavn sidecar in background (if it exists)
if [ -d "./musicbot/jiosaavn-sidecar-clean/artifacts/api-server" ]; then
  if [ -f "./musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json" ]; then
    echo "Installing JioSaavn sidecar dependencies..."
    cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server
    npm ci --omit=dev || npm install --omit=dev
    echo "Starting JioSaavn sidecar..."
    PORT=${PORT:-8080} PORT=$PORT node --enable-source-maps ./dist/index.mjs &>/tmp/sidecar.log &
    cd - >/dev/null || true
  fi
fi

# Start the Python bot in foreground
cd musicbot
echo "Starting Python music bot..."
uv run python3 -m anony
