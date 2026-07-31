"""
scripts/ml/tom_ml_filter.py — Turn-of-Month + Logistic Regression Backtest
===========================================================================
Walk-Forward Backtest: Klassisches Turn-of-Month Fenster (letzte 3 + erste 3
Handelstage pro Monat) gefiltert durch einen Logistic Regression Classifier.

Strategien:
  buy_and_hold  — immer investiert, kumulierte Log-Renditen
  tom_naive     — im ToM-Fenster long, sonst flat
  tom_ml        — im ToM-Fenster long NUR wenn ML-Signal = 1, sonst flat

Walk-Forward: Train 5 Jahre, Test 1 Jahr, Slide +1 (mind. 3 Test-Perioden).
Features (alle lookahead-frei, d.h. um 1 Tag versetzt wo noetig):
  tdom, tdom_from_end, weekday, log_return_lag1, rolling_vol_20, rsi_14

Aufruf:
  py -3.14 scripts/ml/tom_ml_filter.py
"""
from __future__ import annotations

import sys
import pathlib

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Projekt-Root in sys.path
_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from shared.yahoo_downloader import download_data  # noqa: E402

# ─── Konfiguration ────────────────────────────────────────────────────────────
TICKERS: list[str] = ['SPY', 'QQQ', '^GDAXI', 'GLD']
TRAIN_YEARS     = 5
MIN_TEST_PERIODS = 3
FEATURE_COLS: list[str] = [
    'tdom', 'tdom_from_end', 'weekday',
    'log_return_lag1', 'rolling_vol_20', 'rsi_14',
]
PERIOD = '10y'


# ─── Feature Engineering ──────────────────────────────────────────────────────

