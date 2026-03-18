"""
shared/sector_rotation.py — Sektor-Rotation Analyse für SeasonalEdge

Analyse: Welche Sektoren (XLK, XLE, XLF, ...) performen wann am besten?
Heatmap: Monat × Sektor mit durchschnittlicher Rendite.

Verwendung:
    from shared.sector_rotation import (
        SECTOR_ETFS, calculate_sector_seasonality,
        get_best_sectors_by_month, calculate_rotation_signal
    )
"""
import pandas as pd
import numpy as np

# ── Standard US-Sektor-ETFs (SPDR) ─────────────────

SECTOR_ETFS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Health Care",
    "XLY": "Consumer Discr.",
    "XLP": "Consumer Staples",
    "XLI": "Industrials",
    "XLB": "Materials",
    "XLU": "Utilities",
    "XLRE": "Real Estate",
    "XLC": "Communication",
}

# Europäische Sektor-ETFs (optional)
EU_SECTOR_ETFS = {
    "EXV6.DE": "Technology",
    "EXV1.DE": "Financials",
    "EXH1.DE": "Energy",
    "EXV4.DE": "Health Care",
    "EXV5.DE": "Consumer Discr.",
    "EXV8.DE": "Industrials",
}


def calculate_sector_seasonality(
    sector_data: dict[str, pd.DataFrame],
    min_years: int = 5,
) -> pd.DataFrame:
    """
    Berechnet die monatliche Saisonalität pro Sektor.

    Args:
        sector_data: {ticker: DataFrame mit Date und Close}
        min_years: Mindestanzahl Jahre für valide Berechnung

    Returns:
        DataFrame mit Index=Monat(1-12), Columns=Ticker, Values=Ø Rendite %
    """
    results = {}

    for ticker, df in sector_data.items():
        df = df.copy()
        if "Date" in df.columns:
            df = df.set_index("Date")
        df = df.sort_index()

        # Monatsrenditen berechnen
        df["month"] = df.index.month
        df["year"] = df.index.year

        # Letzter Kurs pro Monat
        monthly = df.groupby(["year", "month"])["Close"].last()
        monthly_returns = monthly.groupby(level="year").pct_change() * 100

        # Durchschnitt pro Monat
        month_avg = {}
        for month in range(1, 13):
            month_vals = monthly_returns.xs(month, level="month", drop_level=False)
            valid = month_vals.dropna()
            if len(valid) >= min_years:
                month_avg[month] = valid.mean()
            else:
                month_avg[month] = np.nan

        results[ticker] = month_avg

    return pd.DataFrame(results)


def get_best_sectors_by_month(
    seasonality_df: pd.DataFrame,
    top_n: int = 3,
) -> dict[int, list[tuple[str, float]]]:
    """
    Gibt die Top-N Sektoren pro Monat zurück.

    Returns:
        {monat: [(ticker, avg_return), ...]}
    """
    result = {}
    for month in seasonality_df.index:
        row = seasonality_df.loc[month].dropna().sort_values(ascending=False)
        result[month] = [(ticker, ret) for ticker, ret in row.head(top_n).items()]
    return result


def get_worst_sectors_by_month(
    seasonality_df: pd.DataFrame,
    bottom_n: int = 3,
) -> dict[int, list[tuple[str, float]]]:
    """
    Gibt die schlechtesten N Sektoren pro Monat zurück.

    Returns:
        {monat: [(ticker, avg_return), ...]}
    """
    result = {}
    for month in seasonality_df.index:
        row = seasonality_df.loc[month].dropna().sort_values(ascending=True)
        result[month] = [(ticker, ret) for ticker, ret in row.head(bottom_n).items()]
    return result


def calculate_rotation_signal(
    seasonality_df: pd.DataFrame,
    current_month: int,
    lookforward: int = 1,
) -> pd.DataFrame:
    """
    Berechnet ein Rotationssignal: Welche Sektoren im nächsten Monat
    (oder lookforward Monaten) historisch am besten performen.

    Args:
        current_month: Aktueller Monat (1-12)
        lookforward: Wie viele Monate vorausschauen

    Returns:
        DataFrame mit Ticker, avg_return, rank sortiert nach Rendite
    """
    future_months = [(current_month + i - 1) % 12 + 1 for i in range(1, lookforward + 1)]

    # Durchschnitt über die nächsten Monate
    avg_returns = {}
    for ticker in seasonality_df.columns:
        returns = [
            seasonality_df.loc[m, ticker]
            for m in future_months
            if m in seasonality_df.index and not np.isnan(seasonality_df.loc[m, ticker])
        ]
        if returns:
            avg_returns[ticker] = np.mean(returns)

    result = pd.DataFrame([
        {"ticker": t, "sector": SECTOR_ETFS.get(t, t), "avg_return_pct": r}
        for t, r in avg_returns.items()
    ]).sort_values("avg_return_pct", ascending=False).reset_index(drop=True)

    result["rank"] = range(1, len(result) + 1)
    return result


def monthly_sector_stats(
    sector_data: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    """
    Erweiterte Statistiken pro Sektor und Monat.

    Returns:
        DataFrame mit: ticker, month, avg_return, std_dev, win_rate, n_years
    """
    rows = []

    for ticker, df in sector_data.items():
        df = df.copy()
        if "Date" in df.columns:
            df = df.set_index("Date")
        df = df.sort_index()

        df["month"] = df.index.month
        df["year"] = df.index.year

        monthly = df.groupby(["year", "month"])["Close"].last()
        monthly_returns = monthly.groupby(level="year").pct_change() * 100

        for month in range(1, 13):
            try:
                vals = monthly_returns.xs(month, level="month").dropna()
            except KeyError:
                continue
            if len(vals) < 3:
                continue
            rows.append({
                "ticker": ticker,
                "sector": SECTOR_ETFS.get(ticker, ticker),
                "month": month,
                "avg_return_pct": vals.mean(),
                "std_dev": vals.std(),
                "win_rate_pct": (vals > 0).mean() * 100,
                "n_years": len(vals),
            })

    return pd.DataFrame(rows)
