"""JARVIS FastAPI server – main entry point."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .routes import chat, memory, models, status, tasks, training, voice
from .websocket import ws_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Server startup and shutdown lifecycle."""
    logger.info("JARVIS API server starting up")
    yield
    logger.info("JARVIS API server shutting down")


app = FastAPI(
    title="JARVIS AI Assistant API",
    description="REST API for the JARVIS AI assistant system",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS – allow all origins for development; restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(status.router)
app.include_router(chat.router)
app.include_router(voice.router)
app.include_router(tasks.router)
app.include_router(memory.router)
app.include_router(models.router)
app.include_router(training.router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bidirectional WebSocket connection."""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # Echo back with type annotation for now
            await ws_manager.send(websocket, {"echo": data, "type": "ack"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/", tags=["root"])
async def root():
    """Root endpoint – redirect hint for API docs."""
    return {
        "message": "JARVIS AI Assistant API",
        "docs": "/docs",
        "status": "/status/",
    }
