from __future__ import annotations
import argparse, textwrap
from datetime import datetime, timezone

from ..api.fetch_gdelt import fetch_gdelt

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--timespan", default="1hours")
    p.add_argument("--max", type=int, default=250, metavar="N")
    p.add_argument("--countries", nargs="*", default= ["US", "UK", "KS", "KN"],
                   help="ISO2 publisher country codes")
    return p.parse_args()

def main():
    args = parse_args()
    arts = fetch_gdelt(set(), timespan=args.timespan,
                           num_records=args.max,
                           countries=args.countries)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    print(f"{now}  {len(arts)} articles (eng or kor)\n")
    for art in arts[:20]:  # preview first 20
        headline = textwrap.shorten(art['headline'], 100)
        date = art['date']
        print(f"-{headline} @{date}")

if __name__ == "__main__":
    main()