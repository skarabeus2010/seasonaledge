"""
SeasonAlpha — Backfill: Open/High/Low in prices-Tabelle
=========================================================
Laedt fuer jeden Ticker die vollstaendigen OHLCV-Daten von Yahoo Finance
und aktualisiert fehlende Open/High/Low-Werte in Supabase.

Historische Daten die bereits Open/High/Low haben werden NICHT ueberschrieben
(nur NULL-Werte werden gefuellt).

Einmalig ausfuehren: py scripts/backfill_ohlc.py
"""

import sys, os, pathlib

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

try:  # Windows: UTF-8 erzwingen (cp1252-Crash bei Datei-Umleitung vermeiden)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
from shared.supabase_client import get_client, fetch_prices, upsert_prices
from shared.yahoo_downloader import download_data
from shared.symbols import get_all_tickers


def backfill_ticker(ticker: str) -> dict:
    """Fuellt fehlende Open/High/Low/log_return fuer einen Ticker.

    Returns:
        dict mit updated, skipped, total Counts.
    """
    # 1. Bestehende Supabase-Daten laden
    db_records = fetch_prices(ticker)
    if not db_records:
        return {"updated": 0, "skipped": 0, "total": 0}

    db_df = pd.DataFrame(db_records)
    db_df["date"] = pd.to_datetime(db_df["date"])
    db_df = db_df.set_index("date").sort_index()

    # Pruefen welche Zeilen Open fehlt
    if "open" not in db_df.columns:
        missing_dates = db_df.index
    else:
        db_df["open"] = pd.to_numeric(db_df["open"], errors="coerce")
        missing_dates = db_df[db_df["open"].isna()].index

    if len(missing_dates) == 0:
        return {"updated": 0, "skipped": len(db_df), "total": len(db_df)}

    # 2. Vollstaendige OHLCV von Yahoo laden (adjusted)
    yahoo_df = download_data(ticker, period="max")
    if yahoo_df is None or yahoo_df.empty:
        return {"updated": 0, "skipped": len(db_df), "total": len(db_df)}

    # log_return berechnen
    yahoo_df["log_return"] = np.log(yahoo_df["Close"] / yahoo_df["Close"].shift(1))

    # 3. Nur fehlende Zeilen aktualisieren
    updates = []
    for dt in missing_dates:
        if dt not in yahoo_df.index:
            continue

        yrow = yahoo_df.loc[dt]
        db_close = float(db_df.loc[dt, "close"]) if "close" in db_df.columns else None

        rec = {
            "ticker": ticker,
            "date": dt.strftime("%Y-%m-%d"),
            "close": round(float(yrow["Close"]), 4),
            "source": "yahoo",
        }

        for col in ["Open", "High", "Low"]:
            if col in yrow.index and pd.notna(yrow[col]):
                rec[col.lower()] = round(float(yrow[col]), 4)

        if "Volume" in yrow.index and pd.notna(yrow["Volume"]):
            rec["volume"] = int(yrow["Volume"])

        if "log_return" in yrow.index and pd.notna(yrow["log_return"]):
            rec["log_return"] = round(float(yrow["log_return"]), 8)

        updates.append(rec)

    # 4. Batch-Upsert (500 pro Chunk)
    chunk_size = 500
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i + chunk_size]
        upsert_prices(chunk)

    return {"updated": len(updates), "skipped": len(db_df) - len(missing_dates), "total": len(db_df)}


def main():
    print("=" * 60)
    print("SeasonAlpha — Backfill Open/High/Low")
    print("=" * 60)

    # Ticker aus symbols.py — prices-Full-Scan timeoutet auf grosser DB (57014)
    all_tickers = get_all_tickers()
    print(f"Gefunden: {len(all_tickers)} Ticker\n")

    total_updated = 0
    total_skipped = 0
    for i, ticker in enumerate(all_tickers, 1):
        try:
            result = backfill_ticker(ticker)
            total_updated += result["updated"]
            total_skipped += result["skipped"]
            status = f"{result['updated']:5d} aktualisiert, {result['skipped']:5d} bereits OK"
            print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — {status}")
        except Exception as e:
            print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — FEHLER: {e}")

    print(f"\nFertig: {total_updated} Zeilen aktualisiert, {total_skipped} bereits vollstaendig.")


if __name__ == "__main__":
    main()
