"""
SeasonAlpha — Backfill: log_return Spalte in prices-Tabelle
==============================================================
Berechnet ln(close_t / close_{t-1}) fuer alle bestehenden Zeilen
und schreibt den Wert in die Spalte `log_return`.

Voraussetzung: ALTER TABLE prices ADD COLUMN log_return DOUBLE PRECISION;

Einmalig ausfuehren: py scripts/backfill_log_return.py
"""

import sys, os, pathlib

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd
from shared.supabase_client import get_client, fetch_prices, upsert_prices
from shared.symbols import get_all_tickers


def backfill_ticker(ticker: str) -> int:
    """Berechnet log_return fuer einen Ticker und schreibt in Supabase.

    Returns:
        Anzahl aktualisierter Zeilen.
    """
    records = fetch_prices(ticker)
    if not records or len(records) < 2:
        return 0

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    # log_return berechnen
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["log_return"] = np.log(df["close"] / df["close"].shift(1))

    # Batch-Update: Nur Zeilen mit gueltigem log_return
    updates = []
    for _, row in df.iterrows():
        if pd.isna(row["log_return"]):
            continue
        updates.append({
            "ticker": ticker,
            "date": row["date"].strftime("%Y-%m-%d"),
            "close": round(float(row["close"]), 4),
            "log_return": round(float(row["log_return"]), 8),
        })

    # Chunked upsert (500 pro Batch)
    chunk_size = 500
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i + chunk_size]
        upsert_prices(chunk)

    return len(updates)


def main():
    print("=" * 60)
    print("SeasonAlpha — Backfill log_return")
    print("=" * 60)

    # Ticker aus symbols.py (robust gegen fehlende/leere tickers-Tabelle)
    all_tickers = get_all_tickers()

    print(f"Gefunden: {len(all_tickers)} Ticker\n")

    total_updated = 0
    for i, ticker in enumerate(all_tickers, 1):
        try:
            count = backfill_ticker(ticker)
            total_updated += count
            print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — {count:6d} Zeilen aktualisiert")
        except Exception as e:
            print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — FEHLER: {e}")

    print(f"\nFertig: {total_updated} Zeilen insgesamt aktualisiert.")


if __name__ == "__main__":
    main()
