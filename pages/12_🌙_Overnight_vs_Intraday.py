# ============================================================
#  SeasonalEdge — Page 12: Overnight vs. Intraday Saisonalität
#  Vergleicht Close→Open (Overnight) vs. Open→Close (Intraday)
# ============================================================

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
from plotly.subplots import make_subplots

from shared.yahoo_downloader import download_data
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS

# ── Farben ────────────────────────────────────────────────────────────────────
COL_OVERNIGHT = "#60a5fa"   # Blau  — Nacht / Gap
COL_INTRADAY  = "#f97316"   # Orange — Tag / Session
COL_TOTAL     = "#a3e635"   # Grün  — Close→Close gesamt

WEEKDAY_LABELS = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
MONTH_LABELS   = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]


# ── Hilfsfunktionen ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def load_and_compute(ticker: str, years: int) -> pd.DataFrame | None:
    """Lädt OHLC-Daten und berechnet die 3 Return-Komponenten."""
    try:
        df_raw = download_data(ticker, period="max")
        if df_raw is None or df_raw.empty:
            return None

        # Sicherstellen dass Open vorhanden
        needed = {"Open", "Close"}
        if not needed.issubset(df_raw.columns):
            return None

        df = df_raw[["Open", "Close"]].copy().dropna()

        # Zeitraum-Filter
        cutoff = df.index.max() - pd.DateOffset(years=years)
        df = df[df.index >= cutoff]

        if len(df) < 50:
            return None

        # Returns berechnen (in Prozent)
        # Overnight: Close[t-1] → Open[t]  (Gap über Nacht)
        df["overnight_ret"] = (df["Open"] / df["Close"].shift(1) - 1) * 100
        # Intraday:  Open[t]  → Close[t]   (Session-Return)
        df["intraday_ret"]  = (df["Close"] / df["Open"] - 1) * 100
        # Total:     Close[t-1] → Close[t] (Standard Close-to-Close)
        df["total_ret"]     = (df["Close"] / df["Close"].shift(1) - 1) * 100

        df = df.dropna()
        df["month"]   = df.index.month
        df["weekday"] = df.index.weekday   # 0=Mo … 4=Fr
        df["year"]    = df.index.year
        df["doy"]     = df.index.dayofyear

        return df

    except Exception as e:
        st.error(f"Fehler beim Laden: {e}")
        return None


def bar_stats(series: pd.Series) -> dict:
    """Ø Rendite, Win-Rate, Std."""
    s = series.dropna()
    return {
        "mean":     s.mean(),
        "win_rate": (s > 0).mean() * 100,
        "std":      s.std(),
        "n":        len(s),
    }


