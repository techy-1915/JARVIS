# JARVIS Deployment Guide

## Local Development

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai) with llama3 model

### Setup

```bash
# Clone and enter repo
git clone <repo-url>
cd JARVIS

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment file
cp config/.env.example .env
# Edit .env with your settings

# Pull Ollama model
ollama pull llama3

# Start the API server
uvicorn jarvis.api.server:app --reload --host 0.0.0.0 --port 8000
```

Open the dashboard: `interface/index.html` in your browser (or serve with any HTTP server).

## Docker

```bash
# Build and start all services
docker-compose up --build

# Access:
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
```

## Production Checklist

- [ ] Set strong `JARVIS_SECRET_KEY`
- [ ] Enable `require_auth: true`
- [ ] Configure HTTPS / TLS
- [ ] Set `CORS_ORIGINS` to your domain only
- [ ] Configure log rotation
- [ ] Set up monitoring and alerts
