"""
SeasonAlpha — Saisonal-Events Kalender
==========================================
Alle marktrelevanten Events der naechsten 12 Monate:
Notenbanken, OPEX, Feiertage, Mondphasen, Crypto-Events.
"""

import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta

from shared.constants import SE_COLORS

st.set_page_config(
    page_title="Saisonal-Events Kalender — SeasonAlpha",
    page_icon="📅",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()


# ══════════════════════════════════════════════════════
# DATEN SAMMELN
# ══════════════════════════════════════════════════════

today = date.today()
end_date = today + timedelta(days=365)
current_year = today.year
next_year = current_year + 1


def _collect_events() -> list[dict]:
    """Sammelt alle Events fuer die naechsten 12 Monate."""
    events = []

    # ── Notenbanken ──────────────────────────────────
    try:
        from shared.fed_dates import FOMC_MEETING_DATES
        for y, m, d in FOMC_MEETING_DATES:
            dt = date(y, m, d)
            if today <= dt <= end_date:
                events.append({
                    "datum": dt,
                    "event": "FOMC Zinsentscheid",
                    "kategorie": "Notenbank",
                    "land": "US",
                    "icon": "🇺🇸",
                    "relevanz": "Hoch",
                    "btc": True,
                })
    except Exception:
        pass

    try:
        from shared.central_banks import (
            FED_MINUTES_DATES, ECB_MEETING_DATES,
            BOE_MEETING_DATES, BOJ_MEETING_DATES,
        )

        for y, m, d in FED_MINUTES_DATES:
            dt = date(y, m, d)
            if today <= dt <= end_date:
                events.append({
                    "datum": dt, "event": "Fed Minutes",
                    "kategorie": "Notenbank", "land": "US",
                    "icon": "🇺🇸", "relevanz": "Mittel", "btc": True,
                })

        for y, m, d in ECB_MEETING_DATES:
            dt = date(y, m, d)
            if today <= dt <= end_date:
                events.append({
                    "datum": dt, "event": "EZB Zinsentscheid",
                    "kategorie": "Notenbank", "land": "EU",
                    "icon": "🇪🇺", "relevanz": "Hoch", "btc": False,
                })

        for y, m, d in BOE_MEETING_DATES:
            dt = date(y, m, d)
            if today <= dt <= end_date:
                events.append({
                    "datum": dt, "event": "BoE Zinsentscheid",
                    "kategorie": "Notenbank", "land": "UK",
                    "icon": "🇬🇧", "relevanz": "Mittel", "btc": False,
                })

        for y, m, d in BOJ_MEETING_DATES:
            dt = date(y, m, d)
            if today <= dt <= end_date:
                events.append({
                    "datum": dt, "event": "BoJ Zinsentscheid",
                    "kategorie": "Notenbank", "land": "JP",
                    "icon": "🇯🇵", "relevanz": "Mittel", "btc": False,
                })
    except Exception:
        pass

    # ── OPEX ─────────────────────────────────────────
    try:
        from shared.nyse_holidays import get_all_opex_dates
        for entry in get_all_opex_dates(current_year, next_year):
            dt = entry["date"]
            if today <= dt <= end_date:
                label = "Triple Witching (OPEX)" if entry["is_triple"] else "OPEX"
                note = entry["holiday_note"] if entry["adjusted"] else ""
                events.append({
                    "datum": dt,
                    "event": label + (" " + note if note else ""),
                    "kategorie": "OPEX",
                    "land": "US",
                    "icon": "⚡" if entry["is_triple"] else "📊",
                    "relevanz": "Hoch" if entry["is_triple"] else "Mittel",
                    "btc": True,
                })
    except Exception:
        pass

    # ── US-Feiertage ─────────────────────────────────
    try:
        from shared.nyse_holidays import _compute_nyse_holidays
        for yr in [current_year, next_year]:
            for dt in _compute_nyse_holidays(yr):
                if today <= dt <= end_date:
                    events.append({
                        "datum": dt, "event": "NYSE Feiertag (Boerse geschlossen)",
                        "kategorie": "Feiertag", "land": "US",
                        "icon": "🏛️", "relevanz": "Info", "btc": False,
                    })
    except Exception:
        pass

    # ── Mondphasen ───────────────────────────────────
    try:
        from shared.central_banks import get_full_moon_dates, get_new_moon_dates

        for entry in get_full_moon_dates(current_year, next_year):
            dt = entry["date"].date() if hasattr(entry["date"], "date") else entry["date"]
            if today <= dt <= end_date:
                events.append({
                    "datum": dt, "event": "Vollmond",
                    "kategorie": "Mondphase", "land": "Global",
                    "icon": "🌕", "relevanz": "Info", "btc": True,
                })

        for entry in get_new_moon_dates(current_year, next_year):
            dt = entry["date"].date() if hasattr(entry["date"], "date") else entry["date"]
            if today <= dt <= end_date:
                events.append({
                    "datum": dt, "event": "Neumond",
                    "kategorie": "Mondphase", "land": "Global",
                    "icon": "🌑", "relevanz": "Info", "btc": True,
                })
    except Exception:
        pass

    # ── Bitcoin-spezifische Events (hardcoded) ───────
    btc_events = [
        (date(2026, 4, 15), "US Steuerfrist (Crypto Sell Pressure)"),
        (date(2026, 6, 30), "Q2 Ende — Rebalancing Institutionelle"),
        (date(2026, 9, 30), "Q3 Ende — Rebalancing Institutionelle"),
        (date(2026, 12, 31), "Jahresende — Tax-Loss Harvesting Crypto"),
    ]
    for dt, label in btc_events:
        if today <= dt <= end_date:
            events.append({
                "datum": dt, "event": label,
                "kategorie": "Crypto", "land": "Global",
                "icon": "₿", "relevanz": "Mittel", "btc": True,
            })

    # Sortieren nach Datum
    events.sort(key=lambda e: e["datum"])
    return events


# ══════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════

st.markdown("## Saisonal-Events Kalender")
st.caption(f"Alle marktrelevanten Termine der naechsten 12 Monate | Stand: {today.strftime('%d.%m.%Y')}")

# ── Sidebar Filter ───────────────────────────────────
with st.sidebar:
    st.markdown("### Filter")

    kat_filter = st.multiselect(
        "Kategorien",
        options=["Notenbank", "OPEX", "Feiertag", "Mondphase", "Crypto"],
        default=["Notenbank", "OPEX", "Feiertag", "Mondphase", "Crypto"],
        key="cal_kat",
    )

    land_filter = st.multiselect(
        "Laender",
        options=["US", "EU", "UK", "JP", "Global"],
        default=["US", "EU", "UK", "JP", "Global"],
        key="cal_land",
    )

    btc_only = st.checkbox("Nur Bitcoin-relevante Events", value=False, key="cal_btc")

    st.markdown("---")
    st.caption(
        "Datenquellen: Fed, EZB, BoE, BoJ Sitzungskalender, "
        "NYSE Feiertagskalender, OPEX-Berechnung, Meeus-Algorithmus (Mond)"
    )

# ── Events laden + filtern ───────────────────────────
with st.spinner("Lade Events..."):
    all_events = _collect_events()

filtered = [
    e for e in all_events
    if e["kategorie"] in kat_filter
    and e["land"] in land_filter
    and (not btc_only or e["btc"])
]

# ── Metriken ─────────────────────────────────────────
st.markdown("---")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Events gesamt", len(filtered))
m2.metric("Notenbank", sum(1 for e in filtered if e["kategorie"] == "Notenbank"))
m3.metric("OPEX", sum(1 for e in filtered if e["kategorie"] == "OPEX"))
m4.metric("Feiertage", sum(1 for e in filtered if e["kategorie"] == "Feiertag"))
m5.metric("Mondphasen", sum(1 for e in filtered if e["kategorie"] == "Mondphase"))

# ── Naechste 5 Events ───────────────────────────────
st.markdown("---")
st.subheader("Naechste Events")

upcoming = filtered[:5]
for e in upcoming:
    days_until = (e["datum"] - today).days
    days_label = f"in {days_until} Tagen" if days_until > 1 else ("morgen" if days_until == 1 else "heute")

    relevanz_color = {
        "Hoch": SE_COLORS["negative"],
        "Mittel": SE_COLORS["accent_warm"],
        "Info": SE_COLORS["text_muted"],
    }.get(e["relevanz"], SE_COLORS["text_muted"])

    st.markdown(
        f'<div style="background:#0c1420;border:1px solid #1e2d42;border-radius:10px;'
        f'padding:.8rem 1.2rem;margin-bottom:.5rem;display:flex;align-items:center;gap:1rem;">'
        f'<div style="font-size:1.5rem;">{e["icon"]}</div>'
        f'<div style="flex:1;">'
        f'<div style="font-weight:700;color:#e8edf5;font-size:.9rem;">{e["event"]}</div>'
        f'<div style="color:#5a6e85;font-size:.78rem;">{e["datum"].strftime("%A, %d.%m.%Y")} · {e["land"]}</div>'
        f'</div>'
        f'<div style="text-align:right;">'
        f'<div style="color:{relevanz_color};font-weight:700;font-size:.85rem;">{days_label}</div>'
        f'<div style="color:#5a6e85;font-size:.7rem;">{e["relevanz"]}</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Vollstaendige Tabelle ────────────────────────────
st.markdown("---")
st.subheader("Alle Events (12 Monate)")

if filtered:
    WOCHENTAGE = {
        "Monday": "Montag", "Tuesday": "Dienstag", "Wednesday": "Mittwoch",
        "Thursday": "Donnerstag", "Friday": "Freitag", "Saturday": "Samstag", "Sunday": "Sonntag",
    }

    table_rows = []
    for e in filtered:
        days_until = (e["datum"] - today).days
        wochentag = WOCHENTAGE.get(e["datum"].strftime("%A"), e["datum"].strftime("%A"))
        btc_tag = "₿" if e["btc"] else ""

        table_rows.append({
            "Datum": e["datum"].strftime("%d.%m.%Y"),
            "Tag": wochentag,
            "In Tagen": days_until,
            "Event": f'{e["icon"]} {e["event"]}',
            "Kategorie": e["kategorie"],
            "Land": e["land"],
            "Relevanz": e["relevanz"],
            "BTC": btc_tag,
        })

    df_table = pd.DataFrame(table_rows)

    # Farbige Relevanz
    def _color_relevanz(val):
        if val == "Hoch":
            return "color: #ff4757; font-weight: bold;"
        if val == "Mittel":
            return "color: #e8a425; font-weight: bold;"
        return "color: #5a6e85;"

    st.dataframe(
        df_table.style.applymap(_color_relevanz, subset=["Relevanz"]),
        use_container_width=True,
        hide_index=True,
        height=600,
        column_config={
            "Datum": st.column_config.TextColumn("Datum", width="small"),
            "Tag": st.column_config.TextColumn("Tag", width="small"),
            "In Tagen": st.column_config.NumberColumn("In Tagen", width="small"),
            "Event": st.column_config.TextColumn("Event", width="large"),
            "Kategorie": st.column_config.TextColumn("Kat.", width="small"),
            "Land": st.column_config.TextColumn("Land", width="small"),
            "Relevanz": st.column_config.TextColumn("Relevanz", width="small"),
            "BTC": st.column_config.TextColumn("₿", width="small"),
        },
    )

    # CSV Export
    csv = df_table.to_csv(index=False).encode("utf-8")
    st.download_button(
        "CSV Export",
        csv,
        f"seasonal_events_{today.strftime('%Y%m%d')}.csv",
        "text/csv",
    )
else:
    st.info("Keine Events fuer die gewaehlten Filter.")

# ── Disclaimer ──
st.markdown("---")
st.caption(
    "Termine basieren auf offiziellen Kalendern und Berechnungen. "
    "Aenderungen vorbehalten. Keine Anlageberatung."
)
