"""Commander agent – top-level request interpreter and coordinator."""

import logging
from typing import Any, Dict, List, Optional

from ...ai.brain import AIBrain
from .agent_base import AgentBase
from .message_bus import Message, MessageBus, MessageType

logger = logging.getLogger(__name__)


class CommanderAgent(AgentBase):
    """Interprets incoming requests using multi-model AI brain."""

    def __init__(
        self,
        message_bus: MessageBus,
        ai_brain: Optional[AIBrain] = None,
    ) -> None:
        super().__init__(name="Commander", description="Top-level request coordinator")
        self._bus = message_bus
        self._brain = ai_brain or AIBrain()
        self._context: List[Dict[str, Any]] = []

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process an incoming user request.

        Args:
            task: Must contain ``"input"`` (the user's message).

        Returns:
            Standardised result dict.
        """
        user_input: str = task.get("input", "")
        if not user_input:
            return self._error("No input provided")
        try:
            # Generate response using AI brain (auto-routes to correct model)
            response = await self._brain.generate(
                prompt=user_input,
                context=self._context,
                stream=False,
            )

            # Update context
            self._context.append({"role": "user", "content": user_input})
            self._context.append({"role": "assistant", "content": response})

            # Keep context manageable (last 20 messages)
            if len(self._context) > 20:
                self._context = self._context[-20:]

            # Extract code blocks
            code_blocks = self._brain.extract_code_blocks(response)

            await self._bus.publish(
                Message(
                    message_type=MessageType.EVENT,
                    sender=self.name,
                    payload={"input": user_input, "response": response},
                )
            )
            return self._success({
                "response": response,
                "code_blocks": code_blocks,
                "type": "chat",
            })
        except Exception as exc:  # noqa: BLE001
            logger.error("Commander error processing input %r: %s", user_input[:50], exc)
            return self._error("Commander failed to process request", exc)