"""Wake word detector – listens for the activation phrase."""

import logging
import threading
from typing import Callable, Optional

logger = logging.getLogger(__name__)

DEFAULT_WAKE_PHRASE = "hey jarvis"


class WakeWordDetector:
    """Detects the wake phrase in a continuous audio stream.

    Uses a simple string-match stub.  Replace with a proper keyword
    spotting library (e.g., pvporcupine) for production use.
    """

    def __init__(
        self,
        wake_phrase: str = DEFAULT_WAKE_PHRASE,
        callback: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialise the detector.

        Args:
            wake_phrase: The phrase to listen for (case-insensitive).
            callback: Function called when the wake phrase is detected.
        """
        self._wake_phrase = wake_phrase.lower()
        self._callback = callback
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def check_text(self, text: str) -> bool:
        """Check if the wake phrase is present in a text string.

        Args:
            text: Text to search within.

        Returns:
            True if the wake phrase was detected.
        """
        detected = self._wake_phrase in text.lower()
        if detected and self._callback:
            self._callback()
        return detected

    def start_listening(self) -> None:
        """Start the background wake word listener (stub)."""
        if self._running:
            return
        self._running = True
        logger.info("Wake word detector started (phrase: '%s')", self._wake_phrase)

    def stop_listening(self) -> None:
        """Stop the background listener."""
        self._running = False
        logger.info("Wake word detector stopped")

    @property
    def is_active(self) -> bool:
        """True if the detector is currently running."""
        return self._running
