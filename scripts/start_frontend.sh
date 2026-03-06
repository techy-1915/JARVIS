#!/usr/bin/env bash
# JARVIS – launch React frontend (Vite dev server)
# Usage: bash scripts/start_frontend.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT/frontend"

echo "=== Starting JARVIS Frontend ==="
echo "URL: http://localhost:5173"
echo ""

npm run dev
