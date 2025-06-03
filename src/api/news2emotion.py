import os, json
from dotenv import load_dotenv; load_dotenv()
from typing import List, Optional, Set
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
                 ):
  
    for art in fetch_gdelt(_seen,
                           timespan=timespan,
                           num_records=num_records,
                           countries=countries):
        yield {
            "text": art["headline"],
            "published": art["date"]
        }

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
        "sentiment": {
                      "label": sent_final, 
                      "confidence": conf_final 
                      },
        "top3": {
            LABELS[int(idx)]: round(float(p), 3)
            for p, idx in zip(top3.values, top3.indices)
        }
    }

# 3. 실행 
def main():
    rows = [headline_emotion(it) for it in fetch_latest(
                timespan="1hours", num_records=50,
                countries=["US","UK","KS","KN"])]

    
    # print(json.dumps(rows, ensure_ascii=False, indent=2))

    for row in rows:
        top3 = ', '.join(f'{k}:{v}' for k, v in row['top3'].items())
        print(f"[{row['timestamp']}] {row['sentiment']['label']}"
              f"({row['sentiment']['confidence']}) – {row['headline']}")
        print(f"   ↳ {top3}\n")

if __name__ == "__main__":
    main()