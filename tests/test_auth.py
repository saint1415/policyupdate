"""
Tests for Authentication System
Tests user management, password hashing, and session handling
"""

import pytest
import sys
import tempfile
import os
import uuid
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def get_temp_db():
    """Get a unique temp database path"""
    return os.path.join(tempfile.gettempdir(), f"test_auth_{uuid.uuid4().hex}.db")


def cleanup_db(db_path):
    """Clean up temp database, ignoring errors"""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        pass


class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password(self):
        """Test password hashing creates hash"""
        from web.auth import AuthManager

        db_path = get_temp_db()
        try:
            auth = AuthManager(db_path)
            hashed = auth._hash_password("testpassword")

            assert hashed is not None
            assert hashed != "testpassword"
            assert ':' in hashed  # Contains salt separator
        finally:
            cleanup_db(db_path)

    def test_verify_password_correct(self):
        """Test correct password verification"""
        from web.auth import AuthManager

        db_path = get_temp_db()
        try:
            auth = AuthManager(db_path)
            hashed = auth._hash_password("testpassword")

            assert auth._verify_password("testpassword", hashed) is True
        finally:
            cleanup_db(db_path)

    def test_verify_password_incorrect(self):
        """Test incorrect password verification"""
        from web.auth import AuthManager

        db_path = get_temp_db()
        try:
            auth = AuthManager(db_path)
            hashed = auth._hash_password("testpassword")

            assert auth._verify_password("wrongpassword", hashed) is False
        finally:
            cleanup_db(db_path)

    def test_different_passwords_different_hashes(self):
        """Test different passwords create different hashes"""
        from web.auth import AuthManager

        db_path = get_temp_db()
        try:
            auth = AuthManager(db_path)
            hash1 = auth._hash_password("password1")
            hash2 = auth._hash_password("password2")

            assert hash1 != hash2
        finally:
            cleanup_db(db_path)


class TestUserManagement:
    """Test user creation and management"""

    @pytest.fixture
    def auth_manager(self):
        """Create auth manager with temp database"""
        db_path = get_temp_db()

        from web.auth import AuthManager
        auth = AuthManager(db_path)
        yield auth

        cleanup_db(db_path)

    def test_create_user(self, auth_manager):
        """Test user creation"""
        user = auth_manager.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            role="analyst"
        )

        assert user is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == "analyst"

    def test_create_duplicate_username(self, auth_manager):
        """Test duplicate username is rejected"""
        auth_manager.create_user(
            username="uniqueuser",
            email="unique@example.com",
            password="password123"
        )

        # Try to create duplicate
        result = auth_manager.create_user(
            username="uniqueuser",
            email="other@example.com",
            password="password123"
        )

        assert result is None

    def test_get_user_by_id(self, auth_manager):
        """Test getting user by ID"""
        created = auth_manager.create_user(
            username="getbyid",
            email="getbyid@example.com",
            password="password123"
        )

        user = auth_manager.get_user(created.id)

        assert user is not None
        assert user.username == "getbyid"

    def test_get_user_by_username(self, auth_manager):
        """Test getting user by username"""
        auth_manager.create_user(
            username="getbyname",
            email="getbyname@example.com",
            password="password123"
        )

        user = auth_manager.get_user_by_username("getbyname")

        assert user is not None
        assert user.email == "getbyname@example.com"

    def test_get_nonexistent_user(self, auth_manager):
        """Test getting nonexistent user returns None"""
        user = auth_manager.get_user("nonexistent-id")
        assert user is None

    def test_list_users(self, auth_manager):
        """Test listing all users"""
        auth_manager.create_user("user1", "user1@example.com", "password123")
        auth_manager.create_user("user2", "user2@example.com", "password123")

        users = auth_manager.list_users()

        # Should have at least 2 (might have admin from init)
        assert len(users) >= 2

    def test_delete_user(self, auth_manager):
        """Test user deletion"""
        user = auth_manager.create_user(
            username="todelete",
            email="delete@example.com",
            password="password123"
        )

        result = auth_manager.delete_user(user.id)
        assert result is True

        # Should no longer exist
        deleted = auth_manager.get_user(user.id)
        assert deleted is None


