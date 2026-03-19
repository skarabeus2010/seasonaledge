"""
SeasonalEdge — Market Scanner
==============================
Scannt alle Ticker und rankt nach KI Seasonal Score.
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
from shared.symbols import SYMBOLS, get_display_name
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.ki_score import scan_tickers

# ── Page Config ───────────────────────────────────────
st.set_page_config(
    page_title="Market Scanner — SeasonalEdge",
    page_icon="🔍",
    layout="wide",
)

# ── Kategorien aus SYMBOLS extrahieren ────────────────
ALL_KATEGORIEN = sorted(set(
    info.get("kategorie", "Sonstige") for info in SYMBOLS.values()
))


def score_color(score: float) -> str:
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


def render_top_cards(results: list[dict], title: str, color: str, n: int = 5):
    """Rendert Top-N Karten (Bullish oder Bearish)."""
    st.markdown(f"#### {title}")
    items = results[:n]
    if not items:
        st.caption("Keine Ergebnisse")
        return

    cols = st.columns(min(len(items), 5))
    for i, item in enumerate(items):
        with cols[i]:
            emoji = signal_emoji(item["signal"])
            st.markdown(f"""
            <div style="background:{SE_COLORS['surface']};border:2px solid {color};
                        border-radius:14px;padding:1rem;text-align:center;min-height:160px;">
                <div style="font-size:1.6rem;font-weight:900;color:{color};">
                    {item['score']}
                </div>
                <div style="font-size:0.7rem;color:{SE_COLORS['text_dim']};margin-bottom:0.4rem;">
                    /10
                </div>
                <div style="font-size:0.95rem;font-weight:700;color:{SE_COLORS['text_primary']};">
                    {item['ticker']}
                </div>
                <div style="font-size:0.72rem;color:{SE_COLORS['text_muted']};margin-bottom:0.3rem;">
                    {item['name'][:20]}
                </div>
                <div style="font-size:0.8rem;color:{color};">
                    {emoji} {item['signal']}
                </div>
                <div style="font-size:0.7rem;color:{SE_COLORS['text_dim']};margin-top:0.2rem;">
                    WR: {item['win_rate']:.0f}% · Ø {item['avg_return']:+.1f}%
                </div>
            </div>
            """, unsafe_allow_html=True)


def build_category_heatmap(results: list[dict]) -> go.Figure:
    """Heatmap: Kategorien × Ticker mit Score als Farbe."""
    # Gruppiere nach Kategorie
    cat_data = {}
    for r in results:
        cat = r["kategorie"]
        if cat not in cat_data:
            cat_data[cat] = []
        cat_data[cat].append(r)

    if not cat_data:
        return go.Figure()

    # Maximal 15 Ticker pro Kategorie
    max_cols = max(len(v) for v in cat_data.values())
    max_cols = min(max_cols, 15)

    categories = sorted(cat_data.keys())
    z_values = []
    hover_texts = []
    x_labels = [f"#{i+1}" for i in range(max_cols)]

    for cat in categories:
        items = sorted(cat_data[cat], key=lambda x: x["score"], reverse=True)
        row_z = []
        row_hover = []
        for i in range(max_cols):
            if i < len(items):
                row_z.append(items[i]["score"])
                row_hover.append(
                    f"{items[i]['ticker']}<br>"
                    f"{items[i]['name']}<br>"
                    f"Score: {items[i]['score']}<br>"
                    f"Signal: {items[i]['signal']}"
                )
            else:
                row_z.append(None)
                row_hover.append("")
        z_values.append(row_z)
        hover_texts.append(row_hover)

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=categories,
        text=hover_texts,
        hovertemplate="%{text}<extra></extra>",
        colorscale=[
            [0, "#ff4757"],
            [0.35, "#ff4757"],
            [0.5, SE_COLORS["accent_warm"]],
            [0.65, SE_COLORS["accent_warm"]],
            [1, SE_COLORS["positive"]],
        ],
        zmin=0, zmax=10,
        colorbar=dict(
            title="Score",
            titlefont=dict(color=SE_COLORS["text_muted"]),
            tickfont=dict(color=SE_COLORS["text_muted"]),
        ),
    ))

    fig = apply_se_heatmap_theme(fig, title="KI Score nach Kategorie", height=max(300, len(categories) * 45))
    return fig


# ── Hauptseite ────────────────────────────────────────

def main():
    # ── Sidebar ──
    with st.sidebar:
        st.markdown("### 🔍 Market Scanner")

        selected_cats = st.multiselect(
            "Kategorien",
            options=ALL_KATEGORIEN,
            default=ALL_KATEGORIEN,
            key="scanner_cats",
        )

        years_back = st.slider(
            "📅 Jahre zurück", 5, 30, 20, key="scanner_years"
        )

        scan_button = st.button(
            "🔍 Scan starten",
            type="primary",
            use_container_width=True,
            key="scanner_start",
        )

        st.markdown("---")
        st.caption(
            "Quick-Mode: Kein Prophet, schnelle "
            "Korrelation statt DTW (~1-2s/Ticker)"
        )

    # ── Header ──
    st.markdown("## 🔍 Market Scanner")
    current_month = MONTH_NAMES_DE[datetime.now().month - 1]
    st.caption(f"Scannt alle Ticker und rankt nach KI Seasonal Score · {current_month} {datetime.now().year}")

    # ── Scan starten ──
    if scan_button:
        # Filter Ticker
        filtered_tickers = [
            t for t, info in SYMBOLS.items()
            if info.get("kategorie", "Sonstige") in selected_cats
        ]

        if not filtered_tickers:
            st.warning("Keine Ticker in den gewählten Kategorien.")
            st.stop()

        st.markdown(f"**Scanne {len(filtered_tickers)} Ticker...**")

        # Progress
        progress_bar = st.progress(0)
        status_text = st.empty()

        def update_progress(i, total):
            if total > 0:
                progress_bar.progress(i / total)
                if i < total:
                    ticker_name = filtered_tickers[i] if i < len(filtered_tickers) else ""
                    status_text.text(f"Scanne {ticker_name} ({i+1}/{total})...")
                else:
                    status_text.text("✅ Scan abgeschlossen!")

        results = scan_tickers(
            filtered_tickers,
            years_back=years_back,
            progress_callback=update_progress,
            quick_mode=True,
        )

        progress_bar.empty()
        status_text.empty()

        st.session_state["scanner_results"] = results
        st.session_state["scanner_count"] = len(filtered_tickers)

    # ── Ergebnisse anzeigen ──
    results = st.session_state.get("scanner_results")
    if not results:
        st.info("👆 Klicke **Scan starten** um alle Ticker zu analysieren.")
        st.stop()

    total_scanned = st.session_state.get("scanner_count", len(results))

    # KPIs
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.metric("Gescannt", f"{len(results)}/{total_scanned}")
    with kpi_cols[1]:
        bullish = len([r for r in results if r["signal"] == "Bullish"])
        st.metric("🟢 Bullish", bullish)
    with kpi_cols[2]:
        neutral = len([r for r in results if r["signal"] == "Neutral"])
        st.metric("🟡 Neutral", neutral)
    with kpi_cols[3]:
        bearish = len([r for r in results if r["signal"] == "Bearish"])
        st.metric("🔴 Bearish", bearish)
    with kpi_cols[4]:
        avg_score = np.mean([r["score"] for r in results])
        st.metric("Ø Score", f"{avg_score:.1f}")

    st.markdown("---")

    # Top/Bottom Karten
    col_bull, col_bear = st.columns(2)
    with col_bull:
        bullish_results = [r for r in results if r["signal"] == "Bullish"]
        render_top_cards(bullish_results, "🟢 Top 5 Bullish", SE_COLORS["positive"])

    with col_bear:
        bearish_results = sorted(
            [r for r in results if r["signal"] == "Bearish"],
            key=lambda x: x["score"]
        )
        render_top_cards(bearish_results, "🔴 Top 5 Bearish", SE_COLORS["negative"])

    st.markdown("---")

    # ── Vollständige Tabelle ──
    st.markdown("### 📋 Alle Ergebnisse")

    table_rows = []
    for r in results:
        table_rows.append({
            "Ticker": r["ticker"],
            "Name": r["name"][:25],
            "Kategorie": r["kategorie"],
            "KI-Score": r["score"],
            "Signal": f"{signal_emoji(r['signal'])} {r['signal']}",
            "Win-Rate (%)": round(r["win_rate"], 1),
            "Ø Rendite (%)": round(r["avg_return"], 2),
            "Abweichung": round(r["deviation"], 3),
        })

    df_table = pd.DataFrame(table_rows)

    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "KI-Score": st.column_config.ProgressColumn(
                "KI-Score",
                min_value=0,
                max_value=10,
                format="%.1f",
            ),
            "Win-Rate (%)": st.column_config.NumberColumn(
                "Win-Rate (%)",
                format="%.1f%%",
            ),
            "Ø Rendite (%)": st.column_config.NumberColumn(
                "Ø Rendite (%)",
                format="%+.2f%%",
            ),
        },
        height=min(len(table_rows) * 38 + 40, 600),
    )

    # ── Kategorie Heatmap ──
    st.markdown("---")
    st.markdown("### 🗺️ Score Heatmap nach Kategorie")

    fig_heatmap = build_category_heatmap(results)
    st.plotly_chart(fig_heatmap, use_container_width=True)

    # ── Export ──
    with st.expander("📥 Ergebnisse exportieren"):
        csv = df_table.to_csv(index=False)
        st.download_button(
            "CSV herunterladen",
            csv,
            f"seasonaledge_scanner_{datetime.now().strftime('%Y%m%d')}.csv",
            "text/csv",
        )

    # ── Disclaimer ──
    st.markdown("---")
    st.caption(
        "⚠️ _Der Market Scanner basiert auf historischen Mustern. "
        "Quick-Mode verwendet vereinfachte Berechnung (Korrelation statt DTW, kein Prophet). "
        "Keine Anlageberatung._"
    )


main()
