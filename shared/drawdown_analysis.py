"""
shared/drawdown_analysis.py — Saisonale Drawdown- & Volatilitäts-Analyse
==========================================================================
Berechnet Drawdown-Serien, Ø-Drawdown-Kurven, monatliche Max-Drawdowns
und Rolling-Volatilität. Wiederverwendbar für alle Pages.

Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional


# ── Farb-Konstanten ────────────────────────────────

SE_DRAWDOWN_COLORSCALE = [
    [0.0, "#0f1923"],
    [0.15, "#2a1215"],
    [0.35, "#5c1a1a"],
    [0.55, "#8b2020"],
    [0.75, "#cc0000"],
    [1.0, "#ff2222"],
]

# ── Monatsgrenzen für 252-Punkt-Kurven (Trading Days) ──

MONTH_BOUNDS_252 = [
    (0, 21), (21, 40), (40, 62), (62, 83), (83, 104), (104, 125),
    (125, 147), (147, 168), (168, 189), (189, 210), (210, 231), (231, 252),
]

MONTH_STARTS_252 = [b[0] for b in MONTH_BOUNDS_252]

# Monatsgrenzen für 365-Punkt-Kurven (Kalendertage)
MONTH_BOUNDS_365 = [
    (0, 31), (31, 59), (59, 90), (90, 120), (120, 151), (151, 181),
    (181, 212), (212, 243), (243, 273), (273, 304), (304, 334), (334, 365),
]

MONTH_LABELS_SHORT = [
    "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez",
]


# ══════════════════════════════════════════════════════════════
# DRAWDOWN BERECHNUNGEN
# ══════════════════════════════════════════════════════════════

def compute_drawdown_series(curve: np.ndarray, base: float = 100.0) -> np.ndarray:
    """
    Einzelne Kurve → Drawdown-Serie (alle Werte ≤ 0).

    Args:
        curve: Normierte Kurve (z.B. full_365 mit base=100, oder Log-Return mit base=0)
        base: Offset zum Verschieben in positive Werte (100 für Jahreszyklus, 0 für Dekaden)

    Returns:
        np.ndarray mit Drawdown-Werten in % (alle ≤ 0)
    """
    cum = np.asarray(curve, dtype=float) + base
    cum = np.maximum(cum, 1e-10)  # Division-by-Zero vermeiden
    peak = np.maximum.accumulate(cum)
    dd = (cum - peak) / peak * 100
    return dd


def compute_avg_drawdown_curve(
    curves: list[np.ndarray],
    base: float = 100.0,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Liste von Kurven → (Ø Drawdown, Std) pro Punkt.

    Returns:
        (avg_dd, std_dd) — beide Arrays mit gleicher Länge wie Input-Kurven
    """
    if not curves:
        return np.array([]), np.array([])

    dd_series = [compute_drawdown_series(c, base) for c in curves]
    dd_matrix = np.array(dd_series)  # shape (n_curves, n_points)

    avg_dd = np.mean(dd_matrix, axis=0)
    std_dd = np.std(dd_matrix, axis=0)

    return avg_dd, std_dd


def compute_drawdown_stats(curve: np.ndarray, base: float = 100.0) -> dict:
    """
    Einzelne Kurve → Drawdown-Statistiken (Intra-Year, ohne Recovery).

    Returns:
        dict mit: max_drawdown, avg_drawdown, max_dd_day
    """
    dd = compute_drawdown_series(curve, base)

    return {
        "max_drawdown": round(float(np.min(dd)), 2),
        "avg_drawdown": round(float(np.mean(dd)), 2),
        "max_dd_day": int(np.argmin(dd)),
    }


