"""
SeasonAlpha - Erweiterte Analyse
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

from shared.ticker_select import ticker_select
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
from shared.info_badge import render_info_badge

st.set_page_config(page_title="SeasonAlpha - Erweitert", page_icon="📊", layout="wide")

from shared.design import inject_se_css
inject_se_css()


def main():
    with st.sidebar:
        st.markdown("## 📊 Erweiterte Analyse")
        st.markdown("---")
        
        ticker = ticker_select(key="adv_ticker", default=DEFAULT_TICKER)
        
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
        
        # ── Outlier-Filter ──
        st.markdown("---")
        from shared.outlier_manager import outlier_sidebar
        outlier_method = outlier_sidebar()

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

    # ── Outlier-Filter anwenden ─────────────────────
    from shared.outlier_manager import filter_year_data, outlier_info_box
    year_data, outlier_years = filter_year_data(year_data, method=outlier_method)
    outlier_info_box(outlier_years, outlier_method)

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
    
    # ── KI-Zusammenfassung ────────────────────────────
    from shared.calculations import calculate_period_stats
    from shared.constants import MONTH_NAMES_DE

    current_month = datetime.now().month
    month_name = MONTH_NAMES_DE[current_month - 1]
    from shared.constants import SE_COLORS

    # Monats-Stats fuer aktuellen Monat
    month_start_doy = {1:1,2:32,3:60,4:91,5:121,6:152,7:182,8:213,9:244,10:274,11:305,12:335}
    month_end_doy = {1:31,2:59,3:90,4:120,5:151,6:181,7:212,8:243,9:273,10:304,11:334,12:365}
    period_stats = calculate_period_stats(year_data, month_start_doy[current_month], month_end_doy[current_month])

    if period_stats:
        summary_stats = {
            "avg_return": period_stats.get("avg_return", 0),
            "win_rate": f"{period_stats.get('win_rate', 0):.0f}%",
            "period": month_name,
            "n_years": period_stats.get("total_years", 0),
            "std_dev": period_stats.get("std_dev", 0),
        }
        # Aktuelles Jahr Tracking
        current_yd = year_data.get(current_year)
        if current_yd and avg:
            today_doy = min(datetime.now().timetuple().tm_yday, 364)
            curr_val = current_yd["full_365"][today_doy]
            avg_val = avg[today_doy]
            if avg_val != 0:
                diff = curr_val - avg_val
                summary_stats["current_tracking"] = (
                    f"{diff:+.1f}% vs Saisonalmuster"
                )

        with st.expander("KI-Zusammenfassung", expanded=False):
            render_info_badge("ki_zusammenfassung")
            from shared.ai_models import generate_page_summary
            with st.spinner("KI analysiert..."):
                summary = generate_page_summary(
                    ticker=ticker,
                    page_name="Saisonale Analyse (Erweitert)",
                    stats=summary_stats,
                )
            if summary:
                st.markdown(summary)
            else:
                st.caption("KI-Zusammenfassung nicht verfügbar (API-Key nicht gesetzt).")

    # ── Anomalie-Heatmap ──────────────────────────────
    with st.expander("Anomalie-Heatmap (KI)", expanded=False):
        render_info_badge("anomalie_heatmap")
        st.caption(
            "Isolation Forest erkennt Monate/Dekaden mit ungewöhnlichen Rendite-Mustern. "
            "Hohe Werte = mehr Ausreißer-Renditen in dieser Zelle."
        )
        from shared.ai_models import build_anomaly_matrix, build_anomaly_heatmap_figure
        with st.spinner("Anomalie-Erkennung laeuft..."):
            a_matrix, a_months, a_digits = build_anomaly_matrix(df)
        if len(a_months) > 0:
            fig_anomaly = build_anomaly_heatmap_figure(a_matrix, a_months, a_digits, ticker)
            st.plotly_chart(fig_anomaly, use_container_width=True)
            # Top-Anomalien als Text
            flat = []
            for mi, ml in enumerate(a_months):
                for di, dl in enumerate(a_digits):
                    if a_matrix[mi, di] > 40:
                        flat.append((ml, dl, a_matrix[mi, di]))
            flat.sort(key=lambda x: x[2], reverse=True)
            if flat:
                top_str = " | ".join(f"{m}/{d}: {v:.0f}" for m, d, v in flat[:5])
                st.caption(f"Stärkste Anomalien: {top_str}")

            with st.expander("So lesen Sie die Anomalie-Heatmap"):
                st.markdown("""
