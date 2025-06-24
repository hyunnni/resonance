import os
import json
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from .worldnews_api import fetch_worldnews
from .emotion_utils import analyze_headline_emotion
from .db import init_db, is_new_article, save_article, get_latest_articles
from .translation_api import translate_text

from .config import TIMESPAN_HOURS, NUM_RECORDS, LATEST_EXPORT_COUNT

# --- Config ---
load_dotenv()
DB_FILE = os.getenv("DB_FILE", "resonance.db")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Logging Setup ---
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def fetch_and_process_articles(
    timespan: float = TIMESPAN_HOURS,
    num_records: int = NUM_RECORDS,
) -> Tuple[List[Dict[str, Any]], int]:

    processed = []
    total_fetched = 0
    
    try:
        news = fetch_worldnews(timespan=timespan, number=num_records)
    except Exception as e:
        logger.error(f"Failed to fetch articles: {e}")
        return [], 0
        
    total_fetched += len(news)
    for art in news:
        url = art["url"]
        if not is_new_article(url):
            continue
        try:
            emotion = analyze_headline_emotion({
                "text": art["headline"],
                "source_country": art["source_country"],
                "published": art["date"]
            })
            label = emotion["sentiment"]["label"]
            confidence = emotion["sentiment"]["confidence"]
        except Exception as e:
            logger.error(f"Sentiment analysis failed for url={url}: {e}")
            continue
        try:  #번역
            headline_ko = translate_text(art["headline"], "ko")
        except Exception as e:
            logger.error(f"Translation failed for url={url}: {e}")
            headline_ko = art["headline"] #fallback
        try:  #저장 
            save_article(url, headline_ko, art["source_country"], art["date"], label, confidence)
        except Exception as e:
            logger.error(f"DB save failed for article={url}: {e}")
            continue
        processed.append({
            "url": url,
            "headline": headline_ko,
            "source_country": art["source_country"],
            "timestamp": art["date"],
            "sentiment": {
                "label": label,
                "confidence": confidence
            }
        })
    return processed, total_fetched

def export_latest_articles_with_sentiment_json(filename: str = "latest_articles_with_sentiment.json") -> None:
    """
    Export the latest 100 articles (with sentiment) from the DB to a JSON file.
    """
    try:
        articles = get_latest_articles(min_count=LATEST_EXPORT_COUNT, hours=TIMESPAN_HOURS)
        data = []
        for url, headline, source_country, timestamp, sentiment_label, sentiment_confidence in articles:
            data.append({
                "url": url,
                "headline": headline,
                "source_country": source_country,
                "timestamp": timestamp,
                "sentiment": {
                    "label": sentiment_label,
                    "confidence": sentiment_confidence
                }
            })
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Exported {len(data)} articles to {filename}")
    except Exception as e:
        logger.error(f"Failed to export articles to JSON: {e}")


def print_articles(processed_news: List[Dict[str, Any]]) -> None:
    """
    Print article details to the terminal.
    """
    for i, row in enumerate(processed_news, 1):
        logger.info(f"[{i:02d}] [{row['timestamp']} @{row['source_country']}] "
                    f"[{row['sentiment']['label']}({row['sentiment']['confidence']})] – {row['headline']}")

def main() -> None:
    init_db()
    processed_news, total_news = fetch_and_process_articles(
        timespan= TIMESPAN_HOURS,
        num_records=NUM_RECORDS
    )
    logger.info(f"Total news articles found: {total_news}")
    logger.info(f"Number of new articles processed: {len(processed_news)}")
    print_articles(processed_news)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"news_sentiment_{timestamp}.json"
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(processed_news, f, ensure_ascii=False, indent=2)
        logger.info(f"Results have been saved to {output_file}")
        logger.info(f"Number of analyzed articles: {len(processed_news)}")
        logger.info(f"Number of filtered out articles: {total_news - len(processed_news)}")
    except Exception as e:
        logger.error(f"Failed to save results to {output_file}: {e}")
    export_latest_articles_with_sentiment_json()

if __name__ == "__main__":
    main()