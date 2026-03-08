"""Tests for the auth backend – user model, user store, and auth routes."""

import time
from unittest.mock import patch

import pytest

from jarvis.models.user import User, UserStore, hash_password, verify_password


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------


class TestPasswordHelpers:
    def test_hash_and_verify(self):
        hashed = hash_password("supersecret")
        assert isinstance(hashed, str)
        assert hashed != "supersecret"
        assert verify_password("supersecret", hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correctpassword")
        assert not verify_password("wrongpassword", hashed)

    def test_empty_password_hashes(self):
        hashed = hash_password("")
        assert isinstance(hashed, str)


# ---------------------------------------------------------------------------
# User model
# ---------------------------------------------------------------------------


class TestUserModel:
    def test_default_id_is_uuid(self):
        u = User(username="alice", email="alice@example.com")
        import uuid
        assert uuid.UUID(u.id)  # does not raise

    def test_set_and_check_password(self):
        u = User()
        u.set_password("mypassword123")
        assert u.check_password("mypassword123")
        assert not u.check_password("wrong")

    def test_record_login_updates_timestamp(self):
        u = User()
        assert u.last_login is None
        u.record_login()
        assert u.last_login is not None

    def test_to_dict_excludes_hash_by_default(self):
        u = User(username="bob", email="bob@example.com")
        u.set_password("secret")
        d = u.to_dict()
        assert "password_hash" not in d
        assert d["username"] == "bob"

    def test_to_dict_includes_hash_when_requested(self):
        u = User(username="bob", email="bob@example.com")
        u.set_password("secret")
        d = u.to_dict(include_hash=True)
        assert "password_hash" in d

    def test_from_dict_roundtrip(self):
        u = User(username="carol", email="carol@example.com")
        u.set_password("pass123")
        d = u.to_dict(include_hash=True)
        u2 = User.from_dict(d)
        assert u2.id == u.id
        assert u2.username == u.username
        assert u2.email == u.email
        assert u2.check_password("pass123")


# ---------------------------------------------------------------------------
# UserStore
# ---------------------------------------------------------------------------


class TestUserStore:
    def _make_store(self, tmp_path):
        return UserStore(db_path=str(tmp_path / "users.json"))

    def test_create_and_retrieve_by_email(self, tmp_path):
        store = self._make_store(tmp_path)
        user = store.create("dave", "dave@example.com", "password123")
        found = store.get_by_email("dave@example.com")
        assert found is not None
        assert found.id == user.id

    def test_create_duplicate_email_raises(self, tmp_path):
        store = self._make_store(tmp_path)
        store.create("dave", "dave@example.com", "password123")
        with pytest.raises(ValueError, match="already registered"):
            store.create("dave2", "dave@example.com", "anotherpass")

    def test_create_duplicate_username_raises(self, tmp_path):
        store = self._make_store(tmp_path)
        store.create("dave", "dave@example.com", "password123")
        with pytest.raises(ValueError, match="already taken"):
            store.create("dave", "dave2@example.com", "anotherpass")

    def test_get_by_id(self, tmp_path):
        store = self._make_store(tmp_path)
        user = store.create("eve", "eve@example.com", "pw12345678")
        found = store.get_by_id(user.id)
        assert found is not None
        assert found.email == "eve@example.com"

    def test_get_by_username(self, tmp_path):
        store = self._make_store(tmp_path)
        store.create("frank", "frank@example.com", "pw12345678")
        found = store.get_by_username("frank")
        assert found is not None
        assert found.email == "frank@example.com"

    def test_update_user(self, tmp_path):
        store = self._make_store(tmp_path)
        user = store.create("grace", "grace@example.com", "pw12345678")
        user.preferences["theme"] = "dark"
        store.update(user)
        found = store.get_by_id(user.id)
        assert found.preferences["theme"] == "dark"

    def test_delete_user(self, tmp_path):
        store = self._make_store(tmp_path)
        user = store.create("henry", "henry@example.com", "pw12345678")
        assert store.delete(user.id) is True
        assert store.get_by_id(user.id) is None

    def test_delete_nonexistent_returns_false(self, tmp_path):
        store = self._make_store(tmp_path)
        assert store.delete("nonexistent-id") is False

    def test_persistence(self, tmp_path):
        """Data written by one store instance is readable by another."""
        store1 = self._make_store(tmp_path)
        user = store1.create("ivan", "ivan@example.com", "pw12345678")

        store2 = self._make_store(tmp_path)
        found = store2.get_by_email("ivan@example.com")
        assert found is not None
        assert found.id == user.id
        assert found.check_password("pw12345678")

    def test_case_insensitive_email(self, tmp_path):
        store = self._make_store(tmp_path)
        store.create("judy", "Judy@Example.COM", "pw12345678")
        assert store.get_by_email("judy@example.com") is not None


# ---------------------------------------------------------------------------
# Auth Manager (JWT)
# ---------------------------------------------------------------------------


class TestAuthManager:
    def test_create_and_verify_token(self):
        from jarvis.core.security.auth import AuthManager
        mgr = AuthManager(secret="test-secret", expire_seconds=3600)
        token = mgr.create_token("user-123", extra_claims={"username": "alice"})
        payload = mgr.verify_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["username"] == "alice"

    def test_expired_token_returns_none(self):
        from jarvis.core.security.auth import AuthManager
        mgr = AuthManager(secret="test-secret", expire_seconds=-1)
        token = mgr.create_token("user-123")
        # Allow slight clock skew
        time.sleep(0.1)
        payload = mgr.verify_token(token)
        assert payload is None

    def test_invalid_token_returns_none(self):
        from jarvis.core.security.auth import AuthManager
        mgr = AuthManager(secret="test-secret")
        payload = mgr.verify_token("not.a.valid.token")
        assert payload is None
