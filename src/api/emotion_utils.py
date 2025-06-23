import torch
import logging
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from .sentiment_nli import nli_sentiment
from typing import Tuple, Dict

# --- Config ---
MODEL_ID = "SamLowe/roberta-base-go_emotions"
POS_SET = {
    "admiration","amusement","approval","caring","excitement",
    "gratitude","joy","love","optimism","pride","relief","surprise"
}
NEG_SET = {
    "anger","annoyance","disappointment","disapproval","disgust",
    "embarrassment","fear","grief","nervousness","remorse","sadness"
}
NEU_LABEL = "neutral"
NEU_FACTOR = 0.3
THRESH = 0.10
USE_NLI = True
ALPHA = 0.6

# --- Logging Setup ---
logger = logging.getLogger(__name__)

# --- Model Loading ---
try:
    tok = AutoTokenizer.from_pretrained(MODEL_ID)
    mdl = AutoModelForSequenceClassification.from_pretrained(MODEL_ID).eval()
    LABELS = mdl.config.id2label
    NEU_ID = [i for i, l in LABELS.items() if 1 == NEU_LABEL[0]]
except Exception as e:
    logger.error(f"Failed to load emotion model: {e}")
    raise

def calculate_sentiment_score(probs: torch.Tensor) -> Tuple[str, float]:
    """
    Calculate sentiment label and confidence from model probabilities.
    """
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
def analyze_headline_emotion(item: Dict) -> Dict:
    """
    Run sentiment analysis on a news item dict.
    Returns a dict with headline, timestamp, sourcecountry, and sentiment result.
    """
    try:
        text = item["text"]
        ts_iso = item["published"]
        sourcecountry = item["source_country"]
        inputs = tok(text, return_tensors="pt", truncation=True, max_length=128)
        probs  = mdl(**inputs).logits.sigmoid()[0]
        sent_ge, conf_ge = calculate_sentiment_score(probs)
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
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            "headline": item.get("text", ""),
            "timestamp": item.get("published", ""),
            "sourcecountry": item.get("source_country", ""),
            "sentiment": {
                "label": None,
                "confidence": None
            },
        } 