Die Anomalie-Heatmap zeigt, in welchen **Monat/Dekaden-Kombinationen** historisch die meisten ungewöhnlichen Renditen aufgetreten sind.

- **Zeilen** = Monate (Januar bis Dezember)
- **Spalten** = Dekaden-Endziffer (X0 bis X9, z.B. X6 = 2006, 2016, 2026)
- **Farbskala:** Dunkel = normale, erwartbare Renditen. Hell/Rot = viele Ausreißer, also Monate in denen die Renditen ungewöhnlich stark vom Durchschnitt abwichen.
- **Gelber Rahmen** = "We are here" — der aktuelle Monat und die aktuelle Dekade.

**Interpretation:** Zellen mit hohen Werten (hell/rot) zeigen Zeiträume, in denen die Märkte besonders unberechenbar waren — sowohl nach oben als auch nach unten. Das bedeutet nicht automatisch Verlust, sondern erhöhte Unsicherheit. Dunkle Zellen stehen für Phasen mit stabilen, vorhersagbaren saisonalen Mustern.

**Methode:** Ein Isolation Forest (Machine Learning) wird über alle historischen Monatsrenditen trainiert und bewertet jede Rendite nach ihrer "Normalität". Der Anomalie-Score pro Zelle ist der Durchschnitt dieser Bewertungen.
""")
        else:
            st.caption("sklearn nicht installiert — Anomalie-Erkennung nicht verfügbar.")

    # ── Anomalie-Radar ──────────────────────────────────
    with st.expander("Anomalie-Radar (KI)", expanded=False):
        render_info_badge("anomalie_radar")
        st.caption("Wie stark weicht das aktuelle Kursverhalten vom saisonalen Muster ab?")
        try:
            from shared.anomaly_engine import compute_ticker_anomaly_score
            with st.spinner("Anomalie-Radar berechnet..."):
                radar = compute_ticker_anomaly_score(df, lookback_days=10)
            if "error" not in radar:
                r_score = radar["anomaly_score"]
                r_dir = radar["direction"]
                if r_score >= 70:
                    r_icon, r_label = "🔴", "Stark anomal"
                elif r_score >= 40:
                    r_icon, r_label = "🟡", "Leicht anomal"
                else:
                    r_icon, r_label = "🟢", "Normal"

                rc1, rc2, rc3, rc4 = st.columns(4)
                rc1.metric("Anomalie-Score", f"{r_score:.0f}/100")
                rc2.metric("Status", f"{r_icon} {r_label}")
                rc3.metric("Aktuelle 10d-Rendite", f'{radar["current_return"]:+.2f}%')
                rc4.metric("Historischer Ø", f'{radar["historical_avg"]:+.2f}%')
                st.caption(
                    f'Vergleich: {radar["n_comparisons"]} historische Fenster '
                    f'am gleichen Kalenderzeitpunkt.'
                )
            else:
                st.caption(radar["error"])
        except Exception as _e:
            st.caption(f"Anomalie-Radar nicht verfügbar: {_e}")

    # ── Saisonale Muster-Brueche ─────────────────────
    with st.expander("Saisonale Muster-Brüche (KI)", expanded=False):
        render_info_badge("pattern_breaks")
        st.caption("Jahre in denen das saisonale Muster am stärksten gebrochen wurde.")
        try:
            from shared.anomaly_engine import detect_pattern_breaks
            breaks = detect_pattern_breaks(year_data, avg, top_n=7)
            if breaks:
                for b in breaks:
                    icon = "⚠️" if b["is_outlier"] else "📊"
                    event_str = f' — *{b["event"]}*' if b["event"] else ""
                    st.markdown(
                        f'{icon} **{b["year"]}** | '
                        f'Bruch-Staerke: **{b["break_strength"]:.0f}** | '
                        f'Korrelation: {b["correlation"]:.2f} | '
                        f'Jahresrendite: {b["year_return"]:+.1f}% | '
                        f'Max DD: {b["max_drawdown"]:.1f}%'
                        f'{event_str}'
                    )
            else:
                st.caption("Keine Muster-Brüche erkannt.")
        except Exception as _e:
            st.caption(f"Muster-Bruch-Erkennung nicht verfügbar: {_e}")

    # ── MSTL Saisonalitaets-Zerlegung ─────────────────
    with st.expander("MSTL Saisonalitäts-Zerlegung", expanded=False):
        render_info_badge("mstl_zerlegung")
        st.caption("Zerlegt den Kurs in Trend + Wochensaisonalität + Jahressaisonalität + Residual.")
        try:
            from shared.mstl_decomposition import decompose_mstl, build_decomposition_figure
            with st.spinner("MSTL Zerlegung..."):
                mstl_result = decompose_mstl(df, periods=[5, 252])
            if mstl_result:
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Trend-Anteil", f'{mstl_result.get("strength_trend", 0):.1f}%')
                mc2.metric("Wochen-Saisonalität", f'{mstl_result.get("strength_weekly", 0):.1f}%')
                mc3.metric("Jahres-Saisonalität", f'{mstl_result.get("strength_yearly", 0):.1f}%')
                fig_mstl = build_decomposition_figure(mstl_result, ticker)
                st.plotly_chart(fig_mstl, use_container_width=True)
            else:
                st.caption("MSTL nicht verfügbar (zu wenig Daten oder statsmodels fehlt).")
        except Exception as _e:
            st.caption(f"MSTL nicht verfügbar: {_e}")

    # ── Chronos Forecast ────────────────────────────────
    with st.expander("Chronos Forecast (KI)", expanded=False):
        render_info_badge("chronos_forecast")
        st.caption("Probabilistische 30-Tage Prognose mit Konfidenzintervall (Amazon Chronos-Bolt).")
        try:
            from shared.chronos_forecast import forecast_chronos, build_chronos_chart
            with st.spinner("Chronos Forecast berechnet..."):
                chronos_fc = forecast_chronos(df, periods=30)
            if chronos_fc is not None:
                cc1, cc2, cc3 = st.columns(3)
                cc1.metric("Erwartete Rendite", f'{chronos_fc.attrs.get("expected_return", 0):+.2f}%')
                cc2.metric("P(positiv)", f'{chronos_fc.attrs.get("p_positive", 50):.0f}%')
                cc3.metric("Letzter Close", f'{chronos_fc.attrs.get("last_close", 0):.2f}')
                fig_chronos = build_chronos_chart(df, chronos_fc, ticker)
                st.plotly_chart(fig_chronos, use_container_width=True)
            else:
                st.caption("Chronos nicht verfügbar (pip install chronos-forecasting).")
        except Exception as _e:
            st.caption(f"Chronos nicht verfügbar: {_e}")

    # ── NeuralProphet Komponenten ───────────────────────
    with st.expander("NeuralProphet Saisonalität (KI)", expanded=False):
        st.caption("Explizite Wochen- und Jahressaisonalität via Neural Network.")
        try:
            from shared.neural_prophet_forecast import forecast_neural_prophet, build_neural_prophet_chart
            with st.spinner("NeuralProphet trainiert..."):
                np_result = forecast_neural_prophet(df, periods=30)
            if np_result:
                st.metric("Erwartete Rendite (30d)", f'{np_result["expected_return"]:+.2f}%')
                fig_np = build_neural_prophet_chart(df, np_result, ticker)
                if fig_np.data:
                    st.plotly_chart(fig_np, use_container_width=True)
            else:
                st.caption("NeuralProphet nicht verfügbar (pip install neuralprophet).")
        except Exception as _e:
            st.caption(f"NeuralProphet nicht verfügbar: {_e}")

    # ── Dateninfo ─────────────────────────────────────
    with st.expander("Dateninfo"):
        st.markdown(f"""
        **Ticker:** {ticker}
        **Analyse-Jahre:** {min(selected_years)} – {max(selected_years)} ({len(year_data)} Jahre)
        **Methode:** Kumulative Log-Returns (Start = 100)
        **Glättung:** {smoothing}-Tage zentrierter MA
        **Präsidentenzyklus:** {current_year} = {get_presidential_cycle_year(current_year)}
        """)
        if indicator_years and indicator_label:
            st.markdown(f"**Aktiver Indikator:** {indicator_label} — {len(indicator_years)} Jahre")
        if outlier_years:
            st.markdown(f"**Outlier-Filter:** {len(outlier_years)} Jahre entfernt/angepasst")


if __name__ == "__main__":
    main()
