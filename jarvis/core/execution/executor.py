"""Main execution coordinator for JARVIS."""

import logging
from typing import Any, Dict

from ..security.confirmation import ConfirmationManager
from ..security.permissions import PermissionManager
from ..security.validator import CommandValidator
from .action_logger import ActionLogger
from .app_launcher import AppLauncher
from .browser_controller import BrowserController
from .file_operations import FileOperations
from .script_runner import ScriptRunner

logger = logging.getLogger(__name__)


class Executor:
    """Routes execution tasks to appropriate sub-executors.

    Acts as the single entry point for all action execution,
    applying security checks before dispatching to specialised modules.
    """

    def __init__(self) -> None:
        self._perms = PermissionManager()
        self._log = ActionLogger()
        self._confirm = ConfirmationManager()
        self._validator = CommandValidator()
        self.files = FileOperations(self._perms, self._log)
        self.apps = AppLauncher(self._perms, self._log)
        self.scripts = ScriptRunner(action_logger=self._log)
        self.browser = BrowserController(self._perms, self._log)

    async def execute(self, action_type: str, **kwargs: Any) -> Dict[str, Any]:
        """Dispatch an action to the correct sub-executor.

        Args:
            action_type: Category of action to perform.
            **kwargs: Action-specific parameters.

        Returns:
            Result dict with ``status`` key.
        """
        logger.info("Executor: dispatching %s", action_type)
        handlers = {
            "file.read": lambda: self.files.read_file(kwargs["path"]),
            "file.write": lambda: self.files.write_file(kwargs["path"], kwargs.get("content", "")),
            "file.delete": lambda: self.files.delete_file(kwargs["path"]),
            "app.launch": lambda: self.apps.launch(kwargs["app"], kwargs.get("args")),
            "script.python": lambda: self.scripts.run_python(kwargs["script"]),
            "shell.run": lambda: self.scripts.run_shell_command(kwargs["command"]),
            "browser.navigate": lambda: self.browser.navigate(kwargs["url"]),
        }
        handler = handlers.get(action_type)
        if handler is None:
            return {"status": "error", "error": f"Unknown action type: {action_type}"}
        return await handler()
