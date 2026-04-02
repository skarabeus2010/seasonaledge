"""
shared/trading_day_header.py — Trading Day Context Header + Converter
======================================================================
Feature 1: Globaler Header "Heute: DD.MM.YYYY · TDOM X · TDOY Y"
Feature 2: Converter Calendar Day ↔ TDOM ↔ TDOY

Kein yfinance-Import! Nutzt vorhandene TDOM/TDOY-Module.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from typing import Optional

from shared.constants import SE_COLORS, MONTH_NAMES_DE


# ══════════════════════════════════════════════════════════════
# FEATURE 1: GLOBALER HEADER
# ══════════════════════════════════════════════════════════════

def render_trading_day_header(df: pd.DataFrame):
    """
    Rendert gelben Header: "Heute: 01.04.2026 · TDOM 1 · TDOY 61"

    Args:
        df: Preprocessed DataFrame (mit tdoy, year, month Spalten)
    """
    if df is None or df.empty:
        return

    # ── Sicherstellen: preprocess()-Spalten vorhanden ──
    if "year" not in df.columns or "tdoy" not in df.columns:
        df = df.copy()
        if "year" not in df.columns:
            df["year"] = df.index.year
        if "month" not in df.columns:
            df["month"] = df.index.month
        if "day_of_year" not in df.columns:
            df["day_of_year"] = df.index.dayofyear
        if "tdoy" not in df.columns:
            df["tdoy"] = df.groupby("year").cumcount() + 1

    today = datetime.now()
    date_str = today.strftime("%d.%m.%Y")

    # ── TDOY aus preprocess()-Spalte ──
    tdoy_val = _get_current_tdoy(df)

    # ── TDOM berechnen ──
    tdom_val = _get_current_tdom(df)

    # ── Wochentag ──
    weekday_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    weekday = weekday_names[today.weekday()]

    # ── Formatierung ──
    tdoy_str = str(tdoy_val) if tdoy_val else "–"
    tdom_str = str(tdom_val) if tdom_val else "–"

    st.markdown(
        f'<div style="'
        f'color: {SE_COLORS["accent_warm"]};'
        f'font-size: 15px;'
        f'font-weight: 600;'
        f'font-variant-numeric: tabular-nums;'
        f'letter-spacing: 0.3px;'
        f'margin: 8px 0 12px 0;'
        f'padding: 8px 0;'
        f'border-bottom: 1px solid rgba(232,164,37,0.2);'
        f'">'
        f'Heute: {weekday} {date_str}'
        f' &nbsp;·&nbsp; TDOM {tdom_str}'
        f' &nbsp;·&nbsp; TDOY {tdoy_str}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# FEATURE 2: CONVERTER
# ══════════════════════════════════════════════════════════════

def convert_trading_days(
    df: pd.DataFrame,
    input_type: str,
    value: int,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Optional[dict]:
    """
    Konvertiert zwischen Calendar Day, TDOM und TDOY.

    Args:
        df: Preprocessed DataFrame (mit tdoy, year, month, day_of_year)
        input_type: "calendar_day" | "tdom" | "tdoy"
        value: int (Tag-Nummer)
        year: int (default: aktuelles Jahr)
        month: int (nur für TDOM → andere nötig)

    Returns:
        dict mit: date, date_str, cdoy, tdom, tdoy, weekday, month_name
        oder None bei Fehler
    """
    if df is None or df.empty:
        return None

    if year is None:
        year = datetime.now().year

    # ── Sicherstellen: TDOM-Spalte vorhanden ──
    if "tdom" not in df.columns:
        df = df.copy()
        df["tdom"] = df.groupby(["year", "month"]).cumcount() + 1

    # ── Sicherstellen: TDOY-Spalte vorhanden ──
    if "tdoy" not in df.columns:
        df = df.copy()
        df["tdoy"] = df.groupby("year").cumcount() + 1

    year_df = df[df["year"] == year].copy()
    if year_df.empty:
        return None

    year_df = year_df.sort_index()

    # ── Sicherstellen: TDOM über alle Jahre konsistent ──
    if "tdom" not in year_df.columns:
        year_df["tdom"] = year_df.groupby(["year", "month"]).cumcount() + 1

    # ── Zielzeile finden ──
    target_row = None

    if input_type == "calendar_day":
        # CDOY → finde den Handelstag an/nach diesem Kalendertag
        matches = year_df[year_df["day_of_year"] == value]
        if len(matches) > 0:
            target_row = matches.iloc[0]
        else:
            # Nächster Handelstag nach dem Kalendertag (falls Wochenende)
            after = year_df[year_df["day_of_year"] > value]
            if len(after) > 0:
                target_row = after.iloc[0]
            else:
                # Kalendertag liegt in der Zukunft → Schätzung aus Vorjahren
                target_row = _estimate_from_previous_years(df, input_type, value, year, month)

    elif input_type == "tdoy":
        matches = year_df[year_df["tdoy"] == value]
        if len(matches) > 0:
            target_row = matches.iloc[0]
        else:
            # TDOY liegt in der Zukunft → Schätzung aus Vorjahren
            target_row = _estimate_from_previous_years(df, input_type, value, year, month)

    elif input_type == "tdom":
        if month is None:
            month = datetime.now().month
        month_df = year_df[year_df["month"] == month]
        if len(month_df) == 0:
            # Monat noch nicht in den Daten → Vorjahre nutzen
            target_row = _estimate_from_previous_years(df, input_type, value, year, month)
        else:
            month_df = month_df.copy()
            month_df["tdom"] = range(1, len(month_df) + 1)
            matches = month_df[month_df["tdom"] == value]
            if len(matches) > 0:
                target_row = matches.iloc[0]

    if target_row is None:
        return None

    # ── Ergebnis zusammenbauen ──
    idx_date = target_row.name  # DatetimeIndex
    if isinstance(idx_date, pd.Timestamp):
        dt = idx_date.to_pydatetime()
    else:
        dt = datetime.now()

    weekday_names_de = [
        "Montag", "Dienstag", "Mittwoch", "Donnerstag",
        "Freitag", "Samstag", "Sonntag",
    ]

    target_month = int(target_row["month"]) if "month" in target_row.index else dt.month

    # Max TDOM für diesen Monat (Median über alle Jahre)
    month_counts = df[df["month"] == target_month].groupby(["year", "month"]).size()
    tdom_max = int(month_counts.median()) if len(month_counts) > 0 else 22

    # Max TDOY (Median über alle Jahre)
    year_counts = df.groupby("year")["tdoy"].max()
    tdoy_max = int(year_counts.median()) if len(year_counts) > 0 else 252

    return {
        "date": dt,
        "date_str": dt.strftime("%d.%m.%Y"),
        "cdoy": int(target_row["day_of_year"]) if "day_of_year" in target_row.index else dt.timetuple().tm_yday,
        "tdom": int(target_row["tdom"]) if "tdom" in target_row.index else None,
        "tdoy": int(target_row["tdoy"]) if "tdoy" in target_row.index else None,
        "weekday": weekday_names_de[dt.weekday()],
        "month_name": MONTH_NAMES_DE[target_month - 1],
        "tdom_max": tdom_max,
        "tdoy_max": tdoy_max,
    }


def render_converter_widget(df: pd.DataFrame):
    """
    Kompakter Trading Day Converter: Datepicker + Einzeiler-Ergebnis (gelb).
    """
    if df is None or df.empty:
        return

    # ── Kompaktes Layout: Label + Datepicker + Ergebnis in einer Zeile ──
    col_label, col_cal, col_result = st.columns([1.2, 1.2, 3])

    with col_label:
        st.markdown(
            f'<div style="padding-top:6px;">'
            f'<span style="color:{SE_COLORS["accent_warm"]}; font-size:14px; '
            f'font-weight:600;">📅 Trading Day Converter</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_cal:
        selected_date = st.date_input(
            "Datum",
            value=date.today(),
            min_value=date(2000, 1, 1),
            max_value=date(date.today().year, 12, 31),
            key="converter_date",
            label_visibility="collapsed",
        )

    with col_result:
        if selected_date:
            cdoy = selected_date.timetuple().tm_yday
            result = convert_trading_days(df, "calendar_day", cdoy, year=selected_date.year)

            if result:
                _render_converter_inline(result)
            else:
                st.markdown(
                    f'<div style="color:{SE_COLORS["accent_warm"]}; font-size:14px; '
                    f'padding-top:6px; font-weight:500;">'
                    f'Kein Handelstag (Wochenende/Feiertag)</div>',
                    unsafe_allow_html=True,
                )


def _render_converter_inline(r: dict):
    """Einzeiler-Ergebnis in Gelb mit Trennstrichen."""
    gold = SE_COLORS["accent_warm"]
    muted = SE_COLORS["text_muted"]

    tdom_str = str(r["tdom"]) if r["tdom"] else "–"

    st.markdown(
        f'<div style="'
        f'color:{gold}; font-size:15px; font-weight:600; '
        f'font-variant-numeric:tabular-nums; padding-top:6px; '
        f'white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'
        f'">'
        f'{r["date_str"]} {r["weekday"]}'
        f' <span style="color:{muted};">·</span> '
        f'CDOY {r["cdoy"]}'
        f' <span style="color:{muted};">·</span> '
        f'<span style="color:#4d9fff;">TDOM {tdom_str}</span>'
        f'<span style="color:{muted};font-size:11px;">/{r["tdom_max"]}</span>'
        f' <span style="color:{muted};">·</span> '
        f'TDOY {r["tdoy"]}'
        f'<span style="color:{muted};font-size:11px;">/{r["tdoy_max"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# INTERNE HELPER
# ══════════════════════════════════════════════════════════════

def _estimate_from_previous_years(
    df: pd.DataFrame,
    input_type: str,
    value: int,
    year: int,
    month: Optional[int] = None,
) -> Optional[pd.Series]:
    """
    Wenn der gesuchte Tag im aktuellen Jahr noch nicht existiert,
    nehme den entsprechenden Tag aus dem letzten verfügbaren Vorjahr
    und projiziere das Datum ins aktuelle Jahr.
    """
    # Versuche die letzten 3 Jahre
    for prev_year in range(year - 1, year - 4, -1):
        prev_df = df[df["year"] == prev_year].copy()
        if prev_df.empty:
            continue

        prev_df = prev_df.sort_index()
        if "tdom" not in prev_df.columns:
            prev_df["tdom"] = prev_df.groupby(["year", "month"]).cumcount() + 1
        if "tdoy" not in prev_df.columns:
            prev_df["tdoy"] = prev_df.groupby("year").cumcount() + 1

        match = None
        if input_type == "calendar_day":
            candidates = prev_df[prev_df["day_of_year"] == value]
            if len(candidates) > 0:
                match = candidates.iloc[0]
        elif input_type == "tdoy":
            candidates = prev_df[prev_df["tdoy"] == value]
            if len(candidates) > 0:
                match = candidates.iloc[0]
        elif input_type == "tdom" and month is not None:
            m_df = prev_df[prev_df["month"] == month].copy()
            m_df["tdom"] = range(1, len(m_df) + 1)
            candidates = m_df[m_df["tdom"] == value]
            if len(candidates) > 0:
                match = candidates.iloc[0]

        if match is not None:
            # Projiziere ins Zieljahr: gleicher Monat/Tag
            prev_date = match.name
            if isinstance(prev_date, pd.Timestamp):
                try:
                    projected = prev_date.replace(year=year)
                    match_copy = match.copy()
                    match_copy.name = projected
                    return match_copy
                except ValueError:
                    # z.B. 29. Feb in Nicht-Schaltjahr
                    continue
    return None


def _get_current_tdoy(df: pd.DataFrame) -> Optional[int]:
    """Aktueller TDOY — berechnet aus pd.bdate_range, nicht aus DB-Daten."""
    today = date.today()
    bdays = pd.bdate_range(date(today.year, 1, 1), today)
    if len(bdays) == 0:
        return None
    return len(bdays)


def _get_current_tdom(df: pd.DataFrame) -> Optional[int]:
    """Aktueller TDOM — berechnet aus pd.bdate_range, nicht aus DB-Daten."""
    today = date.today()
    bdays = pd.bdate_range(date(today.year, today.month, 1), today)
    if len(bdays) == 0:
        return None
    return len(bdays)
