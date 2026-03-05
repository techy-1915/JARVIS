# JARVIS – AI Assistant

[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Tests](https://github.com/techy-1915/JARVIS/actions/workflows/test.yml/badge.svg)](https://github.com/techy-1915/JARVIS/actions)

A modular, privacy-first AI assistant with voice interaction, multi-agent reasoning, task execution, memory, and mobile integration.

## ✨ Features

- 🎤 **Voice & Chat** – Respond to voice commands and text messages
- 🤖 **Multi-Agent Reasoning** – Commander, Planner, Reasoning, and Specialist agents
- 🧠 **Local AI** – Runs with Ollama/LLaMA locally; brain is swappable for custom models
- 💾 **Memory** – Short-term context, long-term preferences, and knowledge documents
- ⚡ **Task Execution** – File operations, app launching, browser automation, scripts
- 🔌 **Plugin System** – Extensible tool architecture
- 📱 **Mobile Ready** – REST API + WebSocket designed for iOS/Android clients
- 🔒 **Security First** – Input validation, sandboxing, JWT auth, encryption

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) (for local LLM)

### Installation

```bash
git clone https://github.com/techy-1915/JARVIS.git
cd JARVIS

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp config/.env.example .env    # Edit with your settings

# Pull the default model
ollama pull llama3
```

### Run the API Server

```bash
uvicorn jarvis.api.server:app --reload --host 0.0.0.0 --port 8000
```

- API docs: **http://localhost:8000/docs**
- Dashboard: Open `interface/index.html` in your browser
- Health check: **http://localhost:8000/status/**

### Docker

```bash
docker-compose up --build
```

### Run Tests

```bash
pytest tests/ -v
```

## 📁 Project Structure

```
jarvis/
├── core/
│   ├── brain/        ← AI brain (Ollama/LLaMA, swappable)
│   ├── agents/       ← Multi-agent orchestration
│   ├── memory/       ← Short-term, long-term, knowledge
│   ├── tools/        ← Browser, file, search, plugins
│   ├── security/     ← Validation, permissions, sandbox
│   ├── execution/    ← Task execution engine
│   ├── perception/   ← Voice & text input processing
│   └── output/       ← Text formatting & TTS
├── api/              ← FastAPI REST server
│   └── routes/       ← chat, voice, tasks, memory, status
├── interface/        ← Web dashboard (HTML/JS)
├── mobile_app/       ← Mobile specs & API contract
├── config/           ← YAML configuration
├── tests/            ← Test suite
└── docs/             ← Documentation
```

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design overview |
| [API.md](docs/API.md) | REST API reference |
| [AGENTS.md](docs/AGENTS.md) | Agent system guide |
| [MEMORY.md](docs/MEMORY.md) | Memory architecture |
| [TOOLS.md](docs/TOOLS.md) | Tool development |
| [SECURITY.md](docs/SECURITY.md) | Security guidelines |
| [MOBILE.md](docs/MOBILE.md) | Mobile app specs |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment instructions |
| [DEVELOPMENT.md](docs/DEVELOPMENT.md) | Development guide |

## 🔮 Custom Model Integration

The AI brain is fully abstracted. Replace Ollama with your own model:

```python
from jarvis.core.brain.brain_interface import BrainInterface

class MyModel(BrainInterface):
    async def think(self, prompt, context=None):
        return my_model.generate(prompt)
    async def is_available(self):
        return True
    def get_model_info(self):
        return {"name": "my-custom-model"}
```

## License

MIT – see [LICENSE](LICENSE)
