"""Model manager – loads and manages the active AI brain."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .brain_interface import BrainInterface
from .local_llm import LocalLLM

logger = logging.getLogger(__name__)

_DEFAULT_REGISTRY_PATH = "models/model_registry.yaml"


class ModelManager:
    """Manages the lifecycle of the AI brain module.

    Responsible for initialising, health-checking, swapping, and
    hot-reloading the underlying brain implementation.

    Extended capabilities (self-learning architecture):
    - Hot-swap models without restarting the system.
    - Track model versions in a YAML registry.
    - Roll back to the previous model on failure.
    - Expose performance metrics for the learning loop.
    """

    def __init__(
        self,
        brain: Optional[BrainInterface] = None,
        registry_path: str = _DEFAULT_REGISTRY_PATH,
    ) -> None:
        """Initialise with an optional pre-built brain instance.

        Args:
            brain: An existing BrainInterface implementation.  If None,
                   a LocalLLM is created with default settings.
            registry_path: Path to the YAML model registry file.
        """
        self._brain: BrainInterface = brain or LocalLLM()
        self._previous_brain: Optional[BrainInterface] = None
        self._registry_path = Path(registry_path)
        self._pending_model: Optional[str] = None

    # ------------------------------------------------------------------
    # Existing public API (unchanged)
    # ------------------------------------------------------------------

    @property
    def brain(self) -> BrainInterface:
        """The active brain instance."""
        return self._brain

    def swap_brain(self, new_brain: BrainInterface) -> None:
        """Replace the active brain with a new implementation.

        Args:
            new_brain: The new BrainInterface implementation.
        """
        logger.info(
            "Swapping brain from %s to %s",
            type(self._brain).__name__,
            type(new_brain).__name__,
        )
        self._previous_brain = self._brain
        self._brain = new_brain

    async def ensure_available(self) -> bool:
        """Check availability and log a warning if unavailable.

        Returns:
            True if the brain is ready.
        """
        available = await self._brain.is_available()
        if not available:
            logger.warning("Brain %s is not available.", type(self._brain).__name__)
        return available

    # ------------------------------------------------------------------
    # New: hot-swap & version management
    # ------------------------------------------------------------------

    async def check_for_new_training(self) -> Optional[str]:
        """Return the path of a newly trained adapter if one is available.

        Scans the ``models/lora_adapters/`` directory for adapters created
        after the currently registered model.

        Returns:
            Path string of the newest adapter, or None if nothing new.
        """
        adapters_dir = Path("models/lora_adapters")
        if not adapters_dir.exists():
            return None

        current_ts = self._get_current_model_timestamp()
        newest_path: Optional[Path] = None
        newest_mtime = 0.0

        for adapter in adapters_dir.iterdir():
            if not adapter.is_dir():
                continue
            mtime = adapter.stat().st_mtime
            if mtime > current_ts and mtime > newest_mtime:
                newest_mtime = mtime
                newest_path = adapter

        return str(newest_path) if newest_path else None

    async def load_new_model(self, model_path: str) -> bool:
        """Stage a new model for potential hot-swapping.

        Validates that the model path exists and stores it as pending.

        Args:
            model_path: Path to the adapter directory or Ollama model name.

        Returns:
            True if the model path is valid and has been staged.
        """
        path = Path(model_path)
        if path.exists():
            self._pending_model = model_path
            logger.info("Staged new model from %s", model_path)
            return True

        # Treat as Ollama model name (not a local path)
        self._pending_model = model_path
        logger.info("Staged Ollama model '%s'", model_path)
        return True

    async def swap_model_runtime(self, new_model_name: str) -> bool:
        """Hot-swap the active brain to a new model without restarting.

        1. Create a new LocalLLM pointed at *new_model_name*.
        2. Run a quick validation ping.
        3. If valid, swap; otherwise keep current model.

        Args:
            new_model_name: Ollama model name or local adapter path.

        Returns:
            True if the swap succeeded.
        """
        logger.info("Hot-swapping model to '%s'", new_model_name)
        new_brain = LocalLLM(model=new_model_name)

        try:
            available = await new_brain.is_available()
        except Exception as exc:  # noqa: BLE001
            logger.warning("New model validation failed: %s", exc)
            available = False

        if available:
            self.swap_brain(new_brain)
            await self._register_model(new_model_name, model_type="fine-tuned")
            logger.info("Hot-swap successful: now using '%s'", new_model_name)
            self._pending_model = None
            return True

        logger.warning(
            "Hot-swap aborted – model '%s' is not available", new_model_name
        )
        return False

    async def rollback_model(self) -> bool:
        """Revert to the previous brain implementation.

        Returns:
            True if a previous model existed and rollback succeeded.
        """
        if self._previous_brain is None:
            logger.warning("No previous model to roll back to")
            return False

        logger.info(
            "Rolling back from %s to %s",
            type(self._brain).__name__,
            type(self._previous_brain).__name__,
        )
        self._brain = self._previous_brain
        self._previous_brain = None
        return True

    async def get_model_performance_metrics(self) -> Dict[str, Any]:
        """Return performance metrics for the current model.

        Currently returns availability status and basic model info.  The
        learning loop uses the ``"score"`` key to compare models.

        Returns:
            Dict with at minimum a ``"score"`` float in [0, 1].
        """
        try:
            info = await self._brain.get_model_info()
            available = await self._brain.is_available()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not fetch model metrics: %s", exc)
            return {"score": 0.0, "available": False}

        return {
            "score": 0.7 if available else 0.0,
            "available": available,
            "model_info": info,
        }

    async def auto_update_check(self) -> bool:
        """Check for a newly trained model and swap if one is found.

        Returns:
            True if a new model was deployed.
        """
        new_path = await self.check_for_new_training()
        if new_path:
            staged = await self.load_new_model(new_path)
            if staged:
                return await self.swap_model_runtime(new_path)
        return False

    # ------------------------------------------------------------------
    # Registry helpers
    # ------------------------------------------------------------------

    def _load_registry(self) -> Dict[str, Any]:
        """Load the model registry YAML, creating it if absent."""
        if self._registry_path.exists():
            try:
                with self._registry_path.open() as fh:
                    data = yaml.safe_load(fh) or {}
                return data
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to read model registry: %s", exc)
        return {"models": []}

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        """Persist the model registry YAML."""
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._registry_path.open("w") as fh:
                yaml.safe_dump(registry, fh, default_flow_style=False)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to save model registry: %s", exc)

    async def _register_model(
        self,
        name: str,
        model_type: str = "base",
        adapter_path: str = "",
    ) -> None:
        """Add or update a model entry in the registry."""
        registry = self._load_registry()
        models: List[Dict[str, Any]] = registry.setdefault("models", [])

        # Determine next version
        versions = [m.get("version", "0.0.0") for m in models]
        next_version = self._bump_version(versions)

        entry: Dict[str, Any] = {
            "version": next_version,
            "name": name,
            "type": model_type,
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        if adapter_path:
            entry["adapter_path"] = adapter_path

        models.append(entry)
        self._save_registry(registry)
        logger.info("Registered model '%s' as version %s", name, next_version)

    def _get_current_model_timestamp(self) -> float:
        """Return the mtime of the latest registered model (0 if none)."""
        registry = self._load_registry()
        models: List[Dict[str, Any]] = registry.get("models", [])
        if not models:
            return 0.0
        last = models[-1]
        created = last.get("created", "")
        if created:
            try:
                dt = datetime.strptime(created, "%Y-%m-%d")
                return dt.timestamp()
            except ValueError:
                pass
        return 0.0

    @staticmethod
    def _bump_version(versions: List[str]) -> str:
        """Increment the patch number of the highest existing version."""
        if not versions:
            return "1.0.0"
        parsed = []
        for v in versions:
            try:
                parts = [int(x) for x in v.split(".")]
                while len(parts) < 3:
                    parts.append(0)
                parsed.append(parts[:3])
            except ValueError:
                pass
        if not parsed:
            return "1.0.0"
        major, minor, patch = max(parsed)
        return f"{major}.{minor}.{patch + 1}"


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_default_manager: Optional[ModelManager] = None


def get_model_manager() -> ModelManager:
    """Return the module-level singleton ModelManager instance."""
    global _default_manager
    if _default_manager is None:
        _default_manager = ModelManager()
    return _default_manager
