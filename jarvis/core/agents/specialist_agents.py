"""Specialist agents: research, coding, data processing, content generation."""

import logging
from typing import Any, Dict

from ..brain.brain_interface import BrainInterface
from .agent_base import AgentBase

logger = logging.getLogger(__name__)


class ResearchAgent(AgentBase):
    """Conducts research and synthesises information."""

    def __init__(self, brain: BrainInterface) -> None:
        super().__init__(name="Research", description="Research and information synthesis")
        self._brain = brain

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query: str = task.get("query", "")
        if not query:
            return self._error("No query provided")
        try:
            result = await self._brain.think(
                f"Research the following topic thoroughly: {query}"
            )
            return self._success({"research": result})
        except Exception as exc:  # noqa: BLE001
            return self._error("Research failed", exc)


class CodingAgent(AgentBase):
    """Generates, explains, and debugs code."""

    def __init__(self, brain: BrainInterface) -> None:
        super().__init__(name="Coding", description="Code generation and analysis")
        self._brain = brain

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        request: str = task.get("request", "")
        language: str = task.get("language", "Python")
        if not request:
            return self._error("No coding request provided")
        try:
            prompt = f"Write {language} code to: {request}\nInclude docstrings and comments."
            result = await self._brain.think(prompt)
            return self._success({"code": result, "language": language})
        except Exception as exc:  # noqa: BLE001
            return self._error("Coding task failed", exc)


class DataProcessingAgent(AgentBase):
    """Processes and analyses data."""

    def __init__(self, brain: BrainInterface) -> None:
        super().__init__(name="DataProcessing", description="Data analysis and transformation")
        self._brain = brain

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        data: str = task.get("data", "")
        instruction: str = task.get("instruction", "Summarise this data")
        if not data:
            return self._error("No data provided")
        try:
            prompt = f"Instruction: {instruction}\n\nData:\n{data}"
            result = await self._brain.think(prompt)
            return self._success({"result": result})
        except Exception as exc:  # noqa: BLE001
            return self._error("Data processing failed", exc)


class ContentGenerationAgent(AgentBase):
    """Generates creative and structured content."""

    def __init__(self, brain: BrainInterface) -> None:
        super().__init__(name="ContentGeneration", description="Creative content generation")
        self._brain = brain

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        prompt: str = task.get("prompt", "")
        content_type: str = task.get("content_type", "text")
        if not prompt:
            return self._error("No prompt provided")
        try:
            instruction = f"Generate {content_type} content: {prompt}"
            result = await self._brain.think(instruction)
            return self._success({"content": result, "type": content_type})
        except Exception as exc:  # noqa: BLE001
            return self._error("Content generation failed", exc)
