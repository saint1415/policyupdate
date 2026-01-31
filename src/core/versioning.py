"""
Policy Versioning Module
Track changes to policies over time with version history and diff capability
"""

import difflib
import hashlib
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

try:
    from core.config import get_logger
    logger = get_logger('core.versioning')
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class PolicyVersion:
    """Represents a specific version of a policy"""
    id: str
    policy_id: str
    version_number: str  # Semantic version: 1.0.0, 1.1.0, etc.
    created_at: datetime
    created_by: Optional[str]
    title: str
    content: str
    content_hash: str
    frontmatter: Dict[str, Any]
    change_summary: str
    change_type: str  # major, minor, patch
    is_current: bool
    parent_version_id: Optional[str] = None

    @property
    def version(self) -> str:
        """Alias for version_number for convenience"""
        return self.version_number

    def to_dict(self) -> Dict:
        d = asdict(self)
        d['created_at'] = self.created_at.isoformat()
        return d


@dataclass
class VersionDiff:
    """Represents the difference between two policy versions"""
    old_version: str
    new_version: str
    policy_id: str
    added_lines: int
    removed_lines: int
    changed_lines: int
    diff_html: str
    diff_unified: str


class PolicyVersionManager:
    """
    Manages policy version history.

    Features:
    - Automatic version numbering (semantic versioning)
    - Content hashing to detect actual changes
    - Diff generation between versions
    - Version rollback capability
    - Change history tracking
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the versioning database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS policy_versions (
                    id TEXT PRIMARY KEY,
                    policy_id TEXT NOT NULL,
                    version_number TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    frontmatter TEXT,
                    change_summary TEXT,
                    change_type TEXT DEFAULT 'patch',
                    is_current INTEGER DEFAULT 0,
                    parent_version_id TEXT,
                    FOREIGN KEY (parent_version_id) REFERENCES policy_versions(id)
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_version_policy ON policy_versions(policy_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_version_current ON policy_versions(policy_id, is_current)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_version_hash ON policy_versions(content_hash)")

            conn.commit()

    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def _parse_version(self, version_str: str) -> Tuple[int, int, int]:
        """Parse semantic version string to tuple"""
        try:
            parts = version_str.split('.')
            return int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            return 1, 0, 0

    def _increment_version(self, current_version: str, change_type: str) -> str:
        """Increment version number based on change type"""
        major, minor, patch = self._parse_version(current_version)

        if change_type == 'major':
            return f"{major + 1}.0.0"
        elif change_type == 'minor':
            return f"{major}.{minor + 1}.0"
        else:  # patch
            return f"{major}.{minor}.{patch + 1}"

    def create_version(self, policy_id: str, title: str, content: str,
                       frontmatter: Dict = None, change_summary: str = "",
                       change_type: str = "patch", created_by: str = None) -> PolicyVersion:
        """
        Create a new version of a policy.

        Args:
            policy_id: Unique identifier for the policy
            title: Policy title
            content: Full policy content (Markdown)
            frontmatter: YAML frontmatter as dictionary
            change_summary: Description of changes
            change_type: 'major', 'minor', or 'patch'
            created_by: Username who made the change

        Returns:
            The created PolicyVersion
        """
        import secrets

        content_hash = self._compute_hash(content)

        # Check if content actually changed
        current = self.get_current_version(policy_id)
        if current and current.content_hash == content_hash:
            logger.debug(f"No changes detected for policy {policy_id}")
            return current

        # Determine new version number
        if current:
            new_version = self._increment_version(current.version_number, change_type)
            parent_id = current.id
        else:
            new_version = "1.0.0"
            parent_id = None

        version_id = secrets.token_hex(16)
        frontmatter_json = json.dumps(frontmatter or {})

        with self._get_conn() as conn:
            # Mark previous version as not current
            if current:
                conn.execute(
                    "UPDATE policy_versions SET is_current = 0 WHERE policy_id = ?",
                    (policy_id,)
                )

            # Insert new version
            conn.execute("""
                INSERT INTO policy_versions
                (id, policy_id, version_number, created_by, title, content,
                 content_hash, frontmatter, change_summary, change_type,
                 is_current, parent_version_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (version_id, policy_id, new_version, created_by, title, content,
                  content_hash, frontmatter_json, change_summary, change_type, parent_id))

            conn.commit()

        logger.info(f"Created version {new_version} for policy {policy_id}")
        return self.get_version(version_id)

    def get_version(self, policy_id_or_version_id: str, version_number: str = None) -> Optional[PolicyVersion]:
        """
        Get a specific version.

        Can be called as:
        - get_version(version_id) - Get by version ID
        - get_version(policy_id, version_number) - Get by policy ID and version number
        """
        if version_number is not None:
            # Called with policy_id and version_number
            return self.get_version_by_number(policy_id_or_version_id, version_number)

        # Called with just version_id
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM policy_versions WHERE id = ?", (policy_id_or_version_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_version(row)
        return None

    def get_current_version(self, policy_id: str) -> Optional[PolicyVersion]:
        """Get the current version of a policy"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM policy_versions WHERE policy_id = ? AND is_current = 1",
                (policy_id,)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_version(row)
        return None

    def get_latest_version(self, policy_id: str) -> Optional[PolicyVersion]:
        """Alias for get_current_version for convenience"""
        return self.get_current_version(policy_id)

    def get_version_by_number(self, policy_id: str, version_number: str) -> Optional[PolicyVersion]:
        """Get a specific version by policy ID and version number"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM policy_versions WHERE policy_id = ? AND version_number = ?",
                (policy_id, version_number)
            )
            row = cursor.fetchone()
            if row:
                return self._row_to_version(row)
        return None

    def _row_to_version(self, row) -> PolicyVersion:
        """Convert database row to PolicyVersion"""
        return PolicyVersion(
            id=row['id'],
            policy_id=row['policy_id'],
            version_number=row['version_number'],
            created_at=datetime.fromisoformat(row['created_at']),
            created_by=row['created_by'],
            title=row['title'],
            content=row['content'],
            content_hash=row['content_hash'],
            frontmatter=json.loads(row['frontmatter']) if row['frontmatter'] else {},
            change_summary=row['change_summary'] or "",
            change_type=row['change_type'] or "patch",
            is_current=bool(row['is_current']),
            parent_version_id=row['parent_version_id']
        )

    def get_version_history(self, policy_id: str, limit: int = 50) -> List[PolicyVersion]:
        """Get version history for a policy, newest first"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM policy_versions
                WHERE policy_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (policy_id, limit))
            return [self._row_to_version(row) for row in cursor.fetchall()]

    def get_diff(self, policy_id: str, version1: str, version2: str,
                  format: str = 'unified') -> Optional[str]:
        """
        Get diff between two versions of a policy.

        Args:
            policy_id: Policy ID
            version1: First version number (older)
            version2: Second version number (newer)
            format: 'unified' or 'html'

        Returns:
            Diff as string in requested format
        """
        v1 = self.get_version_by_number(policy_id, version1)
        v2 = self.get_version_by_number(policy_id, version2)

        if not v1 or not v2:
            return None

        lines1 = v1.content.splitlines(keepends=True)
        lines2 = v2.content.splitlines(keepends=True)

        if format == 'html':
            return difflib.HtmlDiff().make_table(
                lines1, lines2,
                fromdesc=f"v{v1.version_number}",
                todesc=f"v{v2.version_number}",
                context=True,
                numlines=3
            )
        else:
            diff = list(difflib.unified_diff(
                lines1, lines2,
                fromfile=f"{v1.policy_id} v{v1.version_number}",
                tofile=f"{v2.policy_id} v{v2.version_number}",
                lineterm=""
            ))
            return '\n'.join(diff)

    def compare_versions(self, version_id_1: str, version_id_2: str) -> Optional[VersionDiff]:
        """
        Compare two versions and generate diff.

        Args:
            version_id_1: ID of first (older) version
            version_id_2: ID of second (newer) version

        Returns:
            VersionDiff object with diff information
        """
        v1 = self.get_version(version_id_1)
        v2 = self.get_version(version_id_2)

        if not v1 or not v2:
            return None

        # Generate unified diff
        lines1 = v1.content.splitlines(keepends=True)
        lines2 = v2.content.splitlines(keepends=True)

        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=f"{v1.policy_id} v{v1.version_number}",
            tofile=f"{v2.policy_id} v{v2.version_number}",
            lineterm=""
        ))

        # Count changes
        added = sum(1 for line in diff if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in diff if line.startswith('-') and not line.startswith('---'))

        # Generate HTML diff
        html_diff = difflib.HtmlDiff().make_table(
            lines1, lines2,
            fromdesc=f"v{v1.version_number}",
            todesc=f"v{v2.version_number}",
            context=True,
            numlines=3
        )

        return VersionDiff(
            old_version=v1.version_number,
            new_version=v2.version_number,
            policy_id=v1.policy_id,
            added_lines=added,
            removed_lines=removed,
            changed_lines=added + removed,
            diff_html=html_diff,
            diff_unified='\n'.join(diff)
        )

    def rollback(self, policy_id: str, target_version: str,
                 created_by: str = None) -> Optional[PolicyVersion]:
        """
        Rollback a policy to a previous version.

        This creates a new version with the content from the target version,
        preserving the version history.

        Args:
            policy_id: Policy to rollback
            target_version: Version number (e.g., "1.0.0") or version ID to rollback to
            created_by: Username performing rollback

        Returns:
            The new version created from rollback
        """
        # Try to get by version number first, then by ID
        target = self.get_version_by_number(policy_id, target_version)
        if not target:
            target = self.get_version(target_version)
        if not target or target.policy_id != policy_id:
            logger.error(f"Cannot rollback: invalid version {target_version}")
            return None

        current = self.get_current_version(policy_id)
        if not current:
            logger.error(f"Cannot rollback: no current version for {policy_id}")
            return None

        # Create new version with content from target
        new_version = self.create_version(
            policy_id=policy_id,
            title=target.title,
            content=target.content,
            frontmatter=target.frontmatter,
            change_summary=f"Rollback to version {target.version_number}",
            change_type="minor",
            created_by=created_by
        )

        logger.info(f"Rolled back {policy_id} from {current.version_number} to {target.version_number}")
        return new_version

    def get_all_policies_with_versions(self) -> List[Dict]:
        """Get list of all policies with their current version info"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT policy_id, version_number, title, created_at, created_by
                FROM policy_versions
                WHERE is_current = 1
                ORDER BY policy_id
            """)

            return [{
                'policy_id': row['policy_id'],
                'current_version': row['version_number'],
                'title': row['title'],
                'last_modified': row['created_at'],
                'last_modified_by': row['created_by']
            } for row in cursor.fetchall()]

    def get_recent_changes(self, days: int = 30, limit: int = 50) -> List[PolicyVersion]:
        """Get recently changed policies"""
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=days)

        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM policy_versions
                WHERE created_at >= ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (cutoff.isoformat(), limit))

            return [self._row_to_version(row) for row in cursor.fetchall()]

    def get_statistics(self) -> Dict:
        """Get versioning statistics"""
        with self._get_conn() as conn:
            # Total versions
            cursor = conn.execute("SELECT COUNT(*) FROM policy_versions")
            total_versions = cursor.fetchone()[0]

            # Unique policies
            cursor = conn.execute("SELECT COUNT(DISTINCT policy_id) FROM policy_versions")
            total_policies = cursor.fetchone()[0]

            # Versions by change type
            cursor = conn.execute("""
                SELECT change_type, COUNT(*) as count
                FROM policy_versions
                GROUP BY change_type
            """)
            by_change_type = {row['change_type']: row['count'] for row in cursor.fetchall()}

            # Recent activity (last 30 days)
            from datetime import timedelta
            cutoff = datetime.now() - timedelta(days=30)
            cursor = conn.execute(
                "SELECT COUNT(*) FROM policy_versions WHERE created_at >= ?",
                (cutoff.isoformat(),)
            )
            recent_changes = cursor.fetchone()[0]

        return {
            'total_versions': total_versions,
            'total_policies': total_policies,
            'by_change_type': by_change_type,
            'recent_changes': recent_changes
        }


# Global version manager instance
_version_manager: Optional[PolicyVersionManager] = None


def get_version_manager(db_path: str = None) -> PolicyVersionManager:
    """Get the global version manager instance"""
    global _version_manager
    if _version_manager is None:
        if db_path is None:
            from core.config import get_config
            config = get_config()
            db_path = str(config.get_data_path() / "versions.db")
        _version_manager = PolicyVersionManager(db_path)
    return _version_manager
