"""API authentication – JWT token management."""

import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import jwt  # type: ignore[import]
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False
    logger.warning("PyJWT not installed; JWT auth is disabled")

SECRET_KEY_ENV = "JARVIS_SECRET_KEY"
DEFAULT_EXPIRE_SECONDS = 3600  # 1 hour


class AuthManager:
    """Issues and validates JWT access tokens for the JARVIS API."""

    def __init__(self, secret: Optional[str] = None, expire_seconds: int = DEFAULT_EXPIRE_SECONDS) -> None:
        """Initialise the auth manager.

        Args:
            secret: JWT signing secret.  Reads from ``JARVIS_SECRET_KEY`` env var if not provided.
            expire_seconds: Token validity window in seconds.
        """
        self._secret = secret or os.environ.get(SECRET_KEY_ENV, "change-me-in-production")
        self._expire_seconds = expire_seconds
        if self._secret == "change-me-in-production":
            logger.warning("Using default JWT secret – set %s in production!", SECRET_KEY_ENV)

    def create_token(self, subject: str, extra_claims: Optional[Dict[str, Any]] = None) -> str:
        """Create a signed JWT access token.

        Args:
            subject: Token subject (e.g., username or device ID).
            extra_claims: Optional additional claims to include.

        Returns:
            Encoded JWT string.

        Raises:
            RuntimeError: If PyJWT is not installed.
        """
        if not _JWT_AVAILABLE:
            raise RuntimeError("PyJWT is required for JWT auth")

        now = int(time.time())
        payload: Dict[str, Any] = {
            "sub": subject,
            "iat": now,
            "exp": now + self._expire_seconds,
        }
        if extra_claims:
            payload.update(extra_claims)
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token.

        Args:
            token: The encoded JWT string.

        Returns:
            Decoded payload if valid, ``None`` otherwise.
        """
        if not _JWT_AVAILABLE:
            logger.error("PyJWT not installed – cannot verify token")
            return None
        try:
            return jwt.decode(token, self._secret, algorithms=["HS256"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("Token verification failed: %s", exc)
            return None
