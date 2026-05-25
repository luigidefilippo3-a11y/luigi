"""Merge S&P 500 constituents with current market caps into data/sp500.json.

Sources:
- datasets/s-and-p-500-companies (canonical S&P 500 membership)
- Ate329/top-us-stock-tickers (current market caps + prices)
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONSTITUENTS = Path("/tmp/constituents.csv")
MARKETCAPS = Path("/tmp/ate_sp500.csv")
OUT = ROOT / "data" / "sp500.json"


def read_constituents():
    rows = {}
    with CONSTITUENTS.open() as f:
        for r in csv.DictReader(f):
            rows[r["Symbol"]] = {
                "ticker": r["Symbol"],
                "name": r["Security"],
                "sector": r["GICS Sector"],
            }
    return rows


def read_marketcaps():
    caps = {}
    with MARKETCAPS.open() as f:
        for r in csv.DictReader(f):
            sym = r["symbol"].replace("/", ".")
            try:
                caps[sym] = float(r["marketCap"])
            except (TypeError, ValueError):
                continue
    return caps


def main():
    constituents = read_constituents()
    caps = read_marketcaps()

    merged = []
    missing_caps = []
    for ticker, meta in constituents.items():
        cap = caps.get(ticker)
        if cap is None:
            missing_caps.append(ticker)
            cap = 0.0
        merged.append({**meta, "marketCap": cap})

    merged.sort(key=lambda r: r["marketCap"], reverse=True)

    total = sum(r["marketCap"] for r in merged)
    for r in merged:
        r["weight"] = r["marketCap"] / total if total else 0.0

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(merged, separators=(",", ":")))

    print(f"Wrote {OUT} with {len(merged)} stocks ({len(missing_caps)} missing market cap)")
    if missing_caps:
        print("Missing:", ", ".join(missing_caps[:20]), "..." if len(missing_caps) > 20 else "")
    print(f"Top 5: {[(r['ticker'], r['marketCap']) for r in merged[:5]]}")


if __name__ == "__main__":
    sys.exit(main())
