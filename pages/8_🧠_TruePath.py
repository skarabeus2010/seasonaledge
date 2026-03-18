"""
SeasonalEdge - TruePath (KI-basierte Saisonalität)
====================================================
Rekalibriert das saisonale Muster auf Basis der Korrelation mit dem
aktuellen Jahresverlauf. Entfernt "Rauschen" von nicht-passenden Jahren.
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
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from scipy.spatial.distance import euclidean

from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS, COLOR_SEASONAL_AVG, COLOR_CURRENT_YEAR
from shared.data import download_data, preprocess
from shared.calculations import (
    build_year_data, calculate_seasonal_average, 
    interpolate_to_365, normalize_year,
    get_presidential_cycle_year
)

st.set_page_config(page_title="SeasonalEdge - TruePath", page_icon="🧠", layout="wide")


# ══════════════════════════════════════════════════════════════
# DTW / KORRELATION
# ══════════════════════════════════════════════════════════════

def calculate_year_similarity(current_curve, historical_curve, method="correlation"):
    """
    Berechne die Ähnlichkeit zwischen aktuellem und historischem Jahresverlauf.
    
    Args:
        current_curve: Normalisierte Kurve des aktuellen Jahres (bis heute)
        historical_curve: Volle 365-Tage normalisierte Kurve
        method: "correlation" oder "euclidean"
    
    Returns:
        float: Ähnlichkeit (0-100, höher = ähnlicher)
    """
    n = len(current_curve)
    if n < 10:
        return 0
    
    hist_segment = historical_curve[:n]
    
    if method == "correlation":
        if np.std(current_curve) == 0 or np.std(hist_segment) == 0:
            return 0
        corr = np.corrcoef(current_curve, hist_segment)[0, 1]
        # Korrelation (-1 bis +1) → Ähnlichkeit (0-100)
        similarity = max(0, (corr + 1) / 2 * 100)
    
    elif method == "euclidean":
        # Normalisiere beide Kurven auf gleiche Skala
        curr_norm = (np.array(current_curve) - np.mean(current_curve)) / (np.std(current_curve) + 1e-8)
        hist_norm = (np.array(hist_segment) - np.mean(hist_segment)) / (np.std(hist_segment) + 1e-8)
        dist = euclidean(curr_norm, hist_norm)
        # Distanz → Ähnlichkeit (kleinere Distanz = höhere Ähnlichkeit)
        similarity = max(0, 100 - dist * 5)
    
    else:
        return 0
    
    return round(similarity, 1)


def find_matching_years(year_data, current_year, method="correlation", top_n=5):
    """
    Finde die historischen Jahre die dem aktuellen Verlauf am ähnlichsten sind.
    
    Returns:
        list of dict: [{year, similarity, full_365}, ...] sortiert nach Ähnlichkeit
    """
    if current_year not in year_data:
        return []
    
    current_yd = year_data[current_year]
    today_doy = datetime.now().timetuple().tm_yday
    
    # Aktuelle Kurve bis heute
    current_curve = current_yd["full_365"][:today_doy]
    
    matches = []
    for year, yd in year_data.items():
        if year == current_year:
            continue
        
        similarity = calculate_year_similarity(current_curve, yd["full_365"], method)
        
        matches.append({
            "year": year,
            "similarity": similarity,
            "full_365": yd["full_365"],
            "cycle": get_presidential_cycle_year(year)
        })
    
    # Sortieren nach Ähnlichkeit (höchste zuerst)
    matches.sort(key=lambda x: x["similarity"], reverse=True)
    
    return matches[:top_n]


def calculate_truepath(year_data, matches, smoothing=5):
    """
    Berechne den TruePath: Gewichteter Durchschnitt der ähnlichsten Jahre.
    
    Gewichtung: Ähnlichkeit als Gewicht (höhere Ähnlichkeit = mehr Einfluss).
    
    Returns:
        list: 365 gewichtete Durchschnittswerte
    """
    if not matches:
        return None
    
    # Gewichte = Ähnlichkeits-Scores
    total_weight = sum(m["similarity"] for m in matches)
    if total_weight == 0:
        return None
    
    truepath = [0.0] * 365
    
    for m in matches:
        weight = m["similarity"] / total_weight
        for d in range(365):
            truepath[d] += m["full_365"][d] * weight
    
    # Glätten
    if smoothing > 1:
        truepath = pd.Series(truepath).rolling(smoothing, center=True, min_periods=1).mean().tolist()
    
    return truepath


def calculate_projection(matches, from_day, projection_days=60):
    """
    Projiziere den zukünftigen Verlauf basierend auf den Match-Jahren.
    
    Returns:
        dict: {days: [...], values: [...], upper: [...], lower: [...]}
    """
    if not matches or from_day >= 365:
        return None
    
    end_day = min(from_day + projection_days, 365)
    proj_days = list(range(from_day, end_day))
    
    # Sammle Werte pro Tag
    total_weight = sum(m["similarity"] for m in matches)
    
    weighted_values = []
    all_values_per_day = []
    
    for d in range(from_day, end_day):
        day_vals = []
        weighted_sum = 0
        for m in matches:
            if d < len(m["full_365"]):
                val = m["full_365"][d]
                day_vals.append(val)
                weighted_sum += val * (m["similarity"] / total_weight)
        
        weighted_values.append(weighted_sum)
        all_values_per_day.append(day_vals)
    
    # Konfidenzband
    upper = [np.mean(vals) + np.std(vals) if vals else 0 for vals in all_values_per_day]
    lower = [np.mean(vals) - np.std(vals) if vals else 0 for vals in all_values_per_day]
    
    return {
        "days": proj_days,
        "values": weighted_values,
        "upper": upper,
        "lower": lower
    }


# ══════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════

def build_truepath_chart(year_data, avg, truepath, matches, ticker, current_year,
                         show_matches, show_classic, smoothing):
    """Erstelle den TruePath Chart."""
    
    fig = go.Figure()
    x_days = list(range(1, 366))
    today_doy = datetime.now().timetuple().tm_yday
    
    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    month_starts = [datetime(2024, m, 1).timetuple().tm_yday for m in range(1, 13)]
    
    # ── Klassischer Saisonaler Durchschnitt (optional, verblasst) ──
    if show_classic and avg:
        avg_smooth = avg
        if smoothing > 1:
            avg_smooth = pd.Series(avg).rolling(smoothing, center=True, min_periods=1).mean().tolist()
        fig.add_trace(go.Scatter(
            x=x_days, y=avg_smooth, mode="lines",
            line=dict(color="rgba(0,206,209,0.3)", width=1.5, dash="dot"),
            name="Klassischer Ø (alle Jahre)",
            hovertemplate="Klassisch<br>Tag %{x}: %{y:.2f}<extra></extra>"
        ))
    
    # ── Match-Jahre einzeln (optional) ──
    if show_matches:
        match_colors = ["#FF6B6B", "#FFA07A", "#FFD93D", "#4ECDC4", "#45B7D1",
                       "#9664B4", "#FF8E72", "#6BCB77"]
        for i, m in enumerate(matches):
            color = match_colors[i % len(match_colors)]
            fig.add_trace(go.Scatter(
                x=x_days, y=m["full_365"], mode="lines",
                line=dict(color=color, width=1.2, dash="dash"),
                name=f"{m['year']} ({m['similarity']:.0f}%)",
                opacity=0.6,
                hovertemplate=f"{m['year']}<br>Tag %{{x}}: %{{y:.2f}}<extra></extra>"
            ))
    
    # ── TruePath (Hauptlinie) ──
    if truepath:
        fig.add_trace(go.Scatter(
            x=x_days, y=truepath, mode="lines",
            line=dict(color="#FF6B6B", width=3.5),
            name=f"TruePath ({len(matches)} beste Matches)",
            hovertemplate="TruePath<br>Tag %{x}: %{y:.2f}<extra></extra>"
        ))
    
    # ── Projektion (gestrichelt, ab heute) ──
    if truepath and today_doy < 365:
        proj = calculate_projection(matches, today_doy, 60)
        if proj:
            fig.add_trace(go.Scatter(
                x=proj["days"], y=proj["upper"], mode="lines",
                line=dict(width=0), showlegend=False, hoverinfo="skip"
            ))
            fig.add_trace(go.Scatter(
                x=proj["days"], y=proj["lower"], mode="lines",
                line=dict(width=0), fill="tonexty",
                fillcolor="rgba(255,107,107,0.1)",
                name="Projektion ±1σ", showlegend=True, hoverinfo="skip"
            ))
            fig.add_trace(go.Scatter(
                x=proj["days"], y=proj["values"], mode="lines",
                line=dict(color="#FF6B6B", width=2, dash="dash"),
                name="Projektion (60 Tage)",
                hovertemplate="Projektion<br>Tag %{x}: %{y:.2f}<extra></extra>"
            ))
    
    # ── Aktuelles Jahr ──
    if current_year in year_data:
        yd = year_data[current_year]
        display_days = [d for d in yd["days"] if d <= today_doy]
        display_vals = yd["cumulative"][:len(display_days)]
        if display_days:
            fig.add_trace(go.Scatter(
                x=display_days, y=display_vals, mode="lines",
                line=dict(color=COLOR_CURRENT_YEAR, width=2.5),
                name=f"{current_year} (aktuell)",
                hovertemplate=f"{current_year}<br>Tag %{{x}}: %{{y:.2f}}<extra></extra>"
            ))
    
    # ── Heute-Markierung ──
    fig.add_vline(x=today_doy, line_dash="solid",
        line_color="rgba(255,255,255,0.5)", line_width=1)
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=550, margin=dict(t=50, b=50, l=60, r=30),
        title=dict(text=f"{ticker} — TruePath (KI-basierte Saisonalität)",
                   font=dict(size=18, color="#e0e0e0")),
        xaxis=dict(tickmode="array", tickvals=month_starts, ticktext=month_names,
                   gridcolor="rgba(255,255,255,0.06)", range=[1, 365]),
        yaxis=dict(title="Normalisiert (Start = 100)", gridcolor="rgba(255,255,255,0.06)",
                   tickformat=".1f"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                    font=dict(size=10)),
        hovermode="x unified"
    )
    
    return fig


# ══════════════════════════════════════════════════════════════
# ENSEMBLE SCORING
# ══════════════════════════════════════════════════════════════

def calculate_seasonal_score(year_data, avg, std, current_year, matches):
    """
    Multi-Faktor SeasonalEdge Score (0-100).
    
    Faktoren:
    1. Saisonalität: Steigt oder fällt der Ø in den nächsten 20 Tagen?
    2. TruePath: Was sagen die ähnlichsten Jahre?
    3. Präsidentenzyklus: Bullish oder bearish?
    4. Volatilität: Ist das Konfidenzband eng (= konsistentes Muster)?
    5. Anomalie: Liegt der aktuelle Kurs über oder unter dem Ø?
    
    Returns:
        dict: {score, factors: [{name, value, weight, signal, description}]}
    """
    today_doy = datetime.now().timetuple().tm_yday
    factors = []
    
    # ── Faktor 1: Saisonalität (30%) ──
    if avg and today_doy < 345:
        lookahead = min(20, 365 - today_doy)
        current_val = avg[today_doy - 1]
        future_val = avg[min(today_doy - 1 + lookahead, 364)]
        expected_move = future_val - current_val
        
        # Score: +2% = 100, -2% = 0, 0 = 50
        seasonal_score = max(0, min(100, 50 + expected_move * 25))
        signal = "bullish" if expected_move > 0.2 else "bearish" if expected_move < -0.2 else "neutral"
        
        factors.append({
            "name": "Saisonalität",
            "value": seasonal_score,
            "weight": 0.30,
            "signal": signal,
            "description": f"Ø Erwartung nächste {lookahead}T: {expected_move:+.2f}%"
        })
    
    # ── Faktor 2: TruePath (25%) ──
    if matches:
        # Was passierte in den Match-Jahren in den nächsten 20 Tagen?
        future_moves = []
        for m in matches:
            if today_doy + 20 < 366:
                move = m["full_365"][min(today_doy + 19, 364)] - m["full_365"][today_doy - 1]
                future_moves.append(move)
        
        if future_moves:
            avg_move = np.mean(future_moves)
            tp_score = max(0, min(100, 50 + avg_move * 20))
            signal = "bullish" if avg_move > 0.3 else "bearish" if avg_move < -0.3 else "neutral"
            
            avg_sim = np.mean([m["similarity"] for m in matches])
            
            factors.append({
                "name": "TruePath",
                "value": tp_score,
                "weight": 0.25,
                "signal": signal,
                "description": f"Top-{len(matches)} Matches (Ø {avg_sim:.0f}% Ähnl.): {avg_move:+.2f}%"
            })
    
    # ── Faktor 3: Präsidentenzyklus (15%) ──
    cycle = get_presidential_cycle_year(current_year)
    cycle_scores = {
        "Year 3 (Pre-Election)": 75,   # Historisch stärkstes Jahr
        "Year 4 (Election Year)": 60,
        "Year 1 (Post-Election)": 40,  # Historisch schwächstes
        "Year 2 (Midterm Election)": 45
    }
    cycle_score = cycle_scores.get(cycle, 50)
    signal = "bullish" if cycle_score >= 60 else "bearish" if cycle_score <= 45 else "neutral"
    
    factors.append({
        "name": "Präsidentenzyklus",
        "value": cycle_score,
        "weight": 0.15,
        "signal": signal,
        "description": f"{cycle}"
    })
    
    # ── Faktor 4: Muster-Konsistenz (15%) ──
    if std and today_doy < 365:
        # Enge Std.Abw. = konsistentes Muster = höhere Zuversicht
        lookahead = min(20, 365 - today_doy)
        avg_std = np.mean(std[today_doy:today_doy + lookahead])
        # Niedrige Std = hoher Score (Std < 2 = 80+, Std > 8 = 20)
        consistency_score = max(0, min(100, 100 - avg_std * 10))
        signal = "bullish" if consistency_score >= 60 else "bearish" if consistency_score <= 30 else "neutral"
        
        factors.append({
            "name": "Muster-Konsistenz",
            "value": consistency_score,
            "weight": 0.15,
            "signal": signal,
            "description": f"Ø Std.Abw. nächste {lookahead}T: {avg_std:.1f}%"
        })
    
    # ── Faktor 5: Aktuelle Position (15%) ──
    if avg and current_year in year_data:
        yd = year_data[current_year]
        if today_doy - 1 < len(yd["full_365"]):
            actual = yd["full_365"][today_doy - 1]
            expected = avg[today_doy - 1]
            deviation = actual - expected
            
            # Über dem Durchschnitt = Stärke
            pos_score = max(0, min(100, 50 + deviation * 10))
            signal = "bullish" if deviation > 1 else "bearish" if deviation < -1 else "neutral"
            
            factors.append({
                "name": "Aktuelle Position",
                "value": pos_score,
                "weight": 0.15,
                "signal": signal,
                "description": f"Aktuell {deviation:+.1f}% vs. saisonaler Ø"
            })
    
    # ── Gesamt-Score ──
    if not factors:
        return {"score": 50, "factors": []}
    
    # Gewichtete Summe, normalisiert auf Gewichte
    total_weight = sum(f["weight"] for f in factors)
    score = sum(f["value"] * f["weight"] for f in factors) / total_weight
    
    return {"score": round(score, 1), "factors": factors}


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.markdown("## 🧠 TruePath")
        st.markdown("_KI-basierte Saisonalität_")
        st.markdown("---")
        
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="tp_ticker").upper().strip()
        
        period_options = [5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider("Analyse-Zeitraum",
            options=period_options, value=DEFAULT_YEARS,
            format_func=lambda x: str(x), key="tp_period")
        years_back_is_max = (years_back_raw == "Max")
        
        st.markdown("---")
        st.markdown("### Pattern Matching")
        
        match_method = st.radio("Ähnlichkeits-Methode",
            ["correlation", "euclidean"],
            format_func=lambda x: "Korrelation (Richtung)" if x == "correlation" else "Euklidisch (Form)",
            index=0, key="tp_method",
            help="Korrelation misst die Richtung, Euklidisch die absolute Form"
        )
        
        top_n = st.slider("Anzahl Matches", 3, 15, 5, key="tp_topn",
            help="Wie viele ähnlichste Jahre fließen in den TruePath ein?")
        
        smoothing = st.slider("Glättung (Tage)", 1, 21, 5, 2, key="tp_smooth")
        
        st.markdown("---")
        st.markdown("### Anzeige")
        
        show_matches = st.checkbox("Match-Jahre anzeigen", value=True, key="tp_show_matches")
        show_classic = st.checkbox("Klassischen Ø anzeigen", value=True, key="tp_show_classic")
    
    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)
    
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return
    
    df = preprocess(raw_df)
    all_years = sorted(df["year"].unique())
    current_year = datetime.now().year
    
    if years_back_is_max:
        selected_years = all_years
    else:
        years_back = int(years_back_raw)
        cutoff_year = current_year - years_back
        selected_years = [y for y in all_years if y >= cutoff_year]
    
    if current_year not in selected_years and current_year in all_years:
        selected_years.append(current_year)
        selected_years.sort()
    
    if len(selected_years) < 5:
        st.warning("Mindestens 5 Jahre Daten nötig für Pattern Matching.")
        return
    
    year_data = build_year_data(df, selected_years)
    avg, std = calculate_seasonal_average(year_data)
    
    if current_year not in year_data:
        st.warning(f"Keine Daten für {current_year} vorhanden.")
        return
    
    # ── Pattern Matching ──────────────────────────────
    with st.spinner("Berechne Ähnlichkeiten..."):
        matches = find_matching_years(year_data, current_year, match_method, top_n)
    
    if not matches:
        st.warning("Konnte keine passenden Jahre finden.")
        return
    
    truepath = calculate_truepath(year_data, matches, smoothing)
    
    # ══════════════════════════════════════════════════
    # 1. TRUEPATH CHART
    # ══════════════════════════════════════════════════
    
    fig = build_truepath_chart(year_data, avg, truepath, matches, ticker,
                               current_year, show_matches, show_classic, smoothing)
    st.plotly_chart(fig, use_container_width=True)
    
    # ══════════════════════════════════════════════════
    # 2. MATCH-TABELLE
    # ══════════════════════════════════════════════════
    
    st.markdown("#### 🎯 Top Matches — Jahre die dem aktuellen Verlauf am ähnlichsten sind")
    
    match_rows = []
    for m in matches:
        # Was passierte im Rest des Jahres?
        today_doy = datetime.now().timetuple().tm_yday
        rest_return = m["full_365"][364] - m["full_365"][today_doy - 1] if today_doy < 365 else 0
        
        match_rows.append({
            "Jahr": m["year"],
            "Ähnlichkeit": f"{m['similarity']:.1f}%",
            "Zyklus": m["cycle"],
            "Jahres-Rendite": f"{m['full_365'][364] - 100:+.1f}%",
            "Rest ab heute": f"{rest_return:+.1f}%"
        })
    
    st.dataframe(pd.DataFrame(match_rows), use_container_width=True, hide_index=True)
    
    # ══════════════════════════════════════════════════
    # 3. SEASONALEDGE SCORE
    # ══════════════════════════════════════════════════
    
    st.markdown("---")
    st.markdown("### 📊 SeasonalEdge Score")
    
    scoring = calculate_seasonal_score(year_data, avg, std, current_year, matches)
    score = scoring["score"]
    
    # Score als große Zahl + Gauge
    score_color = "#4CAF50" if score >= 60 else "#F44336" if score <= 40 else "#FFD700"
    
    if score >= 70:
        label = "🟢 Stark Bullish"
    elif score >= 60:
        label = "🟢 Bullish"
    elif score >= 50:
        label = "🟡 Neutral-Bullish"
    elif score >= 40:
        label = "🟡 Neutral-Bearish"
    elif score >= 30:
        label = "🔴 Bearish"
    else:
        label = "🔴 Stark Bearish"
    
    col_score, col_label = st.columns([1, 3])
    with col_score:
        st.markdown(f"<h1 style='color:{score_color}; text-align:center; margin:0;'>{score:.0f}</h1>",
                    unsafe_allow_html=True)
        st.markdown(f"<p style='text-align:center; color:{score_color};'>{label}</p>",
                    unsafe_allow_html=True)
    
    with col_label:
        st.markdown("**Faktor-Aufschlüsselung:**")
        for f in scoring["factors"]:
            emoji = "🟢" if f["signal"] == "bullish" else "🔴" if f["signal"] == "bearish" else "🟡"
            bar_width = int(f["value"])
            st.markdown(
                f"{emoji} **{f['name']}** ({f['weight']*100:.0f}%): "
                f"**{f['value']:.0f}**/100 — {f['description']}"
            )
    
    # Disclaimer
    st.markdown("---")
    st.caption(
        "⚠️ _Der SeasonalEdge Score basiert auf historischen Mustern und statistischen Wahrscheinlichkeiten. "
        "Keine Anlageberatung. Vergangene Performance ist kein Indikator für zukünftige Ergebnisse._"
    )


if __name__ == "__main__":
    main()
