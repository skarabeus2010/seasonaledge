"""
SeasonalEdge — Premium Dashboard (Seasonax-Style)
===================================================
Alles auf einer Seite: Saisonalkurve, KPIs, Jahresrenditen,
Monatsrenditen, Heatmap, Box-Plot, Jahres-Tabelle, KI-Score.
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
from shared.calculations import (
    build_year_data, calculate_seasonal_average, calculate_period_stats,
)
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.ki_score import calculate_ki_score, SIGNAL_THRESHOLDS

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="Premium Dashboard — SeasonalEdge",
    page_icon="⭐",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

# ── Monat → DOY Mapping ──────────────────────────────
MONTH_START = {1:1,2:32,3:60,4:91,5:121,6:152,7:182,8:213,9:244,10:274,11:305,12:335}
MONTH_END = {1:31,2:59,3:90,4:120,5:151,6:181,7:212,8:243,9:273,10:304,11:334,12:365}


# ══════════════════════════════════════════════════════
# HILFSFUNKTIONEN
# ══════════════════════════════════════════════════════

def score_color(score: float) -> str:
    if score >= SIGNAL_THRESHOLDS["bullish"]:
        return SE_COLORS["positive"]
    elif score <= SIGNAL_THRESHOLDS["bearish"]:
        return SE_COLORS["negative"]
    return SE_COLORS["accent_warm"]


def render_kpi_cards(stats: dict, years: int):
    """4 KPI-Karten in einer Reihe."""
    cards = [
        ("Ø Rendite", f"{stats.get('avg_return', 0):+.2f}%",
         SE_COLORS["positive"] if stats.get("avg_return", 0) > 0 else SE_COLORS["negative"]),
        ("Win-Rate", f"{stats.get('win_rate', 0):.1f}%",
         SE_COLORS["positive"] if stats.get("win_rate", 0) >= 50 else SE_COLORS["negative"]),
        ("Max Gewinn", f"{stats.get('max_gain', 0):+.2f}%", SE_COLORS["positive"]),
        ("Max Verlust", f"{stats.get('max_loss', 0):+.2f}%", SE_COLORS["negative"]),
    ]

    cols = st.columns(4)
    for i, (label, value, color) in enumerate(cards):
        with cols[i]:
            st.markdown(f"""
            <div style="background:{SE_COLORS['surface']};border:1px solid {SE_COLORS['panel_border']};
                        border-radius:12px;padding:1rem 1.2rem;text-align:center;">
                <div style="color:{SE_COLORS['text_muted']};font-size:0.7rem;text-transform:uppercase;
                            letter-spacing:1px;">{label}</div>
                <div style="color:{color};font-size:1.6rem;font-weight:800;margin:0.3rem 0;">
                    {value}
                </div>
                <div style="color:{SE_COLORS['text_dim']};font-size:0.65rem;">
                    {years} Jahre · {stats.get('total_years', 0)} Datenpunkte
                </div>
            </div>
            """, unsafe_allow_html=True)


def build_yearly_bar_chart(year_data: dict, start_doy: int, end_doy: int, ticker: str) -> go.Figure:
    """Balkendiagramm: Jahresrendite im gewählten Fenster."""
    years_sorted = sorted(year_data.keys())
    returns = []
    colors = []

    for year in years_sorted:
        yd = year_data[year]
        s_idx = max(0, min(start_doy - 1, 364))
        e_idx = max(0, min(end_doy - 1, 364))
        start_val = yd["full_365"][s_idx]
        end_val = yd["full_365"][e_idx]
        ret = (end_val / start_val - 1) * 100 if start_val > 0 else 0
        returns.append(ret)
        colors.append(SE_COLORS["positive"] if ret >= 0 else SE_COLORS["negative"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(y) for y in years_sorted],
        y=returns,
        marker_color=colors,
        hovertemplate="%{x}: %{y:+.2f}%<extra></extra>",
    ))

    fig.add_hline(y=0, line_color=SE_COLORS["zero_line"], line_width=1)

    avg_ret = np.mean(returns) if returns else 0
    fig.add_hline(
        y=avg_ret, line_dash="dash",
        line_color=SE_COLORS["accent_blue"], line_width=1.5,
        annotation_text=f"Ø {avg_ret:+.2f}%",
        annotation_position="top right",
        annotation_font=dict(color=SE_COLORS["accent_blue"], size=10),
    )

    fig = apply_se_theme(fig, title=f"{ticker} — Jahresrenditen im Zeitfenster", height=320)
    fig.update_xaxes(title="Jahr", tickangle=-45, tickfont=dict(size=9))
    fig.update_yaxes(title="Rendite (%)", tickformat="+.1f", ticksuffix="%")
    return fig


def build_monthly_bar_chart(year_data: dict, ticker: str) -> tuple[go.Figure, pd.DataFrame]:
    """12 Balken mit Ø Monatsrenditen + Statistik-Tabelle."""
    month_stats = []

    for m in range(1, 13):
        s = MONTH_START[m]
        e = MONTH_END[m]
        stats = calculate_period_stats(year_data, s, e)
        month_stats.append({
            "Monat": MONTH_NAMES_DE[m - 1],
            "Ø Rendite (%)": round(stats.get("avg_return", 0), 2),
            "Win-Rate (%)": round(stats.get("win_rate", 0), 1),
            "Median (%)": round(stats.get("median_return", 0), 2),
            "Std-Dev": round(stats.get("std_dev", 0), 2),
            "Jahre": stats.get("total_years", 0),
            "_avg": stats.get("avg_return", 0),
        })

    # Bar Chart
    fig = go.Figure()
    colors = [
        SE_COLORS["positive"] if ms["_avg"] >= 0 else SE_COLORS["negative"]
        for ms in month_stats
    ]
    fig.add_trace(go.Bar(
        x=[ms["Monat"][:3] for ms in month_stats],
        y=[ms["_avg"] for ms in month_stats],
        marker_color=colors,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Ø Rendite: %{y:+.2f}%<br>"
            "<extra></extra>"
        ),
        customdata=[
            [ms["Win-Rate (%)"], ms["Median (%)"], ms["Std-Dev"]]
            for ms in month_stats
        ],
    ))

    # Hover erweitern
    fig.data[0].hovertemplate = (
        "<b>%{x}</b><br>"
        "Ø Rendite: %{y:+.2f}%<br>"
        "Win-Rate: %{customdata[0]:.1f}%<br>"
        "Median: %{customdata[1]:+.2f}%<br>"
        "Std-Dev: %{customdata[2]:.2f}%"
        "<extra></extra>"
    )

    fig.add_hline(y=0, line_color=SE_COLORS["zero_line"], line_width=1)
    fig = apply_se_theme(fig, title=f"{ticker} — Monatliche Ø Renditen", height=320)
    fig.update_yaxes(title="Ø Rendite (%)", tickformat="+.2f", ticksuffix="%")

    # Tabelle (ohne interne Spalte)
    df_table = pd.DataFrame(month_stats).drop(columns=["_avg"])
    return fig, df_table


def build_yearly_table(year_data: dict, df: pd.DataFrame, start_doy: int, end_doy: int) -> pd.DataFrame:
    """Jahres-Tabelle wie bei Seasonax."""
    rows = []
    for year in sorted(year_data.keys(), reverse=True):
        yd = year_data[year]
        year_df = yd["df"]

        s_idx = max(0, min(start_doy - 1, 364))
        e_idx = max(0, min(end_doy - 1, 364))

        start_val = yd["full_365"][s_idx]
        end_val = yd["full_365"][e_idx]
        ret = (end_val / start_val - 1) * 100 if start_val > 0 else 0

        # Max Rise / Max Drop im Zeitfenster
        window = yd["full_365"][s_idx:e_idx + 1]
        if len(window) > 1:
            running_max = 0
            running_min = 0
            peak = window[0]
            trough = window[0]
            for v in window[1:]:
                change = (v / start_val - 1) * 100
                running_max = max(running_max, change)
                running_min = min(running_min, change)
        else:
            running_max = 0
            running_min = 0

        # Start/End Preise (echte Close-Werte)
        start_price = year_df["Close"].iloc[0] if len(year_df) > 0 else 0
        end_close_mask = year_df[year_df["day_of_year"] <= end_doy]
        end_price = end_close_mask["Close"].iloc[-1] if len(end_close_mask) > 0 else start_price

        rows.append({
            "Jahr": year,
            "Start": round(start_price, 2),
            "Ende": round(end_price, 2),
            "Rendite (%)": round(ret, 2),
            "Max Rise (%)": round(running_max, 2),
            "Max Drop (%)": round(running_min, 2),
            "Ergebnis": "✅" if ret > 0 else "❌",
        })

    return pd.DataFrame(rows)


def build_ki_score_gauge(score: float, signal: str) -> str:
    """HTML für KI-Score Gauge."""
    color = score_color(score)
    emoji = "🟢" if signal == "Bullish" else "🔴" if signal == "Bearish" else "🟡"
    return f"""
    <div style="background:{SE_COLORS['surface']};border:2px solid {color};
                border-radius:20px;padding:1.5rem;text-align:center;">
        <div style="font-size:0.7rem;color:{SE_COLORS['text_muted']};text-transform:uppercase;
                    letter-spacing:1px;">KI Seasonal Score</div>
        <div style="font-size:3.5rem;font-weight:900;color:{color};line-height:1.1;margin:0.5rem 0;">
            {score}
        </div>
        <div style="font-size:0.75rem;color:{SE_COLORS['text_dim']};">von 10.0</div>
        <div style="font-size:1.2rem;font-weight:700;color:{color};margin-top:0.5rem;">
            {emoji} {signal}
        </div>
    </div>
    """


def render_premium_placeholder(title: str, description: str):
    """Gesperrter Platzhalter für Premium-Features."""
    st.markdown(f"""
    <div style="background:{SE_COLORS['surface']};border:1px dashed {SE_COLORS['panel_border']};
                border-radius:12px;padding:2rem;text-align:center;opacity:0.5;">
        <div style="font-size:2rem;margin-bottom:0.5rem;">🔒</div>
        <div style="color:{SE_COLORS['text_muted']};font-size:1rem;font-weight:700;">
            {title}
        </div>
        <div style="color:{SE_COLORS['text_dim']};font-size:0.8rem;margin-top:0.3rem;">
            {description}
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
# HAUPTSEITE
# ══════════════════════════════════════════════════════

