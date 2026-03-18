"""
SeasonalEdge - Erweiterte Analyse
==================================
Präsidentenzyklus, Dekadenzyklus, Pressure, Krieg/Frieden, Indikatoren.
"""

import streamlit as st
import pandas as pd
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
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE,
    COLOR_SEASONAL_AVG, COLOR_PRESSURE, COLOR_WAR,
    CYCLE_COLORS, DECADE_COLORS
)
from shared.data import download_data, preprocess
from shared.calculations import (
    build_year_data, calculate_seasonal_average,
    get_presidential_cycle_year, get_decade_digit,
    calculate_pressure_curve, classify_december_low,
    classify_january_first5, get_war_years, get_peace_years
)
from shared.charts import build_seasonal_chart

st.set_page_config(page_title="SeasonalEdge - Erweitert", page_icon="📊", layout="wide")


def main():
    with st.sidebar:
        st.markdown("## 📊 Erweiterte Analyse")
        st.markdown("---")
        
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="adv_ticker").upper().strip()
        
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider(
            "Analyse-Zeitraum (Jahre)",
            options=period_options, value=DEFAULT_YEARS,
            format_func=lambda x: str(x), key="adv_period"
        )
        years_back_is_max = (years_back_raw == "Max")
        
        smoothing = st.slider("Glättung (Tage)", 1, 21, 5, 2, key="adv_smooth")
        show_individual = st.checkbox("Einzelne Jahre", value=False, key="adv_indiv")
        show_bands = st.checkbox("Konfidenzband (±1σ)", value=True, key="adv_bands")
        show_current = st.checkbox("Aktuelles Jahr", value=True, key="adv_current")
        
        # ── Präsidentenzyklus ──
        st.markdown("---")
        st.markdown("### Präsidentenzyklus")
        selected_cycles = st.multiselect(
            "Zyklen anzeigen",
            options=list(CYCLE_COLORS.keys()),
            default=None,
            help="Leere Auswahl = keine Zykluslinien"
        )
        
        # ── Dekadenzyklus ──
        st.markdown("---")
        st.markdown("### Dekadenzyklus")
        current_digit = get_decade_digit(datetime.now().year)
        selected_decades = st.multiselect(
            "Endziffer anzeigen",
            options=list(range(10)),
            format_func=lambda x: f"X{x}er Jahre" + (" ← aktuell" if x == current_digit else ""),
            default=None,
            help="Durchschnitt aller Jahre mit gleicher Endziffer"
        )
        
        # ── Pressure ──
        st.markdown("---")
        st.markdown("### Pressure Chart")
        show_pressure = st.checkbox("Pressure im Hauptchart", value=False,
                                    help="Addiert die Ø-Tagesrenditen der letzten 10-80 Jahre")
        
        # ── Krieg/Frieden ──
        st.markdown("---")
        st.markdown("### War-Verlauf")
        war_mode = st.selectbox(
            "US-Kriegsjahre",
            ["Aus", "Kriegsjahre (Ø Verlauf)", "Friedensjahre (Ø Verlauf)", "Beide"],
            help="Durchschnittlicher saisonaler Verlauf in Jahren mit/ohne US-Kriegsbeteiligung"
        )
        
        # ── Indikatoren ──
        st.markdown("---")
        st.markdown("### Saisonale Indikatoren")
        
        dec_low_mode = st.selectbox(
            "December Low Indikator",
            ["Aus", "Dez-Tief NICHT unterschritten (bullish)", "Dez-Tief unterschritten (bearish)"],
            help="Filtert Jahre nach Dezember-Tief Verhalten"
        )
        
        jan_indicator_mode = st.selectbox(
            "Januar Indikator (First 5 Days)",
            ["Aus", "Erste 5 Tage POSITIV (bullish)", "Erste 5 Tage NEGATIV (bearish)"],
            help="Filtert Jahre nach ersten 5 Handelstagen im Januar"
        )
        
        # ── Overlay ──
        st.markdown("---")
        st.markdown("### 🔗 Overlay")
        overlay_options = st.multiselect(
            "Vergleichslinien",
            options=["Last Year", "Last 5 Years", "Last 10 Years"],
            default=None, key="adv_overlay"
        )
    
    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)
    
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return
    
    df = preprocess(raw_df)
    all_years = sorted(df["year"].unique())
    
    if years_back_is_max:
        selected_years = all_years
    else:
        years_back = int(years_back_raw)
        cutoff_year = datetime.now().year - years_back
        selected_years = [y for y in all_years if y >= cutoff_year]
    
    current_year = datetime.now().year
    if current_year in all_years and current_year not in selected_years:
        selected_years.append(current_year)
        selected_years.sort()
    
    if len(selected_years) < 2:
        st.warning("Nicht genügend Daten.")
        return
    
    year_data = build_year_data(df, selected_years)
    avg, std = calculate_seasonal_average(year_data)
    
    # ── Indikatoren berechnen ─────────────────────────
    indicator_years = None
    indicator_label = None
    indicator_color = None
    
    if dec_low_mode != "Aus":
        dec_classification = classify_december_low(df)
        if "NICHT" in dec_low_mode:
            indicator_years = [y for y, bullish in dec_classification.items() if bullish and y in year_data]
            indicator_label = "Dez-Low gehalten"
            indicator_color = "#4CAF50"
        else:
            indicator_years = [y for y, bullish in dec_classification.items() if not bullish and y in year_data]
            indicator_label = "Dez-Low gebrochen"
            indicator_color = "#F44336"
    
    if jan_indicator_mode != "Aus":
        jan_classification = classify_january_first5(df)
        if "POSITIV" in jan_indicator_mode:
            indicator_years = [y for y, positive in jan_classification.items() if positive and y in year_data]
            indicator_label = "Jan First 5 ↑"
            indicator_color = "#4CAF50"
        else:
            indicator_years = [y for y, positive in jan_classification.items() if not positive and y in year_data]
            indicator_label = "Jan First 5 ↓"
            indicator_color = "#F44336"
    
    # ── Pressure berechnen ────────────────────────────
    pressure_curve_data = None
    pressure_info = None
    if show_pressure:
        pressure_curve_data, max_years, avail_periods = calculate_pressure_curve(df, smoothing_window=smoothing)
        from shared.constants import PRESSURE_PERIODS
        unavailable = [p for p in PRESSURE_PERIODS if p > max_years]
        if unavailable and avail_periods:
            pressure_info = (
                f"⚠️ Pressure Chart nur über die letzten **{max(avail_periods)} Jahre** verfügbar "
                f"(Datenreihe: {max_years} Jahre)."
            )
    
    # ── War-Verlauf berechnen ─────────────────────────
    war_years_data = None
    war_label = None
    peace_years_data = None
    peace_label = None
    
    if war_mode != "Aus":
        all_war_years = get_war_years()
        all_peace_years = set(get_peace_years(list(year_data.keys())))
        
        if war_mode in ["Kriegsjahre (Ø Verlauf)", "Beide"]:
            war_years_data = [y for y in year_data.keys() if y in all_war_years]
            war_label = "Kriegsjahre"
        
        if war_mode in ["Friedensjahre (Ø Verlauf)", "Beide"]:
            peace_years_data = [y for y in year_data.keys() if y in all_peace_years]
            peace_label = "Friedensjahre"
    
    # ── Chart ─────────────────────────────────────────
    fig = build_seasonal_chart(
        year_data=year_data, avg=avg, std=std,
        ticker=ticker, smoothing_window=smoothing,
        show_individual=show_individual,
        show_bands=show_bands,
        show_current_year=show_current,
        selected_range=None,
        selected_cycles=selected_cycles if selected_cycles else None,
        selected_decades=selected_decades if selected_decades else None,
        indicator_years=indicator_years,
        indicator_label=indicator_label,
        indicator_color=indicator_color,
        pressure_curve=None,  # Pressure wird separat als y2 hinzugefügt
        war_years_data=war_years_data,
        war_label=war_label,
        df=df,
        overlay_options=overlay_options if overlay_options else None
    )
    
    # Friedensjahre als extra Linie
    if peace_years_data and peace_label:
        peace_matching = [y for y in year_data.keys() if y in peace_years_data]
        if len(peace_matching) >= 2:
            x_days = list(range(1, 366))
            peace_curves = [year_data[y]["full_365"] for y in peace_matching]
            peace_avg = [np.mean([c[d] for c in peace_curves]) for d in range(365)]
            if smoothing > 1:
                peace_avg = pd.Series(peace_avg).rolling(smoothing, center=True, min_periods=1).mean().tolist()
            fig.add_trace(go.Scatter(
                x=x_days, y=peace_avg,
                mode="lines",
                line=dict(color="#4CAF50", width=2.5, dash="dash"),
                name=f"{peace_label} ({len(peace_matching)}y)",
                hovertemplate=f"{peace_label}<br>Tag %{{x}}<br>Wert: %{{y:.2f}}<extra></extra>"
            ))
    
    # Pressure als sekundäre Y-Achse
    if pressure_curve_data:
        x_days = list(range(1, 366))
        fig.add_trace(go.Scatter(
            x=x_days, y=pressure_curve_data,
            mode="lines", line=dict(color=COLOR_PRESSURE, width=2),
            name="Pressure", yaxis="y2",
            hovertemplate="Pressure: %{y:+.2f}<extra></extra>"
        ))
        fig.update_layout(
            yaxis2=dict(
                title=dict(text="Pressure", font=dict(color=COLOR_PRESSURE, size=11)),
                tickfont=dict(color=COLOR_PRESSURE, size=10),
                overlaying="y", side="right", showgrid=False,
                tickformat="+.1f", zeroline=True,
                zerolinecolor="rgba(255,105,180,0.2)"
            )
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    if pressure_info:
        st.info(pressure_info)
    
    # ── Dateninfo ─────────────────────────────────────
    with st.expander("ℹ️ Dateninfo"):
        st.markdown(f"""
        **Ticker:** {ticker}  
        **Analyse-Jahre:** {min(selected_years)} – {max(selected_years)} ({len(year_data)} Jahre)  
        **Methode:** Kumulative Log-Returns (Start = 100)  
        **Glättung:** {smoothing}-Tage zentrierter MA  
        **Präsidentenzyklus:** {current_year} = {get_presidential_cycle_year(current_year)}  
        """)
        if indicator_years and indicator_label:
            st.markdown(f"**Aktiver Indikator:** {indicator_label} — {len(indicator_years)} Jahre")


if __name__ == "__main__":
    main()
