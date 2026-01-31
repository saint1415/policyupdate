"""
Audit Logging Module
Comprehensive audit trail for all system actions
"""

import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    from core.config import get_logger
    logger = get_logger('core.audit')
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AuditAction(Enum):
    """Types of auditable actions"""
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGIN_FAILURE = "auth.login.failed"  # Alias for compatibility
    LOGIN_ATTEMPT = "auth.login.attempt"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGE = "auth.password.change"
    PASSWORD_RESET = "auth.password.reset"

    # User Management
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_LOCK = "user.lock"
    USER_UNLOCK = "user.unlock"

    # Client Management
    CLIENT_CREATE = "client.create"
    CLIENT_UPDATE = "client.update"
    CLIENT_DELETE = "client.delete"
    CLIENT_VARIABLE_SET = "client.variable.set"

    # Policy Generation
    PACKAGE_GENERATE = "package.generate"
    PACKAGE_EXPORT_DOCX = "package.export.docx"
    PACKAGE_EXPORT_PDF = "package.export.pdf"
    PACKAGE_EXPORT_HTML = "package.export.html"
    PACKAGE_EXPORT_MARKDOWN = "package.export.markdown"

    # Policy Management
    POLICY_VIEW = "policy.view"
    POLICY_CREATE = "policy.create"
    POLICY_UPDATE = "policy.update"
    POLICY_DELETE = "policy.delete"
    POLICY_VERSION = "policy.version"

    # Framework Management
    FRAMEWORK_VIEW = "framework.view"
    FRAMEWORK_ANALYSIS = "framework.analysis"

    # Monitoring
    FEED_CHECK = "monitor.feed.check"
    ALERT_CREATE = "monitor.alert.create"
    ALERT_ACKNOWLEDGE = "monitor.alert.acknowledge"
    ALERT_RESOLVE = "monitor.alert.resolve"

    # System
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_CONFIG_CHANGE = "system.config.change"
    SYSTEM_BACKUP = "system.backup"
    SYSTEM_RESTORE = "system.restore"

    # API Access
    API_ACCESS = "api.access"
    API_ERROR = "api.error"


class AuditSeverity(Enum):
    """Severity levels for audit events"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Represents a single audit log entry"""
    id: str
    timestamp: datetime
    action: str
    severity: str
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    resource_type: Optional[str]
    resource_id: Optional[str]
    details: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


