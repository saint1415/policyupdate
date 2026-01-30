"""
Automation Module
Handles monitoring of compliance framework updates and change detection
"""

from .feed_monitor import FeedMonitor, FeedItem, FeedConfig
from .change_detector import ChangeDetector, ChangeAlert, PolicyImpact

__all__ = [
    'FeedMonitor', 'FeedItem', 'FeedConfig',
    'ChangeDetector', 'ChangeAlert', 'PolicyImpact'
]
