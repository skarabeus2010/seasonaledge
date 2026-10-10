#!/usr/bin/env python3
"""
SeasonAlpha — Backfill New Ticker (Full Historical Load)
=========================================================
Laedt einen NEUEN Ticker komplett in Supabase:
- Yahoo Finance historische OHLCV (period='max')
- Split+Dividend-adjustiert (via yahoo_downloader)
- Upsert in prices-Tabelle (ticker, date, open, high, low, close, volume, log_return)
- TDOM + TDOY nach Börsenkalender (tdom_tdoy_fuer_ticker) — NUR für neue Zeilen;
  bestehende behalten ihre Werte (historische Korrektur = P5)
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
from shared.exchange_holidays import tdom_tdoy_fuer_ticker


def vorhandene_daten(ticker: str) -> set[str]:
    """Alle Daten, für die `prices` schon eine Zeile hat (seitenweise, 1000er Grenze von PostgREST).

    Bestehende Zeilen behalten ihre TDOM/TDOY — die historische Korrektur ist P5 (eine freigegebene
    Transaktion), nicht die Tail-Reparatur, die check_db_completeness --fix hierüber auslöst (Codex R7).
    Ein Lesefehler bricht ab: ohne diese Menge lässt sich nicht entscheiden, was neu ist.
    """
    client, daten, start = get_client(), set(), 0
    while True:
        r = (client.table("prices").select("date").eq("ticker", ticker)
             .order("date").range(start, start + 999).execute())
        daten.update(x["date"] for x in (r.data or []))
        if len(r.data or []) < 1000:
            return daten
        start += 1000


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

    # 5. TDOM/TDOY nach Börsenkalender (P2) — nur für Zeilen, die es in prices noch nicht gibt
    print(f"  Berechne TDOM/TDOY (Exchange: {exchange_hol})...")
    iso_daten = [d.strftime("%Y-%m-%d") for d in df.index]
    try:
        tdoy_map = dict(zip(iso_daten, tdom_tdoy_fuer_ticker(ticker, iso_daten)))
        schon_da = vorhandene_daten(ticker)
    except Exception as e:
        return {"ok": False, "error": f"TDOM/TDOY bzw. Bestand nicht ermittelbar: {e}"}
    print(f"  {len(schon_da)} Zeilen schon vorhanden — deren TDOM/TDOY bleiben unverändert")

    # 6. Records bauen
    records = []
    for dt, row in df.iterrows():
        ds = dt.strftime("%Y-%m-%d")

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
        if ds not in schon_da:
            # auch 0 (geschlossener Tag vor der ersten Sitzung der Periode) — früher nur Werte > 0
            rec["tdom"], rec["tdoy"] = tdoy_map[ds]

        records.append(rec)

    print(f"  ✓ {len(records)} Records vorbereitet")

    # 7. Batch-Upsert (500er Chunks)
    chunk_size = 500
    total_written = 0
    fehler = []
    for i in range(0, len(records), chunk_size):
        chunk = records[i:i + chunk_size]
        try:
            upsert_prices(chunk)
            total_written += len(chunk)          # erst NACH bestätigtem Schreiben zählen
            print(f"  … {total_written}/{len(records)} geschrieben")
        except Exception as e:
            total_written += getattr(e, "geschrieben", 0)   # bestätigter Teil vor dem Fehler (UpsertTeilfehler)
            fehler.append(f"Chunk {i}: {str(e)[:120]}")
            print(f"  ! Upsert-Fehler (Chunk {i}): {e}")

    if fehler:
        # Früher ok=True trotz gescheiterter Chunks (Codex R7: abgelehnter Upsert → ok=True, rows=0).
        return {"ok": False, "error": f"{len(fehler)} von {(len(records) + chunk_size - 1) // chunk_size} "
                                      f"Chunks nicht geschrieben: {fehler[0]}", "rows": total_written}
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
    # Ein gescheiterter Ticker muss den Lauf rot machen — vorher endete er mit Exit 0
    # und onboard_ticker.py sah einen Erfolg (Codex R4, A3).
    return 1 if any(not res.get("ok") for _, res in summary) else 0


if __name__ == "__main__":
    sys.exit(main())
