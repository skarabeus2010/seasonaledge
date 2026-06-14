"""
scripts/compute_regime_scores.py — Isolation Forest Regime-Scoring
==================================================================
Berechnet historische + aktuelle Risk-Scores und schreibt sie in Supabase.

Usage:
    python3 compute_regime_scores.py                  # SPY (Default)
    python3 compute_regime_scores.py --ticker ^DJI    # Beliebiger Ticker
    python3 compute_regime_scores.py --full            # Alle Scores neu berechnen
    python3 compute_regime_scores.py --incremental     # Nur neue Tage (Default)
"""

import sys
import os
import gc
import pathlib
import argparse
from datetime import datetime, timedelta

# ── Project Path ──
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import numpy as np
import pandas as pd

from shared.supabase_client import get_client
from shared.data import download_data, preprocess
from shared.yahoo_downloader import clear_cache
from shared.logger import app_logger


# ══════════════════════════════════════════════════════════════
# ISOLATION FOREST REGIME-BERECHNUNG
# ══════════════════════════════════════════════════════════════

def compute_regime_scores(df, windows=None):
    """
    Berechnet Risk-Score fuer JEDEN Tag via Isolation Forest.

    Features pro Tag: Rendite 1d, Volatilitaet (5d, 10d, 20d),
    Returns (5d, 20d), Drawdown vom 20d-Hoch.

    Returns:
        pd.DataFrame mit Spalten: date, risk_score, traffic_light,
        vol_5d, vol_10d, vol_20d, drawdown, ret_1d, ret_5d, ret_20d, anomaly_score
    """
    if windows is None:
        windows = [5, 10, 20]

    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        app_logger.error("sklearn nicht installiert — pip install scikit-learn")
        return pd.DataFrame()

    if len(df) < 100:
        app_logger.warning(f"Zu wenig Daten: {len(df)} Zeilen")
        return pd.DataFrame()

    # ── Features berechnen ──
    feat_df = pd.DataFrame(index=df.index)
    feat_df["ret_1d"] = df["Close"].pct_change() * 100

    for w in windows:
        feat_df[f"vol_{w}d"] = feat_df["ret_1d"].rolling(w).std()
        feat_df[f"ret_{w}d"] = df["Close"].pct_change(w) * 100

    # Drawdown vom 20d-Hoch
    feat_df["high_20d"] = df["Close"].rolling(20).max()
    feat_df["drawdown"] = (df["Close"] - feat_df["high_20d"]) / feat_df["high_20d"] * 100

    feat_df = feat_df.dropna()
    if len(feat_df) < 100:
        app_logger.warning(f"Zu wenig Features: {len(feat_df)} Zeilen nach dropna")
        return pd.DataFrame()

    feature_cols = [c for c in feat_df.columns if c != "high_20d"]
    X = feat_df[feature_cols].values

    # ── Isolation Forest trainieren ──
    app_logger.info(f"Training Isolation Forest auf {len(X)} Datenpunkten...")
    clf = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
    clf.fit(X)

    # ── Alle Tage scoren ──
    raw_scores = clf.decision_function(X)  # Negativer = anomaler
    # Scores in Percentile umrechnen (0-100, hoeher = anomaler)
    # Fuer jeden Tag: wie viele Tage hatten hoeheren (weniger anomalen) Score?
    risk_scores = np.array([
        round(max(0, min(100, (1 - (raw_scores >= s).mean()) * 100)), 1)
        for s in raw_scores
    ])

    # Traffic Light
    traffic_lights = []
    for rs in risk_scores:
        if rs >= 70:
            traffic_lights.append("red")
        elif rs >= 40:
            traffic_lights.append("yellow")
        else:
            traffic_lights.append("green")

    # ── Ergebnis-DataFrame ──
    result = pd.DataFrame({
        "date": feat_df.index,
        "risk_score": risk_scores,
        "traffic_light": traffic_lights,
        "vol_5d": feat_df["vol_5d"].round(4).values,
        "vol_10d": feat_df["vol_10d"].round(4).values,
        "vol_20d": feat_df["vol_20d"].round(4).values,
        "drawdown": feat_df["drawdown"].round(4).values,
        "ret_1d": feat_df["ret_1d"].round(4).values,
        "ret_5d": feat_df["ret_5d"].round(4).values,
        "ret_20d": feat_df["ret_20d"].round(4).values,
        "anomaly_score": raw_scores.round(6),
    })

    app_logger.info(f"Berechnet: {len(result)} Scores, "
                    f"Green: {(result['traffic_light']=='green').sum()}, "
                    f"Yellow: {(result['traffic_light']=='yellow').sum()}, "
                    f"Red: {(result['traffic_light']=='red').sum()}")

    return result


# ══════════════════════════════════════════════════════════════
# SUPABASE UPSERT
# ══════════════════════════════════════════════════════════════