def _compute_tdom_features(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """
    TDOM (Trading Day of Month, 1-basiert ab Monatsanfang) und
    tdom_from_end (1 = letzter Handelstag des Monats) aus dem Index.
    """
    tdom          = pd.Series(0, index=df.index, dtype=int)
    tdom_from_end = pd.Series(0, index=df.index, dtype=int)

    for _period, group in df.groupby(df.index.to_period('M')):
        n = len(group)
        tdom.loc[group.index]          = list(range(1, n + 1))
        tdom_from_end.loc[group.index] = list(range(n, 0, -1))

    return tdom, tdom_from_end


def _compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Standard-RSI(period) aus Close-Preisen (einfaches Rolling-Mean)."""
    delta    = close.diff()
    gain     = delta.clip(lower=0)
    loss     = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs       = avg_gain / avg_loss.replace(0, 1e-10)
    return 100.0 - (100.0 / (1.0 + rs))


def build_features(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Baut die Feature-Matrix aus rohem OHLCV-DataFrame.

    Alle Indikatoren sind um 1 Tag versetzt (rsi_14, rolling_vol_20),
    oder bereits ein Lag (log_return_lag1), so dass fuer Tag t nur
    Informationen bis einschliesslich t-1 verwendet werden —
    kein Lookahead in die heutige Rendite.

    tdom und weekday sind vor Handelsstart bekannt → kein Versatz noetig.
    """
    df = df_raw[['Close']].copy()

    # Log-Rendite
    df['log_return'] = np.log(df['Close'] / df['Close'].shift(1))

    # Lag-1-Rendite (Vortagsrendite)
    df['log_return_lag1'] = df['log_return'].shift(1)

    # TDOM-Features (kalendarisch, kein Lookahead)
    df['tdom'], df['tdom_from_end'] = _compute_tdom_features(df)

    # Wochentag 0=Mo … 4=Fr
    df['weekday'] = df.index.dayofweek

    # Rolling-Volatilitaet: shift(1) damit nur Daten bis t-1 einfliessen
    df['rolling_vol_20'] = df['log_return'].rolling(20).std().shift(1)

    # RSI: shift(1) damit nur Close bis t-1 einfliessen
    df['rsi_14'] = _compute_rsi(df['Close']).shift(1)

    # ToM-Fenster: letzte 3 + erste 3 Handelstage im Monat
    df['in_tom_window'] = (df['tdom_from_end'] <= 3) | (df['tdom'] <= 3)

    # Ziel: ist die heutige Rendite positiv?
    # Da Features um 1 versetzt sind, ist das aequivalent zu "next_day" bei unversetzten Features
    df['target'] = (df['log_return'] > 0).astype(int)

    return df.dropna()


# ─── Metriken ─────────────────────────────────────────────────────────────────

def compute_metrics(returns: pd.Series) -> dict[str, float]:
    """
    Berechnet CAGR, Sharpe (annualisiert, rf=0), Max Drawdown und Win-Rate
    aus einer taeglich indizierten Serie von Log-Renditen.

    Tage mit Rendite = 0 (= Cash-Tage) gehen in Sharpe ein und druecken
    ihn korrekt nach unten (nicht investierte Zeit wird bestraft).
    """
    n = len(returns)
    if n == 0:
        return {'CAGR': 0.0, 'Sharpe': 0.0, 'MaxDD': 0.0, 'WinRate': 0.0}

    n_years = n / 252.0

    # CAGR
    total_return = float(np.exp(returns.sum()))
    cagr = (total_return ** (1.0 / n_years) - 1.0) if n_years > 0 else 0.0

    # Sharpe (alle Tage inkl. Cash = 0)
    mean_d = float(returns.mean())
    std_d  = float(returns.std(ddof=1))
    sharpe = (mean_d / std_d * np.sqrt(252.0)) if std_d > 1e-12 else 0.0

    # Max Drawdown auf kumulierten Renditen
    cum         = np.exp(returns.cumsum())
    rolling_max = cum.cummax()
    drawdown    = (cum - rolling_max) / rolling_max
    max_dd      = float(drawdown.min())

    # Win-Rate: nur aktiv investierte Tage (Rendite != 0)
    active   = returns[returns != 0.0]
    win_rate = float((active > 0).mean()) if len(active) > 0 else 0.0

    return {'CAGR': cagr, 'Sharpe': sharpe, 'MaxDD': max_dd, 'WinRate': win_rate}


# ─── Walk-Forward Backtest ────────────────────────────────────────────────────

def backtest_ticker(ticker: str) -> dict | None:
    """
    Fuehrt den Walk-Forward Backtest fuer einen einzelnen Ticker durch.

    Gibt ein Dict mit Metriken fuer alle drei Strategien zurueck,
    oder None bei ungenuegenden Daten.
    """
    print(f"\nLade Daten fuer {ticker} (period={PERIOD})...")
    df_raw = download_data(ticker, period=PERIOD)

    if df_raw is None or len(df_raw) < 500:
        print(f"  WARNUNG: Zu wenige Rohdaten fuer {ticker} ({len(df_raw) if df_raw is not None else 0} Zeilen).")
        return None

    df = build_features(df_raw)

    if len(df) < 400:
        print(f"  WARNUNG: Zu wenige Zeilen nach Feature-Berechnung ({len(df)}).")
        return None

    all_years  = sorted(df.index.year.unique())
    first_year = all_years[0]
    last_year  = all_years[-1]

    print(f"  Bereich: {df.index[0].date()} bis {df.index[-1].date()} "
          f"({len(all_years)} Kalenderjahre, {len(df)} Handelstage)")

    # Erster Test-Jahrgang: first_year + TRAIN_YEARS
    first_test_year = first_year + TRAIN_YEARS
    n_test_periods  = last_year - first_test_year + 1

    if n_test_periods < MIN_TEST_PERIODS:
        print(f"  WARNUNG: Nur {n_test_periods} Test-Perioden (Minimum {MIN_TEST_PERIODS}) — uebersprungen.")
        return None

    print(f"  Walk-Forward: Train {TRAIN_YEARS}J, Test 1J, "
          f"{n_test_periods} Perioden ({first_test_year}–{last_year})")

    # ML-Signale sammeln (NaN = kein Signal / kein ToM-Fenster-Tag)
    ml_signals = pd.Series(np.nan, index=df.index)

    for test_year in range(first_test_year, last_year + 1):
        train_start = test_year - TRAIN_YEARS

        train_mask = (df.index.year >= train_start) & (df.index.year < test_year)
        test_mask  = (df.index.year == test_year)

        # Nur ToM-Fenster-Tage fuer Training und Inferenz
        train_tom = df[train_mask & df['in_tom_window']]
        test_tom  = df[test_mask  & df['in_tom_window']]

        if len(train_tom) < 30 or len(test_tom) < 3:
            print(f"    Jahr {test_year}: zu wenige ToM-Tage (train={len(train_tom)}, test={len(test_tom)}) — uebersprungen.")
            continue

        X_train = train_tom[FEATURE_COLS].values
        y_train = train_tom['target'].values
        X_test  = test_tom[FEATURE_COLS].values

        scaler      = StandardScaler()
        X_train_s   = scaler.fit_transform(X_train)
        X_test_s    = scaler.transform(X_test)

        model = LogisticRegression(max_iter=1000, random_state=42)
        model.fit(X_train_s, y_train)

        preds = model.predict(X_test_s)
        ml_signals.loc[test_tom.index] = preds.astype(float)

    # ── Auswertung: alle Handelstage ab erstem Testjahr ─────────────────────
    eval_start_date = df.index[df.index.year >= first_test_year][0]
    eval_mask       = df.index >= eval_start_date
    eval_df         = df[eval_mask].copy()
    ml_sig_eval     = ml_signals[eval_mask].fillna(0.0)

    # Strategie-Renditen
    bh_ret       = eval_df['log_return']
    tom_naive_ret = eval_df['log_return'] * eval_df['in_tom_window'].astype(float)
    tom_ml_ret    = (eval_df['log_return']
                     * eval_df['in_tom_window'].astype(float)
                     * (ml_sig_eval == 1.0).astype(float))

    # Anteil ToM-Fenster-Tage
    tom_pct = eval_df['in_tom_window'].mean() * 100
    ml_active_pct = (ml_sig_eval == 1.0)[eval_df['in_tom_window']].mean() * 100

    print(f"  ToM-Fenster: {tom_pct:.1f}% aller Handelstage | "
          f"ML aktiv (von ToM-Tagen): {ml_active_pct:.1f}%")

    return {
        'ticker':     ticker,
        'date_range': f"{first_year}–{last_year}",
        'eval_range': f"{eval_start_date.year}–{last_year}",
        'bh':         compute_metrics(bh_ret),
        'tom_naive':  compute_metrics(tom_naive_ret),
        'tom_ml':     compute_metrics(tom_ml_ret),
    }


# ─── Ausgabe ──────────────────────────────────────────────────────────────────

def print_results(results: dict) -> None:
    """Gibt die Ergebnis-Tabelle fuer einen Ticker auf der Konsole aus."""
    ticker     = results['ticker']
    date_range = results['date_range']
    eval_range = results['eval_range']

    strategies = [
        ('bh',        'buy_and_hold'),
        ('tom_naive', 'tom_naive'),
        ('tom_ml',    'tom_ml'),
    ]

    line_len = 58
    print(f"\n{'=' * line_len}")
    print(f"  {ticker}  ({date_range})  — Eval-Zeitraum: {eval_range}")
    print(f"{'=' * line_len}")
    print(f"{'Strategie':22s} {'CAGR':>7s} {'Sharpe':>8s} {'MaxDD':>8s} {'WinRate':>9s}")
    print(f"{'-' * line_len}")

    for key, label in strategies:
        m = results[key]
        print(
            f"{label:22s} "
            f"{m['CAGR']:>6.1%}  "
            f"{m['Sharpe']:>7.2f}  "
            f"{m['MaxDD']:>6.1%}  "
            f"{m['WinRate']:>7.1%}"
        )


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    banner = "Turn-of-Month + Logistic Regression Walk-Forward Backtest"
    print("=" * len(banner))
    print(banner)
    print("=" * len(banner))
    print(f"Ticker: {', '.join(TICKERS)}")
    print(f"Konfiguration: Train {TRAIN_YEARS}J / Test 1J / min. {MIN_TEST_PERIODS} Perioden")
    print(f"Features: {', '.join(FEATURE_COLS)}")

    all_results: list[dict] = []

    for ticker in TICKERS:
        result = backtest_ticker(ticker)
        if result:
            all_results.append(result)

    print("\n\n" + "=" * 58)
    print("  ERGEBNISSE")
    print("=" * 58)

    for result in all_results:
        print_results(result)

    if not all_results:
        print("\nKeine Ergebnisse — Datenproblem?")

    print("\nFertig.")


if __name__ == '__main__':
    main()
