import sqlite3
import os
import logging
from datetime import datetime, timedelta
from typing import Tuple

# --- Config ---
DB_FILE = os.getenv("DB_FILE", "collected_articles.db")

# --- Logging Setup ---
logger = logging.getLogger(__name__)

def get_conn() -> sqlite3.Connection:
    """Get a new SQLite connection."""
    try:
        conn = sqlite3.connect(DB_FILE)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to DB: {e}")
        raise

def init_db() -> None:
    """Initialize the articles table if it does not exist."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                url TEXT PRIMARY KEY,
                headline TEXT,
                source_country TEXT,
                timestamp TEXT,
                sentiment_label TEXT,
                sentiment_confidence REAL
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to initialize DB: {e}")
        raise

def save_article(url: str, headline: str, source_country: str, timestamp: str, sentiment_label: str = None, sentiment_confidence: float = None) -> None:
    """Save or update an article in the DB."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('''
            INSERT INTO articles (url, headline, source_country, timestamp, sentiment_label, sentiment_confidence)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                sentiment_label=excluded.sentiment_label,
                sentiment_confidence=excluded.sentiment_confidence
        ''', (url, headline, source_country, timestamp, sentiment_label, sentiment_confidence))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to save article url={url}: {e}")

def is_new_article(url: str) -> bool:
    """Check if an article URL is new (not in the DB)."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT 1 FROM articles WHERE url=?', (url,))
        result = c.fetchone()
        conn.close()
        return result is None
    except Exception as e:
        logger.error(f"Failed to check article url={url}: {e}")
        return False

def get_latest_articles(min_count: int = 100, hours: int = 1):
    """Get the latest articles (with sentiment) from the DB."""
    try:
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=hours)
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT url, headline, source_country, timestamp, sentiment_label, sentiment_confidence FROM articles WHERE timestamp >= ? ORDER BY timestamp DESC', (one_hour_ago.strftime('%Y%m%dT%H%M%SZ'),))
        recent_articles = c.fetchall()
        recent_urls = set(url for url, *_ in recent_articles)
        count_needed = min_count - len(recent_articles)
        if count_needed > 0:
            if recent_urls:
                placeholders = ','.join('?'*len(recent_urls))
                c.execute(f'SELECT url, headline, source_country, timestamp, sentiment_label, sentiment_confidence FROM articles WHERE url NOT IN ({placeholders}) ORDER BY timestamp DESC LIMIT ?', (*recent_urls, count_needed))
            else:
                c.execute('SELECT url, headline, source_country, timestamp, sentiment_label, sentiment_confidence FROM articles ORDER BY timestamp DESC LIMIT ?', (count_needed,))
            extra_articles = c.fetchall()
            articles = recent_articles + extra_articles
        else:
            articles = recent_articles[:min_count]
        conn.close()
        return articles
    except Exception as e:
        logger.error(f"Failed to get latest articles: {e}")
        return []