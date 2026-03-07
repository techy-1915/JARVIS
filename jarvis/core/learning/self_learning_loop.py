"""Autonomous self-learning loop – runs continuously in the background."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Default configuration (overridden by learning_config.yaml)
# ---------------------------------------------------------------------------

_DEFAULT_INTERVAL_HOURS = 24
_DEFAULT_MIN_CONVERSATIONS = 100
_DEFAULT_IMPROVEMENT_THRESHOLD = 0.05  # 5 %
_DEFAULT_MIN_SCORE = 0.7


class SelfLearningLoop:
    """Background async task that periodically:

    1. Collects recent high-quality conversations.
    2. Builds a training dataset.
    3. (Optionally) triggers LoRA fine-tuning.
    4. Evaluates improvements and deploys if threshold met.
    5. Consolidates vector memory knowledge.

    Usage::

        loop = SelfLearningLoop()
        asyncio.create_task(loop.start())
    """

    def __init__(
        self,
        interval_hours: float = _DEFAULT_INTERVAL_HOURS,
        min_conversations: int = _DEFAULT_MIN_CONVERSATIONS,
        improvement_threshold: float = _DEFAULT_IMPROVEMENT_THRESHOLD,
        min_score: float = _DEFAULT_MIN_SCORE,
        auto_train: bool = False,
    ) -> None:
        self._interval_hours = interval_hours
        self._min_conversations = min_conversations
        self._improvement_threshold = improvement_threshold
        self._min_score = min_score
        self._auto_train = auto_train
        self._running = False
        self._task: Optional[asyncio.Task] = None  # type: ignore[type-arg]

    # ------------------------------------------------------------------
    # Public control API
    # ------------------------------------------------------------------

    def start(self) -> asyncio.Task:  # type: ignore[type-arg]
        """Schedule the autonomous learning loop as an asyncio background task.

        Returns:
            The created asyncio.Task.
        """
        if self._task is not None and not self._task.done():
            logger.debug("SelfLearningLoop already running")
            return self._task
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="self_learning_loop")
        logger.info(
            "SelfLearningLoop started (interval=%.1fh, min_convs=%d)",
            self._interval_hours,
            self._min_conversations,
        )
        return self._task

    def stop(self) -> None:
        """Request the learning loop to stop after the current iteration."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("SelfLearningLoop stop requested")

    @property
    def is_running(self) -> bool:
        """True if the loop task is active."""
        return self._task is not None and not self._task.done()

    # ------------------------------------------------------------------
    # Internal loop
    # ------------------------------------------------------------------

    async def _loop(self) -> None:
        """Main async loop body."""
        while self._running:
            try:
                await self.run_once()
            except asyncio.CancelledError:
                break
            except Exception as exc:  # noqa: BLE001
                logger.error("SelfLearningLoop iteration failed: %s", exc, exc_info=True)

            # Wait for next interval
            interval_secs = self._interval_hours * 3600
            logger.debug("SelfLearningLoop sleeping for %.1f hours", self._interval_hours)
            try:
                await asyncio.sleep(interval_secs)
            except asyncio.CancelledError:
                break

    async def run_once(self) -> Dict[str, Any]:
        """Execute a single learning cycle.

        Returns:
            Summary dict describing what happened.
        """
        logger.info("SelfLearningLoop: starting learning cycle")
        summary: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "conversations_collected": 0,
            "dataset_built": False,
            "training_triggered": False,
            "model_deployed": False,
            "knowledge_consolidated": False,
        }

        since = datetime.now(timezone.utc) - timedelta(hours=self._interval_hours)

        # 1. Collect recent conversations
        conversations = await self._collect_conversations(since)
        summary["conversations_collected"] = len(conversations)
        logger.info(
            "SelfLearningLoop: collected %d conversations", len(conversations)
        )

        if len(conversations) >= self._min_conversations:
            # 2. Build training dataset
            dataset_path = await self._build_dataset(since)
            summary["dataset_built"] = bool(dataset_path)

            # 3. Optionally trigger LoRA fine-tuning
            if self._auto_train and dataset_path:
                adapter_path = await self._train_lora(dataset_path)
                if adapter_path:
                    summary["training_triggered"] = True
                    # 4. Evaluate and deploy
                    deployed = await self._evaluate_and_deploy(adapter_path)
                    summary["model_deployed"] = deployed
        else:
            logger.info(
                "SelfLearningLoop: skipping training (%d/%d conversations)",
                len(conversations),
                self._min_conversations,
            )

        # 5. Consolidate vector memory knowledge (always run)
        consolidated = await self._consolidate_knowledge()
        summary["knowledge_consolidated"] = consolidated

        logger.info("SelfLearningLoop: cycle complete – %s", summary)
        return summary

    # ------------------------------------------------------------------
    # Step helpers
    # ------------------------------------------------------------------

    async def _collect_conversations(
        self, since: datetime
    ) -> list:
        """Collect conversations logged since *since*."""
        try:
            from .conversation_logger import get_conversation_logger

            hours_back = max(1, int(self._interval_hours) + 1)
            conv_logger = get_conversation_logger()
            entries = await conv_logger.get_recent(days=hours_back // 24 + 1)
            # Filter by timestamp
            result = []
            for entry in entries:
                ts_str = entry.get("metadata", {}).get("timestamp", "")
                if ts_str:
                    try:
                        if datetime.fromisoformat(ts_str) >= since:
                            result.append(entry)
                    except ValueError:
                        result.append(entry)
                else:
                    result.append(entry)
            return result
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to collect conversations: %s", exc)
            return []

    async def _build_dataset(self, since: datetime) -> str:
        """Run the auto-dataset pipeline and return the output path."""
        try:
            from .auto_dataset_builder import get_auto_dataset_builder

            builder = get_auto_dataset_builder()
            result = await builder.run_pipeline(
                min_score=self._min_score,
                since=since,
            )
            return result.get("filename", "")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to build dataset: %s", exc)
            return ""

    async def _train_lora(self, dataset_path: str) -> str:
        """Trigger LoRA fine-tuning in a subprocess.

        Returns the adapter output path or empty string on failure.
        """
        import subprocess
        import sys

        logger.info("SelfLearningLoop: launching LoRA training on %s", dataset_path)
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "training/fine_tune_lora.py",
                    "--dataset",
                    dataset_path,
                ],
                capture_output=True,
                text=True,
                timeout=4 * 3600,  # max 4 hours
            )
            if result.returncode == 0:
                # Parse adapter path from stdout
                for line in result.stdout.splitlines():
                    if line.startswith("ADAPTER_PATH:"):
                        return line.split(":", 1)[1].strip()
            else:
                logger.error("LoRA training failed:\n%s", result.stderr[-2000:])
        except Exception as exc:  # noqa: BLE001
            logger.error("LoRA training subprocess error: %s", exc)
        return ""

    async def _evaluate_and_deploy(self, adapter_path: str) -> bool:
        """Evaluate trained adapter and deploy if improvement threshold met."""
        try:
            from ..brain.model_manager import get_model_manager

            mgr = get_model_manager()
            metrics = await mgr.get_model_performance_metrics()
            baseline_score = metrics.get("score", 0.5)

            # Simple heuristic: load adapter and run a validation check
            new_available = await mgr.load_new_model(adapter_path)
            if not new_available:
                return False

            new_metrics = await mgr.get_model_performance_metrics()
            new_score = new_metrics.get("score", 0.5)

            improvement = (new_score - baseline_score) / max(baseline_score, 1e-6)
            logger.info(
                "Model evaluation: baseline=%.3f new=%.3f improvement=%.1f%%",
                baseline_score,
                new_score,
                improvement * 100,
            )

            if improvement >= self._improvement_threshold:
                await mgr.swap_model_runtime(adapter_path)
                logger.info(
                    "Deployed improved model from %s (improvement=%.1f%%)",
                    adapter_path,
                    improvement * 100,
                )
                return True
            else:
                logger.info(
                    "Improvement %.1f%% below threshold %.1f%% – keeping current model",
                    improvement * 100,
                    self._improvement_threshold * 100,
                )
                await mgr.rollback_model()
        except Exception as exc:  # noqa: BLE001
            logger.error("Model evaluation/deployment failed: %s", exc)
        return False

    async def _consolidate_knowledge(self) -> bool:
        """Run knowledge consolidation and return True on success."""
        try:
            from .knowledge_consolidator import get_knowledge_consolidator

            consolidator = get_knowledge_consolidator()
            stats = await consolidator.consolidate_knowledge()
            logger.info("Knowledge consolidation: %s", stats)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Knowledge consolidation failed: %s", exc)
            return False


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_loop: Optional[SelfLearningLoop] = None


def get_self_learning_loop() -> SelfLearningLoop:
    """Return the module-level singleton SelfLearningLoop instance."""
    global _default_loop
    if _default_loop is None:
        _default_loop = SelfLearningLoop()
    return _default_loop