class AuditLogger:
    """
    Comprehensive audit logging system.

    Features:
    - Tracks all user actions
    - Records authentication events
    - Logs policy generation and exports
    - Monitors system changes
    - Supports search and filtering
    - Retention policy enforcement
    """

    DEFAULT_RETENTION_DAYS = 365

    def __init__(self, db_path: str, retention_days: int = None):
        self.db_path = db_path
        self.retention_days = retention_days or self.DEFAULT_RETENTION_DAYS
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize the audit database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    action TEXT NOT NULL,
                    severity TEXT DEFAULT 'info',
                    user_id TEXT,
                    username TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    success INTEGER DEFAULT 1,
                    error_message TEXT
                )
            """)

            # Create indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id)")

            conn.commit()

    def log(self, action: AuditAction, user_id: str = None, username: str = None,
            ip_address: str = None, user_agent: str = None, resource_type: str = None,
            resource_id: str = None, details: Dict = None, success: bool = True,
            error_message: str = None, severity: AuditSeverity = AuditSeverity.INFO) -> str:
        """
        Log an audit event.

        Args:
            action: The type of action being logged
            user_id: ID of the user performing the action
            username: Username of the user
            ip_address: IP address of the request
            user_agent: User agent string
            resource_type: Type of resource affected (client, policy, etc.)
            resource_id: ID of the affected resource
            details: Additional details as dictionary
            success: Whether the action was successful
            error_message: Error message if action failed
            severity: Severity level of the event

        Returns:
            ID of the created audit entry
        """
        import secrets

        entry_id = secrets.token_hex(16)
        timestamp = datetime.now()

        action_str = action.value if isinstance(action, AuditAction) else action
        severity_str = severity.value if isinstance(severity, AuditSeverity) else severity
        details_json = json.dumps(details or {})

        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO audit_logs
                (id, timestamp, action, severity, user_id, username, ip_address,
                 user_agent, resource_type, resource_id, details, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (entry_id, timestamp.isoformat(), action_str, severity_str,
                  user_id, username, ip_address, user_agent, resource_type,
                  resource_id, details_json, 1 if success else 0, error_message))
            conn.commit()

        # Also log to application logger
        log_method = getattr(logger, severity_str, logger.info)
        log_method(f"AUDIT: {action_str} user={username} resource={resource_type}:{resource_id} success={success}")

        return entry_id

    def get_entries(self, start_date: datetime = None, end_date: datetime = None,
                   action: str = None, user_id: str = None, resource_type: str = None,
                   resource_id: str = None, success: bool = None, severity: str = None,
                   limit: int = 100, offset: int = 0) -> List[AuditEntry]:
        """
        Query audit log entries with filters.

        Args:
            start_date: Start of date range
            end_date: End of date range
            action: Filter by action type
            user_id: Filter by user
            resource_type: Filter by resource type
            resource_id: Filter by specific resource
            success: Filter by success/failure
            severity: Filter by severity level
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            List of AuditEntry objects
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date.isoformat())

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date.isoformat())

        if action:
            query += " AND action = ?"
            params.append(action)

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)

        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)

        if success is not None:
            query += " AND success = ?"
            params.append(1 if success else 0)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            return [self._row_to_entry(row) for row in cursor.fetchall()]

    def get_logs(self, limit: int = 100, offset: int = 0, username: str = None,
                 action_filter: str = None) -> List[Dict]:
        """
        Get audit logs in dictionary format for API compatibility.

        Args:
            limit: Maximum number of entries
            offset: Number of entries to skip
            username: Filter by username
            action_filter: Filter by action (substring match)

        Returns:
            List of log entries as dictionaries
        """
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []

        if username:
            query += " AND username = ?"
            params.append(username)

        if action_filter:
            query += " AND UPPER(action) LIKE UPPER(?)"
            params.append(f"%{action_filter}%")

        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_conn() as conn:
            cursor = conn.execute(query, params)
            results = []
            for row in cursor.fetchall():
                entry = self._row_to_entry(row)
                results.append(entry.to_dict())
            return results

    def _row_to_entry(self, row) -> AuditEntry:
        """Convert database row to AuditEntry"""
        return AuditEntry(
            id=row['id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            action=row['action'],
            severity=row['severity'],
            user_id=row['user_id'],
            username=row['username'],
            ip_address=row['ip_address'],
            user_agent=row['user_agent'],
            resource_type=row['resource_type'],
            resource_id=row['resource_id'],
            details=json.loads(row['details']) if row['details'] else {},
            success=bool(row['success']),
            error_message=row['error_message']
        )

    def get_entry(self, entry_id: str) -> Optional[AuditEntry]:
        """Get a specific audit entry by ID"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM audit_logs WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_entry(row)
        return None

    def get_user_activity(self, user_id: str, days: int = 30) -> List[AuditEntry]:
        """Get recent activity for a specific user"""
        start_date = datetime.now() - timedelta(days=days)
        return self.get_entries(start_date=start_date, user_id=user_id, limit=500)

    def get_resource_history(self, resource_type: str, resource_id: str) -> List[AuditEntry]:
        """Get all audit entries for a specific resource"""
        return self.get_entries(resource_type=resource_type, resource_id=resource_id, limit=1000)

    def get_failed_logins(self, hours: int = 24) -> List[AuditEntry]:
        """Get recent failed login attempts"""
        start_date = datetime.now() - timedelta(hours=hours)
        return self.get_entries(
            start_date=start_date,
            action=AuditAction.LOGIN_FAILED.value,
            limit=500
        )

    def get_statistics(self, days: int = 30) -> Dict:
        """Get audit statistics for dashboard"""
        start_date = datetime.now() - timedelta(days=days)

        with self._get_conn() as conn:
            # Total events
            cursor = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ?",
                (start_date.isoformat(),)
            )
            total_events = cursor.fetchone()[0]

            # Events by action
            cursor = conn.execute("""
                SELECT action, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ?
                GROUP BY action
                ORDER BY count DESC
                LIMIT 10
            """, (start_date.isoformat(),))
            by_action = {row['action']: row['count'] for row in cursor.fetchall()}

            # Events by user
            cursor = conn.execute("""
                SELECT username, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ? AND username IS NOT NULL
                GROUP BY username
                ORDER BY count DESC
                LIMIT 10
            """, (start_date.isoformat(),))
            by_user = {row['username']: row['count'] for row in cursor.fetchall()}

            # Failed events
            cursor = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE timestamp >= ? AND success = 0",
                (start_date.isoformat(),)
            )
            failed_events = cursor.fetchone()[0]

            # Events by severity
            cursor = conn.execute("""
                SELECT severity, COUNT(*) as count
                FROM audit_logs
                WHERE timestamp >= ?
                GROUP BY severity
            """, (start_date.isoformat(),))
            by_severity = {row['severity']: row['count'] for row in cursor.fetchall()}

        return {
            'total_events': total_events,
            'failed_events': failed_events,
            'by_action': by_action,
            'by_user': by_user,
            'by_severity': by_severity,
            'period_days': days
        }

    def enforce_retention(self, retention_days: int = None) -> int:
        """
        Delete audit entries older than retention period.

        Args:
            retention_days: Number of days to retain (default: 365)

        Returns:
            Number of entries deleted
        """
        if retention_days is None:
            retention_days = self.DEFAULT_RETENTION_DAYS

        cutoff_date = datetime.now() - timedelta(days=retention_days)

        with self._get_conn() as conn:
            cursor = conn.execute(
                "DELETE FROM audit_logs WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            deleted = cursor.rowcount
            conn.commit()

        if deleted > 0:
            logger.info(f"Audit retention: deleted {deleted} entries older than {retention_days} days")

        return deleted

    def export_to_json(self, filepath: str, start_date: datetime = None,
                       end_date: datetime = None) -> int:
        """
        Export audit logs to JSON file.

        Args:
            filepath: Path to output file
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Number of entries exported
        """
        entries = self.get_entries(start_date=start_date, end_date=end_date, limit=100000)

        output = {
            'exported_at': datetime.now().isoformat(),
            'total_entries': len(entries),
            'entries': [e.to_dict() for e in entries]
        }

        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2)

        logger.info(f"Exported {len(entries)} audit entries to {filepath}")
        return len(entries)

    def export_logs(self, filepath: str, format: str = 'json',
                    start_date: datetime = None, end_date: datetime = None) -> int:
        """
        Export audit logs to file.

        Args:
            filepath: Path to output file
            format: Output format ('json' or 'csv')
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Number of entries exported
        """
        if format == 'json':
            return self.export_to_json(filepath, start_date, end_date)
        elif format == 'csv':
            import csv
            entries = self.get_entries(start_date=start_date, end_date=end_date, limit=100000)
            with open(filepath, 'w', newline='') as f:
                if entries:
                    writer = csv.DictWriter(f, fieldnames=entries[0].to_dict().keys())
                    writer.writeheader()
                    for entry in entries:
                        writer.writerow(entry.to_dict())
            return len(entries)
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(db_path: str = None) -> AuditLogger:
    """Get the global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        if db_path is None:
            from core.config import get_config
            config = get_config()
            db_path = str(config.get_data_path() / "audit.db")
        _audit_logger = AuditLogger(db_path)
    return _audit_logger


def audit_log(action: AuditAction, **kwargs) -> str:
    """Convenience function to log an audit event"""
    return get_audit_logger().log(action, **kwargs)
