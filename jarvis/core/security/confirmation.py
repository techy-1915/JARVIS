"""User confirmation system for dangerous operations."""

import asyncio
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Operations that require explicit user confirmation
DANGEROUS_OPERATIONS = {
    "file.delete",
    "system.exec",
    "browser.download",
    "memory.clear",
}


class ConfirmationManager:
    """Manages user confirmation flows for sensitive actions.

    In non-interactive (API) mode, pending confirmations are queued
    and resolved via the API.
    """

    def __init__(self) -> None:
        self._pending: Dict[str, asyncio.Future] = {}

    def is_dangerous(self, operation: str) -> bool:
        """Check if an operation requires confirmation."""
        return operation in DANGEROUS_OPERATIONS

    async def request(self, operation: str, details: str, timeout: float = 30.0) -> bool:
        """Request user confirmation for a dangerous operation.

        In interactive mode this could prompt the user directly.
        In API mode, a pending confirmation is registered.

        Args:
            operation: The operation name.
            details: Human-readable description of what will happen.
            timeout: Seconds to wait for confirmation before denying.

        Returns:
            True if the user confirmed, False otherwise.
        """
        logger.warning("Confirmation required for %s: %s", operation, details)
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending[operation] = future
        try:
            result = await asyncio.wait_for(future, timeout=timeout)
            return bool(result)
        except asyncio.TimeoutError:
            logger.info("Confirmation timed out for %s – denying", operation)
            return False
        finally:
            self._pending.pop(operation, None)

    def resolve(self, operation: str, approved: bool) -> None:
        """Resolve a pending confirmation (called from API/UI).

        Args:
            operation: The operation to resolve.
            approved: Whether the user approved the action.
        """
        future = self._pending.get(operation)
        if future and not future.done():
            future.set_result(approved)
