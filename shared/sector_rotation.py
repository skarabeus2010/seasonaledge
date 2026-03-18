"""
SeasonalEdge — Sektor-Rotation Analyse

Fragestellung:
  "Welche Sektoren performen wann am besten?"
  Heatmap: Monat × Sektor → Durchschnittliche Rendite

Standard-Sektoren (SPDR Select Sector ETFs):
  XLK  Technology       XLV  Health Care     XLF  Financials
  XLE  Energy           XLI  Industrials     XLP  Consumer Staples
  XLY  Consumer Discr.  XLU  Utilities       XLB  Materials
  XLRE Real Estate      XLC  Communication

Verwendung:
  from shared.sector_rotation import (
      calc_sector_monthly_returns,
      build_rotation_heatmap,
      get_best_sectors_by_month,
      calc_sector_seasonality,
      SECTOR_ETFS,
  )
"""

import numpy as np
import pandas as pd

from shared.logger import app_logger, error_logger


# ── Sektor-Definitionen ─────────────────────────────────────

SECTOR_ETFS = {
    "XLK":  "Technology",
    "XLV":  "Health Care",
    "XLF":  "Financials",
    "XLE":  "Energy",
    "XLI":  "Industrials",
    "XLP":  "Consumer Staples",
    "XLY":  "Consumer Discr.",
    "XLU":  "Utilities",
    "XLB":  "Materials",
    "XLRE": "Real Estate",
    "XLC":  "Communication",
}

# Europäische Sektoren (iShares STOXX Europe 600)
EU_SECTOR_ETFS = {
    "EXV8.DE":  "Technology",
    "EXV4.DE":  "Health Care",
    "EXV1.DE":  "Financials",
    "EXV6.DE":  "Energy",
    "EXV9.DE":  "Industrials",
    "EXV3.DE":  "Consumer Staples",
    "EXV5.DE":  "Consumer Discr.",
    "EXV7.DE":  "Utilities",
    "EXV2.DE":  "Basic Resources",
    "EXSA.DE":  "Real Estate",
}

MONTH_NAMES_DE = {
    1: "Jan", 2: "Feb", 3: "Mär", 4: "Apr",
    5: "Mai", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Okt", 11: "Nov", 12: "Dez",
}

MONTH_NAMES_EN = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
    5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
    9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


# ── Monatliche Renditen berechnen ────────────────────────────

def calc_sector_monthly_returns(
    sector_data: dict[str, pd.DataFrame],
    date_col: str = "Date",
    close_col: str = "Close",
    min_years: int = 5,
) -> pd.DataFrame:
    """
    Berechnet durchschnittliche Monatsrenditen pro Sektor.

    Args:
        sector_data: Dict {Ticker: DataFrame mit Date + Close}
        min_years: Mindestanzahl Jahre für Aufnahme

    Returns:
        DataFrame (Index=Monat 1-12, Columns=Sektor-Ticker, Values=Avg Return %)
    """
    all_monthly = {}

    for ticker, df in sector_data.items():
        try:
            work = df.copy()
            if date_col in work.columns:
                work[date_col] = pd.to_datetime(work[date_col])
                work = work.set_index(date_col)
            work = work.sort_index()

            # Monatliche Renditen
            monthly = work[close_col].resample("ME").last().pct_change() * 100
            monthly = monthly.dropna()

            if len(monthly) < min_years * 12:
                app_logger.warning(
                    f"Sektor {ticker}: nur {len(monthly)} Monate — übersprungen"
                )
                continue

            # Durchschnitt pro Kalendermonat
            monthly_avg = monthly.groupby(monthly.index.month).mean()
            all_monthly[ticker] = monthly_avg

        except Exception as e:
            error_logger.error(f"Sektor-Rendite fehlgeschlagen: {ticker} — {e}")
            continue

    if not all_monthly:
        return pd.DataFrame()

    result = pd.DataFrame(all_monthly)
    result.index.name = "month"
    return result


# ── Rotation Heatmap ─────────────────────────────────────────

def build_rotation_heatmap(
    monthly_returns: pd.DataFrame,
    sector_names: dict[str, str] | None = None,
    language: str = "de",
) -> pd.DataFrame:
    """
    Formatiert die Monatsrenditen als Heatmap-fähige Tabelle.

    Args:
        monthly_returns: Ergebnis von calc_sector_monthly_returns()
        sector_names: Mapping Ticker → Name (default: SECTOR_ETFS)
        language: "de" oder "en" für Monatsnamen

    Returns:
        DataFrame (Index=Monatsname, Columns=Sektorname, Values=Avg Return %)
    """
    if monthly_returns.empty:
        return pd.DataFrame()

    if sector_names is None:
        sector_names = {**SECTOR_ETFS, **EU_SECTOR_ETFS}

    month_names = MONTH_NAMES_DE if language == "de" else MONTH_NAMES_EN

    heatmap = monthly_returns.copy()

    # Spalten umbenennen: Ticker → Name
    heatmap.columns = [
        sector_names.get(col, col) for col in heatmap.columns
    ]

    # Index umbenennen: Monatsnummer → Name
    heatmap.index = [month_names.get(m, str(m)) for m in heatmap.index]

    # Runden
    heatmap = heatmap.round(2)

    return heatmap


