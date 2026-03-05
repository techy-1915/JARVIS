"""Status API routes."""

import platform
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/status", tags=["status"])


@router.get("/", summary="Health check")
async def get_status():
    """Return basic system health information."""
    return {
        "status": "ok",
        "service": "JARVIS",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system(),
        "python": platform.python_version(),
    }


@router.get("/version", summary="Version info")
async def get_version():
    """Return version and build information."""
    return {
        "version": "0.1.0",
        "service": "JARVIS AI Assistant",
        "phase": "architecture",
    }
