"""
scripts/ml/regime_clustering.py — KMeans Regime-Clustering für SeasonAlpha
===========================================================================
Teilt Markttage automatisch in 3 Regime-Cluster ein (Bull/Sideways/Bear)
anhand von Rolling-Statistiken. Zeigt dann: Wie performen saisonale Signale
(Monat, TDOM) IN verschiedenen Regimes?

Ausgabe-Blöcke:
  1. Regime-Verteilung (Count / Anteil / Avg daily ret / Ann. Sharpe)
  2. Monats-Heatmap per Regime (avg daily log_return)
  3. TDOM-Muster per Regime (Monatsanfang TDOM 1–5, Monatsende 18–22)
  4. Strategie-Vergleich: Buy&Hold vs. saisonaler Filter vs. Regime-gefilterter Filter

Usage:
    py -3.14 scripts/ml/regime_clustering.py
    py -3.14 scripts/ml/regime_clustering.py --ticker QQQ --period 15y
    py -3.14 scripts/ml/regime_clustering.py --months 4,11,12
"""
from __future__ import annotations

import argparse
import math
import os
import pathlib
import sys

import numpy as np
import pandas as pd

# ── Project-Root in sys.path ──────────────────────────────────────────────────
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Yahoo-direkter Import (kein Supabase-Layer) — volle 20-Jahres-Geschichte
from shared.yahoo_downloader import download_data, preprocess


# ══════════════════════════════════════════════════════════════════════════════
# SCHRITT 1 — Daten laden und vorbereiten
# ══════════════════════════════════════════════════════════════════════════════

def load_and_prepare(ticker: str, period: str = "max") -> pd.DataFrame:
    """
    Lädt Kursdaten, ergänzt log_return via preprocess().

    Returns:
        DataFrame mit DatetimeIndex, Spalten: Open/High/Low/Close/Volume,
        log_return, year, month, tdom, tdoy.
    """
    print(f"[regime_clustering] Lade {ticker} ({period}) ...")
    df = download_data(ticker, period=period)

    if df is None or df.empty:
        raise RuntimeError(f"Keine Daten für '{ticker}' erhalten — Ticker prüfen.")

    df = preprocess(df)

    # log_return sicherstellen (preprocess setzt es, aber defensiv)
    if "log_return" not in df.columns or df["log_return"].isna().all():
        df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))

    df = df.dropna(subset=["log_return"])

    print(
        f"[regime_clustering] {len(df)} Handelstage geladen "
        f"({df.index[0].date()} – {df.index[-1].date()})"
    )
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SCHRITT 2 — Regime-Features (Rolling, kein Lookahead via shift(1))
# ══════════════════════════════════════════════════════════════════════════════

