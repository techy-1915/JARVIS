"""Authentication API routes – register, login, logout, verify, and user info."""

import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from ...core.security.auth import AuthManager
from ...models.user import UserStore, get_user_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Module-level singletons
_auth: Optional[AuthManager] = None
_store: Optional[UserStore] = None


def _get_auth() -> AuthManager:
    global _auth
    if _auth is None:
        _auth = AuthManager()
    return _auth


def _get_store() -> UserStore:
    global _store
    if _store is None:
        _store = get_user_store()
    return _store


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=8, max_length=200)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address")
        return v.lower().strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError("Username may only contain letters, numbers, _ and -")
        return v.strip()


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=5, max_length=200)
    password: str = Field(..., min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    created_at: str
    last_login: Optional[str]
    is_active: bool
    preferences: Dict[str, Any]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_bearer(authorization: Optional[str]) -> Optional[str]:
    """Extract the token from an ``Authorization: Bearer <token>`` header."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def _require_current_user(authorization: Optional[str]) -> Dict[str, Any]:
    """Decode the bearer token and return the payload, or raise 401."""
    token = _extract_bearer(authorization)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = _get_auth().verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest) -> TokenResponse:
    """Register a new user and return an access token.

    Args:
        body: Registration payload (username, email, password).

    Returns:
        JWT access token and basic user info.

    Raises:
        422: On validation errors.
        409: If username or email is already taken.
    """
    store = _get_store()
    try:
        user = store.create(body.username, body.email, body.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    token = _get_auth().create_token(user.id, extra_claims={"username": user.username})
    logger.info("New user registered: %s (%s)", user.username, user.id)
    return TokenResponse(access_token=token, user=user.to_dict())


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Authenticate a user and return an access token.

    Args:
        body: Login payload (email, password).

    Returns:
        JWT access token and basic user info.

    Raises:
        401: If credentials are invalid.
    """
    store = _get_store()
    user = store.get_by_email(body.email)
    if user is None or not user.check_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )

    user.record_login()
    store.update(user)

    token = _get_auth().create_token(user.id, extra_claims={"username": user.username})
    logger.info("User logged in: %s", user.username)
    return TokenResponse(access_token=token, user=user.to_dict())


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(authorization: Optional[str] = Header(default=None)) -> Dict[str, str]:
    """Invalidate the current session (client-side token removal).

    JWT tokens are stateless; the client should discard the token.  A
    server-side blocklist can be added here for stricter security.

    Args:
        authorization: ``Authorization: Bearer <token>`` header.

    Returns:
        Success message.
    """
    _require_current_user(authorization)
    return {"message": "Logged out successfully"}


@router.get("/verify", status_code=status.HTTP_200_OK)
async def verify(authorization: Optional[str] = Header(default=None)) -> Dict[str, Any]:
    """Verify the current access token.

    Args:
        authorization: ``Authorization: Bearer <token>`` header.

    Returns:
        Token payload if valid.

    Raises:
        401: If the token is missing or invalid.
    """
    payload = _require_current_user(authorization)
    return {"valid": True, "payload": payload}


@router.get("/user", response_model=UserResponse)
async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> UserResponse:
    """Return the authenticated user's profile.

    Args:
        authorization: ``Authorization: Bearer <token>`` header.

    Returns:
        User profile data.

    Raises:
        401: If unauthenticated.
        404: If the user record no longer exists.
    """
    payload = _require_current_user(authorization)
    user_id: str = payload.get("sub", "")
    store = _get_store()
    user = store.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserResponse(**user.to_dict())