def color_bar(val: float, base_color: str, alpha_pos=0.85, alpha_neg=0.55) -> str:
    alpha = alpha_pos if val >= 0 else alpha_neg
    r = int(base_color[1:3], 16)
    g = int(base_color[3:5], 16)
    b = int(base_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ── Monatschart ──────────────────────────────────────────────────────────────

def build_monthly_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.65, 0.35],
        subplot_titles=("Ø Rendite pro Monat (%)", "Win-Rate (%)"),
        vertical_spacing=0.12,
    )

    ret_cols = {
        "Overnight (C→O)": ("overnight_ret", COL_OVERNIGHT),
        "Intraday (O→C)":  ("intraday_ret",  COL_INTRADAY),
        "Total (C→C)":     ("total_ret",      COL_TOTAL),
    }

    x = MONTH_LABELS
    bar_width = 0.25
    offsets = [-bar_width, 0, bar_width]

    for idx, (label, (col, color)) in enumerate(ret_cols.items()):
        means     = [bar_stats(df[df["month"] == m+1][col])["mean"]     for m in range(12)]
        win_rates = [bar_stats(df[df["month"] == m+1][col])["win_rate"] for m in range(12)]
        bar_colors = [color_bar(v, color) for v in means]

        fig.add_trace(go.Bar(
            name=label,
            x=[i + offsets[idx] for i in range(12)],
            y=means,
            marker_color=bar_colors,
            marker_line_color=color,
            marker_line_width=1,
            width=bar_width,
            legendgroup=label,
            showlegend=True,
            hovertemplate=f"<b>{label}</b><br>%{{text}}<br>Ø: %{{y:.3f}}%<extra></extra>",
            text=x,
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            name=label,
            x=list(range(12)),
            y=win_rates,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=6),
            legendgroup=label,
            showlegend=False,
            hovertemplate=f"<b>{label}</b><br>Win-Rate: %{{y:.1f}}%<extra></extra>",
        ), row=2, col=1)

    fig = apply_se_theme(fig, title=f"{ticker} — Overnight vs. Intraday nach Monat", height=560)
    fig.update_xaxes(
        tickvals=list(range(12)),
        ticktext=MONTH_LABELS,
        row=1, col=1,
    )
    fig.update_xaxes(
        tickvals=list(range(12)),
        ticktext=MONTH_LABELS,
        row=2, col=1,
    )
    fig.add_hline(y=0,  line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_hline(y=50, line_dash="dot",  line_color="gray", row=2, col=1)
    fig.update_yaxes(title_text="Rendite (%)",  row=1, col=1)
    fig.update_yaxes(title_text="Win-Rate (%)", row=2, col=1, range=[30, 70])

    return fig


# ── Wochentag-Chart ──────────────────────────────────────────────────────────

def build_weekday_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.65, 0.35],
        subplot_titles=("Ø Rendite pro Wochentag (%)", "Win-Rate (%)"),
        vertical_spacing=0.12,
    )

    ret_cols = {
        "Overnight (C→O)": ("overnight_ret", COL_OVERNIGHT),
        "Intraday (O→C)":  ("intraday_ret",  COL_INTRADAY),
        "Total (C→C)":     ("total_ret",      COL_TOTAL),
    }

    bar_width = 0.25
    offsets = [-bar_width, 0, bar_width]

    for idx, (label, (col, color)) in enumerate(ret_cols.items()):
        means     = [bar_stats(df[df["weekday"] == wd][col])["mean"]     for wd in range(5)]
        win_rates = [bar_stats(df[df["weekday"] == wd][col])["win_rate"] for wd in range(5)]
        bar_colors = [color_bar(v, color) for v in means]

        fig.add_trace(go.Bar(
            name=label,
            x=[i + offsets[idx] for i in range(5)],
            y=means,
            marker_color=bar_colors,
            marker_line_color=color,
            marker_line_width=1,
            width=bar_width,
            legendgroup=label,
            showlegend=True,
            hovertemplate=f"<b>{label}</b><br>%{{text}}<br>Ø: %{{y:.3f}}%<extra></extra>",
            text=WEEKDAY_LABELS,
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            name=label,
            x=list(range(5)),
            y=win_rates,
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=6),
            legendgroup=label,
            showlegend=False,
            hovertemplate=f"<b>{label}</b><br>Win-Rate: %{{y:.1f}}%<extra></extra>",
        ), row=2, col=1)

    fig = apply_se_theme(fig, title=f"{ticker} — Overnight vs. Intraday nach Wochentag", height=520)
    fig.update_xaxes(tickvals=list(range(5)), ticktext=WEEKDAY_LABELS, row=1, col=1)
    fig.update_xaxes(tickvals=list(range(5)), ticktext=WEEKDAY_LABELS, row=2, col=1)
    fig.add_hline(y=0,  line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_hline(y=50, line_dash="dot",  line_color="gray", row=2, col=1)
    fig.update_yaxes(title_text="Rendite (%)",  row=1, col=1)
    fig.update_yaxes(title_text="Win-Rate (%)", row=2, col=1, range=[30, 70])

    return fig


# ── Kumulierter Jahreschart ───────────────────────────────────────────────────

def build_cumulative_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Kumulierter Return Overnight vs. Intraday über das Jahr (DOY-normiert)."""
    fig = go.Figure()

    ret_cols = {
        "Overnight (C→O)": ("overnight_ret", COL_OVERNIGHT),
        "Intraday (O→C)":  ("intraday_ret",  COL_INTRADAY),
        "Total (C→C)":     ("total_ret",      COL_TOTAL),
    }

    # Gruppierung nach DOY — Ø über alle Jahre
    for label, (col, color) in ret_cols.items():
        doy_mean = df.groupby("doy")[col].mean()
        cum = (1 + doy_mean / 100).cumprod() * 100 - 100   # kumuliert in %

        fig.add_trace(go.Scatter(
            name=label,
            x=doy_mean.index,
            y=cum.values,
            mode="lines",
            line=dict(color=color, width=2.5),
            hovertemplate=f"<b>{label}</b><br>DOY: %{{x}}<br>Kumuliert: %{{y:.2f}}%<extra></extra>",
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig = apply_se_theme(fig, title=f"{ticker} — Kumulierter Jahresverlauf: Overnight vs. Intraday", height=420)
    return fig


# ── Statistik-Tabelle ─────────────────────────────────────────────────────────

def render_stats_table(df: pd.DataFrame):
    """Übersichts-Tabelle: Overnight vs. Intraday vs. Total."""
    rows = []
    for label, col in [
        ("🌙 Overnight (C→O)", "overnight_ret"),
        ("☀️ Intraday (O→C)",  "intraday_ret"),
        ("📊 Total (C→C)",     "total_ret"),
    ]:
        s = df[col].dropna()
        rows.append({
            "Return-Typ":   label,
            "Ø Return %":   f"{s.mean():+.4f}%",
            "Win-Rate":     f"{(s > 0).mean()*100:.1f}%",
            "Std.Abw.":     f"{s.std():.3f}%",
            "Summe %":      f"{s.sum():+.1f}%",
            "Anzahl Tage":  len(s),
        })

    st.dataframe(
        pd.DataFrame(rows).set_index("Return-Typ"),
        use_container_width=True,
    )


# ── Heatmap Monat × Wochentag ─────────────────────────────────────────────────

def build_heatmap(df: pd.DataFrame, col: str, title: str) -> go.Figure:
    matrix = np.zeros((5, 12))
    for wd in range(5):
        for m in range(1, 13):
            subset = df[(df["weekday"] == wd) & (df["month"] == m)][col]
            matrix[wd, m-1] = subset.mean() if len(subset) > 0 else np.nan

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=MONTH_LABELS,
        y=WEEKDAY_LABELS,
        colorscale="RdYlGn",
        zmid=0,
        text=[[f"{v:+.3f}%" if not np.isnan(v) else "" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(size=10),
        hovertemplate="<b>%{y} / %{x}</b><br>Ø: %{z:.3f}%<extra></extra>",
        colorbar=dict(title="Ø %"),
    ))
    fig = apply_se_theme(fig, title="", height=280)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN UI
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="Overnight vs. Intraday", page_icon="🌙", layout="wide")

st.title("🌙 Overnight vs. Intraday Saisonalität")
st.caption(
    "Trennt den täglichen Return in zwei Komponenten: "
    "**Overnight** (Close→Open, außerbörslich) und **Intraday** (Open→Close, Handelssession). "
    "Zeigt welcher Anteil der saisonalen Performance wann entsteht."
)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Einstellungen")
    ticker  = st.text_input("Ticker", value="SPY").upper().strip()
    years   = st.slider("Zeitraum (Jahre)", min_value=3, max_value=30, value=10, step=1)
    st.markdown("---")
    st.markdown(
        "**🌙 Overnight** = Close[t−1] → Open[t]  \n"
        "**☀️ Intraday** = Open[t] → Close[t]  \n"
        "**📊 Total** = Close[t−1] → Close[t]"
    )
    st.markdown("---")
    show_heatmap = st.checkbox("Heatmap Monat × Wochentag", value=False)
    show_cumulative = st.checkbox("Kumulierter Jahresverlauf", value=True)

# ── Daten laden ───────────────────────────────────────────────────────────────
with st.spinner(f"Lade {ticker}…"):
    df = load_and_compute(ticker, years)

if df is None:
    st.error(f"Keine Daten für **{ticker}** verfügbar. Bitte anderen Ticker versuchen.")
    st.stop()

# Infoleiste
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ticker",      ticker)
c2.metric("Zeitraum",    f"{years} Jahre")
c3.metric("Handelstage", f"{len(df):,}")
c4.metric(
    "Overnight Anteil am Total-Return",
    f"{df['overnight_ret'].sum() / (df['overnight_ret'].sum() + df['intraday_ret'].sum()) * 100:.0f}%",
    help="Wie viel % des gesamten kumulierten Returns entfällt auf die Overnight-Komponente",
)

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "📆 Nach Monat",
    "📅 Nach Wochentag",
    "📊 Statistik & Übersicht",
])

with tab1:
    st.plotly_chart(build_monthly_chart(df, ticker), use_container_width=True)

    if show_heatmap:
        st.markdown("#### Heatmap: Ø Return nach Monat × Wochentag")
        col_sel = st.selectbox(
            "Return-Typ für Heatmap",
            ["overnight_ret", "intraday_ret", "total_ret"],
            format_func=lambda x: {"overnight_ret": "🌙 Overnight", "intraday_ret": "☀️ Intraday", "total_ret": "📊 Total"}[x],
            key="hm_month",
        )
        st.plotly_chart(
            build_heatmap(df, col_sel, f"Heatmap — {ticker}"),
            use_container_width=True,
        )

    if show_cumulative:
        st.plotly_chart(build_cumulative_chart(df, ticker), use_container_width=True)

with tab2:
    st.plotly_chart(build_weekday_chart(df, ticker), use_container_width=True)

    if show_heatmap:
        st.markdown("#### Heatmap: Ø Return nach Monat × Wochentag")
        col_sel2 = st.selectbox(
            "Return-Typ für Heatmap",
            ["overnight_ret", "intraday_ret", "total_ret"],
            format_func=lambda x: {"overnight_ret": "🌙 Overnight", "intraday_ret": "☀️ Intraday", "total_ret": "📊 Total"}[x],
            key="hm_wd",
        )
        st.plotly_chart(
            build_heatmap(df, col_sel2, f"Heatmap — {ticker}"),
            use_container_width=True,
        )

with tab3:
    st.subheader("📊 Gesamtstatistik")
    render_stats_table(df)

    st.markdown("---")
    st.subheader("🔍 Was bedeutet das?")
    ov_sum  = df["overnight_ret"].sum()
    id_sum  = df["intraday_ret"].sum()
    tot_sum = df["total_ret"].sum()
    ov_pct  = ov_sum / tot_sum * 100 if tot_sum != 0 else 0

    if ov_pct > 60:
        st.success(
            f"**{ticker}** generiert den Großteil seines Returns ({ov_pct:.0f}%) **außerbörslich** (Overnight). "
            "Das bedeutet: Wer nur während der Handelssession investiert ist, verpasst den Hauptteil der Performance. "
            "Gap-Trader und Overnight-Hold-Strategien haben hier einen strukturellen Vorteil."
        )
    elif ov_pct < 40:
        st.info(
            f"**{ticker}** generiert den Großteil seines Returns ({100-ov_pct:.0f}%) **während der Handelssession** (Intraday). "
            "Intraday-Strategien und Day-Trader haben hier einen strukturellen Vorteil gegenüber reinen Overnight-Haltern."
        )
    else:
        st.info(
            f"**{ticker}** verteilt seinen Return relativ gleichmäßig zwischen Overnight ({ov_pct:.0f}%) "
            f"und Intraday ({100-ov_pct:.0f}%). Kein klarer struktureller Bias."
        )

    # Bester/Schlechtester Monat pro Typ
    st.markdown("---")
    st.subheader("🏆 Top & Flop Monate")
    colA, colB, colC = st.columns(3)
    for col_widget, ret_col, emoji, label in [
        (colA, "overnight_ret", "🌙", "Overnight"),
        (colB, "intraday_ret",  "☀️", "Intraday"),
        (colC, "total_ret",     "📊", "Total"),
    ]:
        monthly = df.groupby("month")[ret_col].mean()
        best  = monthly.idxmax()
        worst = monthly.idxmin()
        with col_widget:
            st.markdown(f"**{emoji} {label}**")
            st.success(f"Best: **{MONTH_LABELS[best-1]}** ({monthly[best]:+.3f}%)")
            st.error(  f"Worst: **{MONTH_LABELS[worst-1]}** ({monthly[worst]:+.3f}%)")

st.markdown("---")
st.caption(
    "💡 **Hinweis:** Open-Kurse bei Yahoo Finance sind nicht immer perfekt split-adjustiert. "
    "Für präzise Overnight-Analysen empfiehlt sich die Verwendung adjustierter Open-Daten. "
    "Die Trends sind dennoch statistisch aussagekräftig über längere Zeiträume."
)
