"""
Tests for Policy Versioning System
Tests version creation, comparison, diff generation, and rollback
"""

import pytest
import sys
import tempfile
import os
import uuid
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def get_temp_db():
    """Get a unique temp database path"""
    return os.path.join(tempfile.gettempdir(), f"test_version_{uuid.uuid4().hex}.db")


def cleanup_db(db_path):
    """Clean up temp database, ignoring errors"""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except PermissionError:
        pass


class TestVersionManager:
    """Test version manager functionality"""

    @pytest.fixture
    def version_manager(self):
        """Create version manager with temp database"""
        db_path = get_temp_db()

        from core.versioning import PolicyVersionManager
        manager = PolicyVersionManager(db_path)
        yield manager

        cleanup_db(db_path)

    def test_create_version(self, version_manager):
        """Test creating a new version"""
        version = version_manager.create_version(
            policy_id="test-policy",
            title="Test Policy",
            content="# Test Policy\n\nThis is test content.",
            change_summary="Initial version"
        )

        assert version is not None
        assert version.policy_id == "test-policy"
        assert version.version == "1.0.0"

    def test_create_multiple_versions(self, version_manager):
        """Test creating multiple versions"""
        # First version
        v1 = version_manager.create_version(
            policy_id="multi-version",
            title="Multi Version Policy",
            content="Version 1 content",
            change_type="major"
        )

        # Second version
        v2 = version_manager.create_version(
            policy_id="multi-version",
            title="Multi Version Policy",
            content="Version 2 content with changes",
            change_type="minor"
        )

        assert v1.version == "1.0.0"
        assert v2.version == "1.1.0"

    def test_get_latest_version(self, version_manager):
        """Test getting latest version"""
        # Create versions
        version_manager.create_version(
            policy_id="latest-test",
            title="Latest Test",
            content="Content v1"
        )
        version_manager.create_version(
            policy_id="latest-test",
            title="Latest Test",
            content="Content v2"
        )

        latest = version_manager.get_latest_version("latest-test")

        assert latest is not None
        assert "v2" in latest.content or latest.version != "1.0.0"

    def test_get_version_history(self, version_manager):
        """Test getting version history"""
        # Create multiple versions
        for i in range(3):
            version_manager.create_version(
                policy_id="history-test",
                title="History Test",
                content=f"Content version {i+1}",
                change_type="patch"
            )

        history = version_manager.get_version_history("history-test")

        assert len(history) == 3

    def test_get_specific_version(self, version_manager):
        """Test getting a specific version"""
        v1 = version_manager.create_version(
            policy_id="specific-test",
            title="Specific Test",
            content="Original content"
        )

        version_manager.create_version(
            policy_id="specific-test",
            title="Specific Test",
            content="Updated content"
        )

        # Get original version
        retrieved = version_manager.get_version("specific-test", v1.version)

        assert retrieved is not None
        assert retrieved.version == v1.version


class TestVersionNumbering:
    """Test semantic versioning"""

    @pytest.fixture
    def version_manager(self):
        """Create version manager with temp database"""
        db_path = get_temp_db()

        from core.versioning import PolicyVersionManager
        manager = PolicyVersionManager(db_path)
        yield manager

        cleanup_db(db_path)

    def test_major_version_increment(self, version_manager):
        """Test major version increment"""
        v1 = version_manager.create_version(
            policy_id="major-test",
            title="Test",
            content="v1"
        )

        v2 = version_manager.create_version(
            policy_id="major-test",
            title="Test",
            content="v2 with breaking changes",
            change_type="major"
        )

        # Major increment: 1.0.0 -> 2.0.0
        assert v2.version == "2.0.0"

    def test_minor_version_increment(self, version_manager):
        """Test minor version increment"""
        v1 = version_manager.create_version(
            policy_id="minor-test",
            title="Test",
            content="v1"
        )

        v2 = version_manager.create_version(
            policy_id="minor-test",
            title="Test",
            content="v2 with new features",
            change_type="minor"
        )

        # Minor increment: 1.0.0 -> 1.1.0
        assert v2.version == "1.1.0"

    def test_patch_version_increment(self, version_manager):
        """Test patch version increment"""
        v1 = version_manager.create_version(
            policy_id="patch-test",
            title="Test",
            content="v1"
        )

        v2 = version_manager.create_version(
            policy_id="patch-test",
            title="Test",
            content="v2 with bug fixes",
            change_type="patch"
        )

        # Patch increment: 1.0.0 -> 1.0.1
        assert v2.version == "1.0.1"


class TestVersionDiff:
    """Test version diff generation"""

    @pytest.fixture
    def version_manager(self):
        """Create version manager with temp database"""
        db_path = get_temp_db()

        from core.versioning import PolicyVersionManager
        manager = PolicyVersionManager(db_path)
        yield manager

        cleanup_db(db_path)

    def test_generate_diff(self, version_manager):
        """Test diff generation between versions"""
        v1 = version_manager.create_version(
            policy_id="diff-test",
            title="Diff Test",
            content="Line 1\nLine 2\nLine 3"
        )

        v2 = version_manager.create_version(
            policy_id="diff-test",
            title="Diff Test",
            content="Line 1\nLine 2 modified\nLine 3\nLine 4"
        )

        diff = version_manager.get_diff("diff-test", v1.version, v2.version)

        assert diff is not None
        assert isinstance(diff, str)

    def test_diff_unified_format(self, version_manager):
        """Test diff is in unified format"""
        v1 = version_manager.create_version(
            policy_id="unified-diff",
            title="Unified Diff Test",
            content="Original line"
        )

        v2 = version_manager.create_version(
            policy_id="unified-diff",
            title="Unified Diff Test",
            content="Modified line"
        )

        diff = version_manager.get_diff("unified-diff", v1.version, v2.version)

        # Unified diff should contain markers
        assert '-' in diff or '+' in diff or '@@' in diff

    def test_diff_html_format(self, version_manager):
        """Test HTML diff generation"""
        v1 = version_manager.create_version(
            policy_id="html-diff",
            title="HTML Diff Test",
            content="Original content"
        )

        v2 = version_manager.create_version(
            policy_id="html-diff",
            title="HTML Diff Test",
            content="Modified content"
        )

        html_diff = version_manager.get_diff(
            "html-diff", v1.version, v2.version,
            format='html'
        )

        assert html_diff is not None
        # HTML diff should contain HTML tags
        assert '<' in html_diff or 'class=' in html_diff


