"""
SeasonAlpha — Fix: OHLC Split-Adjustierung in Supabase
========================================================
Vor dem Fix vom 2026-03-20 wurden Open/High/Low OHNE adj_factor gespeichert.
Dieses Script laedt fuer jeden Ticker die adjustierten OHLCV von Yahoo
und UEBERSCHREIBT alle Zeilen in Supabase.

Einmalig ausfuehren: py scripts/fix_ohlc_adjustment.py
"""
from __future__ import annotations

import sys, os, pathlib

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd
from shared.supabase_client import get_client, fetch_prices, upsert_prices
from shared.yahoo_downloader import download_data


def fix_ticker(ticker: str) -> dict:
    """Ueberschreibt OHLC+log_return fuer einen Ticker mit adjustierten Yahoo-Daten.

    Vergleicht Open/Close Ratio — nur Ticker mit defekten Daten werden gefixt.
    """
    # 1. Bestehende Supabase-Daten laden
    db_records = fetch_prices(ticker)
    if not db_records or len(db_records) < 10:
        return {"status": "skip_empty", "updated": 0, "total": 0}

    db_df = pd.DataFrame(db_records)
    db_df["date"] = pd.to_datetime(db_df["date"])
    db_df = db_df.set_index("date").sort_index()

    for col in ["open", "close"]:
        if col in db_df.columns:
            db_df[col] = pd.to_numeric(db_df[col], errors="coerce")

    # 2. Pruefen ob OHLC-Daten defekt sind
    # Check A: Split-Adjustierung (Open/Close Ratio extrem)
    # Check B: Dividend-Adjustierung (mittlere Intraday-Rendite zu weit von 0)
    if "open" in db_df.columns and "close" in db_df.columns:
        ratio = (db_df["open"] / db_df["close"]).dropna()
        if len(ratio) > 50:
            # Split-Check
            extreme_pct = ((ratio > 1.5) | (ratio < 0.67)).mean()
            # Dividend-Check: mittlere Intraday = mean(Close/Open - 1)
            mean_intraday = (1 / ratio - 1).mean() * 100
            if extreme_pct <= 0.005 and abs(mean_intraday) <= 0.15:
                return {"status": "ok", "updated": 0, "total": len(db_df)}

    # 3. Yahoo-Daten laden (adjustiert)
    yahoo_df = download_data(ticker, period="max")
    if yahoo_df is None or yahoo_df.empty:
        return {"status": "yahoo_fail", "updated": 0, "total": len(db_df)}

    # Dates normalisieren (Yahoo hat Uhrzeiten, Supabase nur Datum)
    yahoo_df.index = yahoo_df.index.normalize()
    db_df.index = db_df.index.normalize()
    # Duplikate entfernen (nach normalize koennen doppelte Dates entstehen)
    yahoo_df = yahoo_df[~yahoo_df.index.duplicated(keep="last")]

    # log_return berechnen
    yahoo_df["log_return"] = np.log(yahoo_df["Close"] / yahoo_df["Close"].shift(1))

    # 4. Alle Zeilen in Supabase aktualisieren
    updates = []
    for dt in db_df.index:
        if dt not in yahoo_df.index:
            continue

        yrow = yahoo_df.loc[dt]
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

    # 5. Batch-Upsert (500 pro Chunk)
    chunk_size = 500
    for i in range(0, len(updates), chunk_size):
        chunk = updates[i:i + chunk_size]
        upsert_prices(chunk)

    status = "fixed" if len(updates) > 0 else "no_match"
    return {"status": status, "updated": len(updates), "total": len(db_df)}


def main():
    print("=" * 60)
    print("SeasonAlpha — Fix OHLC Split-Adjustierung")
    print("=" * 60)
    print("Prüft jeden Ticker auf defekte Open/Close Ratios")
    print("und überschreibt OHLC mit adjustierten Yahoo-Daten.\n")

    # Alle Ticker aus prices-Tabelle (paginiert)
    client = get_client()
    all_tickers = set()
    offset = 0
    while True:
        result = (client.table("prices")
                  .select("ticker")
                  .range(offset, offset + 999)
                  .execute())
        if not result.data:
            break
        for r in result.data:
            all_tickers.add(r["ticker"])
        if len(result.data) < 1000:
            break
        offset += 1000

    all_tickers = sorted(all_tickers)
    print(f"Gefunden: {len(all_tickers)} Ticker\n")

    total_fixed = 0
    total_ok = 0
    total_rows = 0

    for i, ticker in enumerate(all_tickers, 1):
        try:
            result = fix_ticker(ticker)
            total_rows += result["updated"]

            if result["status"] == "fixed":
                total_fixed += 1
                print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — ⚡ GEFIXT: {result['updated']:6d} Zeilen überschrieben")
            elif result["status"] == "ok":
                total_ok += 1
                print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — ✓ OK ({result['total']:6d} Zeilen)")
            elif result["status"] == "yahoo_fail":
                print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — ⚠ Yahoo-Download fehlgeschlagen")
            else:
                print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — ⚠ Übersprungen ({result['status']})")

        except Exception as e:
            print(f"  [{i:3d}/{len(all_tickers)}] {ticker:12s} — FEHLER: {e}")

    print(f"\n{'=' * 60}")
    print(f"Ergebnis: {total_fixed} Ticker gefixt, {total_ok} bereits OK")
    print(f"Gesamt: {total_rows} Zeilen aktualisiert")


if __name__ == "__main__":
    main()
