"""FastAPI authentication middleware for JARVIS API."""

import logging
from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer

from ..core.security.auth import AuthManager

logger = logging.getLogger(__name__)

_auth_manager = AuthManager()
_security = HTTPBearer(auto_error=False)


async def verify_token(request: Request) -> Optional[dict]:
    """Extract and verify a JWT token from the Authorization header.

    Args:
        request: The incoming FastAPI request.

    Returns:
        Decoded token payload if valid.

    Raises:
        HTTPException: 401 if the token is missing or invalid.
    """
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )
    token = auth_header[len("Bearer "):]
    payload = _auth_manager.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    return payload
