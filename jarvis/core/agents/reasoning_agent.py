"""Reasoning agent – applies chain-of-thought logic to complex problems."""

import logging
from typing import Any, Dict

from ..brain.brain_interface import BrainInterface
from .agent_base import AgentBase

logger = logging.getLogger(__name__)

REASONING_PROMPT = """You are a logical reasoning engine.
Think step-by-step through the problem.  Show your reasoning clearly,
then provide a concise conclusion.  Format your answer as:
REASONING: <step-by-step thinking>
CONCLUSION: <final answer>"""


class ReasoningAgent(AgentBase):
    """Performs chain-of-thought reasoning on complex problems."""

    def __init__(self, brain: BrainInterface) -> None:
        super().__init__(name="Reasoning", description="Chain-of-thought logical reasoning")
        self._brain = brain

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Reason through a problem.

        Args:
            task: Must contain ``"problem"`` key.

        Returns:
            Standardised result with ``"reasoning"`` and ``"conclusion"`` keys.
        """
        problem: str = task.get("problem", "")
        if not problem:
            return self._error("No problem provided")

        # Retrieve relevant memories to augment the prompt
        memory_context = ""
        try:
            from ..memory.vector_memory import get_vector_memory

            vm = get_vector_memory()
            memories = await vm.retrieve_similar(problem, top_k=3)
            if memories:
                memory_context = "\n".join(m["text"] for m in memories)
                logger.debug(
                    "Retrieved %d memory snippets for reasoning", len(memories)
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Vector memory retrieval skipped: %s", exc)

        # Build enhanced prompt
        if memory_context:
            enhanced_problem = (
                f"Context from memory:\n{memory_context}\n\nProblem: {problem}"
            )
        else:
            enhanced_problem = problem

        try:
            raw = await self._brain.think(
                enhanced_problem,
                [{"role": "system", "content": REASONING_PROMPT}],
            )
            reasoning, conclusion = "", raw
            if "CONCLUSION:" in raw:
                parts = raw.split("CONCLUSION:", 1)
                reasoning = parts[0].replace("REASONING:", "").strip()
                conclusion = parts[1].strip()
            return self._success({"reasoning": reasoning, "conclusion": conclusion})
        except Exception as exc:  # noqa: BLE001
            return self._error("Reasoning failed", exc)
