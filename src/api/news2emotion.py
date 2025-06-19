import os
import json
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from .fetch_gdelt import fetch_gdelt
from .emotion_utils import headline_emotion
from .db import is_new_article, save_article, get_latest_articles

# --- Config ---
load_dotenv()
DB_FILE = os.getenv("DB_FILE", "collected_articles.db")
DEFAULT_COUNTRIES = ["US","UK","KS","KN","JA","CH","GM","FR","RS","IN","BR"]
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# --- Logging Setup ---
logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def fetch_and_process_articles(
    timespan: str = "1hours",
    num_records: int = 250,
    countries: Optional[List[str]] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch latest news articles, deduplicate, run sentiment analysis, and store in DB.
    Returns:
        processed (List[Dict]): List of processed articles with sentiment.
        total_fetched (int): Total number of articles fetched from GDELT.
    """
    if not countries:
        countries = DEFAULT_COUNTRIES
    records_per_country = num_records // len(countries)
    processed = []
    total_fetched = 0
    for country in countries:
        try:
            country_news = fetch_gdelt(
                timespan=timespan,
                num_records=records_per_country,
                countries=[country]
            )
        except Exception as e:
            logger.error(f"Failed to fetch articles for {country}: {e}")
            continue
        total_fetched += len(country_news)
        for art in country_news:
            url = art["url"]
            if not is_new_article(url):
                continue
            try:
                emotion = headline_emotion({
                    "text": art["headline"],
                    "source_country": art["source_country"],
                    "published": art["date"]
                })
                label = emotion["sentiment"]["label"]
                confidence = emotion["sentiment"]["confidence"]
            except Exception as e:
                logger.error(f"Sentiment analysis failed for url={url}: {e}")
                continue
            try:
                save_article(url, art["headline"], art["source_country"], art["date"], label, confidence)
            except Exception as e:
                logger.error(f"DB save failed for url={url}: {e}")
                continue
            processed.append({
                "url": url,
                "headline": art["headline"],
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
        articles = get_latest_articles(min_count=100, hours=1)
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

def print_country_counts(processed_news: List[Dict[str, Any]]) -> None:
    """
    Print the number of articles per country.
    """
    country_counts = {}
    for row in processed_news:
        country = row['source_country']
        country_counts[country] = country_counts.get(country, 0) + 1
    logger.info("News count by country:")
    for country, count in sorted(country_counts.items()):
        logger.info(f"{country}: {count}")

def print_articles(processed_news: List[Dict[str, Any]]) -> None:
    """
    Print article details to the terminal.
    """
    for i, row in enumerate(processed_news, 1):
        logger.info(f"[{i:02d}] [{row['timestamp']} @{row['source_country']}] "
                    f"[{row['sentiment']['label']}({row['sentiment']['confidence']})] – {row['headline']}")

def main() -> None:
    """
    Orchestrate the full pipeline: fetch, analyze, save, and export articles.
    """
    processed_news, total_news = fetch_and_process_articles(
        timespan="1days", num_records=250, countries=DEFAULT_COUNTRIES
    )
    logger.info(f"Total news articles found: {total_news}")
    logger.info(f"Number of new articles processed: {len(processed_news)}")
    print_country_counts(processed_news)
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