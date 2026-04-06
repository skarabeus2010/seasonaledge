#!/usr/bin/env python3
"""
SeasonAlpha — Backfill New Ticker (Full Historical Load)
=========================================================
Laedt einen NEUEN Ticker komplett in Supabase:
- Yahoo Finance historische OHLCV (period='max')
- Split+Dividend-adjustiert (via yahoo_downloader)
- Upsert in prices-Tabelle (ticker, date, open, high, low, close, volume, log_return)
- Berechnet TDOM + TDOY boersenspezifisch (via is_trading_day)
- Schreibt ticker-Metadata in tickers-Tabelle (aus SYMBOLS)

Aufruf:
  py scripts/backfill_new_ticker.py V1X.DE
  py scripts/backfill_new_ticker.py V1X.DE ^VDAX    # mehrere auf einmal

Der Ticker muss bereits in shared/symbols.py SYMBOLS registriert sein.
"""
from __future__ import annotations

import sys, os, pathlib

try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd
from datetime import datetime, timezone

from shared.yahoo_downloader import download_data
from shared.supabase_client import get_client, upsert_prices, upsert_tickers
from shared.symbols import SYMBOLS, get_exchange_for_holidays
from shared.exchange_holidays import is_trading_day


def compute_tdoy_tdom(dates: list, exchange: str) -> dict:
    """Berechnet TDOM + TDOY fuer sortierte Date-Liste. Returns: {date_str: (tdom, tdoy)}."""
    result = {}
    tdoy_counter = 0
    tdom_counter = 0
    current_year = None
    current_month = None

    for d in dates:
        if d.year != current_year:
            current_year = d.year
            tdoy_counter = 0
            current_month = d.month
            tdom_counter = 0
        if d.month != current_month:
            current_month = d.month
            tdom_counter = 0

        if is_trading_day(d, exchange):
            tdoy_counter += 1
            tdom_counter += 1

        result[d.strftime("%Y-%m-%d")] = (tdom_counter, tdoy_counter)

    return result


def backfill_ticker(ticker: str) -> dict:
    """Volle historische Last fuer einen neuen Ticker."""
    print(f"\n{'=' * 60}")
    print(f"  {ticker}")
    print(f"{'=' * 60}")

    # 1. Metadaten aus SYMBOLS
    if ticker not in SYMBOLS:
        return {"ok": False, "error": f"{ticker} nicht in SYMBOLS registriert"}
    sym_info = SYMBOLS[ticker]
    exchange_hol = get_exchange_for_holidays(ticker)
    print(f"  Exchange: {exchange_hol}")
    print(f"  Kategorie: {sym_info['kategorie']}")

    # 2. Ticker-Metadata in tickers-Tabelle
    try:
        now = datetime.now(timezone.utc).isoformat()
        upsert_tickers([{
            "ticker": ticker,
            "name": sym_info["name"],
            "kategorie": sym_info["kategorie"],
            "waehrung": sym_info.get("währung", "USD"),
            "exchange": sym_info.get("exchange", ""),
            "beschreibung": sym_info.get("beschreibung", ""),
            "aktiv": True,
            "updated_at": now,
        }])
        print(f"  ✓ tickers-Metadata geschrieben")
    except Exception as e:
        print(f"  ! tickers-Metadata fehlgeschlagen: {e}")

    # 3. Yahoo Finance Download (period='max', split+div-adjusted)
    print(f"  Lade Yahoo Finance...")
    df = download_data(ticker, period="max")
    if df is None or df.empty:
        return {"ok": False, "error": "Yahoo lieferte keine Daten"}

    print(f"  ✓ {len(df)} Zeilen von {df.index[0].date()} bis {df.index[-1].date()}")

    # 4. log_return berechnen
    df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))

    # 5. TDOM/TDOY berechnen (boersenspezifisch)
    print(f"  Berechne TDOM/TDOY (Exchange: {exchange_hol})...")
    dates = sorted([d.date() for d in df.index])
    tdoy_map = compute_tdoy_tdom(dates, exchange_hol)

    # 6. Records bauen
    records = []
    for dt, row in df.iterrows():
        ds = dt.strftime("%Y-%m-%d")
        tdom, tdoy = tdoy_map.get(ds, (None, None))

        close_val = row.get("Close")
        if pd.isna(close_val):
            continue

        rec = {
            "ticker": ticker,
            "date": ds,
            "close": round(float(close_val), 4),
            "source": "yahoo",
        }
        for col in ["Open", "High", "Low"]:
            if col in row.index and pd.notna(row[col]):
                rec[col.lower()] = round(float(row[col]), 4)
        if "Volume" in row.index and pd.notna(row["Volume"]):
            try:
                rec["volume"] = int(row["Volume"])
            except (ValueError, OverflowError):
                pass
        if "log_return" in row.index and pd.notna(row["log_return"]):
            rec["log_return"] = round(float(row["log_return"]), 8)
        if tdom is not None and tdom > 0:
            rec["tdom"] = int(tdom)
        if tdoy is not None and tdoy > 0:
            rec["tdoy"] = int(tdoy)

        records.append(rec)

    print(f"  ✓ {len(records)} Records vorbereitet")

    # 7. Batch-Upsert (500er Chunks)
    chunk_size = 500
    total_written = 0
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            upsert_prices(chunk)
            total_written += len(chunk)
            print(f"  … {total_written}/{len(records)} geschrieben")
        except Exception as e:
            print(f"  ! Upsert-Fehler (Chunk {i}): {e}")

    print(f"  ✓ Fertig: {total_written} Zeilen in Supabase")
    return {
        "ok": True,
        "rows": total_written,
        "from": str(df.index[0].date()),
        "to": str(df.index[-1].date()),
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nFEHLER: Mindestens ein Ticker als Argument erforderlich.")
        print("Beispiel: py scripts/backfill_new_ticker.py V1X.DE")
        sys.exit(1)

    tickers = sys.argv[1:]
    print(f"\n{'#' * 60}")
    print(f"# SeasonAlpha — Backfill {len(tickers)} neue Ticker")
    print(f"# {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#' * 60}")

    summary = []
    for ticker in tickers:
        try:
            result = backfill_ticker(ticker)
            summary.append((ticker, result))
        except Exception as e:
            print(f"\n! FATAL {ticker}: {e}")
            import traceback
            traceback.print_exc()
            summary.append((ticker, {"ok": False, "error": str(e)}))

    print(f"\n{'#' * 60}")
    print(f"# ZUSAMMENFASSUNG")
    print(f"{'#' * 60}")
    for ticker, res in summary:
        if res.get("ok"):
            print(f"  ✓ {ticker:15s} {res['rows']:6d} Zeilen  {res['from']} → {res['to']}")
        else:
            print(f"  ✗ {ticker:15s} FEHLER: {res.get('error', 'unbekannt')}")


if __name__ == "__main__":
    main()