# ── Beste Sektoren pro Monat ─────────────────────────────────

def get_best_sectors_by_month(
    monthly_returns: pd.DataFrame,
    top_n: int = 3,
    sector_names: dict[str, str] | None = None,
) -> dict[int, list[dict]]:
    """
    Gibt die Top-N Sektoren pro Monat zurück.

    Returns:
        Dict {Monat: [{"ticker": "XLK", "name": "Technology", "avg_return": 2.3}, ...]}
    """
    if sector_names is None:
        sector_names = {**SECTOR_ETFS, **EU_SECTOR_ETFS}

    result = {}
    for month in range(1, 13):
        if month not in monthly_returns.index:
            continue
        row = monthly_returns.loc[month].sort_values(ascending=False)
        top = []
        for ticker, ret in row.head(top_n).items():
            top.append({
                "ticker": ticker,
                "name": sector_names.get(ticker, ticker),
                "avg_return": round(ret, 2),
            })
        result[month] = top

    return result


# ── Erweiterte Saisonalität pro Sektor ───────────────────────

def calc_sector_seasonality(
    sector_data: dict[str, pd.DataFrame],
    date_col: str = "Date",
    close_col: str = "Close",
    min_years: int = 5,
) -> dict[str, pd.DataFrame]:
    """
    Berechnet detaillierte Saisonalitäts-Statistiken pro Sektor.

    Returns:
        Dict {Ticker: DataFrame mit Monats-Statistiken}
        Jeder DataFrame hat Spalten:
          month, avg_return, median_return, std_dev, win_rate, n_years,
          best_year, best_return, worst_year, worst_return
    """
    results = {}

    for ticker, df in sector_data.items():
        try:
            work = df.copy()
            if date_col in work.columns:
                work[date_col] = pd.to_datetime(work[date_col])
                work = work.set_index(date_col)
            work = work.sort_index()

            # Monatliche Renditen
            monthly = work[close_col].resample("ME").last().pct_change() * 100
            monthly = monthly.dropna()

            if len(monthly) < min_years * 12:
                continue

            # Statistiken pro Monat
            stats_rows = []
            for month in range(1, 13):
                month_data = monthly[monthly.index.month == month]
                if len(month_data) < min_years:
                    continue

                best_idx = month_data.idxmax()
                worst_idx = month_data.idxmin()

                stats_rows.append({
                    "month": month,
                    "avg_return": round(month_data.mean(), 2),
                    "median_return": round(month_data.median(), 2),
                    "std_dev": round(month_data.std(), 2),
                    "win_rate": round(
                        (month_data > 0).sum() / len(month_data) * 100, 1
                    ),
                    "n_years": len(month_data),
                    "best_year": best_idx.year if pd.notna(best_idx) else None,
                    "best_return": round(month_data.max(), 2),
                    "worst_year": worst_idx.year if pd.notna(worst_idx) else None,
                    "worst_return": round(month_data.min(), 2),
                })

            if stats_rows:
                results[ticker] = pd.DataFrame(stats_rows)
                app_logger.info(f"Sektor-Saisonalität berechnet: {ticker}")

        except Exception as e:
            error_logger.error(
                f"Sektor-Saisonalität fehlgeschlagen: {ticker} — {e}",
                exc_info=True,
            )

    return results


# ── Relative Stärke: Sektor vs. Benchmark ────────────────────

def calc_relative_strength(
    df_sector: pd.DataFrame,
    df_benchmark: pd.DataFrame,
    date_col: str = "Date",
    close_col: str = "Close",
) -> pd.DataFrame:
    """
    Berechnet die relative Stärke eines Sektors vs. Benchmark (z.B. SPY).

    Returns:
        DataFrame mit: Date, sector_return, benchmark_return,
                       relative_strength (Sektor - Benchmark)
    """
    sector = df_sector.copy()
    bench = df_benchmark.copy()

    for df in [sector, bench]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)

    # Monatliche Renditen
    s_monthly = sector[close_col].resample("ME").last().pct_change() * 100
    b_monthly = bench[close_col].resample("ME").last().pct_change() * 100

    # Zusammenführen
    combined = pd.DataFrame({
        "sector_return": s_monthly,
        "benchmark_return": b_monthly,
    }).dropna()

    combined["relative_strength"] = (
        combined["sector_return"] - combined["benchmark_return"]
    )

    return combined.reset_index()
