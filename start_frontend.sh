#!/bin/bash
# start_frontend.sh — Start the RepoPulse React frontend
# Run this from the RepoPulse root:  bash start_frontend.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Check node_modules exist
if [ ! -d "$FRONTEND_DIR/node_modules/@monaco-editor" ]; then
  echo "📦 Installing frontend dependencies..."
  cd "$FRONTEND_DIR" && npm install
fi

echo "🎨 Starting RepoPulse frontend on http://localhost:5173"
cd "$FRONTEND_DIR" && npm run dev
