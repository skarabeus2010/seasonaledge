#!/usr/bin/env python3
"""
SeasonAlpha — Backfill TDOM/TDOY
=================================
Berechnet TDOM (Trading Day of Month) und TDOY (Trading Day of Year)
fuer alle Zeilen in der prices-Tabelle und schreibt sie zurueck.

Nutzt den boersenspezifischen Feiertagskalender pro Ticker.

Aufruf:  py scripts/backfill_tdoy.py
"""
from __future__ import annotations

import sys, os, pathlib

# -- Projekt-Root finden --
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

from datetime import date, datetime, timedelta
from shared.supabase_client import get_client
from shared.exchange_holidays import is_trading_day
from shared.symbols import SYMBOLS, get_exchange_for_holidays

print("=" * 60)
print("SeasonAlpha — Backfill TDOM/TDOY")
print("=" * 60)
print(datetime.now())


def compute_tdoy_tdom(dates: list[date], exchange: str) -> list[dict]:
    """Berechnet TDOM + TDOY fuer eine sortierte Liste von Dates."""
    results = []
    tdoy_counter = 0
    tdom_counter = 0
    current_year = None
    current_month = None

    for d in dates:
        # Jahr/Monat Reset
        if d.year != current_year:
            current_year = d.year
            tdoy_counter = 0
            current_month = d.month
            tdom_counter = 0
        if d.month != current_month:
            current_month = d.month
            tdom_counter = 0

        # Nur Handelstage zaehlen
        if is_trading_day(d, exchange):
            tdoy_counter += 1
            tdom_counter += 1

        results.append({"date": d, "tdom": tdom_counter, "tdoy": tdoy_counter})

    return results


def backfill_ticker(client, ticker: str, exchange: str) -> int:
    """Backfill TDOM/TDOY fuer einen Ticker. Returns: Anzahl aktualisierter Zeilen."""

    # Alle Rows fuer diesen Ticker laden (date + close fuer Upsert)
    all_rows = []
    page_size = 1000
    offset = 0
    while True:
        result = (client.table("prices")
                  .select("date,close")
                  .eq("ticker", ticker)
                  .order("date")
                  .range(offset, offset + page_size - 1)
                  .execute())
        if not result.data:
            break
        all_rows.extend(result.data)
        if len(result.data) < page_size:
            break
        offset += page_size

    if not all_rows:
        return 0

    all_dates = [date.fromisoformat(r["date"]) for r in all_rows]

    # TDOM/TDOY berechnen
    td_values = compute_tdoy_tdom(all_dates, exchange)

    # In Batches zurueckschreiben (Upsert MIT close → NOT NULL constraint OK)
    batch_size = 500
    total_updated = 0

    for i in range(0, len(td_values), batch_size):
        batch = td_values[i:i + batch_size]
        records = []
        for j, v in enumerate(batch):
            row_idx = i + j
            records.append({
                "ticker": ticker,
                "date": v["date"].isoformat(),
                "close": all_rows[row_idx]["close"],  # Bestehenden Close mitgeben
                "tdom": v["tdom"],
                "tdoy": v["tdoy"],
            })
        try:
            client.table("prices").upsert(
                records,
                on_conflict="ticker,date"
            ).execute()
            total_updated += len(records)
        except Exception as e:
            print(f"    ⚠ Batch-Fehler bei {ticker}: {e}")

    return total_updated


def main():
    client = get_client()

    # Alle Ticker aus SYMBOLS
    tickers = sorted(SYMBOLS.keys())
    print(f"\nGefunden: {len(tickers)} Ticker\n")

    total_rows = 0
    total_fixed = 0

    for idx, ticker in enumerate(tickers, 1):
        exchange = get_exchange_for_holidays(ticker)
        updated = backfill_ticker(client, ticker, exchange)

        if updated > 0:
            total_fixed += 1
            total_rows += updated
            print(f"  [{idx:3d}/{len(tickers)}] {ticker:<12s} — ✓ {updated:6d} Zeilen ({exchange})")
        else:
            print(f"  [{idx:3d}/{len(tickers)}] — ⚠ Übersprungen (keine Daten)")

    print(f"\n{'=' * 60}")
    print(f"Fertig: {total_fixed} Ticker, {total_rows} Zeilen aktualisiert")


if __name__ == "__main__":
    main()