def upsert_regime_scores(ticker, scores_df):
    """Schreibt Regime-Scores in Supabase (Upsert)."""
    if scores_df.empty:
        return

    records = []
    for _, row in scores_df.iterrows():
        records.append({
            "ticker": ticker,
            "date": row["date"].strftime("%Y-%m-%d") if hasattr(row["date"], "strftime") else str(row["date"])[:10],
            "risk_score": float(row["risk_score"]),
            "traffic_light": row["traffic_light"],
            "vol_5d": float(row["vol_5d"]) if pd.notna(row["vol_5d"]) else None,
            "vol_10d": float(row["vol_10d"]) if pd.notna(row["vol_10d"]) else None,
            "vol_20d": float(row["vol_20d"]) if pd.notna(row["vol_20d"]) else None,
            "drawdown": float(row["drawdown"]) if pd.notna(row["drawdown"]) else None,
            "ret_1d": float(row["ret_1d"]) if pd.notna(row["ret_1d"]) else None,
            "ret_5d": float(row["ret_5d"]) if pd.notna(row["ret_5d"]) else None,
            "ret_20d": float(row["ret_20d"]) if pd.notna(row["ret_20d"]) else None,
            "anomaly_score": float(row["anomaly_score"]) if pd.notna(row["anomaly_score"]) else None,
        })

    client = get_client()
    batch_size = 500
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        client.table("regime_scores").upsert(
            batch, on_conflict="ticker,date"
        ).execute()
        app_logger.info(f"Upserted {len(batch)} regime scores ({i + len(batch)}/{len(records)})")


def get_last_score_date(ticker):
    """Letztes Datum in regime_scores fuer diesen Ticker."""
    try:
        client = get_client()
        res = client.table("regime_scores") \
            .select("date") \
            .eq("ticker", ticker) \
            .order("date", desc=True) \
            .limit(1) \
            .execute()
        if res.data:
            return pd.Timestamp(res.data[0]["date"])
    except Exception:
        pass
    return None


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def _process_ticker(ticker: str, full: bool) -> tuple[int, str | None]:
    """Returnt (Anzahl neu geschriebener Scores, Fehlertext|None)."""
    ticker = ticker.upper()
    try:
        raw_df = download_data(ticker)
        if raw_df is None or raw_df.empty:
            return 0, "keine Daten"
        df = preprocess(raw_df)
        scores_df = compute_regime_scores(df)
        if scores_df.empty:
            return 0, "keine Scores berechnet"
        if not full:
            last_date = get_last_score_date(ticker)
            if last_date is not None:
                scores_df = scores_df[scores_df["date"] > last_date]
                if scores_df.empty:
                    return 0, None
        upsert_regime_scores(ticker, scores_df)
        return len(scores_df), None
    except Exception as exc:
        return 0, str(exc)


def main():
    parser = argparse.ArgumentParser(description="Compute Isolation Forest Regime Scores")
    parser.add_argument("--ticker", default=None, help="Einzel-Ticker (default: SPY wenn nichts anderes)")
    parser.add_argument("--tickers", nargs="*", help="Liste mehrerer Ticker")
    parser.add_argument("--all-relevant", action="store_true",
                        help="Alle US-ETF + US-Aktie + EU-Aktie aus symbols.py (Daily-Newsletter-Universum)")
    parser.add_argument("--full", action="store_true", help="Recompute ALL scores from scratch")
    parser.add_argument("--incremental", action="store_true", default=True, help="Only compute new days (default)")
    args = parser.parse_args()

    # Ticker-Liste zusammenstellen
    if args.all_relevant:
        from shared.symbols import get_symbols_by_category
        tickers = sorted(set(
            list(get_symbols_by_category("US-ETF").keys()) +
            list(get_symbols_by_category("US-Aktie").keys()) +
            list(get_symbols_by_category("EU-Aktie").keys())
        ))
    elif args.tickers:
        tickers = [t.upper() for t in args.tickers]
    else:
        tickers = [(args.ticker or "SPY").upper()]

    app_logger.info(f"=== Regime Scores: {len(tickers)} Ticker ({'FULL' if args.full else 'INCREMENTAL'}) ===")

    ok = err = skip = total_rows = 0
    errors: list[str] = []
    for i, ticker in enumerate(tickers, 1):
        n, exc = _process_ticker(ticker, args.full)
        if exc:
            err += 1
            errors.append(f"{ticker}: {exc}")
            app_logger.warning(f"[{i}/{len(tickers)}] {ticker} ERR: {exc}")
        elif n == 0:
            skip += 1
            app_logger.info(f"[{i}/{len(tickers)}] {ticker} skip (keine neuen Daten)")
        else:
            ok += 1
            total_rows += n
            app_logger.info(f"[{i}/{len(tickers)}] {ticker} OK ({n} Scores)")
        # OOM-Schutz: download_data cached jede Voll-Historie → pro Ticker freigeben
        # (sonst SIGKILL/exit 137 bei Full-Universe-Lauf, siehe full_scanner_run).
        try:
            clear_cache()
        except Exception:
            pass
        gc.collect()

    app_logger.info(f"=== Fertig: {ok} OK · {skip} skip · {err} err · {total_rows} Rows ===")
    if errors:
        app_logger.warning("Fehler-Details:\n  " + "\n  ".join(errors[:20]))


if __name__ == "__main__":
    main()
