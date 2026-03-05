"""Async message bus for inter-agent communication."""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """Enumeration of supported message types."""

    COMMAND = "COMMAND"
    QUERY = "QUERY"
    RESPONSE = "RESPONSE"
    EVENT = "EVENT"


class Message:
    """A single message on the bus."""

    def __init__(
        self,
        message_type: MessageType,
        sender: str,
        payload: Dict[str, Any],
        recipient: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        self.id: str = str(uuid.uuid4())
        self.message_type: MessageType = message_type
        self.sender: str = sender
        self.recipient: Optional[str] = recipient
        self.payload: Dict[str, Any] = payload
        self.correlation_id: Optional[str] = correlation_id
        self.timestamp: datetime = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the message to a dictionary."""
        return {
            "id": self.id,
            "type": self.message_type.value,
            "sender": self.sender,
            "recipient": self.recipient,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }


class MessageBus:
    """Simple async pub/sub message bus.

    Agents subscribe to message types; published messages are
    delivered to all matching subscribers in parallel.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[MessageType, List[Callable]] = {
            t: [] for t in MessageType
        }
        self._history: List[Message] = []
        self._max_history: int = 1000

    def subscribe(self, message_type: MessageType, handler: Callable) -> None:
        """Register a handler for a given message type.

        Args:
            message_type: The type of message to listen for.
            handler: An async callable that accepts a ``Message``.
        """
        self._subscribers[message_type].append(handler)
        logger.debug("Subscribed %s to %s", handler, message_type)

    def unsubscribe(self, message_type: MessageType, handler: Callable) -> None:
        """Remove a previously registered handler."""
        try:
            self._subscribers[message_type].remove(handler)
        except ValueError:
            pass

    async def publish(self, message: Message) -> None:
        """Deliver a message to all registered subscribers.

        Args:
            message: The message to deliver.
        """
        self._history.append(message)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        handlers = self._subscribers.get(message.message_type, [])
        if handlers:
            await asyncio.gather(*[h(message) for h in handlers], return_exceptions=True)

        logger.debug("Published %s from %s", message.message_type, message.sender)

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return recent message history.

        Args:
            limit: Maximum number of messages to return.

        Returns:
            List of serialised message dictionaries.
        """
        return [m.to_dict() for m in self._history[-limit:]]
