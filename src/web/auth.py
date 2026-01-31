"""
Authentication Module
User authentication and session management for the web interface
"""

import hashlib
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Optional, List

try:
    from flask import g, request, redirect, url_for, session, flash
    from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user
    FLASK_LOGIN_AVAILABLE = True
except ImportError:
    FLASK_LOGIN_AVAILABLE = False
    UserMixin = object

try:
    from core.config import get_logger
    logger = get_logger('web.auth')
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class User(UserMixin):
    """User model for authentication"""
    id: str
    username: str
    email: str
    password_hash: str
    role: str = 'viewer'  # admin, manager, analyst, viewer
    is_active: bool = True
    created_at: datetime = None
    last_login: Optional[datetime] = None
    failed_attempts: int = 0
    locked_until: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def is_authenticated(self) -> bool:
        """Flask-Login: user is authenticated if active"""
        return self.is_active

    def get_id(self):
        return self.id

    def is_admin(self):
        return self.role == 'admin'

    def has_role(self, required_role: str) -> bool:
        """Check if user has the required role or higher"""
        role_hierarchy = ['viewer', 'analyst', 'manager', 'admin']
        try:
            user_level = role_hierarchy.index(self.role)
            required_level = role_hierarchy.index(required_role)
            return user_level >= required_level
        except ValueError:
            return False

    def can_edit(self):
        return self.role in ['admin', 'manager']

    def can_generate(self):
        return self.role in ['admin', 'manager', 'analyst']

    def can_view(self):
        return True


