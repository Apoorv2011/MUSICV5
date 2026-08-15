#!/bin/bash
set -euo pipefail

# --- Config ---
SIDECAR_DIR="musicbot/jiosaavn-sidecar-clean/artifacts/api-server"
SIDECAR_DIST="$SIDECAR_DIR/dist/index.mjs"
SIDECAR_LOG="/tmp/sidecar.log"

# --- Start JioSaavn sidecar on internal port 8081 ---
if [ -d "$SIDECAR_DIR" ]; then
  if [ -f "$SIDECAR_DIST" ]; then
    echo "Starting pre-built JioSaavn sidecar on internal port 8081..."
    ( cd "$SIDECAR_DIR" && PORT=8081 node --enable-source-maps ./dist/index.mjs ) &> "$SIDECAR_LOG" &
    echo "Sidecar started (logs -> $SIDECAR_LOG)"
  else
    echo "Warning: sidecar dist not found at $SIDECAR_DIST — skipping sidecar start" >&2
  fi
fi

# --- Start the Python music bot in the foreground ---
cd musicbot
echo "Starting Python music bot..."
python3 -m anony