def compute_real_recovery(
    df: pd.DataFrame,
    year: int,
) -> Optional[dict]:
    """
    Berechnet den echten Recovery-Zeitraum aus den Preisdaten.
    Schaut über das Jahresende hinaus, bis der Peak-Preis wieder erreicht wird.

    Args:
        df: Vollständiger preprocessed DataFrame (alle Jahre)
        year: Jahr für das der Max-DD berechnet wird

    Returns:
        dict mit: max_drawdown, peak_date, trough_date, recovery_date,
                  recovery_days, recovery_str, recovered
    """
    year_df = df[df.index.year == year]
    if len(year_df) < 50:
        return None

    closes = year_df["Close"].values.astype(float)
    peaks = np.maximum.accumulate(closes)
    dd = (closes - peaks) / peaks * 100

    max_dd_idx = int(np.argmin(dd))
    max_dd = float(dd[max_dd_idx])
    peak_price = float(peaks[max_dd_idx])

    # Peak-Datum = höchster Kurs VOR dem Trough
    peak_date = year_df.index[int(np.argmax(closes[:max_dd_idx + 1]))]
    trough_date = year_df.index[max_dd_idx]

    # Ab Trough: wann wird peak_price wieder überschritten?
    after_trough = df[df.index >= trough_date]
    recovered_mask = after_trough["Close"] >= peak_price

    if recovered_mask.any():
        recovery_date = after_trough[recovered_mask].index[0]
        recovery_days = len(df[(df.index >= trough_date) & (df.index <= recovery_date)])
        recovered = True
    else:
        recovery_date = None
        recovery_days = len(after_trough)
        recovered = False

    # Formatierung: "X Mon + Y Tage"
    months = recovery_days // 21
    rest_days = recovery_days % 21
    if not recovered:
        recovery_str = f"nicht erholt (>{months} Mon)"
    elif months == 0:
        recovery_str = f"{rest_days} Tage"
    elif rest_days == 0:
        recovery_str = f"{months} Mon"
    else:
        recovery_str = f"{months} Mon + {rest_days}d"

    return {
        "year": year,
        "max_drawdown": round(max_dd, 1),
        "peak_date": peak_date,
        "trough_date": trough_date,
        "recovery_date": recovery_date,
        "recovery_days": recovery_days,
        "recovery_str": recovery_str,
        "recovered": recovered,
    }


def compute_drawdown_kpi(curves: list[np.ndarray], base: float = 100.0) -> dict:
    """
    Zusammenfassung über alle Kurven für KPI-Karten.

    Returns:
        dict: avg_max_dd, worst_max_dd, worst_dd_idx, n
    """
    if not curves:
        return {}

    stats_list = [compute_drawdown_stats(c, base) for c in curves]
    max_dds = [s["max_drawdown"] for s in stats_list]
    worst_idx = int(np.argmin(max_dds))

    return {
        "avg_max_dd": round(float(np.mean(max_dds)), 2),
        "worst_max_dd": round(float(np.min(max_dds)), 2),
        "worst_dd_idx": worst_idx,
        "n": len(curves),
    }


def compute_monthly_max_drawdown(
    curves_dict: dict,
    n_points: int = 365,
    base: float = 100.0,
) -> pd.DataFrame:
    """
    Dict {label: list[curve]} → DataFrame für Heatmap.

    Args:
        curves_dict: z.B. {"2020": [curve1], "2021": [curve2]} oder {"x5": [c1,c2,...]}
        n_points: 365 (Kalendertage) oder 252 (Trading Days)
        base: Offset für Drawdown-Berechnung

    Returns:
        DataFrame: Index=label, Columns=Monat (Jan-Dez), Values=Max Drawdown %
    """
    bounds = MONTH_BOUNDS_365 if n_points >= 365 else MONTH_BOUNDS_252

    rows = []
    for label, curves in curves_dict.items():
        if not curves:
            continue

        monthly_dds = []
        for m_idx, (start, end) in enumerate(bounds):
            # Über alle Kurven in diesem Label den Ø Max-DD pro Monat berechnen
            month_dds = []
            for curve in curves:
                dd = compute_drawdown_series(curve, base)
                end_safe = min(end, len(dd))
                start_safe = min(start, len(dd))
                if start_safe < end_safe:
                    month_dd = float(np.min(dd[start_safe:end_safe]))
                    month_dds.append(month_dd)

            if month_dds:
                monthly_dds.append(round(float(np.mean(month_dds)), 2))
            else:
                monthly_dds.append(0.0)

        rows.append({"label": label, **{MONTH_LABELS_SHORT[i]: monthly_dds[i] for i in range(12)}})

    if not rows:
        return pd.DataFrame()

    result = pd.DataFrame(rows).set_index("label")
    return result


# ══════════════════════════════════════════════════════════════
# ROLLING VOLATILITÄT
# ══════════════════════════════════════════════════════════════

