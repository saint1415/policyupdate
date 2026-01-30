"""
Notification Module
Sends alerts for compliance framework updates via email and webhooks
"""

import json
import smtplib
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class NotificationConfig:
    """Configuration for notifications"""
    # Email settings
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)

    # Webhook settings
    webhook_url: str = ""
    webhook_secret: str = ""

    # Notification preferences
    min_severity: str = "medium"  # critical, high, medium, low
    notify_on_new_items: bool = True
    notify_on_alerts: bool = True
    daily_digest: bool = False


@dataclass
class Notification:
    """A notification to be sent"""
    id: str
    title: str
    message: str
    severity: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class Notifier:
    """
    Sends notifications for compliance updates.

    Supports:
    - Email (SMTP)
    - Webhooks (Slack, Teams, Discord, generic)
    - Console output

    Usage:
        config = NotificationConfig(
            smtp_host="smtp.gmail.com",
            email_from="alerts@company.com",
            email_to=["security@company.com"]
        )
        notifier = Notifier(config)
        notifier.send_alert(alert)
    """

    SEVERITY_ORDER = {"critical": 1, "high": 2, "medium": 3, "low": 4}

    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or NotificationConfig()
        self._notifications_sent: List[str] = []

    def should_notify(self, severity: str) -> bool:
        """Check if notification should be sent based on severity"""
        min_level = self.SEVERITY_ORDER.get(self.config.min_severity, 3)
        current_level = self.SEVERITY_ORDER.get(severity, 4)
        return current_level <= min_level

    def send_alert(self, alert) -> bool:
        """Send notification for a change alert"""
        if not self.config.notify_on_alerts:
            return False

        if not self.should_notify(alert.severity):
            return False

        notification = Notification(
            id=f"alert_{alert.id}",
            title=f"[{alert.severity.upper()}] {alert.title}",
            message=self._format_alert_message(alert),
            severity=alert.severity,
            timestamp=datetime.now(),
            source="change_detector",
            metadata={
                "frameworks": alert.frameworks_affected,
                "policies_affected": len(alert.policy_impacts),
                "source_url": alert.source_url
            }
        )

        return self._send(notification)

    def send_feed_update(self, items: List) -> bool:
        """Send notification for new feed items"""
        if not self.config.notify_on_new_items:
            return False

        if not items:
            return False

        # Find highest severity
        max_severity = "low"
        for item in items:
            if item.relevance_score >= 0.7:
                max_severity = "high"
                break
            elif item.relevance_score >= 0.4:
                max_severity = "medium"

        if not self.should_notify(max_severity):
            return False

        notification = Notification(
            id=f"feed_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            title=f"Compliance Update: {len(items)} new items",
            message=self._format_feed_message(items),
            severity=max_severity,
            timestamp=datetime.now(),
            source="feed_monitor",
            metadata={
                "item_count": len(items),
                "frameworks": list(set(
                    fw for item in items
                    for fw in item.frameworks_affected
                ))
            }
        )

        return self._send(notification)

    def send_daily_digest(self, alerts: List, items: List) -> bool:
        """Send daily digest of all updates"""
        if not self.config.daily_digest:
            return False

        if not alerts and not items:
            return False

        notification = Notification(
            id=f"digest_{datetime.now().strftime('%Y%m%d')}",
            title=f"Daily Compliance Digest - {datetime.now().strftime('%B %d, %Y')}",
            message=self._format_digest_message(alerts, items),
            severity="medium",
            timestamp=datetime.now(),
            source="daily_digest",
            metadata={
                "alert_count": len(alerts),
                "item_count": len(items)
            }
        )

        return self._send(notification)

    def _send(self, notification: Notification) -> bool:
        """Send notification via all configured channels"""
        success = False

        # Try email
        if self.config.email_to and self.config.smtp_host:
            try:
                self._send_email(notification)
                success = True
            except Exception as e:
                print(f"Email notification failed: {e}")

        # Try webhook
        if self.config.webhook_url:
            try:
                self._send_webhook(notification)
                success = True
            except Exception as e:
                print(f"Webhook notification failed: {e}")

        # Always log to console
        self._log_notification(notification)

        if success:
            self._notifications_sent.append(notification.id)

        return success

    def _send_email(self, notification: Notification):
        """Send email notification"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = notification.title
        msg['From'] = self.config.email_from
        msg['To'] = ', '.join(self.config.email_to)

        # Plain text version
        text_body = notification.message

        # HTML version
        html_body = self._format_html_email(notification)

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
            if self.config.smtp_use_tls:
                server.starttls()
            if self.config.smtp_user and self.config.smtp_password:
                server.login(self.config.smtp_user, self.config.smtp_password)
            server.sendmail(
                self.config.email_from,
                self.config.email_to,
                msg.as_string()
            )

    def _send_webhook(self, notification: Notification):
        """Send webhook notification"""
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests library required for webhooks")

        # Detect webhook type and format accordingly
        url = self.config.webhook_url.lower()

        if "slack.com" in url:
            payload = self._format_slack_payload(notification)
        elif "teams.microsoft.com" in url or "office.com" in url:
            payload = self._format_teams_payload(notification)
        elif "discord.com" in url:
            payload = self._format_discord_payload(notification)
        else:
            payload = self._format_generic_payload(notification)

        headers = {"Content-Type": "application/json"}
        if self.config.webhook_secret:
            headers["Authorization"] = f"Bearer {self.config.webhook_secret}"

        response = requests.post(
            self.config.webhook_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

    def _format_slack_payload(self, notification: Notification) -> Dict:
        """Format notification for Slack webhook"""
        color = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745"
        }.get(notification.severity, "#6c757d")

        return {
            "attachments": [{
                "color": color,
                "title": notification.title,
                "text": notification.message[:2000],
                "footer": f"PolicyUpdate | {notification.source}",
                "ts": int(notification.timestamp.timestamp())
            }]
        }

    def _format_teams_payload(self, notification: Notification) -> Dict:
        """Format notification for Microsoft Teams webhook"""
        color = {
            "critical": "dc3545",
            "high": "fd7e14",
            "medium": "ffc107",
            "low": "28a745"
        }.get(notification.severity, "6c757d")

        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": color,
            "summary": notification.title,
            "sections": [{
                "activityTitle": notification.title,
                "text": notification.message[:2000],
                "facts": [
                    {"name": "Severity", "value": notification.severity.upper()},
                    {"name": "Source", "value": notification.source},
                    {"name": "Time", "value": notification.timestamp.strftime("%Y-%m-%d %H:%M")}
                ]
            }]
        }

    def _format_discord_payload(self, notification: Notification) -> Dict:
        """Format notification for Discord webhook"""
        color = {
            "critical": 0xdc3545,
            "high": 0xfd7e14,
            "medium": 0xffc107,
            "low": 0x28a745
        }.get(notification.severity, 0x6c757d)

        return {
            "embeds": [{
                "title": notification.title,
                "description": notification.message[:2000],
                "color": color,
                "footer": {"text": f"PolicyUpdate | {notification.source}"},
                "timestamp": notification.timestamp.isoformat()
            }]
        }

    def _format_generic_payload(self, notification: Notification) -> Dict:
        """Format notification for generic webhook"""
        return {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "severity": notification.severity,
            "timestamp": notification.timestamp.isoformat(),
            "source": notification.source,
            "metadata": notification.metadata
        }

    def _format_html_email(self, notification: Notification) -> str:
        """Format HTML email body"""
        color = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745"
        }.get(notification.severity, "#6c757d")

        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: {color}; color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">{notification.severity.upper()}</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <h2>{notification.title}</h2>
                <p>{notification.message.replace(chr(10), '<br>')}</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    Source: {notification.source}<br>
                    Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
            <div style="background: #f5f5f5; padding: 10px; text-align: center; font-size: 12px;">
                PolicyUpdate GRC Platform
            </div>
        </body>
        </html>
        """

    def _format_alert_message(self, alert) -> str:
        """Format change alert as message text"""
        lines = [
            f"Change Type: {alert.change_type}",
            f"Frameworks Affected: {', '.join(alert.frameworks_affected)}",
            f"Policies Impacted: {len(alert.policy_impacts)}",
            "",
            alert.description[:500] if alert.description else "No description",
            "",
            f"Source: {alert.source_url}"
        ]
        return '\n'.join(lines)

    def _format_feed_message(self, items: List) -> str:
        """Format feed items as message text"""
        lines = [f"Found {len(items)} new compliance-related items:", ""]

        for item in items[:10]:
            lines.append(f"- {item.title[:80]}...")
            if item.frameworks_affected:
                lines.append(f"  Frameworks: {', '.join(item.frameworks_affected)}")
            lines.append("")

        if len(items) > 10:
            lines.append(f"... and {len(items) - 10} more items")

        return '\n'.join(lines)

    def _format_digest_message(self, alerts: List, items: List) -> str:
        """Format daily digest as message text"""
        lines = [
            "Daily Compliance Update Summary",
            "=" * 40,
            "",
            f"Change Alerts: {len(alerts)}",
            f"New Feed Items: {len(items)}",
            ""
        ]

        if alerts:
            lines.append("## Change Alerts")
            for alert in alerts[:5]:
                lines.append(f"- [{alert.severity.upper()}] {alert.title[:60]}...")
            if len(alerts) > 5:
                lines.append(f"  ... and {len(alerts) - 5} more alerts")
            lines.append("")

        if items:
            lines.append("## New Items")
            for item in items[:5]:
                lines.append(f"- {item.title[:60]}...")
            if len(items) > 5:
                lines.append(f"  ... and {len(items) - 5} more items")

        return '\n'.join(lines)

    def _log_notification(self, notification: Notification):
        """Log notification to console"""
        print(f"\n[NOTIFICATION] {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Severity: {notification.severity.upper()}")
        print(f"  Title: {notification.title}")
        print(f"  Source: {notification.source}")


def main():
    """Test the notifier"""
    print("Notification System Test")
    print("=" * 60)

    # Create test config (console only, no actual sending)
    config = NotificationConfig(
        min_severity="low",
        notify_on_alerts=True,
        notify_on_new_items=True
    )

    notifier = Notifier(config)

    # Test notification
    test_notification = Notification(
        id="test_001",
        title="Test Compliance Alert",
        message="This is a test notification to verify the notification system is working correctly.",
        severity="high",
        timestamp=datetime.now(),
        source="test",
        metadata={"test": True}
    )

    print("\nSending test notification...")
    notifier._log_notification(test_notification)

    print("\n" + "=" * 60)
    print("Notification system ready!")
    print("\nTo enable email notifications, configure:")
    print("  - smtp_host, smtp_port, smtp_user, smtp_password")
    print("  - email_from, email_to")
    print("\nTo enable webhook notifications, configure:")
    print("  - webhook_url (Slack, Teams, Discord, or generic)")


if __name__ == "__main__":
    main()
