"""User model with bcrypt password hashing and JWT integration."""

import hashlib
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional bcrypt import (falls back to SHA-256 if unavailable)
# ---------------------------------------------------------------------------

try:
    import bcrypt as _bcrypt  # type: ignore[import]
    _BCRYPT_AVAILABLE = True
except ImportError:
    _bcrypt = None  # type: ignore[assignment]
    _BCRYPT_AVAILABLE = False
    logger.warning("bcrypt not installed; password hashing will use SHA-256 (not for production)")


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


def hash_password(plain_password: str) -> str:
    """Hash *plain_password* using bcrypt (SHA-256 fallback if unavailable).

    Args:
        plain_password: The user's plaintext password.

    Returns:
        Hashed password string.
    """
    if _BCRYPT_AVAILABLE:
        return _bcrypt.hashpw(plain_password.encode(), _bcrypt.gensalt()).decode()
    # Fallback: not suitable for production
    return hashlib.sha256(plain_password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify *plain_password* against *hashed_password*.

    Args:
        plain_password: The user's plaintext password.
        hashed_password: Previously hashed value.

    Returns:
        ``True`` if the password matches.
    """
    if _BCRYPT_AVAILABLE:
        try:
            return _bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
        except Exception:  # noqa: BLE001
            return False
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


# ---------------------------------------------------------------------------
# User model (in-memory / JSON-serialisable, no SQLAlchemy dependency)
# ---------------------------------------------------------------------------


@dataclass
class User:
    """Represents an authenticated user of the JARVIS system.

    Attributes:
        id: UUID string – unique identifier.
        username: Unique display name.
        email: Unique email address.
        password_hash: Bcrypt-hashed password.
        created_at: ISO-8601 creation timestamp.
        last_login: ISO-8601 last-login timestamp (or None).
        is_active: Whether the account is active.
        preferences: Arbitrary JSON-serialisable preferences dict.
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    username: str = ""
    email: str = ""
    password_hash: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_login: Optional[str] = None
    is_active: bool = True
    preferences: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def set_password(self, plain_password: str) -> None:
        """Hash and store *plain_password*."""
        self.password_hash = hash_password(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """Return ``True`` if *plain_password* matches the stored hash."""
        return verify_password(plain_password, self.password_hash)

    def record_login(self) -> None:
        """Update the last-login timestamp to now."""
        self.last_login = datetime.now(timezone.utc).isoformat()

    def to_dict(self, include_hash: bool = False) -> Dict[str, Any]:
        """Serialise to a plain dictionary.

        Args:
            include_hash: Include password_hash in the output (default False).

        Returns:
            Dict representation suitable for JSON serialisation.
        """
        d: Dict[str, Any] = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "is_active": self.is_active,
            "preferences": self.preferences,
        }
        if include_hash:
            d["password_hash"] = self.password_hash
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """Deserialise from a plain dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            username=data.get("username", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            last_login=data.get("last_login"),
            is_active=data.get("is_active", True),
            preferences=data.get("preferences", {}),
        )


# ---------------------------------------------------------------------------
# Simple in-memory user store (replace with SQLAlchemy for production)
# ---------------------------------------------------------------------------


class UserStore:
    """Thread-safe in-memory user registry backed by a JSON file.

    For production use, swap this implementation for a proper database layer
    (e.g. SQLAlchemy + PostgreSQL).
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        import json
        import pathlib
        import threading

        self._lock = threading.Lock()
        self._db_path = db_path or os.environ.get(
            "JARVIS_USER_DB", "jarvis/data/users.json"
        )
        self._users: Dict[str, User] = {}  # id → User
        self._email_index: Dict[str, str] = {}  # email → id
        self._username_index: Dict[str, str] = {}  # username → id
        self._load()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def create(self, username: str, email: str, plain_password: str) -> User:
        """Create and persist a new user.

        Args:
            username: Desired username (must be unique).
            email: Email address (must be unique).
            plain_password: Plaintext password to hash and store.

        Returns:
            The newly created :class:`User`.

        Raises:
            ValueError: If username or email is already taken.
        """
        with self._lock:
            email_lower = email.lower().strip()
            username_lower = username.lower().strip()
            if email_lower in self._email_index:
                raise ValueError(f"Email '{email}' is already registered")
            if username_lower in self._username_index:
                raise ValueError(f"Username '{username}' is already taken")

            user = User(username=username, email=email_lower)
            user.set_password(plain_password)
            self._users[user.id] = user
            self._email_index[email_lower] = user.id
            self._username_index[username_lower] = user.id
            self._save()
            return user

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Retrieve a user by ID."""
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by email address (case-insensitive)."""
        uid = self._email_index.get(email.lower().strip())
        return self._users.get(uid) if uid else None

    def get_by_username(self, username: str) -> Optional[User]:
        """Retrieve a user by username (case-insensitive)."""
        uid = self._username_index.get(username.lower().strip())
        return self._users.get(uid) if uid else None

    def update(self, user: User) -> None:
        """Persist changes to an existing user."""
        with self._lock:
            self._users[user.id] = user
            self._save()

    def delete(self, user_id: str) -> bool:
        """Delete a user. Returns ``True`` if the user was found and removed."""
        with self._lock:
            user = self._users.pop(user_id, None)
            if user is None:
                return False
            self._email_index.pop(user.email, None)
            self._username_index.pop(user.username.lower(), None)
            self._save()
            return True

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        import json
        import pathlib
        path = pathlib.Path(self._db_path)
        if not path.exists():
            return
        try:
            with path.open("r", encoding="utf-8") as fh:
                records: List[Dict[str, Any]] = json.load(fh)
            for record in records:
                user = User.from_dict(record)
                self._users[user.id] = user
                self._email_index[user.email.lower()] = user.id
                self._username_index[user.username.lower()] = user.id
        except Exception as exc:  # noqa: BLE001
            logger.warning("Could not load user database: %s", exc)

    def _save(self) -> None:
        import json
        import pathlib
        path = pathlib.Path(self._db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(
                    [u.to_dict(include_hash=True) for u in self._users.values()],
                    fh,
                    indent=2,
                )
        except Exception as exc:  # noqa: BLE001
            logger.error("Could not save user database: %s", exc)


# Module-level singleton
_store: Optional[UserStore] = None


def get_user_store() -> UserStore:
    """Return the module-level :class:`UserStore` singleton."""
    global _store
    if _store is None:
        _store = UserStore()
    return _store
