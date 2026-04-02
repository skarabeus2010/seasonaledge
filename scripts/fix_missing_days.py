#!/usr/bin/env python3
"""
SeasonAlpha — Fix Missing Trading Days

Prüft alle Ticker auf fehlende Handelstage in Supabase und lädt
die Lücken automatisch von Yahoo nach. Anschließend TDOM/TDOY
neu berechnen (backfill_tdoy.py separat laufen lassen).

Nutzung:
    python scripts/fix_missing_days.py              # Alle Ticker
    python scripts/fix_missing_days.py --ticker AAPL  # Nur ein Ticker
    python scripts/fix_missing_days.py --dry-run    # Nur prüfen, nichts schreiben
    python scripts/fix_missing_days.py --year 2026  # Nur ein Jahr prüfen
"""

import sys
import os
import pathlib
import time
from datetime import date, timedelta

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd
from shared.supabase_client import get_client, upsert_prices
from shared.symbols import SYMBOLS, get_exchange_for_holidays
from shared.exchange_holidays import is_trading_day


def get_expected_trading_days(exchange, year_start, year_end):
    """Alle erwarteten Handelstage für eine Börse im Zeitraum."""
    days = []
    d = year_start
    while d <= year_end:
        if is_trading_day(d, exchange):
            days.append(d)
        d += timedelta(days=1)
    return days


def get_db_dates(client, ticker, year_start, year_end):
    """Alle Dates für einen Ticker aus Supabase (paginiert)."""
    all_dates = set()
    page_size = 1000
    offset = 0
    while True:
        result = (client.table("prices")
                  .select("date")
                  .eq("ticker", ticker)
                  .gte("date", year_start.strftime("%Y-%m-%d"))
                  .lte("date", year_end.strftime("%Y-%m-%d"))
                  .order("date")
                  .range(offset, offset + page_size - 1)
                  .execute())
        if not result.data:
            break
        for row in result.data:
            all_dates.add(row["date"])
        if len(result.data) < page_size:
            break
        offset += page_size
    return all_dates


def download_and_fill(ticker, missing_dates, dry_run=False):
    """Lädt fehlende Tage von Yahoo und schreibt sie in Supabase."""
    if not missing_dates:
        return 0

    if dry_run:
        return len(missing_dates)

    from shared.yahoo_downloader import download_data

    # Zeitraum bestimmen: ältester fehlender Tag bis heute + Puffer
    min_date = min(missing_dates)
    max_date = max(missing_dates)
    days_back = (date.today() - min_date).days + 5

    # Yahoo-Perioden: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    if days_back <= 25:
        period = "1mo"
    elif days_back <= 80:
        period = "3mo"
    elif days_back <= 170:
        period = "6mo"
    elif days_back <= 350:
        period = "1y"
    elif days_back <= 700:
        period = "2y"
    elif days_back <= 1800:
        period = "5y"
    else:
        period = "max"

    df = download_data(ticker, period=period)
    if df is None or df.empty:
        return 0

    # Index normalisieren (Yahoo hat manchmal Uhrzeiten)
    df.index = df.index.normalize()

    missing_set = set(d.strftime("%Y-%m-%d") for d in missing_dates)
    records = []

    for idx, row in df.iterrows():
        d_str = idx.strftime("%Y-%m-%d")
        if d_str not in missing_set:
            continue
        if pd.isna(row.get("Close")):
            continue

        rec = {
            "ticker": ticker,
            "date": d_str,
            "close": round(float(row["Close"]), 4),
            "source": "yahoo",
        }
        for col in ["Open", "High", "Low"]:
            if col in row and pd.notna(row[col]):
                rec[col.lower()] = round(float(row[col]), 4)
        if "Volume" in row and pd.notna(row["Volume"]):
            rec["volume"] = int(row["Volume"])
        # log_return
        rec["log_return"] = None  # Wird beim nächsten preprocess() berechnet

        records.append(rec)

    if records:
        # Batch-Upsert (500er Batches)
        for i in range(0, len(records), 500):
            batch = records[i:i+500]
            try:
                upsert_prices(batch)
            except Exception as e:
                print(f"    ⚠ Batch-Fehler bei {ticker}: {e}")

    return len(records)


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    single_ticker = None
    check_year = date.today().year

    for i, arg in enumerate(args):
        if arg == "--ticker" and i + 1 < len(args):
            single_ticker = args[i + 1]
        if arg == "--year" and i + 1 < len(args):
            check_year = int(args[i + 1])

    print("=" * 60)
    print(f"  SeasonAlpha — Fix Missing Trading Days")
    print(f"  Jahr: {check_year}")
    if dry_run:
        print("  ** DRY RUN — nur prüfen, nichts schreiben **")
    if single_ticker:
        print(f"  Ticker: {single_ticker}")
    print("=" * 60)

    client = get_client()

    # Ticker-Liste
    if single_ticker:
        tickers = [single_ticker]
    else:
        tickers = sorted(SYMBOLS.keys())

    year_start = date(check_year, 1, 1)
    year_end = min(date(check_year, 12, 31), date.today())

    total_missing = 0
    total_fixed = 0
    tickers_with_gaps = []

    for i, ticker in enumerate(tickers, 1):
        exchange = get_exchange_for_holidays(ticker)

        # DB-Dates holen
        db_dates = get_db_dates(client, ticker, year_start, year_end)
        if len(db_dates) < 5:
            print(f"  [{i:3d}/{len(tickers)}] {ticker:12s} — ⚠ Übersprungen (< 5 Zeilen in DB)")
            continue

        # Erste und letzte DB-Date bestimmen (nur innerhalb der DB-Range prüfen)
        db_min = min(db_dates)
        db_max = max(db_dates)
        range_start = max(year_start, date.fromisoformat(db_min))
        range_end = min(year_end, date.fromisoformat(db_max))

        # Erwartete Handelstage
        expected = get_expected_trading_days(exchange, range_start, range_end)
        expected_set = set(d.strftime("%Y-%m-%d") for d in expected)

        # Fehlende Tage
        missing = [d for d in expected if d.strftime("%Y-%m-%d") not in db_dates]

        if not missing:
            print(f"  [{i:3d}/{len(tickers)}] {ticker:12s} — ✓ OK ({len(db_dates)} Zeilen, {exchange})")
            continue

        total_missing += len(missing)
        tickers_with_gaps.append((ticker, len(missing)))

        # Nachladen
        filled = download_and_fill(ticker, missing, dry_run)
        total_fixed += filled

        status = "geprüft" if dry_run else "nachgeladen"
        print(f"  [{i:3d}/{len(tickers)}] {ticker:12s} — ⚡ {len(missing)} fehlend, {filled} {status} ({exchange})")

        # Rate-Limiting (Yahoo)
        if not dry_run and filled > 0:
            time.sleep(0.5)

    print(f"\n{'=' * 60}")
    print(f"  Ergebnis: {len(tickers_with_gaps)} Ticker mit Lücken")
    print(f"  Fehlende Tage gesamt: {total_missing}")
    print(f"  Nachgeladen: {total_fixed}")
    if tickers_with_gaps:
        print(f"\n  Ticker mit Lücken:")
        for t, n in sorted(tickers_with_gaps, key=lambda x: -x[1]):
            print(f"    {t:12s}: {n} fehlende Tage")
    print(f"\n  ⚠ TDOM/TDOY Backfill nochmal laufen lassen!")
    print(f"    python scripts/backfill_tdoy.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
