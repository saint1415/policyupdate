"""
Feed Monitor Module
Monitors RSS feeds and websites for compliance framework updates

Supports:
- RSS/Atom feed parsing
- Website change detection
- Keyword-based filtering
- Impact analysis linking to affected policies
"""

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass
class FeedConfig:
    """Configuration for a monitored feed"""
    id: str
    name: str
    url: str
    feed_type: str = "rss"  # rss, atom, webpage
    check_interval: str = "daily"  # hourly, daily, weekly
    keywords: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class FeedItem:
    """A single item from a monitored feed"""
    id: str
    feed_id: str
    title: str
    link: str
    summary: str
    published: datetime
    fetched_at: datetime
    keywords_matched: List[str] = field(default_factory=list)
    frameworks_affected: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    processed: bool = False


class FeedMonitor:
    """
    Monitors RSS feeds and websites for compliance framework updates.

    Usage:
        monitor = FeedMonitor("data/feeds.db")
        monitor.add_feed(FeedConfig(
            id="nist-csrc",
            name="NIST CSRC News",
            url="https://csrc.nist.gov/news/rss",
            keywords=["CSF", "800-53", "cybersecurity"]
        ))
        updates = monitor.check_all_feeds()
    """

    # Default framework keywords for relevance scoring
    FRAMEWORK_KEYWORDS = {
        "nist_csf_2.0": ["CSF", "cybersecurity framework", "NIST CSF", "CSF 2.0"],
        "nist_800_53": ["800-53", "NIST 800-53", "security controls"],
        "nist_800_171": ["800-171", "CUI", "controlled unclassified"],
        "iso_27001_2022": ["ISO 27001", "ISO/IEC 27001", "27001:2022", "information security management"],
        "soc2": ["SOC 2", "SOC2", "trust services criteria", "service organization"],
        "pci_dss_4": ["PCI DSS", "PCI-DSS", "payment card", "cardholder data"],
        "hipaa": ["HIPAA", "health insurance portability", "PHI", "protected health information"],
        "gdpr": ["GDPR", "general data protection", "EU privacy", "data protection regulation"],
        "ccpa": ["CCPA", "CPRA", "california privacy", "california consumer privacy"],
        "sec_cyber": ["SEC cyber", "SEC cybersecurity", "cyber disclosure", "material incident"],
        "nis2": ["NIS2", "NIS 2", "network information security", "EU cybersecurity directive"],
        "eu_ai_act": ["AI Act", "artificial intelligence act", "EU AI", "high-risk AI"]
    }

    def __init__(self, db_path: str = "data/feeds.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feeds (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                feed_type TEXT DEFAULT 'rss',
                check_interval TEXT DEFAULT 'daily',
                keywords TEXT,
                frameworks TEXT,
                enabled INTEGER DEFAULT 1,
                last_checked TIMESTAMP,
                last_etag TEXT,
                last_modified TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feed_items (
                id TEXT PRIMARY KEY,
                feed_id TEXT NOT NULL,
                title TEXT,
                link TEXT,
                summary TEXT,
                published TIMESTAMP,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                keywords_matched TEXT,
                frameworks_affected TEXT,
                relevance_score REAL DEFAULT 0.0,
                processed INTEGER DEFAULT 0,
                FOREIGN KEY (feed_id) REFERENCES feeds(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS webpage_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id TEXT NOT NULL,
                content_hash TEXT,
                captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (feed_id) REFERENCES feeds(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feed_items_feed_id
            ON feed_items(feed_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_feed_items_published
            ON feed_items(published DESC)
        """)

        conn.commit()
        conn.close()

    def add_feed(self, config: FeedConfig) -> bool:
        """Add or update a feed configuration"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO feeds
            (id, name, url, feed_type, check_interval, keywords, frameworks, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config.id,
            config.name,
            config.url,
            config.feed_type,
            config.check_interval,
            json.dumps(config.keywords),
            json.dumps(config.frameworks),
            1 if config.enabled else 0
        ))

        conn.commit()
        conn.close()
        return True

    def get_feeds(self, enabled_only: bool = True) -> List[FeedConfig]:
        """Get all configured feeds"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        query = "SELECT id, name, url, feed_type, check_interval, keywords, frameworks, enabled FROM feeds"
        if enabled_only:
            query += " WHERE enabled = 1"

        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        feeds = []
        for row in rows:
            feeds.append(FeedConfig(
                id=row[0],
                name=row[1],
                url=row[2],
                feed_type=row[3],
                check_interval=row[4],
                keywords=json.loads(row[5]) if row[5] else [],
                frameworks=json.loads(row[6]) if row[6] else [],
                enabled=bool(row[7])
            ))

        return feeds

    def check_feed(self, feed_id: str) -> List[FeedItem]:
        """Check a single feed for new items"""
        feeds = [f for f in self.get_feeds(enabled_only=False) if f.id == feed_id]
        if not feeds:
            return []

        feed = feeds[0]

        if feed.feed_type in ["rss", "atom"]:
            return self._check_rss_feed(feed)
        elif feed.feed_type == "webpage":
            return self._check_webpage(feed)

        return []

    def check_all_feeds(self) -> List[FeedItem]:
        """Check all enabled feeds for new items"""
        all_items = []
        for feed in self.get_feeds(enabled_only=True):
            if self._should_check(feed):
                items = self.check_feed(feed.id)
                all_items.extend(items)
        return all_items

    def _should_check(self, feed: FeedConfig) -> bool:
        """Determine if feed should be checked based on interval"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT last_checked FROM feeds WHERE id = ?", (feed.id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            return True

        last_checked = datetime.fromisoformat(row[0])
        now = datetime.now()

        intervals = {
            "hourly": timedelta(hours=1),
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1)
        }

        interval = intervals.get(feed.check_interval, timedelta(days=1))
        return (now - last_checked) >= interval

    def _check_rss_feed(self, feed: FeedConfig) -> List[FeedItem]:
        """Parse an RSS/Atom feed and return new items"""
        if not FEEDPARSER_AVAILABLE:
            print("Warning: feedparser not installed. Run: pip install feedparser")
            return []

        try:
            parsed = feedparser.parse(feed.url)
        except Exception as e:
            print(f"Error fetching feed {feed.id}: {e}")
            return []

        # Update last checked
        self._update_last_checked(feed.id)

        new_items = []
        for entry in parsed.entries:
            item_id = self._generate_item_id(feed.id, entry)

            # Check if already processed
            if self._item_exists(item_id):
                continue

            # Parse publication date
            published = datetime.now()
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6])

            # Get summary
            summary = ""
            if hasattr(entry, 'summary'):
                summary = self._clean_html(entry.summary)[:1000]
            elif hasattr(entry, 'description'):
                summary = self._clean_html(entry.description)[:1000]

            # Analyze relevance
            text = f"{entry.get('title', '')} {summary}"
            keywords_matched, frameworks_affected = self._analyze_relevance(text, feed)
            relevance_score = self._calculate_relevance_score(keywords_matched, frameworks_affected)

            # Create item
            item = FeedItem(
                id=item_id,
                feed_id=feed.id,
                title=entry.get('title', 'No Title'),
                link=entry.get('link', ''),
                summary=summary,
                published=published,
                fetched_at=datetime.now(),
                keywords_matched=keywords_matched,
                frameworks_affected=frameworks_affected,
                relevance_score=relevance_score
            )

            # Save to database
            self._save_item(item)
            new_items.append(item)

        return new_items

    def _check_webpage(self, feed: FeedConfig) -> List[FeedItem]:
        """Check a webpage for changes"""
        if not REQUESTS_AVAILABLE:
            print("Warning: requests not installed. Run: pip install requests")
            return []

        try:
            response = requests.get(feed.url, timeout=30)
            response.raise_for_status()
            content = response.text
        except Exception as e:
            print(f"Error fetching webpage {feed.id}: {e}")
            return []

        # Calculate content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()

        # Check if content changed
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content_hash FROM webpage_snapshots
            WHERE feed_id = ?
            ORDER BY captured_at DESC LIMIT 1
        """, (feed.id,))
        row = cursor.fetchone()

        if row and row[0] == content_hash:
            # No change
            self._update_last_checked(feed.id)
            conn.close()
            return []

        # Content changed - save snapshot
        cursor.execute("""
            INSERT INTO webpage_snapshots (feed_id, content_hash)
            VALUES (?, ?)
        """, (feed.id, content_hash))
        conn.commit()
        conn.close()

        self._update_last_checked(feed.id)

        # Create a feed item for the change
        item_id = f"{feed.id}_{datetime.now().isoformat()}"
        keywords_matched, frameworks_affected = self._analyze_relevance(content, feed)
        relevance_score = self._calculate_relevance_score(keywords_matched, frameworks_affected)

        item = FeedItem(
            id=item_id,
            feed_id=feed.id,
            title=f"Page Updated: {feed.name}",
            link=feed.url,
            summary="The monitored webpage has been updated. Review for potential framework changes.",
            published=datetime.now(),
            fetched_at=datetime.now(),
            keywords_matched=keywords_matched,
            frameworks_affected=frameworks_affected,
            relevance_score=relevance_score
        )

        self._save_item(item)
        return [item]

    def _analyze_relevance(self, text: str, feed: FeedConfig) -> tuple:
        """Analyze text for keywords and framework relevance"""
        text_lower = text.lower()

        # Check feed-specific keywords
        keywords_matched = []
        for keyword in feed.keywords:
            if keyword.lower() in text_lower:
                keywords_matched.append(keyword)

        # Check framework keywords
        frameworks_affected = list(feed.frameworks)  # Start with configured frameworks

        for fw_id, keywords in self.FRAMEWORK_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if fw_id not in frameworks_affected:
                        frameworks_affected.append(fw_id)
                    break

        return keywords_matched, frameworks_affected

    def _calculate_relevance_score(self, keywords: List[str], frameworks: List[str]) -> float:
        """Calculate a relevance score from 0.0 to 1.0"""
        score = 0.0

        # Keywords contribute up to 0.4
        score += min(len(keywords) * 0.1, 0.4)

        # Frameworks contribute up to 0.6
        score += min(len(frameworks) * 0.15, 0.6)

        return min(score, 1.0)

    def _generate_item_id(self, feed_id: str, entry: Any) -> str:
        """Generate a unique ID for a feed item"""
        # Use link or id if available, otherwise hash title+published
        if hasattr(entry, 'id') and entry.id:
            return f"{feed_id}_{hashlib.md5(entry.id.encode()).hexdigest()[:12]}"
        if hasattr(entry, 'link') and entry.link:
            return f"{feed_id}_{hashlib.md5(entry.link.encode()).hexdigest()[:12]}"

        unique_str = f"{entry.get('title', '')}{entry.get('published', '')}"
        return f"{feed_id}_{hashlib.md5(unique_str.encode()).hexdigest()[:12]}"

    def _item_exists(self, item_id: str) -> bool:
        """Check if an item already exists in the database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM feed_items WHERE id = ?", (item_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def _save_item(self, item: FeedItem):
        """Save a feed item to the database"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO feed_items
            (id, feed_id, title, link, summary, published, fetched_at,
             keywords_matched, frameworks_affected, relevance_score, processed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item.id,
            item.feed_id,
            item.title,
            item.link,
            item.summary,
            item.published.isoformat(),
            item.fetched_at.isoformat(),
            json.dumps(item.keywords_matched),
            json.dumps(item.frameworks_affected),
            item.relevance_score,
            1 if item.processed else 0
        ))

        conn.commit()
        conn.close()

    def _update_last_checked(self, feed_id: str):
        """Update the last_checked timestamp for a feed"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE feeds SET last_checked = ? WHERE id = ?
        """, (datetime.now().isoformat(), feed_id))
        conn.commit()
        conn.close()

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        return re.sub(r'<[^>]+>', '', text).strip()

    def get_recent_items(self, days: int = 7, min_relevance: float = 0.0) -> List[FeedItem]:
        """Get recent feed items"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        cursor.execute("""
            SELECT id, feed_id, title, link, summary, published, fetched_at,
                   keywords_matched, frameworks_affected, relevance_score, processed
            FROM feed_items
            WHERE published >= ? AND relevance_score >= ?
            ORDER BY relevance_score DESC, published DESC
        """, (cutoff, min_relevance))

        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            items.append(FeedItem(
                id=row[0],
                feed_id=row[1],
                title=row[2],
                link=row[3],
                summary=row[4],
                published=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                fetched_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                keywords_matched=json.loads(row[7]) if row[7] else [],
                frameworks_affected=json.loads(row[8]) if row[8] else [],
                relevance_score=row[9],
                processed=bool(row[10])
            ))

        return items

    def get_pending_items(self) -> List[FeedItem]:
        """Get items that haven't been processed yet"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, feed_id, title, link, summary, published, fetched_at,
                   keywords_matched, frameworks_affected, relevance_score, processed
            FROM feed_items
            WHERE processed = 0 AND relevance_score > 0
            ORDER BY relevance_score DESC, published DESC
        """)

        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            items.append(FeedItem(
                id=row[0],
                feed_id=row[1],
                title=row[2],
                link=row[3],
                summary=row[4],
                published=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                fetched_at=datetime.fromisoformat(row[6]) if row[6] else datetime.now(),
                keywords_matched=json.loads(row[7]) if row[7] else [],
                frameworks_affected=json.loads(row[8]) if row[8] else [],
                relevance_score=row[9],
                processed=bool(row[10])
            ))

        return items

    def mark_processed(self, item_id: str):
        """Mark an item as processed"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("UPDATE feed_items SET processed = 1 WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()

    def load_default_feeds(self):
        """Load default compliance framework feeds"""
        default_feeds = [
            FeedConfig(
                id="nist-csrc",
                name="NIST CSRC News",
                url="https://csrc.nist.gov/News/rss",
                keywords=["CSF", "800-53", "800-171", "cybersecurity", "framework"],
                frameworks=["nist_csf_2.0", "nist_800_53", "nist_800_171"]
            ),
            FeedConfig(
                id="pci-blog",
                name="PCI Perspectives Blog",
                url="https://blog.pcisecuritystandards.org/rss.xml",
                keywords=["PCI DSS", "payment", "security", "standard"],
                frameworks=["pci_dss_4"]
            ),
            FeedConfig(
                id="sec-news",
                name="SEC Press Releases",
                url="https://www.sec.gov/rss/news/press.xml",
                keywords=["cybersecurity", "disclosure", "breach", "material"],
                frameworks=["sec_cyber"]
            ),
            FeedConfig(
                id="hipaa-journal",
                name="HIPAA Journal",
                url="https://www.hipaajournal.com/feed/",
                keywords=["HIPAA", "PHI", "healthcare", "privacy"],
                frameworks=["hipaa"]
            ),
            FeedConfig(
                id="gdpr-today",
                name="GDPR Today",
                url="https://www.gdprtoday.org/feed/",
                keywords=["GDPR", "privacy", "data protection", "EU"],
                frameworks=["gdpr"]
            ),
            FeedConfig(
                id="eu-official",
                name="EU Official Journal - Cybersecurity",
                url="https://eur-lex.europa.eu/EN/atom/recent-oj",
                keywords=["NIS2", "AI Act", "cybersecurity", "DORA"],
                frameworks=["nis2", "eu_ai_act"]
            )
        ]

        for feed in default_feeds:
            self.add_feed(feed)

        return len(default_feeds)


def main():
    """Test the feed monitor"""
    print("Feed Monitor Test")
    print("=" * 60)

    # Initialize monitor
    monitor = FeedMonitor("data/feeds.db")

    # Load default feeds
    count = monitor.load_default_feeds()
    print(f"\nLoaded {count} default feeds")

    # List feeds
    feeds = monitor.get_feeds()
    print(f"\nConfigured Feeds ({len(feeds)}):")
    for feed in feeds:
        print(f"  - {feed.id}: {feed.name}")
        print(f"    URL: {feed.url}")
        print(f"    Keywords: {', '.join(feed.keywords)}")
        print(f"    Frameworks: {', '.join(feed.frameworks)}")

    # Check if we can actually fetch feeds
    if FEEDPARSER_AVAILABLE:
        print("\n" + "=" * 60)
        print("Checking feeds (this may take a moment)...")

        # Try to check one feed
        if feeds:
            items = monitor.check_feed(feeds[0].id)
            print(f"\nFound {len(items)} new items from {feeds[0].name}")

            for item in items[:5]:
                print(f"\n  Title: {item.title[:60]}...")
                print(f"  Score: {item.relevance_score:.2f}")
                if item.frameworks_affected:
                    print(f"  Frameworks: {', '.join(item.frameworks_affected)}")
    else:
        print("\n[WARN] feedparser not installed - cannot check RSS feeds")
        print("       Install with: pip install feedparser")


if __name__ == "__main__":
    main()
