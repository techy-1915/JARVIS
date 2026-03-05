# JARVIS AI Assistant – Docker container
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY jarvis/ ./jarvis/
COPY config/ ./config/
COPY interface/ ./interface/

# Create log and data directories
RUN mkdir -p jarvis/logs jarvis/data

# Expose API port
EXPOSE 8000

# Default command
CMD ["uvicorn", "jarvis.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
