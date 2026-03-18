#!/bin/bash
# start_backend.sh — Reliable RepoPulse FastAPI backend starter
# Usage: bash ~/Documents/MOGLI/POJECTS/RepoPulse/start_backend.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
PYTHON="$BACKEND_DIR/venv/bin/python3"

echo "📁 Backend dir: $BACKEND_DIR"

# Create venv if missing
if [ ! -f "$PYTHON" ]; then
  echo "🔧 Creating virtual environment..."
  python3 -m venv "$BACKEND_DIR/venv"
fi

# Install deps
echo "📦 Installing/verifying dependencies..."
"$PYTHON" -m pip install -q -r "$BACKEND_DIR/requirements.txt"

# Verify imports
echo "🔍 Verifying backend imports..."
cd "$BACKEND_DIR"
"$PYTHON" -c "
import sys
sys.path.insert(0, '.')
from models.schemas import AnalyzeRequest
from cache.store import get, set
from services.repo_cloner import clone_repository
from services.commit_parser import parse_commits
from services.line_tracker import track_line_churn
from services.risk_engine import compute_risk_scores
from main import app
print('✅ All imports OK — starting server...')
"

# Kill anything on port 8000
lsof -ti :8000 | xargs kill -9 2>/dev/null || true

echo ""
echo "🚀 Starting FastAPI on http://localhost:8000"
echo "📖 API docs: http://localhost:8000/docs"
echo ""
"$BACKEND_DIR/venv/bin/python3" main.py
