"""Structured logging for the AI router."""

import logging
import os
from datetime import date
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_router_logger(name: str = "ai_router") -> logging.Logger:
    """Return a logger configured for AI router output.

    Logs go to both the console (via the root handler) and a dated file under
    ``logs/ai_router_YYYY-MM-DD.log``.

    Args:
        name: Logger name (default ``"ai_router"``).

    Returns:
        Configured :class:`logging.Logger` instance.
    """
    router_logger = logging.getLogger(name)

    if router_logger.handlers:
        # Already configured – return as-is
        return router_logger

    router_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] [AI ROUTER] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ------------------------------------------------------------------
    # File handler – rotate at 10 MB, keep last 7 files
    # ------------------------------------------------------------------
    log_dir = Path(os.environ.get("JARVIS_LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"ai_router_{date.today()}.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    router_logger.addHandler(file_handler)

    # ------------------------------------------------------------------
    # Console handler
    # ------------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    router_logger.addHandler(console_handler)

    # Prevent double-logging via the root logger
    router_logger.propagate = False

    return router_logger
