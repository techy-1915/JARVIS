"""Command validator – sanitises and validates all incoming commands."""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Patterns that are always blocked
BLOCKED_PATTERNS: List[str] = [
    r"rm\s+-rf\s+/",          # recursive root delete
    r"dd\s+if=",              # disk dump
    r"mkfs",                  # format filesystem
    r"shutdown|reboot|halt",  # system power
    r"chmod\s+777",           # world-writable
    r"sudo\s+rm",             # privileged delete
    r">\s*/dev/(sda|hda)",    # overwrite disk
]

_COMPILED: List[re.Pattern] = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

MAX_INPUT_LENGTH = 10_000


class CommandValidator:
    """Validates commands and inputs before execution.

    Raises ``ValueError`` for dangerous or malformed commands.
    """

    def validate(self, command: str) -> str:
        """Validate and sanitise a command string.

        Args:
            command: The raw command or user input.

        Returns:
            The sanitised command string.

        Raises:
            ValueError: If the command is blocked or invalid.
        """
        if not command or not command.strip():
            raise ValueError("Empty command")

        if len(command) > MAX_INPUT_LENGTH:
            raise ValueError(f"Command too long ({len(command)} chars; max {MAX_INPUT_LENGTH})")

        for pattern in _COMPILED:
            if pattern.search(command):
                logger.warning("Blocked dangerous command pattern: %s", pattern.pattern)
                raise ValueError(f"Command blocked by security policy: {pattern.pattern}")

        return command.strip()

    def validate_path(self, path: str) -> str:
        """Validate a filesystem path for safety.

        Args:
            path: The path string to validate.

        Returns:
            The validated path string.

        Raises:
            ValueError: If the path contains traversal sequences.
        """
        if ".." in path or path.startswith("/etc") or path.startswith("/sys"):
            raise ValueError(f"Path not allowed: {path}")
        return path
