"""
SeasonalEdge — KI Seasonal Score
=================================
Composite Score 1-10 aus DTW, Prophet, Win-Rate & Tracking.
"""

# ── sys.path Fix ──────────────────────────────────────
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

# ── Imports ───────────────────────────────────────────
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import DEFAULT_TICKER, SE_COLORS, MONTH_NAMES_DE
from shared.data import download_data, preprocess
from shared.calculations import build_year_data, calculate_seasonal_average
from shared.charts import apply_se_theme
from shared.ki_score import calculate_ki_score

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="KI Score — SeasonalEdge",
    page_icon="🧠",
    layout="wide",
)


# ── Hilfsfunktionen ──────────────────────────────────

def score_color(score: float) -> str:
    """Farbe basierend auf Score-Wert."""
    if score >= 6.5:
        return SE_COLORS["positive"]
    elif score <= 3.5:
        return SE_COLORS["negative"]
    return SE_COLORS["accent_warm"]


def signal_emoji(signal: str) -> str:
    if signal == "Bullish":
        return "🟢"
    elif signal == "Bearish":
        return "🔴"
    return "🟡"


def build_radar_chart(sub_scores: dict) -> go.Figure:
    """Radar-Chart für die 4 Sub-Scores."""
    labels = ["DTW\nÄhnlichkeit", "Prophet\nPrognose", "Win-Rate", "Tracking\nQualität"]
    values = [
        sub_scores["dtw"]["weighted"],
        sub_scores["prophet"]["weighted"],
        sub_scores["win_rate"]["weighted"],
        sub_scores["tracking"]["weighted"],
    ]
    # Schließe den Kreis
    labels_closed = labels + [labels[0]]
    values_closed = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=labels_closed,
        fill="toself",
        fillcolor="rgba(0,212,170,0.15)",
        line=dict(color=SE_COLORS["accent"], width=2),
        marker=dict(size=8, color=SE_COLORS["accent"]),
        name="KI Score",
        hovertemplate="%{theta}: %{r:.2f}/2.5<extra></extra>",
    ))

    fig = apply_se_theme(fig, title="Sub-Score Radar", height=380, show_watermark=False)
    fig.update_layout(
        polar=dict(
            bgcolor=SE_COLORS["surface"],
            radialaxis=dict(
                visible=True,
                range=[0, 2.5],
                gridcolor=SE_COLORS["grid"],
                linecolor=SE_COLORS["grid"],
                tickfont=dict(color=SE_COLORS["text_dim"], size=9),
            ),
            angularaxis=dict(
                gridcolor=SE_COLORS["grid"],
                linecolor=SE_COLORS["grid"],
                tickfont=dict(color=SE_COLORS["text_muted"], size=11),
            ),
        ),
    )
    return fig


def build_forecast_chart(forecast_df: pd.DataFrame, ticker: str) -> go.Figure:
    """30-Tage Prophet Forecast Chart."""
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=forecast_df["ds"], y=forecast_df["yhat_upper"],
        mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["ds"], y=forecast_df["yhat_lower"],
        mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(0,212,170,0.1)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=forecast_df["ds"], y=forecast_df["yhat"],
        mode="lines",
        line=dict(color=SE_COLORS["accent"], width=2.5),
        name="Forecast",
        hovertemplate="%{x|%d.%m}: %{y:.2f}<extra></extra>",
    ))

    fig = apply_se_theme(fig, title=f"{ticker} — Prophet Prognose 30 Tage", height=320)
    fig.update_yaxes(title="Preis (geschätzt)")
    return fig


def build_tracking_chart(
    current_curve: list[float],
    seasonal_avg: list[float],
    days_compared: int,
    ticker: str,
) -> go.Figure:
    """Overlay: Aktuelles Jahr vs. Saisonaler Durchschnitt."""
    fig = go.Figure()
    x = list(range(1, days_compared + 1))

    fig.add_trace(go.Scatter(
        x=x, y=seasonal_avg[:days_compared],
        mode="lines",
        line=dict(color=SE_COLORS["accent_blue"], width=2, dash="dash"),
        name="Ø Saisonal",
    ))
    fig.add_trace(go.Scatter(
        x=x, y=current_curve[:days_compared],
        mode="lines",
        line=dict(color=SE_COLORS["current_year"], width=2.5),
        name=f"{datetime.now().year}",
    ))

    fig = apply_se_theme(fig, title=f"{ticker} — Tracking {datetime.now().year} vs. Ø", height=320)
    fig.update_xaxes(title="Kalendertag")
    fig.update_yaxes(title="Normiert (Start=100)")
    return fig


