"""Task execution API routes."""

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...core.execution.executor import Executor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])

_executor: Optional[Executor] = None


def _get_executor() -> Executor:
    global _executor
    if _executor is None:
        _executor = Executor()
    return _executor


class TaskRequest(BaseModel):
    """Task execution request."""

    action_type: str
    parameters: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    """Task execution response."""

    status: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/execute", response_model=TaskResponse, summary="Execute a task")
async def execute_task(body: TaskRequest):
    """Execute a system task (file, app, script, browser)."""
    try:
        executor = _get_executor()
        result = await executor.execute(body.action_type, **body.parameters)
        return TaskResponse(
            status=result.get("status", "unknown"),
            result=result if result.get("status") == "success" else None,
            error=result.get("error"),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Task execution error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/history", summary="Get task history")
async def get_task_history(limit: int = 50):
    """Return recent task execution history."""
    executor = _get_executor()
    return {"history": executor._log.get_recent(limit)}
