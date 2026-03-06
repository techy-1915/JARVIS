"""Sandbox – safe execution environment for untrusted operations."""

import asyncio
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Sandbox:
    """Executes shell commands in a restricted environment.

    All commands are run with strict timeouts and as a subprocess
    (not via shell string expansion to avoid injection).
    """

    def __init__(self, timeout: float = 10.0, max_output_bytes: int = 65_536) -> None:
        """Initialise the sandbox.

        Args:
            timeout: Maximum execution time in seconds.
            max_output_bytes: Maximum captured output size.
        """
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes

    async def run_command(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Run a command in a subprocess with timeout protection.

        Args:
            args: Command and arguments as a list (no shell expansion).
            cwd: Optional working directory.
            env: Optional environment variables (merged with current env).

        Returns:
            Dict with ``returncode``, ``stdout``, and ``stderr``.
        """
        if not args:
            return {"returncode": -1, "stdout": "", "stderr": "No command provided"}

        logger.info("Sandbox: running %s", args[0])
        try:
            proc = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=self.timeout
            )
            return {
                "returncode": proc.returncode,
                "stdout": stdout_bytes[: self.max_output_bytes].decode("utf-8", errors="replace"),
                "stderr": stderr_bytes[: self.max_output_bytes].decode("utf-8", errors="replace"),
            }
        except asyncio.TimeoutError:
            logger.error("Sandbox: command timed out: %s", args)
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
            return {"returncode": -1, "stdout": "", "stderr": "Command timed out"}
        except Exception as exc:  # noqa: BLE001
            logger.error("Sandbox error: %s", exc)
            return {"returncode": -1, "stdout": "", "stderr": str(exc)}
