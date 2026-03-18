#!/usr/bin/env python3
"""
server.py — Start RepoPulse backend (Flask-based, works with existing venv).
Usage: python3 server.py
"""
import os, sys, subprocess
from pathlib import Path

ROOT    = Path(__file__).parent.resolve()
BACKEND = ROOT / "backend"
VENV    = BACKEND / "venv"
PY      = VENV / "bin" / "python3"

print("=" * 50)
print("  RepoPulse Backend (Flask)")
print("=" * 50)
print(f"  Backend: {BACKEND}")

# Verify Flask is available
check = subprocess.run([str(PY), "-c", "import flask; print('Flask', flask.__version__)"],
                       capture_output=True, text=True)
if check.returncode != 0:
    print("❌ Flask not found in venv. Run:")
    print(f"   source {VENV}/bin/activate && pip install flask flask-cors")
    sys.exit(1)
print(f"  ✅ {check.stdout.strip()}")

# Kill any existing process on port 8000
subprocess.run("lsof -ti :8000 | xargs kill -9 2>/dev/null || true", shell=True)

print(f"\n🚀 Starting Flask server at http://localhost:8000")
print(f"   Health → http://localhost:8000/health")
print(f"   Press Ctrl+C to stop.\n")

os.chdir(str(BACKEND))
os.execv(str(PY), [str(PY), str(BACKEND / "main.py")])
