"""
scripts/generate_decade_data.py — Dekadenzyklus-Daten fuer Landing Page
=========================================================================
Berechnet alle Dekaden-Daten (Rendite, Drawdown, Volatilität, Anomalie)
und speichert als JSON fuer die statische HTML-Page.

Aufruf: py scripts/generate_decade_data.py
        py scripts/generate_decade_data.py --ticker AAPL
"""

import sys
import os
import pathlib
import json
import argparse
from datetime import datetime

_project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd
from shared.yahoo_downloader import download_data as _yahoo_download, preprocess
from shared.data import download_data as _supabase_download


def _approx_date(year, trading_day_idx):
    """Approximiert ein Datum aus dem Handelstag-Index (0-251)."""
    from datetime import timedelta
    jan1 = datetime(year, 1, 2)  # Erster Handelstag ~ 2. Januar
    cal_days = int(trading_day_idx * 365 / 252)
    d = jan1 + timedelta(days=cal_days)
    return d.strftime("%d.%m.%Y")


def compute_drawdown_series(curve, base=100.0):
    """Berechnet Drawdown-Serie aus kumulierter Kurve."""
    cum = np.asarray(curve) + base
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak * 100
    return dd


def generate(ticker="^DJI", vola_window=20, output_dir=None):
    """Generiert komplette Dekadenzyklus-Daten als JSON."""
    if output_dir is None:
        output_dir = os.path.join(_project_dir, "landing", "data")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Generiere Dekaden-Daten fuer {ticker} ...")

    # Yahoo+Stooq direkt aufrufen (NICHT Supabase) um maximale Historie zu erhalten.
    # Supabase hat nur ~30 Jahre (Bulk-Load), Stooq hat bis zu 131 Jahre fuer Indizes.
    raw_df = _yahoo_download(ticker, period="max")
    if raw_df is None or raw_df.empty:
        print("FEHLER: Keine Daten!")
        return
    df = preprocess(raw_df)

    current_year = datetime.now().year
    current_digit = current_year % 10
    all_years = sorted(df["year"].unique())
    valid_years = [y for y in all_years if len(df[df["year"] == y]) >= 200]
    print(f"  {len(df)} Zeilen, {len(valid_years)} vollstaendige Jahre ({min(valid_years)}-{max(valid_years)})")

    # ── Dekaden-Kohorten berechnen ──
    decades = {}
    for digit in range(10):
        years_in_cohort = [y for y in valid_years if y % 10 == digit]
        curves = []
        returns = []

        for year in years_in_cohort:
            ydf = df[df["year"] == year].sort_index()
            closes = ydf["Close"].values.astype(float)
            if len(closes) < 200 or closes[0] <= 0:
                continue
            log_curve = (np.log(closes) - np.log(closes[0])) * 100

            # Interpolieren auf 252 Punkte
            if len(log_curve) < 252:
                x_orig = np.linspace(0, 251, len(log_curve))
                x_new = np.arange(252)
                log_curve = np.interp(x_new, x_orig, log_curve)
            elif len(log_curve) > 252:
                indices = np.linspace(0, len(log_curve) - 1, 252).astype(int)
                log_curve = log_curve[indices]

            curves.append(log_curve)
            # Simple Return fuer Statistiken (nie < -100%, intuitiver als Log-Return)
            simple_return = (closes[-1] / closes[0] - 1) * 100
            returns.append(round(float(simple_return), 2))

        n = len(curves)
        if n == 0:
            decades[str(digit)] = {
                "years": [], "n": 0, "avg_curve": [], "std_curve": [],
                "avg_return": 0, "median_return": 0, "win_rate": 0,
                "volatility": 0, "returns": [],
                "dd_avg_curve": [], "dd_worst": 0,
                "vola_avg_curve": [],
            }
            continue

        avg_curve = np.mean(curves, axis=0)
        std_curve = np.std(curves, axis=0)

        # Smoothing (5-Tage MA)
        avg_smooth = pd.Series(avg_curve).rolling(5, center=True, min_periods=1).mean().values

        # Drawdown pro Jahr → Durchschnitt
        dd_curves = [compute_drawdown_series(c) for c in curves]
        dd_avg = np.mean(dd_curves, axis=0)
        dd_worst = float(min(np.min(dc) for dc in dd_curves))

        # Rolling Volatilitaet pro Jahr → Durchschnitt
        vola_curves = []
        for year in years_in_cohort:
            ydf = df[df["year"] == year].sort_index()
            if len(ydf) < vola_window + 10:
                continue
            daily_ret = ydf["Close"].pct_change() * 100
            rolling_std = daily_ret.rolling(vola_window).std()
            vola = (rolling_std * np.sqrt(252)).dropna().values
            if len(vola) > 0:
                # Interpolieren auf 252
                x_orig = np.linspace(0, 251, len(vola))
                x_new = np.arange(252)
                vola_interp = np.interp(x_new, x_orig, vola)
                vola_curves.append(vola_interp)

        vola_avg = np.mean(vola_curves, axis=0).tolist() if vola_curves else []

        decades[str(digit)] = {
            "years": years_in_cohort,
            "n": n,
            "avg_curve": [round(float(v), 2) for v in avg_smooth],
            "std_curve": [round(float(v), 2) for v in std_curve],
            "avg_return": round(float(np.mean(returns)), 2),
            "median_return": round(float(np.median(returns)), 2),
            "win_rate": round(float(sum(1 for r in returns if r > 0) / n * 100), 1),
            "volatility": round(float(np.std(returns)), 2),
            "returns": returns,
            "individual_curves": [[round(float(v), 1) for v in c] for c in curves],
            "dd_avg_curve": [round(float(v), 2) for v in dd_avg],
            "dd_worst": round(dd_worst, 1),
            "vola_avg_curve": [round(float(v), 1) for v in vola_avg],
        }

    # ── Aktuelles Jahr ──
    cy_df = df[df["year"] == current_year].sort_index()
    current_curve = []
    current_dd = []
    if len(cy_df) >= 10:
        closes = cy_df["Close"].values.astype(float)
        if closes[0] > 0:
            log_c = (np.log(closes) - np.log(closes[0])) * 100
            current_curve = [round(float(v), 2) for v in log_c]
            dd_c = compute_drawdown_series(log_c)
            current_dd = [round(float(v), 2) for v in dd_c]

    # ── Monats-Heatmap (Rendite) ──
    monthly_heatmap = {}
    for digit in range(10):
        years_in = [y for y in valid_years if y % 10 == digit]
        month_returns = []
        for month in range(1, 13):
            rets = []
            for year in years_in:
                mdf = df[(df["year"] == year) & (df["month"] == month)]
                if len(mdf) >= 10:
                    c = mdf["Close"].values.astype(float)
                    if c[0] > 0:
                        rets.append(float((c[-1] / c[0] - 1) * 100))
            month_returns.append(round(np.mean(rets), 2) if rets else 0.0)
        monthly_heatmap[str(digit)] = month_returns

    # ── DD-Monats-Heatmap ──
    dd_monthly_heatmap = {}
    for digit in range(10):
        d = decades[str(digit)]
        if d["n"] == 0:
            dd_monthly_heatmap[str(digit)] = [0.0] * 12
            continue
        dd_avg = d["dd_avg_curve"]
        if len(dd_avg) < 252:
            dd_monthly_heatmap[str(digit)] = [0.0] * 12
            continue
        month_dd = []
        for m in range(12):
            start = int(m * 21)
            end = min(int((m + 1) * 21), 252)
            month_dd.append(round(float(min(dd_avg[start:end])), 1))
        dd_monthly_heatmap[str(digit)] = month_dd

    # ── Worst-DD-Tabelle (mit echten Daten + Recovery) ──
    worst_dd_table = []
    try:
        from shared.drawdown_analysis import compute_real_recovery
        has_recovery = True
    except ImportError:
        has_recovery = False

    for digit in range(10):
        d = decades[str(digit)]
        for i, year in enumerate(d.get("years", [])):
            if i < len(d.get("individual_curves", [])):
                curve = d["individual_curves"][i]
                dd_curve = compute_drawdown_series(np.array(curve))
                max_dd = float(np.min(dd_curve))
                if max_dd < -10:
                    entry = {
                        "digit": digit,
                        "year": year,
                        "max_dd": round(max_dd, 1),
                        "peak_date": "",
                        "trough_date": "",
                        "recovery_str": "",
                        "recovered": False,
                    }

                    # Echte Daten + Recovery wenn moeglich
                    if has_recovery:
                        try:
                            rec = compute_real_recovery(df, year)
                            if rec:
                                entry["peak_date"] = rec["peak_date"].strftime("%d.%m.%Y")
                                entry["trough_date"] = rec["trough_date"].strftime("%d.%m.%Y")
                                entry["recovery_str"] = rec["recovery_str"]
                                entry["recovered"] = rec["recovered"]
                        except Exception:
                            # Fallback: Datum aus Handelstag-Index approximieren
                            trough_idx = int(np.argmin(dd_curve))
                            peak_idx = int(np.argmax(np.array(curve)[:trough_idx + 1])) if trough_idx > 0 else 0
                            entry["peak_date"] = _approx_date(year, peak_idx)
                            entry["trough_date"] = _approx_date(year, trough_idx)

                    worst_dd_table.append(entry)

    worst_dd_table.sort(key=lambda x: x["max_dd"])
    worst_dd_table = worst_dd_table[:25]

    # ── Anomalie ──
    anomaly = {"score": 0, "status": "normal", "return_10d": 0, "avg_10d": 0, "n_comparisons": 0}
    try:
        from shared.anomaly_engine import compute_ticker_anomaly_score
        radar = compute_ticker_anomaly_score(df, lookback_days=10)
        if "error" not in radar:
            anomaly = {
                "score": round(radar["anomaly_score"], 0),
                "status": "anomal" if radar["anomaly_score"] >= 40 else "normal",
                "return_10d": round(radar["current_return"], 2),
                "avg_10d": round(radar["historical_avg"], 2),
                "n_comparisons": radar.get("n_comparisons", 0),
            }
    except Exception:
        pass

    # ── Zusammenbauen ──
    result = {
        "ticker": ticker,
        "data_start": int(min(valid_years)),
        "data_end": int(max(valid_years)),
        "total_years": len(valid_years),
        "current_year": current_year,
        "current_digit": current_digit,
        "vola_window": vola_window,
        "decades": decades,
        "current_year_curve": current_curve,
        "current_year_dd": current_dd,
        "monthly_heatmap": monthly_heatmap,
        "dd_monthly_heatmap": dd_monthly_heatmap,
        "anomaly": anomaly,
        "worst_dd_table": worst_dd_table,
        "generated_at": datetime.now().isoformat(),
    }

    # ── Speichern ──
    safe_ticker = ticker.replace("^", "").replace("=", "").replace("-", "")
    filename = f"{safe_ticker}-decade.json"
    filepath = os.path.join(output_dir, filename)

    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(result, f, separators=(",", ":"), cls=NumpyEncoder)

    size_kb = os.path.getsize(filepath) / 1024
    print(f"  Gespeichert: {filepath} ({size_kb:.0f} KB)")
    print(f"  {len(valid_years)} Jahre, {sum(d['n'] for d in decades.values())} Kurven")
    return filepath


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="^DJI")
    parser.add_argument("--vola-window", type=int, default=20)
    args = parser.parse_args()
    generate(ticker=args.ticker, vola_window=args.vola_window)
