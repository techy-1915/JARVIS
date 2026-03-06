#!/usr/bin/env bash
# JARVIS – launch FastAPI backend
# Usage: bash scripts/start_backend.sh [--port 8000]

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PORT="${1:-8000}"

echo "=== Starting JARVIS Backend ==="
echo "URL:  http://localhost:$PORT"
echo "Docs: http://localhost:$PORT/docs"
echo ""

uvicorn jarvis.api.server:app \
    --reload \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info
