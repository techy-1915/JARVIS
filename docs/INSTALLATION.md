# JARVIS – Installation Guide

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16 GB | 32 GB |
| CPU | 4 cores | 8+ cores |
| Disk | 20 GB free | 50 GB free |
| GPU | Optional | NVIDIA (CUDA) or Apple Silicon |
| OS | Linux, macOS, Windows (WSL2) | Ubuntu 22.04+ / macOS 13+ |
| Python | 3.10+ | 3.11 |
| Node.js | 18+ | 20 LTS |

---

## 1. Install Ollama

Ollama runs the local AI models. Install it before anything else.

### Linux / macOS
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows
Download the installer from https://ollama.com/download and follow the wizard.

Verify the installation:
```bash
ollama --version
```

---

## 2. Download AI Models

JARVIS requires three Ollama models (total ~12 GB):

```bash
ollama pull phi3          # Conversational intelligence (~2.3 GB)
ollama pull deepseek-coder # Coding intelligence (~3.8 GB)
ollama pull mistral       # Reasoning intelligence (~4.1 GB)
```

Or use the provided script:
```bash
bash scripts/install_ollama_models.sh
```

---

## 3. Clone the Repository

```bash
git clone https://github.com/techy-1915/JARVIS.git
cd JARVIS
```

---

## 4. Install Python Dependencies

### Option A – One command
```bash
pip install -e .
```

### Option B – From requirements.txt
```bash
pip install -r requirements.txt
```

### Optional extras
```bash
# Vector database (for semantic memory search)
pip install chromadb

# Speech-to-text (large download)
pip install openai-whisper

# Text-to-speech (offline)
pip install pyttsx3

# ML fine-tuning pipeline
pip install torch transformers peft datasets accelerate
```

---

## 5. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

Requires Node.js 18+. Download from https://nodejs.org.

---

## 6. Configure Environment Variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API endpoint |
| `JARVIS_PORT` | `8000` | Backend API port |
| `DATASET_DIR` | `datasets` | Directory for training data |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 7. Run JARVIS

### Start backend
```bash
# Option A – script
bash scripts/start_backend.sh

# Option B – uvicorn directly
uvicorn jarvis.api.server:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

### Start frontend
```bash
# Option A – script
bash scripts/start_frontend.sh

# Option B – npm
cd frontend && npm run dev
```

UI available at: http://localhost:5173

---

## 8. Full Automated Setup

Run everything in one step:

```bash
bash scripts/setup.sh
```

---

## 9. Verify Installation

Run the test suite:
```bash
pytest tests/ -v
```

Check the API health endpoint:
```bash
curl http://localhost:8000/status/
```

Expected response:
```json
{"status": "ok", "service": "JARVIS", ...}
```

---

## Troubleshooting

### Ollama not found
Make sure `~/.ollama/bin` is in your `PATH` or that you restarted your terminal after install.

### Model download fails
Check your internet connection and disk space (`df -h`). Models require ~12 GB total.

### Port already in use
Change the port: `uvicorn jarvis.api.server:app --port 8001`

### Python version errors
JARVIS requires Python 3.10+. Check with `python3 --version`.

### Module not found
Run `pip install -e .` from the repository root to install JARVIS as an editable package.
