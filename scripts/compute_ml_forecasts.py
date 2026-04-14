#!/usr/bin/env python3
"""
scripts/compute_ml_forecasts.py — MSTL Saisonale Stärke Pre-Compute
=====================================================================
Berechnet MSTL-Dekomposition (statsmodels) für die Top-N Ticker
und speichert strength_yearly in Supabase `ml_forecasts`.

Chronos + NeuralProphet wurden am 2026-04-14 entfernt (kein Mehrwert
auf Finanzdaten, hoher operativer Aufwand mit PyTorch).

Usage:
    python3 scripts/compute_ml_forecasts.py                  # Alle aus Scanner
    python3 scripts/compute_ml_forecasts.py --ticker SPY     # Einzelner Ticker
    python3 scripts/compute_ml_forecasts.py --ticker SPY --dry-run  # Nur anzeigen
"""

import sys
import os
import pathlib
import json
import argparse
import time
import gc
from datetime import datetime, timezone

# ── Projekt-Root ──
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd


# ── Helpers ──────────────────────────────────────────────────

def get_all_tickers() -> list[str]:
    """Alle Ticker aus scanner_results (sortiert nach Score)."""
    from shared.supabase_client import get_client
    sb = get_client()
    all_rows = []
    batch = 1000
    offset = 0
    while True:
        res = sb.table("scanner_results") \
            .select("ticker") \
            .order("score", desc=True) \
            .range(offset, offset + batch - 1) \
            .execute()
        all_rows.extend(res.data)
        if len(res.data) < batch:
            break
        offset += batch
    return [r["ticker"] for r in all_rows]


def load_prices(ticker: str) -> pd.DataFrame | None:
    """Preise aus Supabase laden, als DataFrame mit DatetimeIndex."""
    from shared.supabase_client import get_client
    sb = get_client()

    # Letzte 3 Jahre (reicht fuer MSTL)
    cutoff = (datetime.now().year - 3)
    cutoff_str = f"{cutoff}-01-01"

    all_rows = []
    batch_size = 1000
    offset = 0
    while True:
        res = sb.table("prices") \
            .select("date,close") \
            .eq("ticker", ticker) \
            .gte("date", cutoff_str) \
            .order("date") \
            .range(offset, offset + batch_size - 1) \
            .execute()
        all_rows.extend(res.data)
        if len(res.data) < batch_size:
            break
        offset += batch_size

    if len(all_rows) < 100:
        return None

    df = pd.DataFrame(all_rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    df["close"] = df["close"].astype(float)
    df.rename(columns={"close": "Close"}, inplace=True)
    return df


def store_result(ticker: str, model: str, data: dict, dry_run: bool = False):
    """Ergebnis in ml_forecasts upserten."""
    if dry_run:
        print(f"  [DRY-RUN] {ticker}/{model}: {len(json.dumps(data))} bytes")
        return

    from shared.supabase_client import get_client
    sb = get_client()
    sb.table("ml_forecasts").upsert({
        "ticker": ticker,
        "model": model,
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "data": data,
    }).execute()


# ── MSTL Runner ─────────────────────────────────────────────

def run_mstl(df: pd.DataFrame, ticker: str) -> dict | None:
    """MSTL Dekomposition — liefert saisonale Staerke + Zerlegung."""
    try:
        from shared.mstl_decomposition import decompose_mstl
        result = decompose_mstl(df, periods=[5, 252])
        if result is None:
            return None

        # Nur letzte 252 Tage fuer JSON (sonst zu gross)
        n = min(252, len(result["trend"]))
        dates = [d.strftime("%Y-%m-%d") for d in result["index"][-n:]]

        data = {
            "dates": dates,
            "strength_weekly": result.get("strength_weekly", 0),
            "strength_yearly": result.get("strength_yearly", 0),
            "strength_trend": result.get("strength_trend", 0),
        }

        if "seasonal_yearly" in result:
            data["seasonal_yearly"] = [round(float(v), 4) for v in result["seasonal_yearly"].values[-n:]]

        return data
    except Exception as e:
        print(f"  [WARN] MSTL {ticker}: {e}")
        return None


# ── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="MSTL Saisonale Staerke Pre-Compute")
    parser.add_argument("--ticker", type=str, help="Einzelner Ticker (sonst alle aus Scanner)")
    parser.add_argument("--models", type=str, default="mstl",
                        help="Komma-separiert (nur mstl verfuegbar)")
    parser.add_argument("--dry-run", action="store_true", help="Nur berechnen, nicht speichern")
    parser.add_argument("--progress-every", type=int, default=10, help="Progress alle N Ticker")
    args = parser.parse_args()

    # Ticker-Liste
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = get_all_tickers()

    print(f"MSTL Strength: {len(tickers)} Ticker")
    if args.dry_run:
        print("DRY-RUN: Keine Daten werden gespeichert")
    print()

    t_start = time.time()
    success = 0
    errors = 0

    for idx, ticker in enumerate(tickers):
        if idx > 0 and idx % args.progress_every == 0:
            elapsed = time.time() - t_start
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (len(tickers) - idx) / rate if rate > 0 else 0
            print(f"  [{idx}/{len(tickers)}] {elapsed:.0f}s elapsed, ETA {eta:.0f}s")

        df = load_prices(ticker)
        if df is None:
            print(f"  [{ticker}] Zu wenig Daten, uebersprungen")
            errors += 1
            continue

        t0 = time.time()
        result = run_mstl(df, ticker)

        if result is not None:
            store_result(ticker, "mstl", result, dry_run=args.dry_run)
            dt = time.time() - t0
            strength = result.get("strength_yearly", 0)
            print(f"  [{ticker}] MSTL: {strength:.1f}% saisonale Staerke ({dt:.1f}s)")
            success += 1
        else:
            print(f"  [{ticker}] MSTL: SKIP (kein Ergebnis)")
            errors += 1

        gc.collect()

    elapsed = time.time() - t_start
    print(f"\nFertig: {success} OK, {errors} Fehler in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
