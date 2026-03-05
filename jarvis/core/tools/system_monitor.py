"""System monitor tool – exposes OS-level metrics."""

import logging
import os
import platform
from typing import Any, Dict

from .tool_base import ToolBase

logger = logging.getLogger(__name__)


class SystemMonitorTool(ToolBase):
    """Reports system resource usage and platform information."""

    def __init__(self) -> None:
        super().__init__(name="system_monitor", description="System resource monitoring")

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "name": "system_monitor",
            "parameters": {
                "metric": {
                    "type": "string",
                    "enum": ["all", "cpu", "memory", "disk", "platform"],
                }
            },
            "required": ["metric"],
        }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Return the requested system metric.

        Uses ``psutil`` if available, otherwise falls back to stdlib ``os``.
        """
        metric: str = kwargs.get("metric", "all")
        info: Dict[str, Any] = {}

        try:
            import psutil  # type: ignore[import]
            if metric in ("all", "cpu"):
                info["cpu_percent"] = psutil.cpu_percent(interval=0.1)
            if metric in ("all", "memory"):
                mem = psutil.virtual_memory()
                info["memory"] = {
                    "total_mb": mem.total // (1024 ** 2),
                    "available_mb": mem.available // (1024 ** 2),
                    "percent": mem.percent,
                }
            if metric in ("all", "disk"):
                disk = psutil.disk_usage("/")
                info["disk"] = {
                    "total_gb": disk.total // (1024 ** 3),
                    "free_gb": disk.free // (1024 ** 3),
                    "percent": disk.percent,
                }
        except ImportError:
            info["note"] = "psutil not installed; limited metrics available"

        if metric in ("all", "platform"):
            info["platform"] = {
                "system": platform.system(),
                "release": platform.release(),
                "python": platform.python_version(),
            }

        return self._success(info)