def compute_current_vola_stats(
    df: pd.DataFrame,
    window: int = 20,
    years: Optional[list[int]] = None,
) -> Optional[dict]:
    """
    Berechnet aktuelle Volatilitäts-Kennzahlen im historischen Kontext.
    Wiederverwendbar für alle Pages.

    Args:
        df: Preprocessed DataFrame (mit log_return, year)
        window: Rolling-Fenster in Tagen
        years: Liste der Vergleichsjahre (None = alle verfügbaren)

    Returns:
        dict mit: current_vola, avg_vola, percentile, zscore,
                  current_year, window, hist_volas, is_elevated
    """
    from datetime import datetime
    today = datetime.now()
    cur_year = today.year

    if "year" not in df.columns:
        return None

    # Aktuelle Vola berechnen
    cur_vola_arr = compute_rolling_volatility(df, cur_year, window)
    if cur_vola_arr is None:
        return None

    # Letzter gültiger Wert (NaN am Anfang möglich)
    valid = cur_vola_arr[~np.isnan(cur_vola_arr)]
    if len(valid) == 0:
        return None
    current_vola = float(valid[-1])

    # Historische Vergleichswerte: Vola am gleichen TDOY für jedes Jahr
    if years is None:
        years = sorted(df["year"].unique())
    years = [y for y in years if y != cur_year]

    # Aktueller TDOY-Index (Position im Jahr)
    cur_year_df = df[df["year"] == cur_year]
    cur_tdoy_idx = len(cur_year_df) - 1  # 0-basiert

    hist_volas_at_tdoy = []
    for y in years:
        v = compute_rolling_volatility(df, y, window)
        if v is None:
            continue
        # Gleiche relative Position im Jahr
        idx = min(cur_tdoy_idx, len(v) - 1)
        val = v[idx]
        if not np.isnan(val):
            hist_volas_at_tdoy.append(float(val))

    if len(hist_volas_at_tdoy) < 3:
        return None

    hist_arr = np.array(hist_volas_at_tdoy)
    avg_vola = float(np.mean(hist_arr))
    std_vola = float(np.std(hist_arr))

    # Perzentil: Wie viel % der historischen Werte sind kleiner als aktuell?
    percentile = float(np.sum(hist_arr <= current_vola) / len(hist_arr) * 100)

    # Z-Score
    zscore = float((current_vola - avg_vola) / std_vola) if std_vola > 0 else 0.0

    return {
        "current_vola": round(current_vola, 1),
        "avg_vola": round(avg_vola, 1),
        "median_vola": round(float(np.median(hist_arr)), 1),
        "min_vola": round(float(np.min(hist_arr)), 1),
        "max_vola": round(float(np.max(hist_arr)), 1),
        "percentile": round(percentile, 0),
        "zscore": round(zscore, 2),
        "delta": round(current_vola - avg_vola, 1),
        "current_year": cur_year,
        "window": window,
        "n_years": len(hist_volas_at_tdoy),
        "is_elevated": current_vola > avg_vola + std_vola,
        "is_low": current_vola < avg_vola - std_vola,
    }


def compute_rolling_volatility(
    df: pd.DataFrame,
    year: int,
    window: int = 20,
) -> Optional[np.ndarray]:
    """
    Ein Jahr → annualisierte Rolling-Volatilität.

    Args:
        df: Preprocessed DataFrame mit log_return + year Spalten
        year: Zieljahr
        window: Rolling-Window in Handelstagen

    Returns:
        np.ndarray (Länge = Handelstage des Jahres) oder None
    """
    year_df = df[df["year"] == year] if "year" in df.columns else df[df.index.year == year]

    if len(year_df) < window + 5:
        return None

    log_ret = year_df["log_return"] if "log_return" in year_df.columns else year_df["return"]
    rolling_std = log_ret.rolling(window=window, min_periods=max(window // 2, 5)).std()

    # Annualisieren (√252 für Aktien — dynamisch aus Datenlänge)
    trading_days = len(year_df)
    annualization = np.sqrt(trading_days)

    vola = (rolling_std * annualization * 100).values
    return vola


def compute_avg_rolling_volatility(
    df: pd.DataFrame,
    years: list[int],
    window: int = 20,
    n_points: int = 365,
) -> Optional[tuple[np.ndarray, np.ndarray]]:
    """
    Mehrere Jahre → (Ø Vola, Std), interpoliert auf n_points.

    Returns:
        (avg_vola, std_vola) oder None bei zu wenig Daten
    """
    all_volas = []

    for year in years:
        vola = compute_rolling_volatility(df, year, window)
        if vola is None:
            continue

        # Auf n_points interpolieren
        n_orig = len(vola)
        if n_orig < 10:
            continue

        x_orig = np.linspace(0, n_points - 1, n_orig)
        x_new = np.arange(n_points)
        # NaN am Anfang (Rolling Warmup) durch erste gültige Werte ersetzen
        vola_clean = pd.Series(vola).ffill().bfill().values
        interp = np.interp(x_new, x_orig, vola_clean)
        all_volas.append(interp)

    if len(all_volas) < 2:
        return None

    vola_matrix = np.array(all_volas)
    avg_vola = np.mean(vola_matrix, axis=0)
    std_vola = np.std(vola_matrix, axis=0)

    return avg_vola, std_vola
