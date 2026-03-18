#!/bin/bash
# install_deps.sh — Install all missing frontend packages
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Installing in: $SCRIPT_DIR"

npm install @monaco-editor/react axios react-router-dom tailwindcss@3 postcss autoprefixer

echo "✅ All frontend deps installed"
echo "Installed packages:"
npm list @monaco-editor/react axios tailwindcss --depth=0 2>/dev/null || true
