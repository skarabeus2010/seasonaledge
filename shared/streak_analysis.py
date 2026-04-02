"""
SeasonAlpha — Streak-Analyse (Wiederverwendbar)
=================================================
Zeigt aktuelle Gewinn-/Verlust-Serien als HTML-Tabelle.

Verwendung:
    from shared.streak_analysis import render_streak_table

    # Variante 1: Fertige Gruppen (z.B. Wochentage, Mondphasen)
    render_streak_table(groups, title="Wochentag")

    # Variante 2: Aus DataFrame berechnen
    groups = compute_streaks_from_df(df, group_col="weekday", label_map=LABELS)
    render_streak_table(groups)

Einsatzgebiete:
    - Wochentage (Mo-Fr / Mo-So)
    - Monatswechsel (Jan→Feb ... Dez→Jan)
    - Mondphasen (Vollmond, Neumond)
    - OPEX (monatliche Verfallstage)
    - Fed-Sitzungen (FOMC Meetings)
    - Feiertags-Effekte
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from typing import Optional


def compute_streaks_from_df(
    df: pd.DataFrame,
    group_col: str,
    return_col: str = "return",
    label_map: Optional[dict] = None,
    sort_groups: bool = True,
) -> list[dict]:
    """
    Berechnet Streak-Daten aus einem DataFrame.

    Args:
        df: DataFrame mit mindestens group_col und return_col
        group_col: Spalte fuer Gruppierung (z.B. "weekday", "month", "phase")
        return_col: Spalte mit Renditen (default: "return")
        label_map: Dict {group_value: "Anzeigename"} (optional)
        sort_groups: Gruppen sortieren (default: True)

    Returns:
        Liste von Dicts: [{"label": str, "entries": [{"date": ..., "ret": float}]}]
    """
    if df is None or df.empty or group_col not in df.columns:
        return []

    _df = df.dropna(subset=[return_col]).copy()
    groups = sorted(_df[group_col].unique()) if sort_groups else list(_df[group_col].unique())

    result = []
    for g in groups:
        g_df = _df[_df[group_col] == g].sort_index(ascending=False)
        entries = [
            {"date": idx, "ret": float(row[return_col]) * 100 if abs(row[return_col]) < 1 else float(row[return_col])}
            for idx, row in g_df.iterrows()
            if pd.notna(row[return_col])
        ]
        label = label_map[g] if label_map and g in label_map else str(g)
        result.append({"label": label, "entries": entries})

    return result


def compute_streaks_from_list(
    data: list[dict],
    group_key: str,
    return_key: str,
    year_key: str = "year",
    label_map: Optional[dict] = None,
) -> list[dict]:
    """
    Berechnet Streak-Daten aus einer Liste von Dicts (z.B. TOM-Ergebnisse).

    Args:
        data: Liste von Dicts mit group_key, return_key, year_key
        group_key: Key fuer Gruppierung (z.B. "month")
        return_key: Key fuer Rendite (z.B. "total_return")
        year_key: Key fuer Sortierung (z.B. "year")
        label_map: Dict {group_value: "Anzeigename"} (optional)

    Returns:
        Liste von Dicts: [{"label": str, "entries": [{"date": year, "ret": float}]}]
    """
    grouped = {}
    for entry in data:
        g = entry[group_key]
        if g not in grouped:
            grouped[g] = []
        grouped[g].append({"date": entry.get(year_key, ""), "ret": entry[return_key]})

    result = []
    for g in sorted(grouped.keys()):
        entries = sorted(grouped[g], key=lambda x: x["date"], reverse=True)
        label = label_map[g] if label_map and g in label_map else str(g)
        result.append({"label": label, "entries": entries})

    return result


def render_streak_table(
    groups: list[dict],
    col_header: str = "Gruppe",
    n_blocks: int = 10,
    interpretation: str = "",
):
    """
    Rendert eine Streak-Tabelle als HTML in Streamlit.

    Args:
        groups: Liste von {"label": str, "entries": [{"date": ..., "ret": float}]}
        col_header: Header fuer die erste Spalte (z.B. "Wochentag", "Monatswechsel")
        n_blocks: Anzahl der W/L-Bloecke (default: 10)
        interpretation: Optionaler Interpretationstext unter der Tabelle
    """
    if not groups:
        st.info("Keine Daten fuer Streak-Analyse verfuegbar.")
        return

    streak_rows = []
    for group in groups:
        entries = group["entries"]
        if not entries:
            continue

        # Aktuelle Streak zaehlen
        streak_type = "win" if entries[0]["ret"] > 0 else "loss"
        streak_count = 0
        for e in entries:
            if (streak_type == "win" and e["ret"] > 0) or (streak_type == "loss" and e["ret"] <= 0):
                streak_count += 1
            else:
                break

        # W/L Bloecke
        blocks = ""
        for e in entries[:n_blocks]:
            color = "#00d4aa" if e["ret"] > 0 else "#ff4757"
            wl = "W" if e["ret"] > 0 else "L"
            # Tooltip: Datum + Rendite
            if hasattr(e["date"], "strftime"):
                d_str = e["date"].strftime("%d.%m.%y")
            else:
                d_str = str(e["date"])
            ret_fmt = "{:+.2f}%".format(e["ret"])
            blocks += ("<span style='display:inline-block; width:36px; height:28px; "
                       "background:{}; border-radius:5px; margin:2px; "
                       "text-align:center; font-size:11px; line-height:28px; "
                       "font-weight:700; color:#FFFFFF;' "
                       "title='{}: {}'>{}</span>".format(color, d_str, ret_fmt, wl))

        streak_color = "#00d4aa" if streak_type == "win" else "#ff4757"
        streak_text = "{}x {}".format(streak_count, "Gewinn" if streak_type == "win" else "Verlust")

        streak_rows.append(
            "<tr>"
            "<td style='color:#FFFFFF; font-size:13px; padding:6px 12px;'>{}</td>"
            "<td style='color:{}; font-weight:700; font-size:13px; "
            "padding:6px 12px; text-align:center;'>{}</td>"
            "<td style='padding:6px 8px;'>{}</td>"
            "</tr>".format(group["label"], streak_color, streak_text, blocks)
        )

    table_html = (
        "<table style='width:100%; border-collapse:collapse;'>"
        "<tr style='border-bottom:1px solid rgba(255,255,255,0.1);'>"
        "<th style='color:#8899aa; font-size:11px; text-align:left; padding:4px 12px;'>{}</th>"
        "<th style='color:#8899aa; font-size:11px; text-align:center; padding:4px 12px;'>Aktuelle Serie</th>"
        "<th style='color:#8899aa; font-size:11px; text-align:left; padding:4px 8px;'>Letzte {} (neueste links)</th>"
        "</tr>"
        "{}"
        "</table>".format(col_header, n_blocks, "".join(streak_rows))
    )
    st.markdown(table_html, unsafe_allow_html=True)

    if interpretation:
        st.markdown(
            "<p style='color:#FFFFFF; font-size:12px; margin-top:12px; line-height:1.6;'>"
            "<b>Interpretation:</b> {}</p>".format(interpretation),
            unsafe_allow_html=True)
