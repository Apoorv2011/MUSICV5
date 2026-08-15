#!/bin/bash
set -euo pipefail

# If the sidecar exists, install its deps and start it in background on PORT 8080
if [ -d "./musicbot/jiosaavn-sidecar-clean/artifacts/api-server" ]; then
  if [ -f "./musicbot/jiosaavn-sidecar-clean/artifacts/api-server/package.json" ]; then
    echo "Installing JioSaavn sidecar dependencies..."
    cd musicbot/jiosaavn-sidecar-clean/artifacts/api-server
    npm ci --omit=dev || true
    echo "Starting JioSaavn sidecar..."
    PORT=${PORT:-8080} PORT=$PORT node --enable-source-maps ./dist/index.mjs &>/tmp/sidecar.log &
    cd - >/dev/null || true
  fi
fi

# Start the Python music bot (uses the same command your repo uses)
cd musicbot
echo "Starting Python music bot..."
uv run python3 -m anony
