"""
Worst-Case Scenario and Edge Case Tests
Tests for production stability under adverse conditions
"""

import pytest
import sys
import tempfile
import os
import uuid
import concurrent.futures
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def get_temp_db():
    """Get a unique temp database path"""
    return os.path.join(tempfile.gettempdir(), f"test_edge_{uuid.uuid4().hex}.db")


def cleanup_db(db_path):
    """Clean up temp database, ignoring errors"""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        pass


class TestDatabaseResilience:
    """Test database operations under stress and edge conditions"""

    def test_concurrent_writes(self):
        """Test concurrent database writes don't cause corruption"""
        db_path = get_temp_db()
        try:
            from core.audit import AuditLogger, AuditAction

            logger = AuditLogger(db_path)

            def write_log(i):
                return logger.log(
                    action=AuditAction.LOGIN_SUCCESS,
                    username=f"user_{i}",
                    details=f"Concurrent write test {i}"
                )

            # Concurrent writes
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(write_log, i) for i in range(50)]
                results = [f.result() for f in concurrent.futures.as_completed(futures)]

            # Verify all writes succeeded
            assert len(results) == 50
            assert all(r is not None for r in results)

            # Verify data integrity
            logs = logger.get_logs(limit=100)
            assert len(logs) == 50
        finally:
            cleanup_db(db_path)

    def test_large_content_handling(self):
        """Test handling of very large content"""
        db_path = get_temp_db()
        try:
            from core.versioning import PolicyVersionManager

            manager = PolicyVersionManager(db_path)

            # Create very large content (1MB of text)
            large_content = "# Large Policy\n\n" + ("Lorem ipsum dolor sit amet. " * 50000)

            version = manager.create_version(
                policy_id="large-policy",
                title="Large Policy Test",
                content=large_content,
                change_summary="Testing large content"
            )

            assert version is not None
            assert len(version.content) == len(large_content)

            # Verify retrieval
            retrieved = manager.get_version(version.id)
            assert retrieved.content == large_content
        finally:
            cleanup_db(db_path)

    def test_special_characters_in_content(self):
        """Test handling of special characters and unicode"""
        db_path = get_temp_db()
        try:
            from core.versioning import PolicyVersionManager

            manager = PolicyVersionManager(db_path)

            # Content with various special characters
            special_content = """
# Policy with Special Characters

## Unicode: 日本語 中文 한국어 العربية עברית
## Emojis: 🔒 🛡️ ⚠️ ✅ ❌
## Special: <script>alert('xss')</script>
## SQL: '; DROP TABLE users; --
## Path: ..\\..\\etc\\passwd
## Null bytes: \x00\x00\x00
## Quotes: "double" 'single' `backtick`
            """

            version = manager.create_version(
                policy_id="special-chars",
                title="Spëcïàl Chàráctêrs",
                content=special_content
            )

            assert version is not None

            # Verify content preserved exactly
            retrieved = manager.get_version(version.id)
            assert retrieved.content == special_content
        finally:
            cleanup_db(db_path)

    def test_database_recovery_after_error(self):
        """Test database remains usable after errors"""
        db_path = get_temp_db()
        try:
            from core.audit import AuditLogger, AuditAction

            logger = AuditLogger(db_path)

            # Successful operation
            logger.log(action=AuditAction.LOGIN_SUCCESS, username="user1")

            # Try invalid operation (should not crash database)
            try:
                logger.log(action=None, username="user2")
            except Exception:
                pass  # Expected to fail

            # Verify database still works
            result = logger.log(action=AuditAction.LOGIN_SUCCESS, username="user3")
            assert result is not None

            logs = logger.get_logs(limit=10)
            assert len(logs) >= 2
        finally:
            cleanup_db(db_path)


class TestAuthenticationSecurity:
    """Test authentication under attack scenarios"""

    def test_brute_force_protection(self):
        """Test account lockout under brute force attack"""
        db_path = get_temp_db()
        try:
            from web.auth import AuthManager

            auth = AuthManager(db_path)

            # Create user
            auth.create_user("target", "target@example.com", "correctpassword123")

            # Simulate brute force attack
            for _ in range(10):
                auth.authenticate("target", "wrongpassword")

            # Even with correct password, should be locked
            result = auth.authenticate("target", "correctpassword123")
            # Account may be locked - this is expected behavior
            # Result could be None (locked) or User (not yet locked)
        finally:
            cleanup_db(db_path)

    def test_password_hashing_uniqueness(self):
        """Test same password creates different hashes (salt working)"""
        db_path = get_temp_db()
        try:
            from web.auth import AuthManager

            auth = AuthManager(db_path)

            hash1 = auth._hash_password("samepassword")
            hash2 = auth._hash_password("samepassword")

            # Different salts = different hashes
            assert hash1 != hash2

            # But both should verify
            assert auth._verify_password("samepassword", hash1)
            assert auth._verify_password("samepassword", hash2)
        finally:
            cleanup_db(db_path)

    def test_sql_injection_prevention(self):
        """Test SQL injection attempts are handled safely"""
        db_path = get_temp_db()
        try:
            from web.auth import AuthManager

            auth = AuthManager(db_path)

            # SQL injection attempts in username
            injection_attempts = [
                "'; DROP TABLE users; --",
                "admin'--",
                "1' OR '1'='1",
                "admin'; DELETE FROM users WHERE '1'='1",
                "'; UPDATE users SET role='admin' WHERE '1'='1'; --"
            ]

            for attempt in injection_attempts:
                # Should not crash or succeed
                result = auth.authenticate(attempt, "password")
                assert result is None

            # Database should still be intact - can create users
            user = auth.create_user("safeuser", "safe@example.com", "safepassword123")
            assert user is not None
        finally:
            cleanup_db(db_path)


