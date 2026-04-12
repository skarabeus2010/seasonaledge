#!/usr/bin/env python3
"""
scripts/compute_ml_forecasts.py — ML Forecast Pre-Compute
===========================================================
Berechnet Chronos, MSTL und NeuralProphet Ergebnisse für die Top-N
Ticker und speichert sie in Supabase `ml_forecasts`.

Usage:
    python3 scripts/compute_ml_forecasts.py                  # Top 50 aus Scanner
    python3 scripts/compute_ml_forecasts.py --top 20         # Top 20
    python3 scripts/compute_ml_forecasts.py --ticker SPY     # Einzelner Ticker
    python3 scripts/compute_ml_forecasts.py --ticker SPY --dry-run  # Nur anzeigen
    python3 scripts/compute_ml_forecasts.py --models chronos,mstl   # Nur bestimmte Modelle
"""

import sys
import os
import pathlib
import json
import argparse
import time
import gc
from datetime import datetime

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

def get_top_tickers(n: int) -> list[str]:
    """Top-N Ticker aus scanner_results nach Score."""
    from shared.supabase_client import get_client
    sb = get_client()
    res = sb.table("scanner_results") \
        .select("ticker") \
        .order("score", desc=True) \
        .limit(n) \
        .execute()
    return [r["ticker"] for r in res.data]


def load_prices(ticker: str) -> pd.DataFrame | None:
    """Preise aus Supabase laden, als DataFrame mit DatetimeIndex."""
    from shared.supabase_client import get_client
    sb = get_client()

    # Letzte 3 Jahre (reicht für MSTL + Chronos)
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
        "computed_at": datetime.utcnow().isoformat(),
        "data": data,
    }).execute()


# ── Modell-Runner ────────────────────────────────────────────

def run_chronos(df: pd.DataFrame, ticker: str) -> dict | None:
    """Chronos-Bolt-Tiny 30d Forecast."""
    try:
        from shared.chronos_forecast import forecast_chronos
        result = forecast_chronos(df, periods=30)
        if result is None:
            return None

        # DataFrame → JSON-serialisierbar
        forecast_list = []
        for _, row in result.iterrows():
            forecast_list.append({
                "ds": row["ds"].strftime("%Y-%m-%d"),
                "yhat": round(float(row["yhat"]), 2),
                "yhat_lower": round(float(row["yhat_lower"]), 2),
                "yhat_upper": round(float(row["yhat_upper"]), 2),
            })

        return {
            "forecast": forecast_list,
            "expected_return": result.attrs.get("expected_return", 0),
            "p_positive": result.attrs.get("p_positive", 50),
            "last_close": result.attrs.get("last_close", 0),
            "periods": 30,
        }
    except Exception as e:
        print(f"  [WARN] Chronos {ticker}: {e}")
        return None


def run_mstl(df: pd.DataFrame, ticker: str) -> dict | None:
    """MSTL Dekomposition."""
    try:
        from shared.mstl_decomposition import decompose_mstl
        result = decompose_mstl(df, periods=[5, 252])
        if result is None:
            return None

        # Nur letzte 252 Tage für JSON (sonst zu groß)
        n = min(252, len(result["trend"]))
        dates = [d.strftime("%Y-%m-%d") for d in result["index"][-n:]]

        data = {
            "dates": dates,
            "trend": [round(float(v), 2) for v in result["trend"].values[-n:]],
            "residual": [round(float(v), 4) for v in result["residual"].values[-n:]],
            "strength_weekly": result.get("strength_weekly", 0),
            "strength_yearly": result.get("strength_yearly", 0),
            "strength_trend": result.get("strength_trend", 0),
        }

        if "seasonal_weekly" in result:
            data["seasonal_weekly"] = [round(float(v), 4) for v in result["seasonal_weekly"].values[-n:]]
        if "seasonal_yearly" in result:
            data["seasonal_yearly"] = [round(float(v), 4) for v in result["seasonal_yearly"].values[-n:]]

        return data
    except Exception as e:
        print(f"  [WARN] MSTL {ticker}: {e}")
        return None


def run_neuralprophet(df: pd.DataFrame, ticker: str) -> dict | None:
    """NeuralProphet Saisonalitäts-Komponenten."""
    try:
        from shared.neural_prophet_forecast import forecast_neural_prophet
        result = forecast_neural_prophet(df, periods=30)
        if result is None:
            return None

        data = {
            "expected_return": result.get("expected_return", 0),
            "last_close": result.get("last_close", 0),
        }

        # Komponenten extrahieren
        components = result.get("components", {})
        for key in ["yearly", "weekly", "trend"]:
            if key in components:
                comp_df = components[key]
                data[f"{key}_seasonality"] = [
                    {"ds": row["ds"].strftime("%Y-%m-%d"), "value": round(float(row[key]), 4)}
                    for _, row in comp_df.iterrows()
                    if not pd.isna(row[key])
                ][-365:]  # Letzte 365 Punkte max

        # Model nicht serialisierbar → entfernen
        return data
    except Exception as e:
        print(f"  [WARN] NeuralProphet {ticker}: {e}")
        return None


# ── Main ─────────────────────────────────────────────────────

MODELS = {
    "chronos": run_chronos,
    "mstl": run_mstl,
    "neuralprophet": run_neuralprophet,
}


def main():
    parser = argparse.ArgumentParser(description="ML Forecast Pre-Compute")
    parser.add_argument("--top", type=int, default=50, help="Top-N Ticker aus Scanner")
    parser.add_argument("--ticker", type=str, help="Einzelner Ticker")
    parser.add_argument("--models", type=str, default="chronos,mstl,neuralprophet",
                        help="Komma-separierte Modell-Liste")
    parser.add_argument("--dry-run", action="store_true", help="Nur berechnen, nicht speichern")
    parser.add_argument("--progress-every", type=int, default=5, help="Progress alle N Ticker")
    args = parser.parse_args()

    selected_models = [m.strip() for m in args.models.split(",") if m.strip() in MODELS]
    if not selected_models:
        print("Keine gültigen Modelle angegeben. Verfügbar:", list(MODELS.keys()))
        sys.exit(1)

    # Ticker-Liste
    if args.ticker:
        tickers = [args.ticker.upper()]
    else:
        tickers = get_top_tickers(args.top)

    print(f"ML Forecasts: {len(tickers)} Ticker × {len(selected_models)} Modelle")
    print(f"Modelle: {selected_models}")
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

        # Preise laden
        df = load_prices(ticker)
        if df is None:
            print(f"  [{ticker}] Zu wenig Daten, übersprungen")
            errors += 1
            continue

        for model_name in selected_models:
            t0 = time.time()
            runner = MODELS[model_name]
            result = runner(df, ticker)

            if result is not None:
                store_result(ticker, model_name, result, dry_run=args.dry_run)
                dt = time.time() - t0
                print(f"  [{ticker}] {model_name}: OK ({dt:.1f}s)")
                success += 1
            else:
                print(f"  [{ticker}] {model_name}: SKIP (kein Ergebnis)")
                errors += 1

            # RAM freigeben nach jedem Modell
            gc.collect()

    elapsed = time.time() - t_start
    print(f"\nFertig: {success} OK, {errors} Fehler in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
