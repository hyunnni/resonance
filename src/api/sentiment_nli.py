# src/api/sentiment_nli.py
"""
Zero-shot NLI 기반 긍/부/중립 추론
모델: facebook/bart-large-mnli
사용 예:
    from sentiment_nli import nli_sentiment
    label, conf, scores = nli_sentiment("Stocks soar on rate cut hopes.")
"""
from transformers import pipeline

# GPU 있으면 device=0, 없으면 -1
_nli = pipeline(
    "zero-shot-classification",
    model = "facebook/bart-large-mnli",
    device = -1
)
CANDIDATES = ["positive", "negative", "neutral"]

def nli_sentiment(text: str):
    out = _nli(text, CANDIDATES)
    scores = dict(zip(out["labels"], out["scores"]))  # 확률 dict
    label  = out["labels"][0]
    conf   = round(float(out["scores"][0]), 3)
    return label, conf, scores