class AuthManager:
    """
    Manages user authentication and authorization.

    Features:
    - Password hashing with salt
    - Account lockout after failed attempts
    - Role-based access control
    - Session management
    """

    LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION = timedelta(minutes=15)
    PASSWORD_MIN_LENGTH = 8

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the users database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'viewer',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    failed_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    ip_address TEXT,
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)

            # Create default admin user if no users exist
            cursor = conn.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                self._create_default_admin(conn)

            conn.commit()

    def _create_default_admin(self, conn):
        """Create default admin user"""
        admin_password = secrets.token_urlsafe(16)
        admin_id = secrets.token_hex(16)
        password_hash = self._hash_password(admin_password)

        conn.execute("""
            INSERT INTO users (id, username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (admin_id, 'admin', 'admin@localhost', password_hash, 'admin', 1))

        # Write credentials to file for first-time setup
        creds_file = Path(self.db_path).parent / 'admin_credentials.txt'
        creds_file.write_text(f"""PolicyUpdate Default Admin Credentials
========================================
Username: admin
Password: {admin_password}

IMPORTANT: Change this password immediately after first login!
Delete this file after recording the credentials securely.
""")
        logger.warning(f"Created default admin user. Credentials saved to: {creds_file}")

    def _hash_password(self, password: str, salt: Optional[str] = None) -> str:
        """Hash a password with salt"""
        if salt is None:
            salt = secrets.token_hex(32)

        # Use PBKDF2-like approach with SHA256
        combined = f"{salt}:{password}"
        for _ in range(100000):  # iterations
            combined = hashlib.sha256(combined.encode()).hexdigest()

        return f"{salt}:{combined}"

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            salt, _ = password_hash.split(':', 1)
            return self._hash_password(password, salt) == password_hash
        except ValueError:
            return False

    def create_user(self, username: str, email: str, password: str,
                    role: str = 'viewer') -> Optional[User]:
        """Create a new user"""
        if len(password) < self.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.PASSWORD_MIN_LENGTH} characters")

        if role not in ['admin', 'manager', 'analyst', 'viewer']:
            raise ValueError(f"Invalid role: {role}")

        user_id = secrets.token_hex(16)
        password_hash = self._hash_password(password)

        try:
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO users (id, username, email, password_hash, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, username.lower(), email.lower(), password_hash, role))
                conn.commit()

            logger.info(f"Created user: {username} with role: {role}")
            return self.get_user(user_id)

        except sqlite3.IntegrityError as e:
            logger.warning(f"Failed to create user {username}: {e}")
            return None

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_user(row)
        return None

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get a user by username"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username.lower(),)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_user(row)
        return None

    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            password_hash=row['password_hash'],
            role=row['role'],
            is_active=bool(row['is_active']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else datetime.now(),
            last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
            failed_attempts=row['failed_attempts'] or 0,
            locked_until=datetime.fromisoformat(row['locked_until']) if row['locked_until'] else None
        )

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user"""
        user = self.get_user_by_username(username)

        if not user:
            logger.warning(f"Authentication failed: user not found: {username}")
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.now():
            logger.warning(f"Authentication failed: account locked: {username}")
            return None

        # Check if account is active
        if not user.is_active:
            logger.warning(f"Authentication failed: account disabled: {username}")
            return None

        # Verify password
        if self._verify_password(password, user.password_hash):
            # Reset failed attempts and update last login
            with self._get_conn() as conn:
                conn.execute("""
                    UPDATE users
                    SET failed_attempts = 0, locked_until = NULL, last_login = ?
                    WHERE id = ?
                """, (datetime.now().isoformat(), user.id))
                conn.commit()

            logger.info(f"User authenticated: {username}")
            return self.get_user(user.id)

        # Increment failed attempts
        failed_attempts = user.failed_attempts + 1
        locked_until = None

        if failed_attempts >= self.LOCKOUT_THRESHOLD:
            locked_until = datetime.now() + self.LOCKOUT_DURATION
            logger.warning(f"Account locked due to failed attempts: {username}")

        with self._get_conn() as conn:
            conn.execute("""
                UPDATE users SET failed_attempts = ?, locked_until = ?
                WHERE id = ?
            """, (failed_attempts, locked_until.isoformat() if locked_until else None, user.id))
            conn.commit()

        logger.warning(f"Authentication failed: invalid password for: {username}")
        return None

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change a user's password"""
        user = self.get_user(user_id)
        if not user:
            return False

        if not self._verify_password(old_password, user.password_hash):
            return False

        if len(new_password) < self.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.PASSWORD_MIN_LENGTH} characters")

        new_hash = self._hash_password(new_password)

        with self._get_conn() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, user_id)
            )
            conn.commit()

        logger.info(f"Password changed for user: {user.username}")
        return True

    def update_user(self, user_id: str, email: str = None, role: str = None,
                    is_active: bool = None) -> Optional[User]:
        """Update user information"""
        updates = []
        params = []

        if email:
            updates.append("email = ?")
            params.append(email.lower())

        if role:
            if role not in ['admin', 'manager', 'analyst', 'viewer']:
                raise ValueError(f"Invalid role: {role}")
            updates.append("role = ?")
            params.append(role)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if is_active else 0)

        if not updates:
            return self.get_user(user_id)

        params.append(user_id)

        with self._get_conn() as conn:
            conn.execute(
                f"UPDATE users SET {', '.join(updates)} WHERE id = ?",
                params
            )
            conn.commit()

        return self.get_user(user_id)

    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        with self._get_conn() as conn:
            cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return cursor.rowcount > 0

    def list_users(self) -> List[User]:
        """List all users"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM users ORDER BY username")
            return [self._row_to_user(row) for row in cursor.fetchall()]

    def reset_password(self, user_id: str, new_password: str) -> bool:
        """Admin reset of user password"""
        if len(new_password) < self.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.PASSWORD_MIN_LENGTH} characters")

        new_hash = self._hash_password(new_password)

        with self._get_conn() as conn:
            cursor = conn.execute(
                "UPDATE users SET password_hash = ?, failed_attempts = 0, locked_until = NULL WHERE id = ?",
                (new_hash, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0


def init_login_manager(app, auth_manager: AuthManager):
    """Initialize Flask-Login with the app"""
    if not FLASK_LOGIN_AVAILABLE:
        logger.warning("Flask-Login not available, authentication disabled")
        return None

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return auth_manager.get_user(user_id)

    return login_manager


def role_required(*roles):
    """Decorator to require specific roles for a view"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Decorator to require admin role"""
    return role_required('admin')(f)


def manager_required(f):
    """Decorator to require manager or admin role"""
    return role_required('admin', 'manager')(f)


def analyst_required(f):
    """Decorator to require analyst, manager, or admin role"""
    return role_required('admin', 'manager', 'analyst')(f)
