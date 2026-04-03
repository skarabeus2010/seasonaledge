"""
scripts/data_audit.py — Daten-Audit: Yahoo vs. Supabase
=========================================================
Zeigt fuer jeden Ticker:
  - Yahoo: erster Tag, letzter Tag, Anzahl Zeilen
  - Supabase: erster Tag, letzter Tag, Anzahl Zeilen, log_return NaN-Quote
  - Luecke: wie viele Jahre fehlen in Supabase

Aufruf:  py -m scripts.data_audit
         py -m scripts.data_audit --category Krypto
         py -m scripts.data_audit --ticker ETH-USD BTC-USD
         py -m scripts.data_audit --missing-only
"""

import sys
import os
import pathlib
import argparse
import time

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

# Windows Console Encoding
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import numpy as np
import pandas as pd
from shared.symbols import SYMBOLS
from shared.yahoo_downloader import download_data as yahoo_download


def get_supabase_info(ticker):
    """Supabase-Daten fuer einen Ticker: count, first, last, log_return NaN."""
    try:
        from shared.supabase_client import get_client
        client = get_client()

        # Erster + letzter Tag
        first = client.table("prices").select("date").eq("ticker", ticker) \
            .order("date", desc=False).limit(1).execute()
        last = client.table("prices").select("date").eq("ticker", ticker) \
            .order("date", desc=True).limit(1).execute()
        count = client.table("prices").select("id", count="exact") \
            .eq("ticker", ticker).execute()

        first_date = first.data[0]["date"] if first.data else None
        last_date = last.data[0]["date"] if last.data else None
        n_rows = count.count if count.count else 0

        # log_return NaN-Quote (Sample: letzte 100 Zeilen)
        lr_check = client.table("prices").select("log_return") \
            .eq("ticker", ticker).order("date", desc=True).limit(100).execute()
        lr_data = lr_check.data if lr_check.data else []
        lr_null = sum(1 for r in lr_data if r.get("log_return") is None)
        lr_pct = (lr_null / len(lr_data) * 100) if lr_data else 0

        return {
            "count": n_rows,
            "first": first_date,
            "last": last_date,
            "lr_null_pct": lr_pct,
            "lr_null_n": lr_null,
        }
    except Exception as e:
        return {"error": str(e)}


def get_yahoo_info(ticker):
    """Yahoo-Daten fuer einen Ticker: count, first, last."""
    try:
        df = yahoo_download(ticker, period="max", timeout=15)
        if df is None or df.empty:
            return None
        return {
            "count": len(df),
            "first": str(df.index[0].date()),
            "last": str(df.index[-1].date()),
            "years": int(df.index[-1].year - df.index[0].year + 1),
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Daten-Audit: Yahoo vs. Supabase")
    parser.add_argument("--ticker", nargs="+", help="Nur bestimmte Ticker pruefen")
    parser.add_argument("--category", help="Nur Kategorie (z.B. Krypto, US-Aktien)")
    parser.add_argument("--missing-only", action="store_true",
                        help="Nur Ticker mit fehlenden Daten zeigen")
    parser.add_argument("--no-yahoo", action="store_true",
                        help="Yahoo-Check ueberspringen (nur Supabase)")
    args = parser.parse_args()

    # Ticker-Liste bestimmen
    if args.ticker:
        tickers = args.ticker
    elif args.category:
        tickers = [t for t, info in SYMBOLS.items()
                    if info.get("kategorie", "").lower() == args.category.lower()]
    else:
        tickers = list(SYMBOLS.keys())

    print("=" * 100)
    print(f"  SeasonAlpha Data Audit — {len(tickers)} Ticker")
    print("=" * 100)

    # Header
    print(f"\n{'Ticker':<12} {'Kat':<12} "
          f"{'Yahoo Start':<12} {'Yahoo Ende':<12} {'Y-Rows':>7} {'Y-Jahre':>7}  "
          f"{'DB Start':<12} {'DB Ende':<12} {'DB-Rows':>7} {'LR-NaN':>7}  "
          f"{'Status'}")
    print("-" * 130)

    results = []
    for i, ticker in enumerate(tickers):
        info = SYMBOLS.get(ticker, {})
        kat = info.get("kategorie", "?")[:11]

        # Supabase
        db = get_supabase_info(ticker)

        # Yahoo (optional)
        yh = None
        if not args.no_yahoo:
            yh = get_yahoo_info(ticker)
            time.sleep(0.3)  # Rate-Limit

        # Status bestimmen
        status = ""
        db_count = db.get("count", 0) if "error" not in db else 0
        yh_count = yh.get("count", 0) if yh and "error" not in yh else 0

        if "error" in db:
            status = f"DB-ERR: {db['error'][:30]}"
        elif db_count == 0:
            status = "FEHLT IN DB"
        elif yh and yh_count > 0:
            gap = yh_count - db_count
            if gap > 500:
                status = f"LUECKE: {gap:,} Zeilen fehlen"
            elif db.get("lr_null_pct", 0) > 20:
                status = f"LR-NULL: {db['lr_null_pct']:.0f}% der letzten 100"
            else:
                status = "OK"
        elif db_count > 0:
            if db.get("lr_null_pct", 0) > 20:
                status = f"LR-NULL: {db['lr_null_pct']:.0f}%"
            else:
                status = "OK (nur DB)"

        # Filter
        if args.missing_only and status == "OK":
            continue

        # Yahoo-Infos
        y_start = yh.get("first", "-") if yh and "error" not in yh else "-"
        y_end = yh.get("last", "-") if yh and "error" not in yh else "-"
        y_rows = str(yh_count) if yh_count > 0 else "-"
        y_years = str(yh.get("years", "-")) if yh and "error" not in yh else "-"

        # DB-Infos
        d_start = db.get("first", "-") or "-"
        d_end = db.get("last", "-") or "-"
        d_rows = str(db_count) if db_count > 0 else "-"
        lr_null = f"{db.get('lr_null_pct', 0):.0f}%" if db_count > 0 else "-"

        print(f"{ticker:<12} {kat:<12} "
              f"{y_start:<12} {y_end:<12} {y_rows:>7} {y_years:>7}  "
              f"{d_start:<12} {d_end:<12} {d_rows:>7} {lr_null:>7}  "
              f"{status}")

        results.append({
            "ticker": ticker, "kat": kat, "status": status,
            "yh_count": yh_count, "db_count": db_count,
            "yh_first": y_start, "db_first": d_start,
            "lr_null_pct": db.get("lr_null_pct", 0),
        })

        # Fortschritt
        if (i + 1) % 50 == 0:
            print(f"\n--- {i+1}/{len(tickers)} ---\n")

    # Zusammenfassung
    n_ok = sum(1 for r in results if r["status"] == "OK")
    n_missing = sum(1 for r in results if "FEHLT" in r["status"])
    n_gap = sum(1 for r in results if "LUECKE" in r["status"])
    n_lr = sum(1 for r in results if "LR-NULL" in r["status"])
    total_yh = sum(r["yh_count"] for r in results)
    total_db = sum(r["db_count"] for r in results)

    print("\n" + "=" * 100)
    print(f"  ZUSAMMENFASSUNG")
    print(f"  Ticker: {len(results)} | OK: {n_ok} | Luecken: {n_gap} | "
          f"Fehlt: {n_missing} | LR-NULL: {n_lr}")
    print(f"  Yahoo gesamt: {total_yh:,} Zeilen | Supabase gesamt: {total_db:,} Zeilen | "
          f"Delta: {total_yh - total_db:,}")
    print("=" * 100)


if __name__ == "__main__":
    main()
