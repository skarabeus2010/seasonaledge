"""
shared/outlier_manager.py — Outlier Manager
=============================================
Erkennt und behandelt Ausreisser in saisonalen Analysen.
3 Methoden: IQR, Winsorize (3 Sigma), Isolation Forest (KI).
Kein Streamlit-Import! Reine Berechnung.
"""

import numpy as np
import pandas as pd
from typing import Optional


# ── Methode 1: IQR (Interquartile Range) ───────────

def detect_outliers_iqr(
    values: list[float],
    factor: float = 1.5,
) -> list[bool]:
    """
    Erkennt Ausreisser via IQR-Methode.

    Args:
        values: Liste von Werten (z.B. Jahresrenditen)
        factor: IQR-Multiplikator (1.5 = mild, 3.0 = nur Extreme)

    Returns:
        Liste von Booleans (True = Ausreisser)
    """
    if len(values) < 4:
        return [False] * len(values)

    arr = np.array(values)
    q1 = np.percentile(arr, 25)
    q3 = np.percentile(arr, 75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr

    return [(v < lower or v > upper) for v in values]


# ── Methode 2: Winsorize (Sigma-Clipping) ──────────

def winsorize_values(
    values: list[float],
    sigma: float = 3.0,
) -> list[float]:
    """
    Clippt Werte auf mean +/- sigma * std.
    Entfernt nichts, begrenzt nur Extreme.

    Args:
        values: Liste von Werten
        sigma: Anzahl Standardabweichungen (3.0 = konservativ)

    Returns:
        Liste mit geclippten Werten
    """
    if len(values) < 3:
        return list(values)

    arr = np.array(values, dtype=float)
    mean = np.mean(arr)
    std = np.std(arr)

    if std == 0:
        return list(values)

    lower = mean - sigma * std
    upper = mean + sigma * std

    return [float(np.clip(v, lower, upper)) for v in values]


# ── Methode 3: Isolation Forest (KI) ───────────────

def detect_outliers_isolation_forest(
    year_returns: dict[int, list[float]],
    contamination: float = 0.1,
) -> list[int]:
    """
    Erkennt Ausreisser-Jahre via Isolation Forest.
    Wrapper um ai_models.detect_outlier_years().

    Args:
        year_returns: {year: [daily_returns_365]}
        contamination: Erwarteter Anteil Ausreisser (0.05-0.2)

    Returns:
        Liste der Ausreisser-Jahre
    """
    try:
        from shared.ai_models import detect_outlier_years
        return detect_outlier_years(year_returns, contamination)
    except Exception:
        return []


# ── Zentrale API ────────────────────────────────────

METHODS = {
    "off": "Aus",
    "iqr": "IQR (1.5x)",
    "iqr_strict": "IQR (3x, streng)",
    "winsorize": "Winsorize (3 Sigma)",
    "isolation_forest": "Isolation Forest (KI)",
}


def filter_year_data(
    year_data: dict,
    method: str = "off",
    contamination: float = 0.1,
) -> tuple[dict, list[int]]:
    """
    Filtert year_data nach gewaehlter Methode.

    Args:
        year_data: Output von build_year_data()
        method: "off", "iqr", "iqr_strict", "winsorize", "isolation_forest"
        contamination: Nur fuer Isolation Forest

    Returns:
        (gefiltertes year_data, Liste der entfernten/geclippten Jahre)
    """
    if method == "off" or not year_data or len(year_data) < 4:
        return year_data, []

    years = sorted(year_data.keys())

    # Jahresrenditen berechnen (full_365: Start vs Ende)
    year_returns_pct = {}
    for y, yd in year_data.items():
        curve = yd["full_365"]
        if curve and len(curve) >= 2 and curve[0] != 0:
            year_returns_pct[y] = (curve[-1] / curve[0] - 1) * 100
        else:
            year_returns_pct[y] = 0.0

    returns_list = [year_returns_pct[y] for y in years]

    # ── IQR ──
    if method in ("iqr", "iqr_strict"):
        factor = 1.5 if method == "iqr" else 3.0
        is_outlier = detect_outliers_iqr(returns_list, factor=factor)
        outlier_years = [y for y, out in zip(years, is_outlier) if out]
        filtered = {y: yd for y, yd in year_data.items() if y not in outlier_years}
        return filtered, outlier_years

    # ── Winsorize ──
    if method == "winsorize":
        clipped = winsorize_values(returns_list, sigma=3.0)
        filtered = {}
        adjusted_years = []
        for y, orig, clip in zip(years, returns_list, clipped):
            if abs(orig - clip) > 0.001:
                # Jahreskurve skalieren
                yd = year_data[y]
                scale = clip / orig if orig != 0 else 1.0
                new_curve = [100 + (v - 100) * scale for v in yd["full_365"]]
                filtered[y] = {
                    **yd,
                    "full_365": new_curve,
                }
                adjusted_years.append(y)
            else:
                filtered[y] = year_data[y]
        return filtered, adjusted_years

    # ── Isolation Forest ──
    if method == "isolation_forest":
        year_curves = {y: yd["full_365"] for y, yd in year_data.items()}
        outlier_years = detect_outliers_isolation_forest(
            year_curves, contamination=contamination
        )
        filtered = {y: yd for y, yd in year_data.items() if y not in outlier_years}
        return filtered, outlier_years

    return year_data, []


# ── Sidebar Widget ──────────────────────────────────

def outlier_sidebar():
    """
    Rendert das Outlier-Manager Widget in der Streamlit-Sidebar.
    Gibt die gewaehlte Methode zurueck.

    Returns:
        str — method key ("off", "iqr", "winsorize", "isolation_forest")
    """
    import streamlit as st

    with st.expander("Outlier-Filter", expanded=False):
        method = st.radio(
            "Methode",
            options=list(METHODS.keys()),
            format_func=lambda k: METHODS[k],
            index=0,
            key="outlier_method",
            help=(
                "**IQR:** Entfernt Jahre ausserhalb 1.5x Interquartilsabstand\n\n"
                "**IQR streng:** Nur extreme Ausreisser (3x IQR)\n\n"
                "**Winsorize:** Clippt Extreme auf 3 Sigma (entfernt nichts)\n\n"
                "**Isolation Forest:** KI erkennt atypische Jahresmuster"
            ),
        )

    return method


def outlier_info_box(outlier_years: list[int], method: str):
    """Zeigt Info-Box mit erkannten Ausreissern."""
    import streamlit as st

    if not outlier_years or method == "off":
        return

    label = METHODS.get(method, method)
    verb = "angepasst" if method == "winsorize" else "entfernt"
    years_str = ", ".join(str(y) for y in sorted(outlier_years))
    st.info(
        f"**Outlier-Filter ({label}):** "
        f"{len(outlier_years)} Jahre {verb}: {years_str}",
        icon="🧹",
    )