# ── Hauptseite ────────────────────────────────────────

def main():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### 🧠 KI Seasonal Score")
        ticker = st.text_input(
            "Ticker", value=DEFAULT_TICKER, key="ki_ticker"
        ).upper().strip()

        years_back = st.slider(
            "📅 Jahre zurück", 5, 50, 20, key="ki_years"
        )

        use_prophet = st.checkbox(
            "🔮 Prophet Forecast (langsamer)", value=False, key="ki_prophet"
        )

        use_claude = st.checkbox(
            "💬 Claude-Kommentar", value=False, key="ki_claude"
        )

        st.markdown("---")
        st.caption(
            "Score = DTW (2.5) + Prophet (2.5) + "
            "Win-Rate (2.5) + Tracking (2.5)"
        )

    # ── Header ──
    st.markdown("## 🧠 KI Seasonal Score")
    st.caption("Composite Score aus 4 KI-Komponenten · Skala 1–10")

    # ── Daten laden ──
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)

    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        st.stop()

    df = preprocess(raw_df)
    if df is None or df.empty:
        st.error(f"Daten für '{ticker}' konnten nicht verarbeitet werden.")
        st.stop()

    # ── Berechnung ──
    current_year = datetime.now().year
    start_year = current_year - years_back
    available_years = sorted([
        y for y in df["year"].unique()
        if start_year <= y <= current_year
    ])

    if len(available_years) < 3:
        st.warning(f"Nur {len(available_years)} Jahre verfügbar — mindestens 3 benötigt.")
        st.stop()

    year_data = build_year_data(df, available_years)
    if len(year_data) < 3:
        st.warning("Zu wenig verwertbare Jahresdaten.")
        st.stop()

    avg, std = calculate_seasonal_average(year_data)

    with st.spinner("Berechne KI Score..."):
        result = calculate_ki_score(
            ticker, df, year_data, avg, std,
            quick_mode=not use_prophet,
        )

    score = result["score"]
    signal = result["signal"]
    sub = result["sub_scores"]
    meta = result["meta"]

    # ── Score Display ──
    col_score, col_radar, col_meta = st.columns([1, 1.2, 0.8])

    with col_score:
        color = score_color(score)
        emoji = signal_emoji(signal)
        st.markdown(f"""
        <div style="background:{SE_COLORS['surface']};border:2px solid {color};
                    border-radius:20px;padding:2rem;text-align:center;margin-top:1rem;">
            <div style="font-size:4rem;font-weight:900;color:{color};line-height:1;">
                {score}
            </div>
            <div style="font-size:0.9rem;color:{SE_COLORS['text_muted']};margin:0.3rem 0;">
                von 10.0
            </div>
            <div style="font-size:1.5rem;font-weight:700;color:{color};margin-top:0.5rem;">
                {emoji} {signal}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_radar:
        radar_fig = build_radar_chart(sub)
        st.plotly_chart(radar_fig, use_container_width=True)

    with col_meta:
        st.markdown(f"""
        <div style="background:{SE_COLORS['surface']};border:1px solid {SE_COLORS['panel_border']};
                    border-radius:12px;padding:1.5rem;margin-top:1rem;">
            <div style="color:{SE_COLORS['text_muted']};font-size:0.75rem;text-transform:uppercase;
                        letter-spacing:1px;margin-bottom:1rem;">Details</div>
            <div style="color:{SE_COLORS['text_primary']};margin-bottom:0.5rem;">
                <b>{ticker}</b> · {meta['total_years']} Jahre
            </div>
            <div style="color:{SE_COLORS['text_muted']};font-size:0.85rem;margin-bottom:0.3rem;">
                📅 Monat: {MONTH_NAMES_DE[meta['current_month'] - 1]}
            </div>
            <div style="color:{SE_COLORS['text_muted']};font-size:0.85rem;margin-bottom:0.3rem;">
                📊 Handelstage YTD: {meta['trading_days_ytd']}
            </div>
            <div style="color:{SE_COLORS['text_muted']};font-size:0.85rem;">
                🗓️ Kalendertag: {meta['current_doy']}/365
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Sub-Score Details ──
    st.markdown("### 📋 Sub-Score Details")

    # DTW
    dtw = sub["dtw"]
    with st.expander(f"🔍 DTW Ähnlichkeit — {dtw['weighted']:.2f} / 2.5"):
        dtw_d = dtw["details"]
        if "error" in dtw_d and not dtw_d.get("similar_years"):
            st.warning(dtw_d["error"])
        else:
            st.markdown(f"**Positive ähnliche Jahre:** {dtw_d.get('positive_ratio', 'N/A')}")
            if dtw_d.get("similar_years"):
                rows = []
                for sy in dtw_d["similar_years"]:
                    rows.append({
                        "Jahr": sy["year"],
                        "Distanz": sy["distance"],
                        "Jahresrendite": f"{sy['return_pct']:+.1f}%",
                        "Positiv": "✅" if sy["positive"] else "❌",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Prophet
    prophet = sub["prophet"]
    with st.expander(f"🔮 Prophet Prognose — {prophet['weighted']:.2f} / 2.5"):
        p_d = prophet["details"]
        if "error" in p_d:
            st.info(p_d["error"])
        else:
            direction = "📈 Bullish" if p_d.get("direction") == "bullish" else "📉 Bearish"
            st.markdown(f"**Erwartete Rendite (30 Tage):** {p_d['forecast_return']:+.2f}% — {direction}")
            if "forecast_df" in p_d and p_d["forecast_df"] is not None:
                fig = build_forecast_chart(p_d["forecast_df"], ticker)
                st.plotly_chart(fig, use_container_width=True)

    # Win-Rate
    wr = sub["win_rate"]
    with st.expander(f"📊 Win-Rate — {wr['weighted']:.2f} / 2.5"):
        wr_d = wr["details"]
        if "error" in wr_d and wr_d.get("total_years", 0) == 0:
            st.warning(wr_d["error"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Win-Rate", f"{wr_d['win_rate']:.1f}%")
            c2.metric("Ø Rendite", f"{wr_d['avg_return']:+.2f}%")
            c3.metric("Median", f"{wr_d['median_return']:+.2f}%")

            c4, c5, c6 = st.columns(3)
            c4.metric("Jahre gesamt", wr_d["total_years"])
            c5.metric("Max Gewinn", f"{wr_d['max_gain']:+.2f}%")
            c6.metric("Max Verlust", f"{wr_d['max_loss']:+.2f}%")

    # Tracking
    tracking = sub["tracking"]
    with st.expander(f"📐 Tracking-Qualität — {tracking['weighted']:.2f} / 2.5"):
        t_d = tracking["details"]
        if "error" in t_d:
            st.info(t_d["error"])
        else:
            c1, c2, c3 = st.columns(3)
            c1.metric("Korrelation", f"{t_d['correlation']:.3f}")
            c2.metric("MAE", f"{t_d['mae']:.3f}")
            c3.metric("Vergl. Tage", t_d["days_compared"])

            current_yd = year_data.get(datetime.now().year)
            if current_yd and t_d["days_compared"] > 10:
                fig = build_tracking_chart(
                    current_yd["full_365"], avg,
                    t_d["days_compared"], ticker
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Claude Kommentar ──
    if use_claude:
        st.markdown("---")
        st.markdown("### 💬 KI-Kommentar")
        with st.spinner("Claude analysiert..."):
            from shared.ai_models import generate_seasonal_commentary
            month_name = MONTH_NAMES_DE[meta["current_month"] - 1]
            wr_details = sub["win_rate"]["details"]

            similar_years = []
            if dtw["details"].get("similar_years"):
                similar_years = [
                    (sy["year"], sy["distance"])
                    for sy in dtw["details"]["similar_years"]
                ]

            commentary = generate_seasonal_commentary(
                ticker=ticker,
                month=month_name,
                avg_return=wr_details.get("avg_return", 0),
                win_rate=wr_details.get("win_rate", 50),
                similar_years=similar_years,
            )

            if commentary:
                st.info(f"🤖 {commentary}")
            else:
                st.warning("Claude-Kommentar nicht verfügbar (API-Key fehlt?).")

    # ── Disclaimer ──
    st.markdown("---")
    st.caption(
        "⚠️ _Der KI Seasonal Score basiert auf historischen Mustern und "
        "statistischen Modellen. Keine Anlageberatung. Vergangene "
        "Performance ist kein Indikator für zukünftige Ergebnisse._"
    )


main()