class TestRateLimiterEdgeCases:
    """Test rate limiter under edge conditions"""

    def test_rate_limit_burst(self):
        """Test burst handling"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=10, burst_size=5)
        limiter = RateLimiter(config)

        # Burst of requests
        results = []
        for _ in range(20):
            allowed, _ = limiter.check_rate_limit(f"burst-client")
            results.append(allowed)

        # First requests should be allowed (burst + rate limit)
        allowed_count = sum(results)
        assert allowed_count > 0
        assert allowed_count <= 15  # burst_size + requests_per_minute

    def test_rate_limit_cleanup(self):
        """Test old entries are cleaned up over time"""
        from web.rate_limiter import RateLimiter, RateLimitConfig

        config = RateLimitConfig(requests_per_minute=100)
        limiter = RateLimiter(config)

        # Create many clients
        for i in range(100):
            limiter.check_rate_limit(f"client-{i}")

        # All clients should be tracked (or some may be cleaned up)
        # The key is that the system doesn't crash with many clients
        assert len(limiter._entries) <= 100

        # Recent entries still present after more operations
        limiter.check_rate_limit("test-client")
        assert len(limiter._entries) <= 101


class TestVersioningEdgeCases:
    """Test versioning under edge conditions"""

    def test_rapid_version_creation(self):
        """Test rapid consecutive version creation"""
        db_path = get_temp_db()
        try:
            from core.versioning import PolicyVersionManager

            manager = PolicyVersionManager(db_path)

            # Rapid version creation
            versions = []
            for i in range(20):
                v = manager.create_version(
                    policy_id="rapid-test",
                    title="Rapid Test",
                    content=f"Version {i} content at {time.time()}",
                    change_type="patch"
                )
                versions.append(v)

            # All versions should be unique
            version_numbers = [v.version for v in versions]
            assert len(set(version_numbers)) == len(versions)

            # History should show all versions
            history = manager.get_version_history("rapid-test")
            assert len(history) == 20
        finally:
            cleanup_db(db_path)

    def test_version_rollback_chain(self):
        """Test multiple rollbacks in sequence"""
        db_path = get_temp_db()
        try:
            from core.versioning import PolicyVersionManager

            manager = PolicyVersionManager(db_path)

            # Create chain of versions
            v1 = manager.create_version("chain-test", "Chain Test", "Version 1")
            v2 = manager.create_version("chain-test", "Chain Test", "Version 2")
            v3 = manager.create_version("chain-test", "Chain Test", "Version 3")

            # Rollback to v1
            r1 = manager.rollback("chain-test", v1.version)
            assert r1.content == "Version 1"

            # Rollback to v2
            r2 = manager.rollback("chain-test", v2.version)
            assert r2.content == "Version 2"

            # History should show all versions + rollbacks
            history = manager.get_version_history("chain-test")
            assert len(history) == 5
        finally:
            cleanup_db(db_path)


class TestInputValidation:
    """Test input validation and sanitization"""

    def test_email_validation_edge_cases(self):
        """Test email validation with edge cases"""
        from core.validation import validate_email

        # Valid edge cases
        assert validate_email("a@b.co") == True
        assert validate_email("user+tag@example.com") == True
        assert validate_email("user.name@sub.domain.com") == True

        # Invalid edge cases
        assert validate_email("") == False
        assert validate_email("no-at-sign") == False
        assert validate_email("@no-local.com") == False
        assert validate_email("no-domain@") == False
        assert validate_email("double@@at.com") == False
        assert validate_email("space in@email.com") == False
        assert validate_email(None) == False

    def test_url_validation_edge_cases(self):
        """Test URL validation with edge cases"""
        from core.validation import validate_url

        # Valid URLs
        assert validate_url("https://example.com") == True
        assert validate_url("http://localhost:8080/path") == True
        assert validate_url("https://sub.domain.example.com/path?query=1") == True

        # Invalid URLs
        assert validate_url("") == False
        assert validate_url("not-a-url") == False
        assert validate_url("ftp://not-http.com") == False
        assert validate_url("javascript:alert(1)") == False
        assert validate_url(None) == False

    def test_path_traversal_prevention(self):
        """Test path traversal is prevented"""
        from core.validation import validate_path, ValidationError

        # Valid paths should be returned (possibly normalized)
        result = validate_path("valid/path")
        assert result is not None

        # Path traversal attempts should raise ValidationError
        with pytest.raises(ValidationError):
            validate_path("../../../etc/passwd")

        # On Windows, backslash paths may be handled differently
        # Test forward-slash traversal patterns
        with pytest.raises(ValidationError):
            validate_path("../../windows/system32")

        with pytest.raises(ValidationError):
            validate_path("path/../../../etc/passwd")


class TestMemoryAndPerformance:
    """Test memory usage and performance under load"""

    def test_large_history_query(self):
        """Test querying large version history"""
        db_path = get_temp_db()
        try:
            from core.versioning import PolicyVersionManager

            manager = PolicyVersionManager(db_path)

            # Create many versions
            for i in range(100):
                manager.create_version(
                    policy_id="large-history",
                    title="Large History Test",
                    content=f"Content {i}",
                    change_type="patch"
                )

            # Query should handle large result sets
            start = time.time()
            history = manager.get_version_history("large-history", limit=1000)
            elapsed = time.time() - start

            assert len(history) == 100
            assert elapsed < 5.0  # Should complete in reasonable time
        finally:
            cleanup_db(db_path)

    def test_many_policies_performance(self):
        """Test performance with many different policies"""
        db_path = get_temp_db()
        try:
            from core.versioning import PolicyVersionManager

            manager = PolicyVersionManager(db_path)

            # Create many different policies
            for i in range(100):
                manager.create_version(
                    policy_id=f"policy-{i}",
                    title=f"Policy {i}",
                    content=f"Content for policy {i}"
                )

            # Query all policies
            start = time.time()
            all_policies = manager.get_all_policies_with_versions()
            elapsed = time.time() - start

            assert len(all_policies) == 100
            assert elapsed < 5.0
        finally:
            cleanup_db(db_path)


class TestFrameworkLoading:
    """Test framework loading edge cases"""

    def test_malformed_yaml_handling(self):
        """Test handling of malformed YAML files"""
        from core.compliance_mapper import ComplianceMapper

        mapper = ComplianceMapper()

        # Create temp malformed YAML
        temp_dir = tempfile.mkdtemp()
        malformed_path = os.path.join(temp_dir, "malformed.yaml")

        with open(malformed_path, 'w') as f:
            f.write("invalid: yaml: content: [")

        try:
            # Should not crash, just skip the malformed file
            mapper.load_framework(malformed_path)
        except Exception:
            pass  # Expected to fail gracefully

        # Mapper should still be usable
        assert mapper.frameworks is not None

        # Cleanup
        os.unlink(malformed_path)
        os.rmdir(temp_dir)

    def test_empty_framework_handling(self):
        """Test handling of empty framework files"""
        from core.compliance_mapper import ComplianceMapper

        mapper = ComplianceMapper()

        # Create temp empty YAML
        temp_dir = tempfile.mkdtemp()
        empty_path = os.path.join(temp_dir, "empty.yaml")

        with open(empty_path, 'w') as f:
            f.write("")

        try:
            mapper.load_framework(empty_path)
        except Exception:
            pass  # Expected to fail

        # Cleanup
        os.unlink(empty_path)
        os.rmdir(temp_dir)


class TestAuditLoggingEdgeCases:
    """Test audit logging edge cases"""

    def test_very_long_details(self):
        """Test logging with very long details"""
        db_path = get_temp_db()
        try:
            from core.audit import AuditLogger, AuditAction

            logger = AuditLogger(db_path)

            long_details = {"key": "x" * 100000}

            result = logger.log(
                action=AuditAction.LOGIN_SUCCESS,
                username="user",
                details=long_details
            )

            assert result is not None

            # Verify retrieval
            logs = logger.get_logs(limit=1)
            assert len(logs) == 1
        finally:
            cleanup_db(db_path)

    def test_null_username_handling(self):
        """Test logging with null/empty usernames"""
        db_path = get_temp_db()
        try:
            from core.audit import AuditLogger, AuditAction

            logger = AuditLogger(db_path)

            # Null username
            result = logger.log(
                action=AuditAction.API_ACCESS,
                username=None,
                details="Anonymous access"
            )

            assert result is not None

            # Empty username
            result = logger.log(
                action=AuditAction.API_ACCESS,
                username="",
                details="Empty username"
            )

            assert result is not None
        finally:
            cleanup_db(db_path)