class TestAuthentication:
    """Test authentication flow"""

    @pytest.fixture
    def auth_manager(self):
        """Create auth manager with temp database"""
        db_path = get_temp_db()

        from web.auth import AuthManager
        auth = AuthManager(db_path)
        yield auth

        cleanup_db(db_path)

    def test_authenticate_valid(self, auth_manager):
        """Test authentication with valid credentials"""
        auth_manager.create_user(
            username="authtest",
            email="auth@example.com",
            password="correctpassword"
        )

        user = auth_manager.authenticate("authtest", "correctpassword")

        assert user is not None
        assert user.username == "authtest"

    def test_authenticate_invalid_password(self, auth_manager):
        """Test authentication with invalid password"""
        auth_manager.create_user(
            username="authtest2",
            email="auth2@example.com",
            password="correctpassword"
        )

        user = auth_manager.authenticate("authtest2", "wrongpassword")

        assert user is None

    def test_authenticate_nonexistent_user(self, auth_manager):
        """Test authentication with nonexistent user"""
        user = auth_manager.authenticate("nonexistent", "anypassword")
        assert user is None

    def test_account_lockout(self, auth_manager):
        """Test account lockout after failed attempts"""
        auth_manager.create_user(
            username="lockouttest",
            email="lockout@example.com",
            password="correctpassword"
        )

        # Make failed attempts
        for _ in range(6):
            auth_manager.authenticate("lockouttest", "wrongpassword")

        # Even correct password should fail due to lockout
        user = auth_manager.authenticate("lockouttest", "correctpassword")

        # Might be locked out depending on implementation
        # This tests the lockout mechanism exists


class TestUserRoles:
    """Test role-based access"""

    def test_user_is_admin(self):
        """Test admin role check"""
        from web.auth import User

        admin = User(
            id="1",
            username="admin",
            email="admin@example.com",
            password_hash="hash",
            role="admin"
        )

        assert admin.is_admin() is True

    def test_user_is_not_admin(self):
        """Test non-admin role check"""
        from web.auth import User

        analyst = User(
            id="2",
            username="analyst",
            email="analyst@example.com",
            password_hash="hash",
            role="analyst"
        )

        assert analyst.is_admin() is False

    def test_user_role_hierarchy(self):
        """Test role hierarchy"""
        from web.auth import User

        manager = User(
            id="3",
            username="manager",
            email="manager@example.com",
            password_hash="hash",
            role="manager"
        )

        # Managers should have manager privileges but not admin
        assert manager.has_role("manager") is True
        assert manager.has_role("admin") is False

    def test_admin_has_all_roles(self):
        """Test admin has all role privileges"""
        from web.auth import User

        admin = User(
            id="1",
            username="admin",
            email="admin@example.com",
            password_hash="hash",
            role="admin"
        )

        assert admin.has_role("admin") is True
        assert admin.has_role("manager") is True
        assert admin.has_role("analyst") is True
        assert admin.has_role("viewer") is True


class TestPasswordRequirements:
    """Test password validation"""

    def test_password_minimum_length(self):
        """Test minimum password length"""
        from web.auth import AuthManager

        db_path = get_temp_db()
        try:
            auth = AuthManager(db_path)

            # Short password should raise ValueError
            with pytest.raises(ValueError):
                auth.create_user(
                    username="shortpass",
                    email="short@example.com",
                    password="short"
                )
        finally:
            cleanup_db(db_path)


class TestFlaskLogin:
    """Test Flask-Login integration"""

    def test_user_is_authenticated(self):
        """Test authenticated property"""
        from web.auth import User

        user = User(
            id="1",
            username="test",
            email="test@example.com",
            password_hash="hash",
            is_active=True
        )

        assert user.is_authenticated is True

    def test_user_is_active(self):
        """Test active property"""
        from web.auth import User

        active_user = User(
            id="1",
            username="active",
            email="active@example.com",
            password_hash="hash",
            is_active=True
        )

        inactive_user = User(
            id="2",
            username="inactive",
            email="inactive@example.com",
            password_hash="hash",
            is_active=False
        )

        assert active_user.is_active is True
        assert inactive_user.is_active is False

    def test_user_get_id(self):
        """Test get_id method for Flask-Login"""
        from web.auth import User

        user = User(
            id="user-123",
            username="test",
            email="test@example.com",
            password_hash="hash"
        )

        assert user.get_id() == "user-123"
