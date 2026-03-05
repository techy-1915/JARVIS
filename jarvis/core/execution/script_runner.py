"""Script runner – executes scripts safely inside the sandbox."""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..security.sandbox import Sandbox
from ..security.validator import CommandValidator
from .action_logger import ActionLogger

logger = logging.getLogger(__name__)


class ScriptRunner:
    """Runs scripts (Python, shell) through the security sandbox."""

    def __init__(
        self,
        sandbox: Optional[Sandbox] = None,
        action_logger: Optional[ActionLogger] = None,
    ) -> None:
        self._sandbox = sandbox or Sandbox(timeout=30.0)
        self._validator = CommandValidator()
        self._log = action_logger or ActionLogger()

    async def run_python(
        self,
        script_path: str,
        args: Optional[List[str]] = None,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a Python script inside the sandbox.

        Args:
            script_path: Path to the ``.py`` script file.
            args: Optional list of arguments to pass.
            cwd: Working directory for the script.

        Returns:
            Dict with ``returncode``, ``stdout``, and ``stderr``.
        """
        try:
            self._validator.validate_path(script_path)
        except ValueError as exc:
            return {"returncode": -1, "stdout": "", "stderr": str(exc)}

        if not Path(script_path).is_file():
            return {"returncode": -1, "stdout": "", "stderr": f"Script not found: {script_path}"}

        cmd = [sys.executable, script_path] + (args or [])
        result = await self._sandbox.run_command(cmd, cwd=cwd)
        self._log.log(
            "script.run",
            {"script": script_path, "returncode": result.get("returncode")},
            status="success" if result.get("returncode") == 0 else "error",
        )
        return result

    async def run_shell_command(
        self,
        command: str,
        cwd: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run a validated shell command inside the sandbox.

        Args:
            command: The shell command string.
            cwd: Working directory.

        Returns:
            Dict with ``returncode``, ``stdout``, and ``stderr``.
        """
        try:
            safe_cmd = self._validator.validate(command)
        except ValueError as exc:
            return {"returncode": -1, "stdout": "", "stderr": str(exc)}

        # Run via sh -c to support pipelines while still using exec
        result = await self._sandbox.run_command(["sh", "-c", safe_cmd], cwd=cwd)
        self._log.log(
            "shell.run",
            {"command": safe_cmd[:200], "returncode": result.get("returncode")},
            status="success" if result.get("returncode") == 0 else "error",
        )
        return result
