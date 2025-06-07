import os, json
from dotenv import load_dotenv; load_dotenv()
from typing import List, Optional, Set, Tuple, Dict, Any
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

from .fetch_gdelt import fetch_gdelt

MODEL_ID = "SamLowe/roberta-base-go_emotions"

tok = AutoTokenizer.from_pretrained(MODEL_ID)
mdl = AutoModelForSequenceClassification.from_pretrained(MODEL_ID).eval()
LABELS = mdl.config.id2label

POS_SET = {
    "admiration","amusement","approval","caring","excitement",
    "gratitude","joy","love","optimism","pride","relief","surprise"
}
NEG_SET = {
    "anger","annoyance","disappointment","disapproval","disgust",
    "embarrassment","fear","grief","nervousness","remorse","sadness"
}
NEU_LABEL = "neutral"
NEU_ID = [i for i, l in LABELS.items() if 1 == NEU_LABEL[0]]

NEU_FACTOR = 0.3
THRESH = 0.10

USE_NLI = True
ALPHA = 0.6

if USE_NLI:
  from .sentiment_nli import nli_sentiment

# 헤드라인 수집
_seen : Set[str] = set()  # 중복 방지
def fetch_latest(
                 *,
                 timespan: str = "1hours",
                 num_records: int = 250,
                 countries: Optional[List[str]] = None
                 ) -> Tuple[List[Dict[str, Any]], int]:
    if not countries:
        countries = ["US","UK","KS","KN","JA","CH","GM","FR","RS","IN","BR"]
    
    # 국가별 고르게 뉴스 수집 
    records_per_country = num_records // len(countries)
    processed = []
    total_fetched = 0
    
    for country in countries:
        country_news = fetch_gdelt(_seen,
                                timespan=timespan,
                                num_records=records_per_country,
                                countries=[country])
        total_fetched += len(country_news)
        
        for art in country_news:
            processed.append({
                "text": art["headline"],
                "source_country" : art["source_country"],
                "published": art["date"]
            })
    
    return processed, total_fetched

# 2. 감정 추론
def sentiment_score(probs: torch.Tensor):
  
  probs = probs.clone()
  probs[NEU_ID] *= NEU_FACTOR
  probs = probs / probs.sum()
  
  pos = probs[[i for i, l in LABELS.items() if l in POS_SET]].sum()
  neg = probs[[i for i, l in LABELS.items() if l in NEG_SET]].sum()
  
  confidence = round(float(abs(pos - neg)), 3)
  
  if pos > neg + THRESH:
    return "positive", confidence
  if neg > pos + THRESH:
    return "negative", confidence
  return "neutral", confidence
  
@torch.no_grad()
def headline_emotion(item: dict) -> dict:
    text = item["text"]
    ts_iso = item["published"]
    sourcecountry = item["source_country"]
    
    inputs = tok(text, return_tensors="pt", truncation=True, max_length=128)
    probs  = mdl(**inputs).logits.sigmoid()[0]
    
    sent_ge, conf_ge = sentiment_score(probs)
    
    if USE_NLI:
      sent_nli, conf_nli, _ = nli_sentiment(text)
      
      if sent_ge == sent_nli:
        sent_final = sent_ge
        conf_final = round(ALPHA * conf_ge + (1 - ALPHA)*conf_nli, 3)
      else:
        if ALPHA * conf_ge >= (1 - ALPHA) * conf_nli:
          sent_final, conf_final = sent_ge, round(ALPHA * conf_ge , 3)
        else:
          sent_final, conf_final = sent_nli, round((1-ALPHA)*conf_nli, 3)
    else:
      sent_final, conf_final = sent_ge, conf_ge
    
    ts_dt = datetime.strptime(ts_iso, "%Y%m%dT%H%M%SZ")
    ts_txt = ts_dt.strftime("%Y-%m-%d %H:%M UTC")
    
    top3   = torch.topk(probs, 3)
    return {
        "headline": text,
        "timestamp": ts_txt,
        "sourcecountry" : sourcecountry,
        "sentiment": {
                      "label": sent_final,
                      "confidence": conf_final
                      },
    }

# 3. 실행 
def main():
    # 감정 분석 수행
    processed_news, total_news = fetch_latest(
                timespan="1days", num_records=250,
                countries=["US","UK","KS","KN","JA","CH","GM","FR","RS","IN","BR"])
    
    rows = [headline_emotion(it) for it in processed_news]
    
    print(f"\nTotal news articles found: {total_news}")
    
    # 국가별 뉴스 수 출력
    country_counts = {}
    for row in rows:
        country = row['sourcecountry']
        country_counts[country] = country_counts.get(country, 0) + 1
    
    print("\nNews count by country:")
    for country, count in sorted(country_counts.items()):
        print(f"{country}: {count}")
    
    # 터미널 출력
    for i, row in enumerate(rows, 1):
        print(f"[{i:02d}] [{row['timestamp']} @{row['sourcecountry']}] [{row['sentiment']['label']}"
              f"({row['sentiment']['confidence']})] – {row['headline']}")

    # JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"news_sentiment_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults have been saved to {output_file}")
    print(f"Number of analyzed articles: {len(rows)}")
    print(f"Number of filtered out articles: {total_news - len(rows)}")

if __name__ == "__main__":
    main()