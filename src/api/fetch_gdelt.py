from __future__ import annotations

import logging
from typing import List, Dict, Any

import pandas as pd
from gdeltdoc import GdeltDoc, Filters

__all__ = ["fetch_gdelt"]

GDOC = GdeltDoc()
MIN_LEN = 15

def fetch_gdelt(
    seen: set[str] | None = None,
    *,
    timespan: str = "1hours",
    num_records: int = 250,
    countries: list[str] | None = None,
) -> List[Dict[str, Any]]:
    filt = Filters(timespan=timespan, num_records=num_records,
                   country=countries or [])
    try:
        df: pd.DataFrame = GDOC.article_search(filt)
    except Exception as exc:
        logging.warning("gdeltdoc fetch failed: %s", exc)
        return []

    keep_langs = {"english"}
    df = df[df["language"].str.lower().isin(keep_langs)]

    fresh: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        url = str(row.get("url", ""))
        if not url or (seen is not None and url in seen):
            continue
        if seen is not None:
            seen.add(url)
        
        date = str(row.get("seendate") or "")
        headline = str(row.get("title") or "").strip()
        if len(headline) < MIN_LEN:
            continue
        
        fresh.append({
            "url": url,
            "headline": headline,
            "date" : date
        })

    return fresh