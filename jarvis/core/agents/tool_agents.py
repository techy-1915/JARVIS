"""Tool agents – bridge between the agent layer and the tool/plugin layer."""

import logging
from typing import Any, Dict

from .agent_base import AgentBase

logger = logging.getLogger(__name__)


class BrowserToolAgent(AgentBase):
    """Delegates browser-related tasks to the browser tool."""

    def __init__(self) -> None:
        super().__init__(name="BrowserTool", description="Browser automation agent")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        action: str = task.get("action", "")
        url: str = task.get("url", "")
        if not action:
            return self._error("No browser action specified")
        return self._success({"action": action, "url": url, "status": "queued"})


class FileToolAgent(AgentBase):
    """Delegates file-system tasks to the file manager tool."""

    def __init__(self) -> None:
        super().__init__(name="FileTool", description="File system agent")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        operation: str = task.get("operation", "")
        path: str = task.get("path", "")
        if not operation:
            return self._error("No file operation specified")
        return self._success({"operation": operation, "path": path, "status": "queued"})


class SearchToolAgent(AgentBase):
    """Delegates web search tasks to the web search tool."""

    def __init__(self) -> None:
        super().__init__(name="SearchTool", description="Web search agent")

    async def run(self, task: Dict[str, Any]) -> Dict[str, Any]:
        query: str = task.get("query", "")
        if not query:
            return self._error("No search query provided")
        return self._success({"query": query, "status": "queued"})