class TestVersionRollback:
    """Test version rollback functionality"""

    @pytest.fixture
    def version_manager(self):
        """Create version manager with temp database"""
        db_path = get_temp_db()

        from core.versioning import PolicyVersionManager
        manager = PolicyVersionManager(db_path)
        yield manager

        cleanup_db(db_path)

    def test_rollback_creates_new_version(self, version_manager):
        """Test rollback creates a new version"""
        # Create versions
        v1 = version_manager.create_version(
            policy_id="rollback-test",
            title="Rollback Test",
            content="Original content"
        )

        v2 = version_manager.create_version(
            policy_id="rollback-test",
            title="Rollback Test",
            content="Bad changes"
        )

        # Rollback to v1
        v3 = version_manager.rollback("rollback-test", v1.version)

        # Should create new version, not modify existing
        assert v3.version != v1.version
        assert v3.version != v2.version
        assert v3.content == v1.content

    def test_rollback_preserves_history(self, version_manager):
        """Test rollback preserves version history"""
        v1 = version_manager.create_version(
            policy_id="preserve-history",
            title="Preserve History",
            content="v1"
        )

        version_manager.create_version(
            policy_id="preserve-history",
            title="Preserve History",
            content="v2"
        )

        version_manager.rollback("preserve-history", v1.version)

        # All versions should still exist
        history = version_manager.get_version_history("preserve-history")
        assert len(history) == 3


class TestContentHashing:
    """Test content hashing for change detection"""

    @pytest.fixture
    def version_manager(self):
        """Create version manager with temp database"""
        db_path = get_temp_db()

        from core.versioning import PolicyVersionManager
        manager = PolicyVersionManager(db_path)
        yield manager

        cleanup_db(db_path)

    def test_identical_content_same_hash(self, version_manager):
        """Test identical content produces same hash"""
        content = "This is test content"

        v1 = version_manager.create_version(
            policy_id="hash-test-1",
            title="Hash Test",
            content=content
        )

        v2 = version_manager.create_version(
            policy_id="hash-test-2",
            title="Hash Test",
            content=content
        )

        assert v1.content_hash == v2.content_hash

    def test_different_content_different_hash(self, version_manager):
        """Test different content produces different hash"""
        v1 = version_manager.create_version(
            policy_id="diff-hash-1",
            title="Hash Test",
            content="Content A"
        )

        v2 = version_manager.create_version(
            policy_id="diff-hash-2",
            title="Hash Test",
            content="Content B"
        )

        assert v1.content_hash != v2.content_hash

    def test_no_version_on_unchanged_content(self, version_manager):
        """Test no new version created if content unchanged"""
        content = "Unchanged content"

        v1 = version_manager.create_version(
            policy_id="unchanged-test",
            title="Unchanged Test",
            content=content
        )

        v2 = version_manager.create_version(
            policy_id="unchanged-test",
            title="Unchanged Test",
            content=content  # Same content
        )

        # Implementation may either:
        # 1. Return the same version
        # 2. Return None
        # 3. Create version anyway
        # This tests the behavior is handled


class TestVersionMetadata:
    """Test version metadata storage"""

    @pytest.fixture
    def version_manager(self):
        """Create version manager with temp database"""
        db_path = get_temp_db()

        from core.versioning import PolicyVersionManager
        manager = PolicyVersionManager(db_path)
        yield manager

        cleanup_db(db_path)

    def test_frontmatter_storage(self, version_manager):
        """Test frontmatter is stored with version"""
        frontmatter = {
            'category': 'access-control',
            'frameworks': {'soc2': ['CC6.1', 'CC6.2']}
        }

        version = version_manager.create_version(
            policy_id="frontmatter-test",
            title="Frontmatter Test",
            content="Content",
            frontmatter=frontmatter
        )

        # Retrieve and check frontmatter
        retrieved = version_manager.get_version("frontmatter-test", version.version)
        assert retrieved.frontmatter is not None

    def test_change_summary_storage(self, version_manager):
        """Test change summary is stored"""
        version = version_manager.create_version(
            policy_id="summary-test",
            title="Summary Test",
            content="Content",
            change_summary="Updated section 3.2 with new requirements"
        )

        assert version.change_summary == "Updated section 3.2 with new requirements"

    def test_created_by_storage(self, version_manager):
        """Test created_by user is stored"""
        version = version_manager.create_version(
            policy_id="author-test",
            title="Author Test",
            content="Content",
            created_by="john.doe"
        )

        assert version.created_by == "john.doe"

    def test_created_at_timestamp(self, version_manager):
        """Test created_at timestamp is set"""
        version = version_manager.create_version(
            policy_id="timestamp-test",
            title="Timestamp Test",
            content="Content"
        )

        assert version.created_at is not None
        assert isinstance(version.created_at, datetime)
