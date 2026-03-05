"""Tests for the JARVIS security modules."""

import pytest
from jarvis.core.security.validator import CommandValidator
from jarvis.core.security.permissions import Permission, PermissionManager
from jarvis.core.security.auth import AuthManager


class TestCommandValidator:
    def setup_method(self):
        self.validator = CommandValidator()

    def test_valid_command(self):
        result = self.validator.validate("echo hello")
        assert result == "echo hello"

    def test_empty_command_raises(self):
        with pytest.raises(ValueError, match="Empty"):
            self.validator.validate("")

    def test_rm_rf_blocked(self):
        with pytest.raises(ValueError):
            self.validator.validate("rm -rf /")

    def test_shutdown_blocked(self):
        with pytest.raises(ValueError):
            self.validator.validate("shutdown -h now")

    def test_long_command_blocked(self):
        with pytest.raises(ValueError, match="too long"):
            self.validator.validate("x" * 10_001)

    def test_path_traversal_blocked(self):
        with pytest.raises(ValueError):
            self.validator.validate_path("../../etc/passwd")

    def test_etc_path_blocked(self):
        with pytest.raises(ValueError):
            self.validator.validate_path("/etc/shadow")


class TestPermissionManager:
    def setup_method(self):
        self.pm = PermissionManager()

    def test_default_permissions(self):
        assert self.pm.has(Permission.FILE_READ)
        assert self.pm.has(Permission.NETWORK_ACCESS)

    def test_grant_and_revoke(self):
        self.pm.grant(Permission.FILE_WRITE)
        assert self.pm.has(Permission.FILE_WRITE)
        self.pm.revoke(Permission.FILE_WRITE)
        assert not self.pm.has(Permission.FILE_WRITE)

    def test_require_raises_when_missing(self):
        self.pm.revoke(Permission.FILE_READ)
        with pytest.raises(PermissionError):
            self.pm.require(Permission.FILE_READ)

    def test_admin_grants_all(self):
        self.pm.grant(Permission.ADMIN)
        assert self.pm.has(Permission.FILE_DELETE)
        assert self.pm.has(Permission.SYSTEM_EXEC)


class TestAuthManager:
    def setup_method(self):
        self.auth = AuthManager(secret="test-secret-key-for-testing")

    def test_create_and_verify_token(self):
        try:
            token = self.auth.create_token("test-user")
            payload = self.auth.verify_token(token)
            assert payload is not None
            assert payload["sub"] == "test-user"
        except RuntimeError:
            pytest.skip("PyJWT not installed")

    def test_invalid_token_returns_none(self):
        result = self.auth.verify_token("not-a-real-token")
        assert result is None
