"""Commander agent – top-level request interpreter and coordinator."""

import logging
from typing import Any, Dict, List, Optional

from ..brain.brain_interface import BrainInterface
from .agent_base import AgentBase
from .message_bus import Message, MessageBus, MessageType

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are JARVIS, an advanced AI assistant.
Analyse the user's request and decide whether to handle it directly
or delegate it to specialist agents. Always respond in JSON with keys:
- "action": one of "respond", "delegate", "plan"
- "response": the text reply (if action is "respond")
- "delegate_to": agent name (if action is "delegate")
- "plan": list of steps (if action is "plan")
"""


class CommanderAgent(AgentBase):
    """Interprets incoming requests, maintains context, and coordinates agents."""

    def __init__(
        self,
        brain: BrainInterface,
        message_bus: MessageBus,
    ) -> None:
        super().__init__(name="Commander", description="Top-level request coordinator")
        self._brain = brain
        self._bus = message_bus
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

        self._context.append({"role": "system", "content": SYSTEM_PROMPT})
        try:
            response = await self._brain.think(user_input, self._context)
            self._context.append({"role": "assistant", "content": response})

            await self._bus.publish(
                Message(
                    message_type=MessageType.EVENT,
                    sender=self.name,
                    payload={"input": user_input, "response": response},
                )
            )
            return self._success({"response": response})
        except Exception as exc:  # noqa: BLE001
            return self._error("Commander failed to process request", exc)
