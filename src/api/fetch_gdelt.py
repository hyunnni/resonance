from __future__ import annotations

import logging
from typing import List, Dict, Any

import pandas as pd
from gdeltdoc import GdeltDoc, Filters
from .db import init_db, get_latest_articles
import json

__all__ = ["fetch_gdelt"]

# --- Config ---
MIN_LEN = 15  # Minimum headline length
GDOC = GdeltDoc()

# --- Logging Setup ---
logger = logging.getLogger(__name__)

def fetch_gdelt(
    *,
    timespan: str = "1hours",
    num_records: int = 250,
    countries: list[str] | None = None,
) -> List[Dict[str, Any]]:
    """
    Fetch articles from GDELT, filter by language and minimum headline length.
    Returns a list of article dicts.
    """
    country_filter = " OR ".join(countries) if countries else ""
    
    filt = Filters(
        timespan=timespan,
        num_records=num_records,
        country=country_filter
    )
    
    try:
        df: pd.DataFrame = GDOC.article_search(filt)
    except Exception as exc:
        logger.warning(f"gdeltdoc fetch failed: {exc}")
        return []

    keep_langs = {"english"}
    df = df[df["language"].str.lower().isin(keep_langs)]

    fresh: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        url = str(row.get("url", ""))
        headline = str(row.get("title") or "").strip()
        source_country = str(row.get("sourcecountry"))
        date = str(row.get("seendate") or "")
        
        if not url or len(headline) < MIN_LEN:
            continue
        
        fresh.append({
            "url": url,
            "source_country": source_country,
            "headline": headline,
            "date": date
        })

    return fresh

def get_latest_articles_with_emotion(min_count: int, hours: int) -> List[Dict[str, Any]]:
    articles = get_latest_articles(min_count=min_count, hours=hours)
    result = []
    for url, headline, source_country, timestamp in articles:
        item = {
            "text": headline,
            "source_country": source_country,
            "published": timestamp
        }
        emotion_result = headline_emotion(item)
        emotion_result["url"] = url
        result.append(emotion_result)
    return result

def save_articles_to_json(articles: List[Dict[str, Any]], filename: str):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

init_db()