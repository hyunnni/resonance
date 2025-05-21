"""
news2emotion.py
  1) NewsAPI 헤드라인 수집
  2) GoEmotions 감정 추론
  3) JSON 출력
환경변수:
  NEWS_API_KEY (.env에서 로드)
"""
import os, json
from datetime import datetime, timezone
from dotenv import load_dotenv; load_dotenv()

from newsapi import NewsApiClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# ── 0. 세팅 ──────────────────────────────────────────
NEWS_KEY = os.getenv("NEWS_API_KEY")
newsapi  = NewsApiClient(api_key=NEWS_KEY)

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
  from sentiment_nli import nli_sentiment

# ── 1. 뉴스 가져오기 ────────────────────────────────
def fetch_latest(country = "us", page_size = 20):
  res = newsapi.get_top_headlines(country = country, page_size = page_size)
  for art in res["articles"]:
    title = art["title"] or ""
    desc = art.get("description") or ""
    text = f"{title}. {desc}".strip()
    if text:
      yield text

# ── 2. 감정 추론 ────────────────────────────────
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
def headline_emotion(text: str) -> dict:
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
    
    top3   = torch.topk(probs, 3)
    return {
        "headline": text,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sentiment": { "label": sent_final, "confidence": conf_final },
        "top3": [
            {"label": LABELS[int(idx)], "prob": round(float(p), 3)}
            for p, idx in zip(top3.values, top3.indices)
        ]
    }

# ── 3. 실행부 ────────────────────────────────────────
def main(country="us", page_size=10):
    data = [headline_emotion(text) for text in fetch_latest(country, page_size)]
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()