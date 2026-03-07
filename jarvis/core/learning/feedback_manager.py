"""Feedback manager – records explicit and implicit quality scores."""

import json
import logging
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_DB_PATH = "data/feedback/feedback.db"

# ---------------------------------------------------------------------------
# Implicit scoring constants
# ---------------------------------------------------------------------------

_MIN_GOOD_LENGTH = 50       # characters – below this penalises brevity
_MAX_GOOD_LENGTH = 2000     # characters – above this penalises verbosity
_REASONING_KEYWORDS = [
    "because",
    "therefore",
    "however",
    "first",
    "second",
    "finally",
    "in conclusion",
    "step",
    "reason",
    "result",
    "REASONING:",
    "CONCLUSION:",
]


class FeedbackManager:
    """Stores and aggregates response quality scores.

    Scores range from 0.0 (worst) to 1.0 (best).  Two score types are
    supported:

    * **explicit** – user-provided thumbs-up/down or numeric rating.
    * **implicit** – computed heuristics (length, reasoning presence, etc.).

    All data is persisted in a SQLite database.
    """

    def __init__(self, db_path: str = _DEFAULT_DB_PATH) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ------------------------------------------------------------------
    # Database bootstrap
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL,
                    score REAL NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_conv_id ON feedback (conversation_id)"
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def record_feedback(
        self,
        conversation_id: str,
        feedback_type: str,
        score: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Persist a feedback entry.

        Args:
            conversation_id: ID of the conversation being scored.
            feedback_type: ``"explicit"`` or ``"implicit"``.
            score: Quality score in [0.0, 1.0].
            metadata: Optional extra data (e.g. raw response text).

        Returns:
            The feedback entry ID.
        """
        score = max(0.0, min(1.0, float(score)))
        entry_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata or {})

        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO feedback VALUES (?, ?, ?, ?, ?, ?)",
                    (entry_id, conversation_id, feedback_type, score, meta_str, now),
                )
                conn.commit()
            logger.debug(
                "Recorded %s feedback for %s: %.2f", feedback_type, conversation_id, score
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to record feedback: %s", exc)

        return entry_id

    async def calculate_implicit_score(
        self, response: str, metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """Estimate quality of *response* using heuristics.

        Factors considered:
        - Response length (penalise very short or very long).
        - Presence of reasoning keywords.
        - Whether the response contains obvious error markers.
        - Task success flag in *metadata* (if provided).

        Returns:
            A score in [0.0, 1.0].
        """
        meta = metadata or {}
        score = 0.5  # neutral baseline

        # Length component (±0.2)
        length = len(response)
        if length < _MIN_GOOD_LENGTH:
            score -= 0.2 * (1.0 - length / _MIN_GOOD_LENGTH)
        elif length > _MAX_GOOD_LENGTH:
            excess = min(length - _MAX_GOOD_LENGTH, _MAX_GOOD_LENGTH)
            score -= 0.1 * (excess / _MAX_GOOD_LENGTH)
        else:
            score += 0.1  # appropriate length bonus

        # Reasoning quality (±0.15)
        lower = response.lower()
        keyword_hits = sum(1 for kw in _REASONING_KEYWORDS if kw.lower() in lower)
        score += min(keyword_hits * 0.03, 0.15)

        # Error penalty (−0.3)
        error_markers = ["[error:", "error:", "exception:", "traceback"]
        if any(marker in lower for marker in error_markers):
            score -= 0.3

        # Task success flag (+0.2 or −0.1)
        task_success = meta.get("task_success")
        if task_success is True:
            score += 0.2
        elif task_success is False:
            score -= 0.1

        # Clamp
        return max(0.0, min(1.0, score))

    async def get_conversation_score(self, conversation_id: str) -> float:
        """Return the weighted average score for a conversation.

        Explicit feedback is weighted 2× relative to implicit.  Returns
        0.0 if no feedback exists.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    "SELECT feedback_type, score FROM feedback WHERE conversation_id = ?",
                    (conversation_id,),
                ).fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch scores: %s", exc)
            return 0.0

        if not rows:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0
        for row in rows:
            weight = 2.0 if row["feedback_type"] == "explicit" else 1.0
            weighted_sum += row["score"] * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    async def get_high_quality_conversations(
        self, min_score: float = 0.7, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Return conversation IDs whose average score is >= *min_score*.

        Args:
            min_score: Minimum acceptable score (0.0–1.0).
            limit: Maximum number of results.

        Returns:
            List of dicts with ``"conversation_id"`` and ``"avg_score"`` keys.
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT
                        conversation_id,
                        SUM(score * CASE feedback_type WHEN 'explicit' THEN 2 ELSE 1 END)
                            / SUM(CASE feedback_type WHEN 'explicit' THEN 2.0 ELSE 1.0 END)
                            AS avg_score
                    FROM feedback
                    GROUP BY conversation_id
                    HAVING avg_score >= ?
                    ORDER BY avg_score DESC
                    LIMIT ?
                    """,
                    (min_score, limit),
                ).fetchall()
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to fetch high-quality conversations: %s", exc)
            return []

        return [
            {"conversation_id": row["conversation_id"], "avg_score": row["avg_score"]}
            for row in rows
        ]

    async def delete_feedback(self, conversation_id: str) -> bool:
        """Remove all feedback for *conversation_id*.

        Returns:
            True on success.
        """
        try:
            with self._connect() as conn:
                conn.execute(
                    "DELETE FROM feedback WHERE conversation_id = ?", (conversation_id,)
                )
                conn.commit()
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to delete feedback: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_fm: Optional[FeedbackManager] = None


def get_feedback_manager() -> FeedbackManager:
    """Return the module-level singleton FeedbackManager instance."""
    global _default_fm
    if _default_fm is None:
        _default_fm = FeedbackManager()
    return _default_fm
