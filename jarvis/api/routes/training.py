"""Training API – trigger dataset export and monitor training pipeline."""

import logging

from fastapi import APIRouter, HTTPException

from ...core.learning.dataset_builder import DatasetBuilder
from ...core.learning.learning_engine import get_learning_engine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/train", tags=["training"])


@router.post("/", summary="Trigger dataset export")
async def trigger_training():
    """Flush the interaction log and export training datasets.

    Exports all three category datasets (conversations, coding, reasoning)
    in Alpaca format to ``datasets/export/``.

    Returns a summary with dataset statistics and exported file paths.
    """
    try:
        engine = get_learning_engine()
        builder = DatasetBuilder(engine)
        stats = engine.get_dataset_stats()
        exported = builder.export_all()
        return {
            "status": "ok",
            "message": "Datasets exported successfully",
            "stats": stats,
            "exported_files": exported,
        }
    except Exception as exc:
        logger.error("Training trigger failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/stats", summary="Dataset statistics")
async def get_stats():
    """Return interaction counts per dataset category."""
    engine = get_learning_engine()
    stats = engine.get_dataset_stats()
    return {"stats": stats}
