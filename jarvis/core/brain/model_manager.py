"""Model manager – loads and manages the active AI brain."""

import logging
from typing import Optional

from .brain_interface import BrainInterface
from .local_llm import LocalLLM

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages the lifecycle of the AI brain module.

    Responsible for initialising, health-checking, and swapping
    the underlying brain implementation.
    """

    def __init__(self, brain: Optional[BrainInterface] = None) -> None:
        """Initialise with an optional pre-built brain instance.

        Args:
            brain: An existing BrainInterface implementation.  If None,
                   a LocalLLM is created with default settings.
        """
        self._brain: BrainInterface = brain or LocalLLM()

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
