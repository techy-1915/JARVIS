"""Planner agent – decomposes complex requests into structured execution plans."""

import json
import logging
from typing import Any, Dict, List

from ..brain.brain_interface import BrainInterface
from .agent_base import AgentBase

logger = logging.getLogger(__name__)

PLANNER_PROMPT = """You are a task planner.  Given the user's goal, break it
into a numbered list of concrete, actionable steps.  Respond ONLY with valid
JSON in the format:
{
  "goal": "<original goal>",
  "steps": [
    {"step": 1, "description": "...", "agent": "<suggested agent>"},
    ...
  ]
}"""


class PlannerAgent(AgentBase):
    """Breaks complex requests into structured execution plans."""

    def __init__(self, brain: BrainInterface) -> None:
        super().__init__(name="Planner", description="Decomposes goals into step-by-step plans")
        self._brain = brain

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a plan for the given goal.

        Args:
            task: Must contain ``"goal"`` key.

        Returns:
            Standardised result with ``"plan"`` key.
        """
        goal: str = task.get("goal", "")
        if not goal:
            return self._error("No goal provided")

        try:
            raw = await self._brain.think(goal, [{"role": "system", "content": PLANNER_PROMPT}])
            plan: Dict[str, Any] = json.loads(raw)
            return self._success(plan)
        except json.JSONDecodeError:
            # Return raw text wrapped in a simple plan structure
            return self._success({"goal": goal, "steps": [{"step": 1, "description": raw}]})
        except Exception as exc:  # noqa: BLE001
            return self._error("Planning failed", exc)
