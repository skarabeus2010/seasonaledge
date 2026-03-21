"""
shared/backtest_engine.py — Generische Backtest Engine & Optimierer
====================================================================
Backtestet Event-basierte Strategien (Feiertage, FOMC, OPEX, Mond, TDoM).
Grid-Search Optimierung, Walk-Forward Validierung, KI Event-Relevanz.

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Callable, Optional
from datetime import date, datetime
import itertools


# ══════════════════════════════════════════════════════
# DATENSTRUKTUREN
# ══════════════════════════════════════════════════════

@dataclass
class EventDefinition:
    """Generisches Event das ein Trade-Fenster ausloest."""
    name: str                          # z.B. "Thanksgiving", "FOMC", "Vollmond"
    category: str                      # "holiday", "fomc", "opex", "moon", "tdom"
    dates_func: Callable               # func(year) -> list[date]


@dataclass
class Trade:
    """Ein einzelner Round-Trip Trade."""
    event_name: str
    event_date: date
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    return_pct: float
    holding_days: int
    year: int
    stopped_out: bool = False
    max_drawdown_pct: float = 0.0
    ki_features: dict = field(default_factory=dict)


@dataclass
class BacktestResult:
    """Ergebnis eines einzelnen Backtest-Laufs."""
    trades: list
    params: dict
    total_return_pct: float = 0.0
    annualized_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    calmar_ratio: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate_pct: float = 0.0
    avg_return_pct: float = 0.0
    median_return_pct: float = 0.0
    profit_factor: float = 0.0
    n_trades: int = 0
    avg_holding_days: float = 0.0
    equity_curve: list = field(default_factory=list)
    is_oos: bool = False


@dataclass
class OptimizationResult:
    """Ergebnis einer Grid-Search Optimierung."""
    results: list
    best_by_objective: dict
    param_grid: dict
    objective_used: str
    walk_forward_results: list = field(default_factory=list)


# ══════════════════════════════════════════════════════
# STOP-LOSS
# ══════════════════════════════════════════════════════

def _apply_stop_loss(
    df: pd.DataFrame,
    entry_idx: int,
    exit_idx: int,
    entry_price: float,
    stop_loss_pct: float,
    stop_type: str = "fixed",
) -> tuple:
    """
    Prueft ob Stop-Loss zwischen Entry und Exit ausgeloest wird.

    Returns:
        (actual_exit_price, actual_exit_idx, was_stopped, max_dd_pct)
    """
    if stop_loss_pct <= 0:
        exit_price = float(df.iloc[exit_idx]["Close"])
        return exit_price, exit_idx, False, 0.0

    high_watermark = entry_price
    max_dd = 0.0

    for i in range(entry_idx + 1, exit_idx + 1):
        row = df.iloc[i]
        low = float(row["Low"])
        high = float(row["High"])

        # Update high watermark
        if high > high_watermark:
            high_watermark = high

        # Stop-Level berechnen
        if stop_type == "trailing":
            stop_level = high_watermark * (1 - stop_loss_pct / 100)
        else:  # fixed
            stop_level = entry_price * (1 - stop_loss_pct / 100)

        # Drawdown tracken
        dd = (low - high_watermark) / high_watermark * 100
        if dd < max_dd:
            max_dd = dd

        # Stop ausgeloest?
        if low <= stop_level:
            return stop_level, i, True, abs(max_dd)

    # Kein Stop — normaler Exit
    exit_price = float(df.iloc[exit_idx]["Close"])
    return exit_price, exit_idx, False, abs(max_dd)


# ══════════════════════════════════════════════════════
# STATISTIKEN
# ══════════════════════════════════════════════════════

def _compute_stats(trades: list, params: dict) -> BacktestResult:
    """Berechnet alle Statistiken aus einer Trade-Liste."""
    result = BacktestResult(trades=trades, params=params)

    if not trades:
        return result

    returns = [t.return_pct for t in trades]
    result.n_trades = len(trades)
    result.avg_return_pct = round(float(np.mean(returns)), 2)
    result.median_return_pct = round(float(np.median(returns)), 2)
    result.avg_holding_days = round(float(np.mean([t.holding_days for t in trades])), 1)

    # Win-Rate
    wins = [r for r in returns if r > 0]
    losses = [r for r in returns if r <= 0]
    result.win_rate_pct = round(len(wins) / len(returns) * 100, 1)

    # Profit Factor
    sum_wins = sum(wins) if wins else 0
    sum_losses = abs(sum(losses)) if losses else 0.001
    result.profit_factor = round(sum_wins / sum_losses, 2)

    # Equity Curve
    equity = [100.0]
    for r in returns:
        equity.append(equity[-1] * (1 + r / 100))
    result.equity_curve = equity

    # Total Return (kumulativ)
    result.total_return_pct = round(equity[-1] - 100, 2)

    # Max Drawdown (aus Equity Curve)
    peak = equity[0]
    max_dd = 0.0
    for val in equity:
        if val > peak:
            peak = val
        dd = (val - peak) / peak * 100
        if dd < max_dd:
            max_dd = dd
    result.max_drawdown_pct = round(abs(max_dd), 2)

    # Annualisierte Rendite
    years_span = len(set(t.year for t in trades))
    if years_span > 0:
        total_factor = equity[-1] / 100
        result.annualized_return_pct = round(
            (total_factor ** (1 / years_span) - 1) * 100, 2
        )

    # Calmar Ratio
    if result.max_drawdown_pct > 0:
        result.calmar_ratio = round(
            result.annualized_return_pct / result.max_drawdown_pct, 2
        )

    # Sharpe Ratio (vereinfacht, risk-free = 0)
    if len(returns) > 1:
        std = float(np.std(returns))
        if std > 0:
            trades_per_year = result.n_trades / max(years_span, 1)
            result.sharpe_ratio = round(
                float(np.mean(returns)) / std * np.sqrt(trades_per_year), 2
            )

    return result


# ══════════════════════════════════════════════════════
# KERN: BACKTEST
# ══════════════════════════════════════════════════════

def run_backtest(
    df: pd.DataFrame,
    events: list,
    days_before: int = 3,
    days_after: int = 3,
    entry_price_col: str = "Close",
    exit_price_col: str = "Close",
    selected_years: list = None,
    stop_loss_pct: float = 0.0,
    stop_loss_type: str = "fixed",
    exclude_years: list = None,
    min_gap_days: int = 5,
) -> BacktestResult:
    """
    Fuehrt einen Backtest fuer Event-basierte Strategien durch.

    Args:
        df: Preprocessed DataFrame mit DatetimeIndex + OHLC
        events: Liste von EventDefinition
        days_before: Handelstage vor Event als Entry
        days_after: Handelstage nach Event als Exit
        entry_price_col: "Open" oder "Close"
        exit_price_col: "Open" oder "Close"
        selected_years: Nur diese Jahre backtesten
        stop_loss_pct: Stop-Loss in % (0 = deaktiviert)
        stop_loss_type: "fixed" oder "trailing"
        exclude_years: Outlier-Jahre ausschliessen
        min_gap_days: Mindestabstand zwischen Trades

    Returns:
        BacktestResult mit allen Trades und Statistiken
    """
    if selected_years is None:
        selected_years = sorted(df.index.year.unique())

    if exclude_years:
        selected_years = [y for y in selected_years if y not in exclude_years]

    trading_days = df.index.tolist()
    trades = []
    last_exit_date = None

    for year in selected_years:
        year_events = []
        for event in events:
            try:
                dates = event.dates_func(year)
                for d in dates:
                    if d is not None:
                        year_events.append((event.name, pd.Timestamp(d)))
            except Exception:
                continue

        # Sortieren nach Datum
        year_events.sort(key=lambda x: x[1])

        for event_name, event_date in year_events:
            # Naechsten Handelstag auf/nach Event finden
            future_days = [t for t in trading_days if t >= event_date]
            if not future_days:
                continue
            t0 = future_days[0]

            try:
                t0_idx = trading_days.index(t0)
            except ValueError:
                continue

            # Entry und Exit Index
            entry_idx = t0_idx - days_before
            exit_idx = t0_idx + days_after

            if entry_idx < 0 or exit_idx >= len(trading_days):
                continue

            entry_date = trading_days[entry_idx]
            exit_date = trading_days[exit_idx]

            # Mindestabstand pruefen
            if last_exit_date and (entry_date - last_exit_date).days < min_gap_days:
                continue

            # Preise
            entry_price = float(df.loc[entry_date, entry_price_col])
            if entry_price <= 0:
                continue

            # Stop-Loss pruefen
            actual_exit_price, actual_exit_idx, stopped, max_dd = _apply_stop_loss(
                df, entry_idx, exit_idx, entry_price,
                stop_loss_pct, stop_loss_type,
            )

            if not stopped:
                actual_exit_price = float(df.iloc[exit_idx][exit_price_col])

            ret = (actual_exit_price - entry_price) / entry_price * 100
            holding = actual_exit_idx - entry_idx

            trades.append(Trade(
                event_name=event_name,
                event_date=event_date.date() if hasattr(event_date, 'date') else event_date,
                entry_date=entry_date.date() if hasattr(entry_date, 'date') else entry_date,
                exit_date=trading_days[actual_exit_idx].date() if hasattr(trading_days[actual_exit_idx], 'date') else trading_days[actual_exit_idx],
                entry_price=round(entry_price, 2),
                exit_price=round(actual_exit_price, 2),
                return_pct=round(ret, 4),
                holding_days=holding,
                year=year,
                stopped_out=stopped,
                max_drawdown_pct=round(max_dd, 2),
            ))

            last_exit_date = trading_days[actual_exit_idx]

    # Chronologisch sortieren
    trades.sort(key=lambda t: t.entry_date)

    params = {
        "days_before": days_before,
        "days_after": days_after,
        "stop_loss_pct": stop_loss_pct,
        "stop_loss_type": stop_loss_type,
        "n_events": len(events),
    }

    return _compute_stats(trades, params)


# ══════════════════════════════════════════════════════
# OPTIMIERUNG
# ══════════════════════════════════════════════════════

OBJECTIVES = {
    "total_return": lambda r: r.total_return_pct,
    "sharpe": lambda r: r.sharpe_ratio,
    "calmar": lambda r: r.calmar_ratio,
    "win_rate": lambda r: r.win_rate_pct,
}


def optimize_parameters(
    df: pd.DataFrame,
    events: list,
    param_grid: dict = None,
    objective: str = "calmar",
    entry_price_col: str = "Close",
    exit_price_col: str = "Close",
    stop_loss_pct: float = 0.0,
    stop_loss_type: str = "fixed",
    selected_years: list = None,
    exclude_years: list = None,
    progress_callback: Callable = None,
) -> OptimizationResult:
    """
    Grid-Search ueber days_before x days_after.

    Args:
        param_grid: z.B. {"days_before": [1,2,...,10], "days_after": [1,2,...,10]}
        objective: "total_return", "sharpe", "calmar", "win_rate"
        progress_callback: callback(i, total) fuer Streamlit Progress

    Returns:
        OptimizationResult mit allen Ergebnissen + Best-of
    """
    if param_grid is None:
        param_grid = {
            "days_before": list(range(1, 11)),
            "days_after": list(range(1, 11)),
        }

    obj_func = OBJECTIVES.get(objective, OBJECTIVES["calmar"])

    # Alle Kombinationen
    keys = list(param_grid.keys())
    values = list(param_grid.values())
    combos = list(itertools.product(*values))

    results = []
    for i, combo in enumerate(combos):
        params = dict(zip(keys, combo))

        if progress_callback:
            progress_callback(i, len(combos))

        result = run_backtest(
            df, events,
            days_before=params.get("days_before", 3),
            days_after=params.get("days_after", 3),
            entry_price_col=entry_price_col,
            exit_price_col=exit_price_col,
            selected_years=selected_years,
            stop_loss_pct=stop_loss_pct,
            stop_loss_type=stop_loss_type,
            exclude_years=exclude_years,
        )
        results.append(result)

    if progress_callback:
        progress_callback(len(combos), len(combos))

    # Best per objective
    best_by = {}
    for obj_name, obj_fn in OBJECTIVES.items():
        sorted_results = sorted(results, key=obj_fn, reverse=True)
        if sorted_results:
            best_by[obj_name] = sorted_results[0]

    # Sortiere nach gewaehltem Objective
    results.sort(key=obj_func, reverse=True)

    return OptimizationResult(
        results=results,
        best_by_objective=best_by,
        param_grid=param_grid,
        objective_used=objective,
    )


# ══════════════════════════════════════════════════════
# WALK-FORWARD VALIDIERUNG
# ══════════════════════════════════════════════════════

def walk_forward(
    df: pd.DataFrame,
    events: list,
    param_grid: dict = None,
    objective: str = "calmar",
    n_folds: int = 5,
    in_sample_ratio: float = 0.7,
    entry_price_col: str = "Close",
    exit_price_col: str = "Close",
    stop_loss_pct: float = 0.0,
    stop_loss_type: str = "fixed",
    exclude_years: list = None,
    progress_callback: Callable = None,
) -> list:
    """
    Walk-Forward Validierung: Optimiere auf In-Sample, teste auf Out-of-Sample.

    Returns:
        Liste von BacktestResult (ein pro Fold, markiert mit is_oos)
    """
    all_years = sorted(df.index.year.unique())
    if exclude_years:
        all_years = [y for y in all_years if y not in exclude_years]

    n_total = len(all_years)
    fold_results = []

    for fold in range(n_folds):
        # Expanding Window
        is_end = int(n_total * (in_sample_ratio + fold * (1 - in_sample_ratio) / n_folds))
        oos_end = int(is_end + n_total * (1 - in_sample_ratio) / n_folds)

        is_end = min(is_end, n_total)
        oos_end = min(oos_end, n_total)

        if is_end >= n_total or is_end == oos_end:
            break

        is_years = all_years[:is_end]
        oos_years = all_years[is_end:oos_end]

        if len(is_years) < 5 or len(oos_years) < 2:
            continue

        if progress_callback:
            progress_callback(fold, n_folds)

        # Optimiere auf In-Sample
        opt_result = optimize_parameters(
            df, events, param_grid, objective,
            entry_price_col, exit_price_col,
            stop_loss_pct, stop_loss_type,
            selected_years=is_years,
            exclude_years=exclude_years,
        )

        if not opt_result.results:
            continue

        best = opt_result.best_by_objective.get(objective, opt_result.results[0])
        best_params = best.params

        # Teste auf Out-of-Sample mit besten Parametern
        oos_result = run_backtest(
            df, events,
            days_before=best_params.get("days_before", 3),
            days_after=best_params.get("days_after", 3),
            entry_price_col=entry_price_col,
            exit_price_col=exit_price_col,
            selected_years=oos_years,
            stop_loss_pct=stop_loss_pct,
            stop_loss_type=stop_loss_type,
            exclude_years=exclude_years,
        )
        oos_result.is_oos = True
        fold_results.append(oos_result)

    if progress_callback:
        progress_callback(n_folds, n_folds)

    return fold_results


# ══════════════════════════════════════════════════════
# EVENT-ADAPTER
# ══════════════════════════════════════════════════════

def make_holiday_events(exchange: str = "NYSE") -> list:
    """Erstellt EventDefinitions fuer alle Feiertage einer Boerse."""
    events = []

    if exchange == "NYSE":
        from shared.nyse_holidays import (
            _compute_nyse_holidays, _good_friday, _nth_weekday,
            _observed, _monday_if_sunday,
        )
        from datetime import date as _date

        holiday_funcs = {
            "New Year's Day":   lambda y: _monday_if_sunday(_date(y, 1, 1)),
            "MLK Day":          lambda y: _nth_weekday(y, 1, 0, 3),
            "Presidents' Day":  lambda y: _nth_weekday(y, 2, 0, 3),
            "Good Friday":      lambda y: _good_friday(y),
            "Memorial Day":     lambda y: _nth_weekday(y, 5, 0, -1),
            "Juneteenth":       lambda y: _observed(_date(y, 6, 19)) if y >= 2022 else None,
            "Independence Day": lambda y: _observed(_date(y, 7, 4)),
            "Labor Day":        lambda y: _nth_weekday(y, 9, 0, 1),
            "Columbus Day":     lambda y: _nth_weekday(y, 10, 0, 2),
            "Veterans Day":     lambda y: _observed(_date(y, 11, 11)),
            "Thanksgiving":     lambda y: _nth_weekday(y, 11, 3, 4),
            "Christmas Day":    lambda y: _observed(_date(y, 12, 25)),
        }

        for name, func in holiday_funcs.items():
            events.append(EventDefinition(
                name=name,
                category="holiday",
                dates_func=lambda y, f=func: [d for d in [f(y)] if d is not None],
            ))

    return events


def make_fomc_events() -> list:
    """Erstellt EventDefinitions fuer FOMC-Sitzungen."""
    from shared.fed_dates import FOMC_MEETING_DATES

    def fomc_dates(year):
        return [date(y, m, d) for y, m, d in FOMC_MEETING_DATES if y == year]

    return [EventDefinition(name="FOMC", category="fomc", dates_func=fomc_dates)]


def make_opex_events(triple_only: bool = False) -> list:
    """Erstellt EventDefinitions fuer OPEX-Termine."""
    from shared.nyse_holidays import get_all_opex_dates

    def opex_dates(year):
        all_opex = get_all_opex_dates(year, year)
        if triple_only:
            return [e["date"] for e in all_opex if e["is_triple"]]
        return [e["date"] for e in all_opex]

    name = "Triple Witching" if triple_only else "OPEX"
    return [EventDefinition(name=name, category="opex", dates_func=opex_dates)]


def make_moon_events(phase: str = "full") -> list:
    """Erstellt EventDefinitions fuer Mondphasen."""
    from shared.central_banks import get_full_moon_dates, get_new_moon_dates

    def moon_dates(year):
        if phase == "full":
            entries = get_full_moon_dates(year, year)
        else:
            entries = get_new_moon_dates(year, year)
        return [e["date"].date() if hasattr(e["date"], "date") else e["date"] for e in entries]

    name = "Vollmond" if phase == "full" else "Neumond"
    return [EventDefinition(name=name, category="moon", dates_func=moon_dates)]


# ══════════════════════════════════════════════════════
# KI: EVENT-RELEVANZ
# ══════════════════════════════════════════════════════

def score_event_relevance(
    df: pd.DataFrame,
    events: list,
    days_before: int = 3,
    days_after: int = 3,
    selected_years: list = None,
) -> pd.DataFrame:
    """
    Bewertet die statistische Relevanz jedes Events.

    Returns:
        DataFrame mit: event_name, avg_return, win_rate, n_trades,
                       t_statistic, p_value, relevance_score
    """
    from scipy import stats

    rows = []

    for event in events:
        result = run_backtest(
            df, [event],
            days_before=days_before,
            days_after=days_after,
            selected_years=selected_years,
        )

        if result.n_trades < 5:
            continue

        returns = [t.return_pct for t in result.trades]

        # t-Test: H0 = mean return = 0
        t_stat, p_value = stats.ttest_1samp(returns, 0)

        # Effect Size (Cohen's d)
        std = float(np.std(returns))
        cohens_d = abs(float(np.mean(returns))) / std if std > 0 else 0

        # Relevance Score
        significance = max(0, 1 - p_value)
        win_component = result.win_rate_pct / 100
        effect_component = min(cohens_d, 1.0)
        relevance = 0.5 * significance + 0.3 * win_component + 0.2 * effect_component

        rows.append({
            "Event": event.name,
            "Kategorie": event.category,
            "Oe Rendite": round(result.avg_return_pct, 2),
            "Win-Rate": round(result.win_rate_pct, 1),
            "n Trades": result.n_trades,
            "t-Statistik": round(float(t_stat), 2),
            "p-Wert": round(float(p_value), 4),
            "Relevanz": round(relevance, 3),
        })

    if not rows:
        return pd.DataFrame()

    result_df = pd.DataFrame(rows).sort_values("Relevanz", ascending=False)
    return result_df


# ══════════════════════════════════════════════════════
# KI: ISOLATION FOREST TRADE FILTER
# ══════════════════════════════════════════════════════

def extract_trade_features(
    df: pd.DataFrame,
    trade: Trade,
    lookback: int = 20,
) -> dict:
    """Extrahiert ML-Features fuer einen Trade."""
    try:
        entry_ts = pd.Timestamp(trade.entry_date)
        pre = df[df.index < entry_ts].tail(lookback)

        if len(pre) < 5:
            return {}

        returns = pre["Close"].pct_change().dropna() * 100

        return {
            "pre_return_5d": round(float(returns.tail(5).sum()), 2),
            "pre_return_20d": round(float(returns.sum()), 2),
            "pre_volatility": round(float(returns.std()), 3),
            "month": trade.entry_date.month if hasattr(trade.entry_date, 'month') else 0,
            "weekday": trade.entry_date.weekday() if hasattr(trade.entry_date, 'weekday') else 0,
        }
    except Exception:
        return {}


def filter_trades_isolation_forest(
    trades: list,
    contamination: float = 0.1,
) -> tuple:
    """
    Filtert anomale Trades via Isolation Forest.

    Returns:
        (filtered_trades, excluded_trades)
    """
    try:
        from sklearn.ensemble import IsolationForest
    except ImportError:
        return trades, []

    # Features extrahieren
    feature_trades = [(t, t.ki_features) for t in trades if t.ki_features]
    if len(feature_trades) < 10:
        return trades, []

    feature_keys = list(feature_trades[0][1].keys())
    X = np.array([[f.get(k, 0) for k in feature_keys] for _, f in feature_trades])

    clf = IsolationForest(contamination=contamination, random_state=42)
    labels = clf.fit_predict(X)

    filtered = []
    excluded = []
    for (trade, _), label in zip(feature_trades, labels):
        if label == 1:
            filtered.append(trade)
        else:
            excluded.append(trade)

    # Trades ohne Features behalten
    no_features = [t for t in trades if not t.ki_features]
    filtered.extend(no_features)

    return filtered, excluded
