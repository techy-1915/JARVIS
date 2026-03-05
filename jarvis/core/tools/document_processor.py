"""Document processor tool – handles various document formats."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .tool_base import ToolBase

logger = logging.getLogger(__name__)


class DocumentProcessorTool(ToolBase):
    """Processes text documents and extracts content."""

    def __init__(self) -> None:
        super().__init__(name="document_processor", description="Document reading and processing")

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "name": "document_processor",
            "parameters": {
                "action": {"type": "string", "enum": ["read", "summarize", "extract_text"]},
                "path": {"type": "string"},
            },
            "required": ["action", "path"],
        }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Process a document file.

        Args:
            action: Processing action to perform.
            path: Path to the document file.

        Returns:
            Standardised result dict with extracted text.
        """
        action: str = kwargs.get("action", "")
        path: str = kwargs.get("path", "")

        if not action or not path:
            return self._error("action and path are required")

        file_path = Path(path)
        if not file_path.exists():
            return self._error(f"File not found: {path}")

        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
            return self._success({"path": path, "content": text, "length": len(text)})
        except OSError as exc:
            return self._error(f"Failed to read document: {exc}")
