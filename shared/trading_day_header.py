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
        f'margin-bottom: 12px;'
        f'padding: 6px 0;'
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
    Rendert den Trading Day Converter als Streamlit-Widget.
    Wird auf der Home-Page eingebunden.
    """
    if df is None or df.empty:
        return

    # ── Section Header ──
    st.markdown(
        f'<div style="text-align:center; margin: 2rem 0 1rem 0;">'
        f'<span style="color:{SE_COLORS["text_secondary"]}; font-size:13px; '
        f'letter-spacing:2px; text-transform:uppercase;">Werkzeug</span>'
        f'<h2 style="color:{SE_COLORS["text_primary"]}; font-size:1.6rem; '
        f'margin:0.3rem 0 0.5rem 0;">Trading Day Converter</h2>'
        f'<p style="color:{SE_COLORS["text_secondary"]}; font-size:0.95rem; '
        f'max-width:600px; margin:0 auto;">Kalendertag, TDOM und TDOY '
        f'umrechnen &mdash; basierend auf echten Handelstagen (S&amp;P 500)</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Input-Bereich ──
    col_type, col_val, col_month, col_btn = st.columns([2, 1.5, 2, 1])

    with col_type:
        input_type = st.selectbox(
            "Eingabe-Typ",
            options=["calendar_day", "tdoy", "tdom"],
            format_func=lambda x: {
                "calendar_day": "Kalendertag (CDOY 1-366)",
                "tdoy": "Handelstag des Jahres (TDOY)",
                "tdom": "Handelstag des Monats (TDOM)",
            }[x],
            key="converter_type",
        )

    with col_val:
        # Sinnvolle Defaults je nach Typ
        today = datetime.now()
        if input_type == "calendar_day":
            default_val = today.timetuple().tm_yday
            max_val = 366
        elif input_type == "tdoy":
            default_val = _get_current_tdoy(df) or 1
            max_val = int(df[df["year"] == today.year]["tdoy"].max()) if "tdoy" in df.columns else 366
        else:
            default_val = _get_current_tdom(df) or 1
            max_val = 23

        value = st.number_input(
            "Wert",
            min_value=1,
            max_value=max_val,
            value=min(default_val, max_val),
            step=1,
            key="converter_value",
        )

    with col_month:
        if input_type == "tdom":
            month = st.selectbox(
                "Monat",
                options=list(range(1, 13)),
                index=today.month - 1,
                format_func=lambda m: MONTH_NAMES_DE[m - 1],
                key="converter_month",
            )
        else:
            st.markdown("<br>", unsafe_allow_html=True)
            month = None

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        convert_clicked = st.button("Umrechnen", key="converter_btn", type="primary")

    # ── Ergebnis ──
    if convert_clicked or st.session_state.get("converter_result"):
        result = convert_trading_days(df, input_type, int(value), month=month)

        if result:
            st.session_state["converter_result"] = result
            _render_converter_result(result)
        else:
            st.warning("Kein Handelstag gefunden. Bitte Eingabe prüfen.")


def _render_converter_result(r: dict):
    """Rendert die 3 Ergebnis-Karten im SE-Design."""
    card_style = (
        "background: linear-gradient(135deg, #0f1923 0%, #131d2a 100%);"
        "border: 1px solid rgba(255,255,255,0.08);"
        "border-radius: 12px;"
        "padding: 16px 20px;"
        "text-align: center;"
    )
    label_style = "color: #8899aa; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px;"
    value_style = "font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; margin: 4px 0;"
    sub_style = "color: #667788; font-size: 12px;"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            f'<div style="{card_style}">'
            f'<div style="{label_style}">Datum</div>'
            f'<div style="{value_style} color: {SE_COLORS["text_primary"]};">{r["date_str"]}</div>'
            f'<div style="{sub_style}">{r["weekday"]} · CDOY {r["cdoy"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f'<div style="{card_style}">'
            f'<div style="{label_style}">TDOM</div>'
            f'<div style="{value_style} color: {SE_COLORS["accent_blue"]};">'
            f'{r["tdom"] if r["tdom"] else "–"}</div>'
            f'<div style="{sub_style}">{r["month_name"]} · von {r["tdom_max"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div style="{card_style}">'
            f'<div style="{label_style}">TDOY</div>'
            f'<div style="{value_style} color: {SE_COLORS["accent_warm"]};">{r["tdoy"]}</div>'
            f'<div style="{sub_style}">von {r["tdoy_max"]} Handelstagen</div>'
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
    """Aktueller TDOY aus den Daten."""
    today = datetime.now()
    if "tdoy" not in df.columns:
        return None
    # Ende des heutigen Tages als Cutoff (damit 07:00 Timestamps eingeschlossen werden)
    cutoff = pd.Timestamp(today.date()) + pd.Timedelta(days=1)
    current = df[(df["year"] == today.year)]
    current = current[current.index < cutoff]
    if len(current) == 0:
        return None
    return int(current["tdoy"].iloc[-1])


def _get_current_tdom(df: pd.DataFrame) -> Optional[int]:
    """Aktueller TDOM aus den Daten. Fallback auf letzten bekannten Tag."""
    today = datetime.now()
    # Ende des heutigen Tages als Cutoff
    cutoff = pd.Timestamp(today.date()) + pd.Timedelta(days=1)
    current = df[(df["year"] == today.year) & (df["month"] == today.month)]
    current = current[current.index < cutoff]
    if len(current) > 0:
        return len(current)
    # Fallback: letzter bekannter Monat (z.B. US-Börse hat noch nicht geöffnet)
    year_df = df[df["year"] == today.year]
    year_df = year_df[year_df.index < cutoff]
    if len(year_df) > 0:
        last_month = int(year_df["month"].iloc[-1])
        if last_month == today.month:
            # Gleicher Monat, aber keine Daten bis heute
            month_df = year_df[year_df["month"] == last_month]
            return len(month_df)
        else:
            # Vormonat — zeige TDOM 1 als Schätzung (neuer Monat hat begonnen)
            return 1
    return None
