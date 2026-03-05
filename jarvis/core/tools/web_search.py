"""Web search tool – searches the web using DuckDuckGo or similar."""

import logging
from typing import Any, Dict

import httpx

from .tool_base import ToolBase

logger = logging.getLogger(__name__)


class WebSearchTool(ToolBase):
    """Performs web searches and returns structured results.

    Uses the DuckDuckGo Instant Answer API by default (no key required).
    """

    def __init__(self, timeout: float = 10.0) -> None:
        super().__init__(name="web_search", description="Web search capability")
        self._timeout = timeout

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "name": "web_search",
            "parameters": {
                "query": {"type": "string"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Search the web for the given query.

        Args:
            query: The search query string.
            max_results: Maximum number of results to return.

        Returns:
            Standardised result dict with a list of results.
        """
        query: str = kwargs.get("query", "")
        if not query:
            return self._error("No query provided")

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_redirect": 1},
                )
                resp.raise_for_status()
                data = resp.json()
                results = [
                    {"title": r.get("Text", ""), "url": r.get("FirstURL", "")}
                    for r in data.get("RelatedTopics", [])
                    if r.get("FirstURL")
                ]
                return self._success({"query": query, "results": results})
        except httpx.RequestError as exc:
            return self._error(f"Search request failed: {exc}")
