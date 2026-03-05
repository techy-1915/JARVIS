"""Memory API routes."""

import logging
from typing import Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.memory.memory_store import MemoryStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])

_memory: Optional[MemoryStore] = None


def _get_memory() -> MemoryStore:
    global _memory
    if _memory is None:
        _memory = MemoryStore()
    return _memory


class MemorySetRequest(BaseModel):
    """Request to store a key-value memory entry."""

    key: str
    value: Any


class LearnRequest(BaseModel):
    """Request to add a knowledge document."""

    content: str
    title: str = ""
    tags: List[str] = []


@router.post("/set", summary="Store a memory")
async def set_memory(body: MemorySetRequest):
    """Store or update a key in long-term memory."""
    _get_memory().remember(body.key, body.value)
    return {"status": "ok", "key": body.key}


@router.get("/get/{key}", summary="Retrieve a memory")
async def get_memory(key: str):
    """Retrieve a value from long-term memory."""
    value = _get_memory().recall(key)
    if value is None:
        raise HTTPException(status_code=404, detail=f"Key not found: {key}")
    return {"key": key, "value": value}


@router.get("/keys", summary="List all memory keys")
async def list_keys():
    """Return all stored long-term memory keys."""
    return {"keys": _get_memory().long_term.list_keys()}


@router.post("/learn", summary="Add knowledge document")
async def learn(body: LearnRequest):
    """Add a document to the knowledge memory."""
    doc_id = _get_memory().learn(body.content, body.title, body.tags)
    return {"status": "ok", "doc_id": doc_id}


@router.get("/search", summary="Search knowledge")
async def search_knowledge(q: str, limit: int = 5):
    """Search knowledge memory by keyword."""
    results = _get_memory().search_knowledge(q, limit)
    return {"query": q, "results": results}
