#!/usr/bin/env bash
# JARVIS – pull required Ollama models
# Usage: bash scripts/install_ollama_models.sh

set -e

echo "=== Downloading JARVIS AI models via Ollama ==="

if ! command -v ollama &>/dev/null; then
    echo "ERROR: Ollama is not installed."
    echo "Install from: https://ollama.com/download"
    echo ""
    echo "Quick install (Linux/macOS):"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

echo "Pulling phi3 (conversational intelligence)..."
ollama pull phi3

echo "Pulling deepseek-coder (coding intelligence)..."
ollama pull deepseek-coder

echo "Pulling mistral (reasoning intelligence)..."
ollama pull mistral

echo ""
echo "All models downloaded. List with: ollama list"
