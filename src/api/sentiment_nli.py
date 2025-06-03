from transformers import pipeline

_nli = pipeline(
    "zero-shot-classification",
    model = "facebook/bart-large-mnli",
    device = -1
)
CANDIDATES = ["positive", "negative", "neutral"]

def nli_sentiment(text: str):
    out = _nli(text, CANDIDATES)
    scores = dict(zip(out["labels"], out["scores"]))
    label  = out["labels"][0]
    conf   = round(float(out["scores"][0]), 3)
    return label, conf, scores