import json
from datetime import datetime
from src.api.emotion_utils import analyze_headline_emotion
from src.api.db import save_article, get_latest_articles, init_db
from src.api.translation_api import translate_text

init_db()

def convert_timestamp(ts: str) -> str:
    try:
        dt = datetime.strptime(ts.replace(" UTC", ""), "%Y-%m-%d %H:%M")
        return dt.strftime("%Y%m%dT%H%M%SZ")
    except Exception as e:
        print(f"Timestamp 변환 실패: {ts} ({e})")
        return "19700101T000000Z"

with open("news_sentiment_20250607_200925.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for i, item in enumerate(data):
    url = f"test_url_{i}"
    headline = item.get("headline", "")
    source_country = item.get("sourcecountry", "TEST")
    raw_ts = item.get("timestamp", "2025-01-01 00:00 UTC")
    timestamp = convert_timestamp(raw_ts)
    headline_ko = translate_text(headline, "ko")
    emotion = analyze_headline_emotion({
        "text": headline_ko,
        "source_country": source_country,
        "published": timestamp
    })
    label = emotion["sentiment"]["label"]
    confidence = emotion["sentiment"]["confidence"]
    save_article(url, headline_ko, source_country, timestamp, label, confidence)

print("DB 저장 완료!")

latest = get_latest_articles(min_count=100, hours=24)
print(f"DB에서 불러온 최신 {len(latest)}개 기사 예시:")
for row in latest[:5]:
    print(row)
    