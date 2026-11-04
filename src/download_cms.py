"""Download a documented slice from the CMS Provider Data API.

Dataset: Medicare Physician & Other Practitioners - by Provider
API dataset UUID: 44ea2789-993f-4d55-ac44-ed7f160b58fa
Endpoint: https://data.cms.gov/data-api/v1/dataset/{uuid}/data
  ?size=1000&offset={offset}

Usage:
    python3 src/download_cms.py --n 5000 --out data/raw_cms_first5000.json

This script was run on 2026-11-04 to fetch the FIRST 5,000 rows
returned by the API in its default order (no filter, no sort).
That slice is documented in DATA_SOURCES.md and in metrics.json.
The raw API file contains provider names / NPIs and is NOT
committed to this repo; src/build_sample.py anonymises it.
"""

import argparse
import json
import pathlib
import time
import urllib.request

UUID = "44ea2789-993f-4d55-ac44-ed7f160b58fa"
BASE = f"https://data.cms.gov/data-api/v1/dataset/{UUID}/data"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--out", default="data/raw_cms_first5000.json")
    args = ap.parse_args()
    rows = []
    for offset in range(0, args.n, 1000):
        url = f"{BASE}?size=1000&offset={offset}"
        with urllib.request.urlopen(url, timeout=60) as r:
            batch = json.load(r)
        print(f"offset {offset}: {len(batch)} rows")
        rows.extend(batch)
        time.sleep(0.5)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rows))
    print(f"Wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