def add_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fügt Rolling-Features an — alle um 1 Tag geshiftet, damit Tag t
    nur Daten bis t-1 nutzt (kein Lookahead).

      f_ret_20 : Rolling Mean(20)  log_return  → Trend-Proxy
      f_vol_20 : Rolling Std(20)   log_return  → Volatilitäts-Proxy
      f_ret_5  : Rolling Mean(5)   log_return  → Kurzfrist-Trend

    Die ersten 21 Zeilen werden anschließend gedroppt (NaN durch Rolling+Shift).
    """
    df = df.copy()
    lr = df["log_return"]

    df["f_ret_20"] = lr.rolling(20).mean().shift(1)
    df["f_vol_20"] = lr.rolling(20).std().shift(1)
    df["f_ret_5"]  = lr.rolling(5).mean().shift(1)

    df = df.dropna(subset=["f_ret_20", "f_vol_20", "f_ret_5"])
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SCHRITT 3 — KMeans Clustering
# ══════════════════════════════════════════════════════════════════════════════

def fit_kmeans(df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    """
    Fitted KMeans auf [f_ret_20, f_vol_20, f_ret_5] (StandardScaler).
    Sortiert Cluster nach mittlerem f_ret_20:
      höchster mittlerer Return  → "Bull"
      mittlerer                  → "Sideways"
      niedrigster                → "Bear"

    Fügt Spalten `cluster` (int) und `regime` (str) zum DataFrame hinzu.
    """
    features  = ["f_ret_20", "f_vol_20", "f_ret_5"]
    X         = df[features].values

    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    km.fit(X_scaled)

    df = df.copy()
    df["cluster"] = km.labels_

    # Cluster nach mittlerem f_ret_20 sortieren → Rang 0=Bull, 1=Sideways, 2=Bear
    cluster_avg  = df.groupby("cluster")["f_ret_20"].mean()
    sorted_clust = cluster_avg.sort_values(ascending=False).index.tolist()
    rank_map     = {c: i for i, c in enumerate(sorted_clust)}

    label_map  = {0: "Bull", 1: "Sideways", 2: "Bear"}
    df["regime"] = df["cluster"].map(rank_map).map(label_map)

    return df


# ══════════════════════════════════════════════════════════════════════════════
# AUSGABE-BLOCK 1 — Regime-Statistiken
# ══════════════════════════════════════════════════════════════════════════════

_TRADING_DAYS_YEAR = 252

def print_regime_stats(df: pd.DataFrame, ticker: str) -> None:
    """Regime-Verteilung: Count, Anteil, Avg daily ret, Ann. Sharpe."""
    y0 = df.index[0].year
    y1 = df.index[-1].year

    print(f"\n{'='*68}")
    print(f"  Regime-Verteilung {ticker} {y0}–{y1}")
    print(f"{'='*68}")
    print(
        f"{'Regime':<12} {'Count':>7} {'Anteil':>8} "
        f"{'Avg daily ret':>14} {'Ann Sharpe':>12}"
    )
    print(f"{'-'*68}")

    total = len(df)
    for regime in ["Bull", "Sideways", "Bear"]:
        sub   = df.loc[df["regime"] == regime, "log_return"]
        cnt   = len(sub)
        share = cnt / total * 100
        avg_r = sub.mean() * 100          # in Prozent
        std_r = sub.std()

        sharpe = (
            (sub.mean() / std_r) * math.sqrt(_TRADING_DAYS_YEAR)
            if std_r > 0 else 0.0
        )

        print(
            f"{regime:<12} {cnt:>7} {share:>7.1f}%  "
            f"{avg_r:>+12.3f}%  {sharpe:>+11.2f}"
        )

    print(f"{'='*68}")


# ══════════════════════════════════════════════════════════════════════════════
# AUSGABE-BLOCK 2 — Monats-Heatmap per Regime
# ══════════════════════════════════════════════════════════════════════════════

_MONTH_ABBR = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

def print_monthly_heatmap(df: pd.DataFrame) -> None:
    """
    ASCII-Heatmap: avg daily log_return (x1e-4) pro Monat x Regime.
    Positiv = tendenziell bullishes Monatsende, Negativ = bärisch.
    """
    if "month" not in df.columns:
        df = df.copy()
        df["month"] = df.index.month

    col_w = 6  # Breite pro Monatsspalte

    print(f"\n{'='*88}")
    print("  Monats-Performance (avg daily log_return x1e-4) per Regime")
    print(f"{'='*88}")

    header = f"{'Regime':<10}" + "".join(f"{m:>{col_w}}" for m in _MONTH_ABBR)
    print(header)
    print("-" * 88)

    for regime in ["Bull", "Sideways", "Bear"]:
        sub = df[df["regime"] == regime]
        grp = sub.groupby("month")["log_return"].mean()
        line = f"{regime:<10}"
        for m in range(1, 13):
            val = grp.get(m, float("nan"))
            if pd.isna(val):
                line += f"{'–':>{col_w}}"
            else:
                scaled = val * 10_000
                line  += f"{scaled:>+{col_w}.0f}"
        print(line)

    print(f"{'='*88}")
    print("  Skala: x1e-4 | Bsp. +8 = log_return 0.0008/Tag ≈ +0.08%/Tag")


# ══════════════════════════════════════════════════════════════════════════════
# AUSGABE-BLOCK 3 — TDOM-Muster per Regime
# ══════════════════════════════════════════════════════════════════════════════

def _ensure_tdom(df: pd.DataFrame) -> pd.DataFrame:
    """Berechnet TDOM (Trading Day of Month) als Fallback wenn nicht vorhanden."""
    df = df.copy()
    if "year" not in df.columns:
        df["year"] = df.index.year
    if "month" not in df.columns:
        df["month"] = df.index.month
    if "tdom" not in df.columns or df["tdom"].isna().all():
        df["tdom"] = df.groupby(["year", "month"]).cumcount() + 1
    return df


def print_tdom_per_regime(df: pd.DataFrame) -> None:
    """
    TDOM-Muster: Monatsanfang (TDOM 1–5) und Monatsende (TDOM 18–22).
    Frage: Ist der Turn-of-Month-Effekt nur im Bull-Regime signifikant?
    """
    df = _ensure_tdom(df)

    tdom_cols  = list(range(1, 6)) + list(range(18, 23))  # 1-5 und 18-22
    col_w      = 7

    print(f"\n{'='*82}")
    print("  TDOM-Muster per Regime (avg log_return x1e-4) — Anfang & Ende des Monats")
    print(f"{'='*82}")

    header = f"{'Regime':<10}" + "".join(f"{'TDOM'+str(t):>{col_w}}" for t in tdom_cols)
    print(header)
    print("-" * 82)

    for regime in ["Bull", "Sideways", "Bear"]:
        sub  = df[df["regime"] == regime]
        grp  = sub.groupby("tdom")["log_return"].mean()
        line = f"{regime:<10}"
        for t in tdom_cols:
            val = grp.get(t, float("nan"))
            if pd.isna(val):
                line += f"{'–':>{col_w}}"
            else:
                scaled = val * 10_000
                line  += f"{scaled:>+{col_w}.0f}"
        print(line)

    print(f"{'='*82}")
    # Bewertung: Vergleiche TDOM 1-5 Bull vs Bear
    try:
        bull_early = df[(df["regime"] == "Bull") & df["tdom"].between(1, 5)]["log_return"].mean()
        bear_early = df[(df["regime"] == "Bear") & df["tdom"].between(1, 5)]["log_return"].mean()
        diff = (bull_early - bear_early) * 10_000
        print(
            f"  Turn-of-Month (TDOM 1-5): Bull Ø{bull_early*10000:+.0f} vs Bear Ø{bear_early*10000:+.0f} "
            f"(Diff {diff:+.0f}x1e-4) → "
            + ("Effekt Bull-spezifisch ✓" if diff > 3 else "kein klarer Bull-Bias")
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# AUSGABE-BLOCK 4 — Strategie-Vergleich (Regime-gefilterter Saisonalitäts-Backtest)
# ══════════════════════════════════════════════════════════════════════════════

def backtest_strategies(
    df: pd.DataFrame,
    ticker: str,
    seasonal_months: tuple[int, ...] = (4, 11, 12),
) -> None:
    """
    Vergleicht 3 Strategien:
      A: Buy & Hold (immer investiert)
      B: nur saisonale Top-Monate (ohne Regime-Filter)
      C: saisonale Top-Monate NUR wenn Regime ≠ Bear

    Metriken: CAGR, Sharpe (nur aktive Tage), Max Drawdown, Investiert%
    """
    if "month" not in df.columns:
        df = df.copy()
        df["month"] = df.index.month

    lr            = df["log_return"].copy()
    seasonal_mask = df["month"].isin(seasonal_months)
    bear_mask     = df["regime"] == "Bear"

    seasonal_names = ", ".join(_MONTH_ABBR[m - 1] for m in sorted(seasonal_months))

    strategies: dict[str, pd.Series] = {
        "A: Buy & Hold":           pd.Series(1.0, index=df.index),
        f"B: {seasonal_names} naiv":   seasonal_mask.astype(float),
        f"C: {seasonal_names} + Regime": (seasonal_mask & ~bear_mask).astype(float),
    }

    n_years = (df.index[-1] - df.index[0]).days / 365.25

    print(f"\n{'='*72}")
    print(f"  Regime-gefilterter Saisonalitäts-Backtest {ticker}")
    print(f"  Saisonale Monate: {seasonal_names}")
    print(f"{'='*72}")
    print(
        f"{'Strategie':<34} {'CAGR':>8} {'Sharpe':>8} "
        f"{'MaxDD':>9} {'Investiert':>11}"
    )
    print(f"{'-'*72}")

    for name, mask in strategies.items():
        # Strategie-Returns: aktive Tage = log_return, sonst 0
        strat_lr = lr * mask.values

        # Equity-Kurve
        equity      = np.exp(strat_lr.cumsum())
        total_ret   = equity.iloc[-1] / equity.iloc[0]
        cagr        = (total_ret ** (1.0 / n_years) - 1.0) * 100.0

        # Sharpe (nur aktive Tage, annualisiert)
        active = strat_lr[mask > 0]
        sharpe = (
            (active.mean() / active.std()) * math.sqrt(_TRADING_DAYS_YEAR)
            if len(active) > 1 and active.std() > 0 else 0.0
        )

        # Max Drawdown
        rolling_max = equity.cummax()
        max_dd      = ((equity - rolling_max) / rolling_max).min() * 100.0

        invest_pct = mask.mean() * 100.0

        print(
            f"{name:<34} {cagr:>+8.1f}%  {sharpe:>7.2f}  "
            f"{max_dd:>8.1f}%  {invest_pct:>9.1f}%"
        )

    print(f"{'='*72}")
    print("  C vs B: Regime-Filter schließt Bear-Tage aus → weniger Drawdown.")
    print("  Hinweis: Einfacher Backtest ohne Transaktionskosten / Slippage.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description="KMeans Regime-Clustering: Bull/Sideways/Bear via Rolling-Features"
    )
    parser.add_argument("--ticker",  default="SPY",    help="Ticker (default: SPY)")
    parser.add_argument("--period",  default="max",
                        help="Zeitraum (default: max — 'max' liefert volle tägliche Yahoo-Geschichte; "
                             "'20y' etc. gibt ggf. nur Monats-Granularität)")
    parser.add_argument(
        "--months", default="4,11,12",
        help="Saisonale Monate für Backtest, kommagetrennt (default: 4,11,12 = Apr/Nov/Dez)"
    )
    parser.add_argument("--clusters", type=int, default=3,
                        help="Anzahl Cluster (default: 3)")
    args = parser.parse_args()

    seasonal_months = tuple(int(m.strip()) for m in args.months.split(",") if m.strip())

    # ── Pipeline ──────────────────────────────────────────────────────────────
    # 1. Daten laden
    df = load_and_prepare(args.ticker, args.period)

    # 2. Rolling-Features (shift(1) = kein Lookahead)
    df = add_regime_features(df)

    # 3. KMeans
    print(
        f"[regime_clustering] KMeans (k={args.clusters}) auf "
        f"{len(df)} Zeilen x 3 Features ..."
    )
    df = fit_kmeans(df, n_clusters=args.clusters)

    regime_counts = df["regime"].value_counts()
    print(
        f"[regime_clustering] Cluster-Größen: "
        + " | ".join(f"{r}: {regime_counts.get(r, 0)}" for r in ["Bull", "Sideways", "Bear"])
    )

    # 4. Ausgabe-Blöcke
    print_regime_stats(df, args.ticker)
    print_monthly_heatmap(df)
    print_tdom_per_regime(df)
    backtest_strategies(df, args.ticker, seasonal_months)

    print("\n[regime_clustering] Fertig.")


if __name__ == "__main__":
    main()
