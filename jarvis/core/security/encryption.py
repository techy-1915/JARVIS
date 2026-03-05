"""Encryption utilities for secure communication."""

import base64
import logging
import os
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    logger.warning("cryptography library not installed; encryption disabled")


class EncryptionManager:
    """Provides symmetric encryption for sensitive data storage and transfer."""

    def __init__(self, key: Optional[bytes] = None) -> None:
        """Initialise with an optional pre-derived Fernet key.

        Args:
            key: 32-byte Fernet key.  Generated if not provided.
        """
        if not _CRYPTO_AVAILABLE:
            self._fernet = None
            return

        if key is None:
            key = Fernet.generate_key()
        self._fernet = Fernet(key)

    @staticmethod
    def derive_key(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
        """Derive a Fernet key from a password using PBKDF2.

        Args:
            password: Human-readable password.
            salt: Optional salt bytes; generated if not provided.

        Returns:
            Tuple of (derived_key, salt).

        Raises:
            RuntimeError: If cryptography library is not installed.
        """
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library required for key derivation")

        if salt is None:
            salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key, salt

    def encrypt(self, data: str) -> Optional[str]:
        """Encrypt a string.

        Args:
            data: Plaintext string.

        Returns:
            Base64-encoded ciphertext, or ``None`` if unavailable.
        """
        if self._fernet is None:
            return None
        return self._fernet.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> Optional[str]:
        """Decrypt a previously encrypted string.

        Args:
            token: Encrypted token string.

        Returns:
            Decrypted plaintext, or ``None`` on failure.
        """
        if self._fernet is None:
            return None
        try:
            return self._fernet.decrypt(token.encode()).decode()
        except Exception as exc:  # noqa: BLE001
            logger.error("Decryption failed: %s", exc)
            return None