def main():
    # ── Sidebar ──────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⭐ Premium Dashboard")
        ticker = st.text_input(
            "Ticker", value=DEFAULT_TICKER, key="pd_ticker"
        ).upper().strip()

        years_back = st.slider("📅 Jahre zurück", 3, 50, 20, key="pd_years")

        st.markdown("**📆 Saisonales Zeitfenster**")
        col_s, col_e = st.columns(2)
        with col_s:
            start_month = st.selectbox(
                "Von Monat", range(1, 13),
                format_func=lambda m: MONTH_NAMES_DE[m - 1],
                index=0, key="pd_start_m",
            )
        with col_e:
            end_month = st.selectbox(
                "Bis Monat", range(1, 13),
                format_func=lambda m: MONTH_NAMES_DE[m - 1],
                index=11, key="pd_end_m",
            )

        start_doy = MONTH_START[start_month]
        end_doy = MONTH_END[end_month]

        show_ki = st.checkbox("🧠 KI-Score anzeigen", value=True, key="pd_ki")
        show_individual = st.checkbox("Einzeljahre im Chart", value=False, key="pd_individual")

        st.markdown("---")
        st.caption(f"Zeitfenster: Tag {start_doy}–{end_doy}")

    # ── Header ───────────────────────────────────────
    st.markdown(f"## ⭐ {ticker} — Premium Dashboard")
    period_label = f"{MONTH_NAMES_DE[start_month-1]} – {MONTH_NAMES_DE[end_month-1]}"
    st.caption(f"Saisonale Analyse · {period_label} · {years_back} Jahre")

    # ── Daten laden ──────────────────────────────────
    with st.spinner(f"Lade {ticker}..."):
        raw_df = download_data(ticker)
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}'.")
        st.stop()

    df = preprocess(raw_df)
    if df is None or df.empty:
        st.error(f"Verarbeitung fehlgeschlagen für '{ticker}'.")
        st.stop()

    current_year = datetime.now().year
    available_years = sorted([
        y for y in df["year"].unique()
        if (current_year - years_back) <= y <= current_year
    ])

    if len(available_years) < 3:
        st.warning("Zu wenig Jahresdaten (mind. 3 benötigt).")
        st.stop()

    year_data = build_year_data(df, available_years)
    if len(year_data) < 3:
        st.warning("Zu wenig verwertbare Jahre.")
        st.stop()

    avg, std = calculate_seasonal_average(year_data)

    # ══════════════════════════════════════════════════
    # SEKTION 1: KPI-Karten
    # ══════════════════════════════════════════════════
    stats = calculate_period_stats(year_data, start_doy, end_doy)
    if stats:
        render_kpi_cards(stats, years_back)
    st.markdown("")

    # ══════════════════════════════════════════════════
    # SEKTION 2: Saisonalkurve + KI-Score
    # ══════════════════════════════════════════════════
    if show_ki:
        col_chart, col_ki = st.columns([3, 1])
    else:
        col_chart = st.container()
        col_ki = None

    with col_chart:
        from shared.charts import build_seasonal_chart
        fig_seasonal = build_seasonal_chart(
            year_data=year_data,
            avg=avg,
            std=std,
            ticker=ticker,
            smoothing_window=5,
            show_individual=show_individual,
            show_bands=True,
            show_current_year=True,
            selected_range=(start_doy, end_doy),
            df=df,
        )
        st.plotly_chart(fig_seasonal, use_container_width=True)

    if show_ki and col_ki is not None:
        with col_ki:
            with st.spinner("KI Score..."):
                ki_result = calculate_ki_score(
                    ticker, df, year_data, avg, std, quick_mode=True,
                )
            st.markdown(
                build_ki_score_gauge(ki_result["score"], ki_result["signal"]),
                unsafe_allow_html=True,
            )

            # Sub-Scores kompakt
            sub = ki_result["sub_scores"]
            st.markdown(f"""
            <div style="background:{SE_COLORS['surface']};border:1px solid {SE_COLORS['panel_border']};
                        border-radius:10px;padding:0.8rem;margin-top:0.8rem;font-size:0.78rem;">
                <div style="color:{SE_COLORS['text_muted']};margin-bottom:0.5rem;">
                    <b>Sub-Scores</b>
                </div>
                <div style="color:{SE_COLORS['text_primary']};margin-bottom:0.3rem;">
                    🔍 DTW: <b>{sub['dtw']['weighted']:.1f}</b>/2.5
                </div>
                <div style="color:{SE_COLORS['text_primary']};margin-bottom:0.3rem;">
                    🔮 Prophet: <b>{sub['prophet']['weighted']:.1f}</b>/2.5
                </div>
                <div style="color:{SE_COLORS['text_primary']};margin-bottom:0.3rem;">
                    📊 Win-Rate: <b>{sub['win_rate']['weighted']:.1f}</b>/2.5
                </div>
                <div style="color:{SE_COLORS['text_primary']};">
                    📐 Tracking: <b>{sub['tracking']['weighted']:.1f}</b>/2.5
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════
    # SEKTION 3: Jahresrenditen-Balken
    # ══════════════════════════════════════════════════
    st.markdown("---")
    fig_yearly = build_yearly_bar_chart(year_data, start_doy, end_doy, ticker)
    st.plotly_chart(fig_yearly, use_container_width=True)

    # ══════════════════════════════════════════════════
    # SEKTION 4: Monatliche Renditen
    # ══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📅 Monatliche Renditen")

    col_mbars, col_mtable = st.columns([1.5, 1])
    fig_monthly, df_monthly = build_monthly_bar_chart(year_data, ticker)

    with col_mbars:
        st.plotly_chart(fig_monthly, use_container_width=True)

    with col_mtable:
        st.dataframe(
            df_monthly,
            use_container_width=True,
            hide_index=True,
            height=450,
            column_config={
                "Ø Rendite (%)": st.column_config.NumberColumn(format="%+.2f%%"),
                "Win-Rate (%)": st.column_config.NumberColumn(format="%.1f%%"),
                "Median (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            },
        )

    # ══════════════════════════════════════════════════
    # SEKTION 5: Heatmap + Box-Plot
    # ══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 🗺️ Verteilung & Muster")

    col_heat, col_box = st.columns(2)

    with col_heat:
        try:
            from shared.distribution_charts import build_decade_monthly_heatmap
            fig_hm = build_decade_monthly_heatmap(df, ticker)
            if fig_hm:
                st.plotly_chart(fig_hm, use_container_width=True)
        except Exception:
            st.caption("Heatmap nicht verfügbar.")

    with col_box:
        try:
            from shared.distribution_charts import build_box_plot
            # Monatliche Renditen als Box-Plot
            month_groups = {}
            for m in range(1, 13):
                s, e = MONTH_START[m], MONTH_END[m]
                rets = []
                for year, yd in year_data.items():
                    sv = yd["full_365"][s - 1]
                    ev = yd["full_365"][min(e - 1, 364)]
                    rets.append((ev / sv - 1) * 100 if sv > 0 else 0)
                month_groups[MONTH_NAMES_DE[m - 1][:3]] = rets

            month_colors = [
                SE_COLORS["positive"] if np.mean(v) >= 0 else SE_COLORS["negative"]
                for v in month_groups.values()
            ]
            fig_box = build_box_plot(
                month_groups, month_colors,
                title=f"{ticker} — Monatsverteilung",
                y_title="Rendite (%)",
            )
            st.plotly_chart(fig_box, use_container_width=True)
        except Exception:
            st.caption("Box-Plot nicht verfügbar.")

    # ══════════════════════════════════════════════════
    # SEKTION 6: Jahres-Tabelle
    # ══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📋 Jahres-Tabelle")

    df_years = build_yearly_table(year_data, df, start_doy, end_doy)
    st.dataframe(
        df_years,
        use_container_width=True,
        hide_index=True,
        height=min(len(df_years) * 38 + 40, 600),
        column_config={
            "Rendite (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            "Max Rise (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            "Max Drop (%)": st.column_config.NumberColumn(format="%+.2f%%"),
            "Start": st.column_config.NumberColumn(format="%.2f"),
            "Ende": st.column_config.NumberColumn(format="%.2f"),
        },
    )

    # Zusammenfassung unter der Tabelle
    if stats:
        total = stats.get("total_years", 0)
        wins = stats.get("winning_years", 0)
        losses = stats.get("losing_years", 0)
        st.caption(
            f"📊 {total} Jahre analysiert · "
            f"✅ {wins} gewonnen · ❌ {losses} verloren · "
            f"Win-Rate: {stats.get('win_rate', 0):.1f}%"
        )

    # ══════════════════════════════════════════════════
    # SEKTION 7: TDoM Kompakt-Ansicht
    # ══════════════════════════════════════════════════
    st.markdown("---")
    st.markdown("### 📅 TDoM — Trading Day of the Month")

    try:
        from shared.tdom_analysis import build_tdom_stats, build_tdom_month_matrix

        tdom_stats = build_tdom_stats(df, "open_to_close", "forward")
        if not tdom_stats.empty:
            # Kompakt-Balkendiagramm
            tdom_colors = [
                SE_COLORS["positive"] if r > 0 else SE_COLORS["negative"]
                for r in tdom_stats["avg_return"]
            ]
            fig_tdom = go.Figure()
            fig_tdom.add_trace(go.Bar(
                x=[str(t) for t in tdom_stats.index],
                y=tdom_stats["avg_return"],
                marker_color=tdom_colors,
                hovertemplate="TDoM %{x}: %{y:+.4f}%<br>Win-Rate: %{customdata:.1f}%<extra></extra>",
                customdata=tdom_stats["win_rate"],
            ))
            fig_tdom.add_hline(y=0, line_color=SE_COLORS["zero_line"], line_width=1)
            fig_tdom = apply_se_theme(
                fig_tdom, title=f"{ticker} — TDoM Ø Rendite (Intraday)", height=300,
            )
            fig_tdom.update_xaxes(title="TDoM", dtick=1)
            fig_tdom.update_yaxes(tickformat="+.3f", ticksuffix="%")
            st.plotly_chart(fig_tdom, use_container_width=True)

            best = tdom_stats["avg_return"].idxmax()
            worst = tdom_stats["avg_return"].idxmin()
            st.caption(
                f"📊 Bester TDoM: **{best}** ({tdom_stats.loc[best, 'avg_return']:+.4f}%) · "
                f"Schlechtester: **{worst}** ({tdom_stats.loc[worst, 'avg_return']:+.4f}%) · "
                f"[→ Vollständige TDoM-Analyse](18_📅_TDOM_Analyse)"
            )
        else:
            st.caption("TDoM-Daten nicht verfügbar.")
    except Exception:
        st.caption("TDoM-Modul nicht geladen.")

    # ── TDOY Platzhalter ──
    st.markdown("")
    render_premium_placeholder(
        "TDOY-Analyse",
        "Trading Day of Year — Rendite nach Handelstag · Coming Soon · Premium"
    )

    # ── Disclaimer ───────────────────────────────────
    st.markdown("---")
    st.caption(
        "⚠️ _Historische Muster sind kein Indikator für zukünftige Ergebnisse. "
        "Keine Anlageberatung. Alle Angaben ohne Gewähr._"
    )


main()
