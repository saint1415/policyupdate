"""
Change Detector Module
Analyzes feed items and framework updates to suggest policy changes

Detects:
- New framework versions
- Control updates
- Guidance changes
- Compliance deadline changes
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .feed_monitor import FeedMonitor, FeedItem


@dataclass
class PolicyImpact:
    """Describes the impact of a change on a policy"""
    policy_id: str
    impact_type: str  # update, review, new_requirement, deprecated
    severity: str  # critical, high, medium, low
    description: str
    suggested_action: str
    source_item_id: str
    frameworks: List[str] = field(default_factory=list)


@dataclass
class ChangeAlert:
    """An alert about a detected framework change"""
    id: str
    title: str
    description: str
    source_url: str
    detected_at: datetime
    change_type: str  # new_version, control_update, guidance, deadline
    frameworks_affected: List[str]
    policy_impacts: List[PolicyImpact]
    severity: str  # critical, high, medium, low
    status: str = "pending"  # pending, acknowledged, resolved, dismissed


class ChangeDetector:
    """
    Analyzes framework updates and detects changes that impact policies.

    Usage:
        detector = ChangeDetector()
        alerts = detector.analyze_recent_updates()
    """

    # Patterns that indicate different types of changes
    CHANGE_PATTERNS = {
        "new_version": [
            r"version\s*(\d+\.?\d*)",
            r"rev(?:ision)?\s*(\d+)",
            r"v(\d+\.?\d*)\s*released",
            r"updated?\s+to\s+(\d+\.?\d*)",
        ],
        "control_update": [
            r"control\s+(?:id\s+)?([A-Z]{2,3}[\.-]\d+[\.-]?\d*)",
            r"requirement\s+(\d+\.?\d*\.?\d*)",
            r"criterion\s+(CC\d+\.?\d*)",
            r"article\s+(\d+)",
        ],
        "deadline": [
            r"effective\s+(?:date\s+)?(\w+\s+\d+,?\s+\d{4})",
            r"compliance\s+deadline\s*[:is]*\s*(\w+\s+\d+,?\s+\d{4})",
            r"must\s+comply\s+by\s+(\w+\s+\d+,?\s+\d{4})",
            r"enforcement\s+begins?\s+(\w+\s+\d+,?\s+\d{4})",
        ],
        "guidance": [
            r"guidance\s+(?:on|for|about)",
            r"faq\s+(?:on|for|about)",
            r"clarification",
            r"interpretation",
            r"best\s+practice",
        ]
    }

    # Keywords that indicate severity
    SEVERITY_KEYWORDS = {
        "critical": [
            "mandatory", "required", "must", "deadline", "enforcement",
            "non-compliance", "penalty", "fine", "breach"
        ],
        "high": [
            "significant", "major", "important", "critical change",
            "new version", "compliance", "audit"
        ],
        "medium": [
            "update", "revision", "change", "modification",
            "clarification", "guidance"
        ],
        "low": [
            "minor", "optional", "recommended", "best practice",
            "suggestion", "consideration"
        ]
    }

    def __init__(self, db_path: str = "data/changes.db", policies_dir: str = "policies"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.policies_dir = Path(policies_dir)
        self._init_db()
        self._policy_framework_map = None

    def _init_db(self):
        """Initialize the changes database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS change_alerts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                source_url TEXT,
                source_item_id TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                change_type TEXT,
                frameworks_affected TEXT,
                severity TEXT,
                status TEXT DEFAULT 'pending',
                acknowledged_at TIMESTAMP,
                resolved_at TIMESTAMP,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_impacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                policy_id TEXT NOT NULL,
                impact_type TEXT,
                severity TEXT,
                description TEXT,
                suggested_action TEXT,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (alert_id) REFERENCES change_alerts(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_alerts_status
            ON change_alerts(status)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_impacts_policy
            ON policy_impacts(policy_id)
        """)

        conn.commit()
        conn.close()

    def analyze_feed_item(self, item: FeedItem) -> Optional[ChangeAlert]:
        """Analyze a single feed item for changes"""
        if not item.frameworks_affected and item.relevance_score < 0.3:
            return None

        # Detect change type
        text = f"{item.title} {item.summary}"
        change_type = self._detect_change_type(text)

        # Calculate severity
        severity = self._calculate_severity(text, item.frameworks_affected)

        # Find affected policies
        policy_impacts = self._find_policy_impacts(
            item, change_type, severity
        )

        if not policy_impacts and severity == "low":
            return None

        # Create alert
        alert = ChangeAlert(
            id=f"alert_{item.id}",
            title=item.title,
            description=item.summary,
            source_url=item.link,
            detected_at=datetime.now(),
            change_type=change_type,
            frameworks_affected=item.frameworks_affected,
            policy_impacts=policy_impacts,
            severity=severity
        )

        self._save_alert(alert)
        return alert

    def analyze_recent_updates(self, days: int = 7) -> List[ChangeAlert]:
        """Analyze all recent feed items for changes"""
        monitor = FeedMonitor()
        items = monitor.get_recent_items(days=days, min_relevance=0.2)

        alerts = []
        for item in items:
            if not item.processed:
                alert = self.analyze_feed_item(item)
                if alert:
                    alerts.append(alert)
                monitor.mark_processed(item.id)

        return alerts

    def _detect_change_type(self, text: str) -> str:
        """Detect the type of change from text"""
        text_lower = text.lower()

        # Check patterns in order of specificity
        for change_type in ["new_version", "deadline", "control_update", "guidance"]:
            patterns = self.CHANGE_PATTERNS.get(change_type, [])
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return change_type

        return "general"

    def _calculate_severity(self, text: str, frameworks: List[str]) -> str:
        """Calculate severity based on text content and frameworks"""
        text_lower = text.lower()

        # Check for critical keywords first
        for severity in ["critical", "high", "medium", "low"]:
            keywords = self.SEVERITY_KEYWORDS.get(severity, [])
            for keyword in keywords:
                if keyword in text_lower:
                    return severity

        # Default based on number of frameworks affected
        if len(frameworks) >= 3:
            return "high"
        elif len(frameworks) >= 1:
            return "medium"

        return "low"

    def _find_policy_impacts(self, item: FeedItem, change_type: str,
                              severity: str) -> List[PolicyImpact]:
        """Find policies impacted by this change"""
        if self._policy_framework_map is None:
            self._build_policy_framework_map()

        impacts = []

        for framework_id in item.frameworks_affected:
            # Find policies mapped to this framework
            policies = self._policy_framework_map.get(framework_id, [])

            for policy_id in policies:
                impact_type = self._determine_impact_type(change_type)
                suggested_action = self._suggest_action(change_type, policy_id)

                impact = PolicyImpact(
                    policy_id=policy_id,
                    impact_type=impact_type,
                    severity=severity,
                    description=f"Framework {framework_id} update may affect this policy",
                    suggested_action=suggested_action,
                    source_item_id=item.id,
                    frameworks=[framework_id]
                )
                impacts.append(impact)

        # Deduplicate by policy_id
        seen = set()
        unique_impacts = []
        for impact in impacts:
            if impact.policy_id not in seen:
                seen.add(impact.policy_id)
                # Merge frameworks for same policy
                impact.frameworks = list(set(
                    fw for i in impacts
                    if i.policy_id == impact.policy_id
                    for fw in i.frameworks
                ))
                unique_impacts.append(impact)

        return unique_impacts

    def _build_policy_framework_map(self):
        """Build a mapping from frameworks to policies"""
        self._policy_framework_map = {}

        if not self.policies_dir.exists():
            return

        import yaml

        for policy_file in self.policies_dir.rglob("*.md"):
            try:
                content = policy_file.read_text(encoding="utf-8")
                if "---" not in content:
                    continue

                # Extract YAML frontmatter
                parts = content.split("---", 2)
                if len(parts) < 3:
                    continue

                frontmatter = yaml.safe_load(parts[1])
                if not frontmatter:
                    continue

                policy_id = frontmatter.get("id", policy_file.stem)
                frameworks = frontmatter.get("frameworks", {})

                for fw_id in frameworks.keys():
                    if fw_id not in self._policy_framework_map:
                        self._policy_framework_map[fw_id] = []
                    self._policy_framework_map[fw_id].append(policy_id)

            except Exception:
                continue

    def _determine_impact_type(self, change_type: str) -> str:
        """Determine impact type from change type"""
        mapping = {
            "new_version": "update",
            "control_update": "update",
            "deadline": "review",
            "guidance": "review",
            "general": "review"
        }
        return mapping.get(change_type, "review")

    def _suggest_action(self, change_type: str, policy_id: str) -> str:
        """Generate a suggested action"""
        actions = {
            "new_version": f"Review {policy_id} for updates required by new framework version",
            "control_update": f"Check if {policy_id} addresses updated control requirements",
            "deadline": f"Verify {policy_id} meets upcoming compliance deadline",
            "guidance": f"Review {policy_id} against new guidance",
            "general": f"Review {policy_id} for potential impacts"
        }
        return actions.get(change_type, actions["general"])

    def _save_alert(self, alert: ChangeAlert):
        """Save an alert to the database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO change_alerts
            (id, title, description, source_url, detected_at, change_type,
             frameworks_affected, severity, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id,
            alert.title,
            alert.description,
            alert.source_url,
            alert.detected_at.isoformat(),
            alert.change_type,
            json.dumps(alert.frameworks_affected),
            alert.severity,
            alert.status
        ))

        # Save policy impacts
        for impact in alert.policy_impacts:
            cursor.execute("""
                INSERT INTO policy_impacts
                (alert_id, policy_id, impact_type, severity, description, suggested_action)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                impact.policy_id,
                impact.impact_type,
                impact.severity,
                impact.description,
                impact.suggested_action
            ))

        conn.commit()
        conn.close()

    def get_pending_alerts(self) -> List[ChangeAlert]:
        """Get all pending alerts"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, title, description, source_url, detected_at, change_type,
                   frameworks_affected, severity, status
            FROM change_alerts
            WHERE status = 'pending'
            ORDER BY
                CASE severity
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    ELSE 4
                END,
                detected_at DESC
        """)

        rows = cursor.fetchall()

        alerts = []
        for row in rows:
            alert = ChangeAlert(
                id=row[0],
                title=row[1],
                description=row[2],
                source_url=row[3],
                detected_at=datetime.fromisoformat(row[4]) if row[4] else datetime.now(),
                change_type=row[5],
                frameworks_affected=json.loads(row[6]) if row[6] else [],
                policy_impacts=[],
                severity=row[7],
                status=row[8]
            )

            # Load policy impacts
            cursor.execute("""
                SELECT policy_id, impact_type, severity, description, suggested_action
                FROM policy_impacts
                WHERE alert_id = ?
            """, (alert.id,))

            for impact_row in cursor.fetchall():
                alert.policy_impacts.append(PolicyImpact(
                    policy_id=impact_row[0],
                    impact_type=impact_row[1],
                    severity=impact_row[2],
                    description=impact_row[3],
                    suggested_action=impact_row[4],
                    source_item_id=alert.id,
                    frameworks=alert.frameworks_affected
                ))

            alerts.append(alert)

        conn.close()
        return alerts

    def acknowledge_alert(self, alert_id: str, notes: str = ""):
        """Mark an alert as acknowledged"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE change_alerts
            SET status = 'acknowledged', acknowledged_at = ?, notes = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), notes, alert_id))
        conn.commit()
        conn.close()

    def resolve_alert(self, alert_id: str, notes: str = ""):
        """Mark an alert as resolved"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE change_alerts
            SET status = 'resolved', resolved_at = ?, notes = COALESCE(notes || ' | ', '') || ?
            WHERE id = ?
        """, (datetime.now().isoformat(), notes, alert_id))
        conn.commit()
        conn.close()

    def dismiss_alert(self, alert_id: str, reason: str = ""):
        """Dismiss an alert as not relevant"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE change_alerts
            SET status = 'dismissed', notes = ?
            WHERE id = ?
        """, (reason, alert_id))
        conn.commit()
        conn.close()

    def get_policy_alerts(self, policy_id: str) -> List[Dict[str, Any]]:
        """Get all alerts affecting a specific policy"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT a.id, a.title, a.severity, a.status, a.detected_at,
                   i.impact_type, i.suggested_action
            FROM change_alerts a
            JOIN policy_impacts i ON a.id = i.alert_id
            WHERE i.policy_id = ?
            ORDER BY a.detected_at DESC
        """, (policy_id,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "alert_id": row[0],
                "title": row[1],
                "severity": row[2],
                "status": row[3],
                "detected_at": row[4],
                "impact_type": row[5],
                "suggested_action": row[6]
            }
            for row in rows
        ]

    def generate_alert_report(self) -> str:
        """Generate a markdown report of pending alerts"""
        alerts = self.get_pending_alerts()

        if not alerts:
            return "# Change Alert Report\n\nNo pending alerts."

        lines = [
            "# Change Alert Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Pending Alerts: {len(alerts)}",
            "",
            "## Summary by Severity",
            "",
        ]

        # Count by severity
        severity_counts = {}
        for alert in alerts:
            severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1

        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts.get(severity, 0)
            if count > 0:
                lines.append(f"- **{severity.upper()}**: {count}")

        lines.extend(["", "## Alerts", ""])

        for alert in alerts:
            lines.extend([
                f"### [{alert.severity.upper()}] {alert.title}",
                "",
                f"**Type:** {alert.change_type}",
                f"**Detected:** {alert.detected_at.strftime('%Y-%m-%d')}",
                f"**Frameworks:** {', '.join(alert.frameworks_affected)}",
                "",
                alert.description[:500] if alert.description else "No description",
                "",
                f"[Source]({alert.source_url})",
                "",
            ])

            if alert.policy_impacts:
                lines.append("**Affected Policies:**")
                for impact in alert.policy_impacts[:10]:
                    lines.append(f"- {impact.policy_id}: {impact.suggested_action}")
                if len(alert.policy_impacts) > 10:
                    lines.append(f"- ... and {len(alert.policy_impacts) - 10} more")
                lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)


def main():
    """Test the change detector"""
    print("Change Detector Test")
    print("=" * 60)

    # Initialize
    detector = ChangeDetector(
        db_path="data/changes.db",
        policies_dir="policies"
    )

    # Get pending alerts
    alerts = detector.get_pending_alerts()
    print(f"\nPending Alerts: {len(alerts)}")

    for alert in alerts[:5]:
        print(f"\n  [{alert.severity.upper()}] {alert.title[:50]}...")
        print(f"  Type: {alert.change_type}")
        print(f"  Frameworks: {', '.join(alert.frameworks_affected)}")
        print(f"  Policies Affected: {len(alert.policy_impacts)}")

    # Generate report
    print("\n" + "=" * 60)
    print("Generating Alert Report...")
    report = detector.generate_alert_report()
    print(f"\nReport length: {len(report)} characters")

    # Save report
    report_path = Path("output/change_alerts.md")
    report_path.parent.mkdir(exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
