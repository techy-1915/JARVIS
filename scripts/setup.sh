#!/usr/bin/env bash
# JARVIS – one-command full setup
# Usage: bash scripts/setup.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "=== JARVIS Setup ==="
echo "Repository: $REPO_ROOT"
cd "$REPO_ROOT"

echo ""
echo "--- Installing system dependencies ---"
bash "$SCRIPT_DIR/install_dependencies.sh"

echo ""
echo "--- Pulling Ollama models ---"
bash "$SCRIPT_DIR/install_ollama_models.sh"

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Start the backend:   bash scripts/start_backend.sh"
echo "Start the frontend:  bash scripts/start_frontend.sh"
echo "API docs:            http://localhost:8000/docs"
