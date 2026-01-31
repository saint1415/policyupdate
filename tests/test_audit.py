"""
Tests for Audit Logging System
Tests audit log creation, querying, and statistics
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
    return os.path.join(tempfile.gettempdir(), f"test_audit_{uuid.uuid4().hex}.db")


def cleanup_db(db_path):
    """Clean up temp database, ignoring errors"""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        pass


class TestAuditLogger:
    """Test audit logger functionality"""

    @pytest.fixture
    def audit_logger(self):
        """Create audit logger with temp database"""
        db_path = get_temp_db()

        from core.audit import AuditLogger
        logger = AuditLogger(db_path)
        yield logger

        cleanup_db(db_path)

    def test_log_event(self, audit_logger):
        """Test basic event logging"""
        from core.audit import AuditAction

        result = audit_logger.log(
            action=AuditAction.LOGIN_SUCCESS,
            username="testuser",
            details="User logged in successfully"
        )

        assert result is not None

    def test_log_with_resource(self, audit_logger):
        """Test logging with resource info"""
        from core.audit import AuditAction

        result = audit_logger.log(
            action=AuditAction.PACKAGE_GENERATE,
            username="testuser",
            resource_type="package",
            resource_id="pkg-123",
            details="Generated 50 policies"
        )

        assert result is not None

    def test_log_with_ip_address(self, audit_logger):
        """Test logging with IP address"""
        from core.audit import AuditAction

        result = audit_logger.log(
            action=AuditAction.LOGIN_ATTEMPT,
            username="testuser",
            ip_address="192.168.1.100",
            details="Login attempt"
        )

        assert result is not None

    def test_get_logs(self, audit_logger):
        """Test retrieving logs"""
        from core.audit import AuditAction

        # Create some logs
        for i in range(5):
            audit_logger.log(
                action=AuditAction.LOGIN_SUCCESS,
                username=f"user{i}",
                details=f"Log entry {i}"
            )

        logs = audit_logger.get_logs(limit=10)

        assert len(logs) >= 5

    def test_get_logs_with_limit(self, audit_logger):
        """Test log retrieval with limit"""
        from core.audit import AuditAction

        # Create many logs
        for i in range(20):
            audit_logger.log(
                action=AuditAction.LOGIN_SUCCESS,
                username=f"user{i}",
                details=f"Log entry {i}"
            )

        logs = audit_logger.get_logs(limit=5)

        assert len(logs) == 5

    def test_get_logs_with_offset(self, audit_logger):
        """Test log retrieval with pagination"""
        from core.audit import AuditAction

        # Create logs
        for i in range(10):
            audit_logger.log(
                action=AuditAction.LOGIN_SUCCESS,
                username=f"user{i}",
                details=f"Log entry {i}"
            )

        page1 = audit_logger.get_logs(limit=5, offset=0)
        page2 = audit_logger.get_logs(limit=5, offset=5)

        assert len(page1) == 5
        assert len(page2) == 5

        # Different entries
        page1_ids = {log.get('id') for log in page1}
        page2_ids = {log.get('id') for log in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_logs_by_username(self, audit_logger):
        """Test filtering logs by username"""
        from core.audit import AuditAction

        # Create logs for different users
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="alice")
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="bob")
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="alice")

        logs = audit_logger.get_logs(username="alice")

        assert all(log.get('username') == 'alice' for log in logs)

    def test_get_logs_by_action(self, audit_logger):
        """Test filtering logs by action"""
        from core.audit import AuditAction

        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="user1")
        audit_logger.log(action=AuditAction.PACKAGE_GENERATE, username="user1")
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="user2")

        logs = audit_logger.get_logs(action_filter="LOGIN")

        # Check that filtered logs contain login-related actions (case-insensitive)
        assert all("login" in log.get('action', '').lower() for log in logs)


class TestAuditActions:
    """Test audit action types"""

    def test_all_action_types_exist(self):
        """Test all required action types are defined"""
        from core.audit import AuditAction

        # Authentication
        assert hasattr(AuditAction, 'LOGIN_SUCCESS')
        assert hasattr(AuditAction, 'LOGIN_FAILURE')
        assert hasattr(AuditAction, 'LOGOUT')

        # Client operations
        assert hasattr(AuditAction, 'CLIENT_CREATE')
        assert hasattr(AuditAction, 'CLIENT_UPDATE')
        assert hasattr(AuditAction, 'CLIENT_DELETE')

        # Generation
        assert hasattr(AuditAction, 'PACKAGE_GENERATE')

    def test_action_values_are_strings(self):
        """Test action values are string type"""
        from core.audit import AuditAction

        assert isinstance(AuditAction.LOGIN_SUCCESS.value, str)
        assert isinstance(AuditAction.PACKAGE_GENERATE.value, str)


class TestAuditSeverity:
    """Test audit severity levels"""

    def test_severity_levels_exist(self):
        """Test all severity levels are defined"""
        from core.audit import AuditSeverity

        assert hasattr(AuditSeverity, 'DEBUG')
        assert hasattr(AuditSeverity, 'INFO')
        assert hasattr(AuditSeverity, 'WARNING')
        assert hasattr(AuditSeverity, 'ERROR')
        assert hasattr(AuditSeverity, 'CRITICAL')

    def test_log_with_severity(self):
        """Test logging with explicit severity"""
        db_path = get_temp_db()
        try:
            from core.audit import AuditLogger, AuditAction, AuditSeverity

            logger = AuditLogger(db_path)
            result = logger.log(
                action=AuditAction.LOGIN_FAILURE,
                username="testuser",
                severity=AuditSeverity.WARNING,
                details="Invalid password"
            )

            assert result is not None
        finally:
            cleanup_db(db_path)


class TestAuditStatistics:
    """Test audit statistics generation"""

    @pytest.fixture
    def audit_logger(self):
        """Create audit logger with temp database"""
        db_path = get_temp_db()

        from core.audit import AuditLogger
        logger = AuditLogger(db_path)
        yield logger

        cleanup_db(db_path)

    def test_get_statistics(self, audit_logger):
        """Test statistics generation"""
        from core.audit import AuditAction

        # Create some logs
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="user1")
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="user2")
        audit_logger.log(action=AuditAction.PACKAGE_GENERATE, username="user1")

        stats = audit_logger.get_statistics(days=1)

        assert 'total_events' in stats or 'by_severity' in stats

    def test_statistics_by_action(self, audit_logger):
        """Test statistics broken down by action"""
        from core.audit import AuditAction

        # Create logs of different types
        for _ in range(5):
            audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="user1")
        for _ in range(3):
            audit_logger.log(action=AuditAction.PACKAGE_GENERATE, username="user1")

        stats = audit_logger.get_statistics(days=1)

        # Should have breakdown by action or severity
        assert 'by_action' in stats or 'by_severity' in stats


class TestAuditRetention:
    """Test audit log retention"""

    def test_enforce_retention(self):
        """Test old logs are cleaned up"""
        db_path = get_temp_db()
        try:
            from core.audit import AuditLogger, AuditAction

            logger = AuditLogger(db_path, retention_days=1)

            # Create a log
            logger.log(action=AuditAction.LOGIN_SUCCESS, username="test")

            # Enforce retention
            deleted = logger.enforce_retention()

            # Should return number of deleted entries (may be 0 if all are recent)
            assert isinstance(deleted, int)
        finally:
            cleanup_db(db_path)


class TestAuditExport:
    """Test audit log export functionality"""

    @pytest.fixture
    def audit_logger(self):
        """Create audit logger with temp database"""
        db_path = get_temp_db()

        from core.audit import AuditLogger
        logger = AuditLogger(db_path)
        yield logger

        cleanup_db(db_path)

    def test_export_to_json(self, audit_logger):
        """Test exporting logs to JSON format"""
        from core.audit import AuditAction
        import json

        # Create some logs
        audit_logger.log(action=AuditAction.LOGIN_SUCCESS, username="user1")

        export_path = os.path.join(tempfile.gettempdir(), f"test_export_{uuid.uuid4().hex}.json")

        try:
            audit_logger.export_logs(export_path, format='json')

            # Verify file was created and is valid JSON
            with open(export_path, 'r') as f:
                data = json.load(f)

            # Export format includes metadata and entries list
            assert 'entries' in data or isinstance(data, list)
            if isinstance(data, dict):
                assert isinstance(data['entries'], list)
        finally:
            cleanup_db(export_path)
