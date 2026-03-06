#!/usr/bin/env bash
# JARVIS – install all Python and Node.js dependencies
# Usage: bash scripts/install_dependencies.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Installing Python dependencies ==="
python3 -m pip install --upgrade pip
pip install -e .

echo ""
echo "=== Installing dev/test extras ==="
pip install "pytest>=8.0.0" "pytest-asyncio>=0.23.0" "ruff>=0.3.0"

echo ""
echo "=== Installing Node.js dependencies ==="
if command -v node &>/dev/null; then
    cd frontend
    npm install
    cd ..
else
    echo "WARNING: Node.js not found. Install from https://nodejs.org (v18+) to use the frontend."
fi

echo ""
echo "Python dependencies installed."
