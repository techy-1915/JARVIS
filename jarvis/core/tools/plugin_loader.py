"""Dynamic plugin loader for JARVIS tools."""

import importlib
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type

from .tool_base import ToolBase

logger = logging.getLogger(__name__)


class PluginLoader:
    """Dynamically discovers and loads ToolBase plugins at runtime.

    Tools can be registered directly (built-in) or loaded from Python
    files in a designated plugin directory.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, ToolBase] = {}

    def register(self, tool: ToolBase) -> None:
        """Register a tool instance directly.

        Args:
            tool: An instantiated ToolBase subclass.
        """
        self._registry[tool.name] = tool
        logger.info("Registered tool: %s", tool.name)

    def load_from_directory(self, plugin_dir: Path) -> List[str]:
        """Scan a directory and load any ToolBase subclass found.

        Args:
            plugin_dir: Directory to scan for plugin ``.py`` files.

        Returns:
            List of successfully loaded tool names.
        """
        loaded: List[str] = []
        if not plugin_dir.is_dir():
            logger.warning("Plugin directory not found: %s", plugin_dir)
            return loaded

        for py_file in plugin_dir.glob("*.py"):
            if py_file.stem.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[py_file.stem] = module
                    spec.loader.exec_module(module)  # type: ignore[union-attr]
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, ToolBase)
                            and attr is not ToolBase
                        ):
                            instance: ToolBase = attr()
                            self.register(instance)
                            loaded.append(instance.name)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to load plugin %s: %s", py_file, exc)

        return loaded

    def get_tool(self, name: str) -> Optional[ToolBase]:
        """Retrieve a registered tool by name."""
        return self._registry.get(name)

    def list_tools(self) -> List[Dict[str, str]]:
        """Return a summary of all registered tools."""
        return [{"name": t.name, "description": t.description} for t in self._registry.values()]
