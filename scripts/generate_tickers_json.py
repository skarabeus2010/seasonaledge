"""
generate_tickers_json.py — regeneriert landing/data/tickers.json aus SYMBOLS.

Die tickers.json wird vom Frontend fuer Autocomplete (alle Pages) und
fuer den Scanner als Metadata-Quelle genutzt (Name + Kategorie pro Ticker,
client-side Join mit scanner_results aus Supabase).

Format (minimiert fuer kleinen Download):
  [
    { "t": "AAPL", "n": "Apple", "k": "US-Aktie" },
    { "t": "SPY",  "n": "SPDR S&P 500 ETF Trust", "k": "US-ETF" },
    ...
  ]

  t = ticker
  n = name (display)
  k = kategorie

Usage:
  py scripts/generate_tickers_json.py
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from shared.symbols import SYMBOLS, get_display_name  # type: ignore

OUT = REPO / "landing" / "data" / "tickers.json"


def main() -> None:
    entries = []
    for ticker in sorted(SYMBOLS.keys()):
        info = SYMBOLS[ticker]
        entries.append({
            "t": ticker,
            "n": info.get("name") or get_display_name(ticker),
            "k": info.get("kategorie", "Sonstige"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(entries, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    categories = {}
    for e in entries:
        categories[e["k"]] = categories.get(e["k"], 0) + 1

    print(f"[OK] {OUT.relative_to(REPO)} ({len(entries)} Ticker, {OUT.stat().st_size} Bytes, UTF-8)")
    print("  Kategorien:")
    for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
        print(f"    {cat:<20} {count:>4}")


if __name__ == "__main__":
    main()
