"""
SeasonAlpha - Weekday Performance
====================================
Wochentags-Performance (Mo-Fr) mit verschiedenen Rendite-Berechnungen,
Praesidentenzyklus-Filter und Monat x Wochentag Heatmap.
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

st.set_page_config(page_title="Wochentagseffekt Aktien & ETFs – SeasonAlpha", page_icon="📅", layout="wide")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

from shared.ticker_select import ticker_select
from shared.constants import (
    DEFAULT_TICKER, DEFAULT_YEARS, MONTH_NAMES_DE, CYCLE_COLORS,
    SE_COLORS, SE_HEATMAP_COLORSCALE, SE_HEATMAP_TEXT_COLOR,
)
from shared.data import download_data
from shared.charts import apply_se_theme, apply_se_heatmap_theme
from shared.calculations import get_presidential_cycle_year

from shared.we_are_here import annotation as wah_annotation, rect as wah_rect, vline as wah_vline
from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()


# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def _heatmap_text_color(value, zmid=0, max_abs=None):
    """Gibt dunkle Schriftfarbe zurueck wenn Zelle zu hell (hohe positive Werte = helles Gruen)."""
    if max_abs is None:
        max_abs = 1
    intensity = abs(value - zmid) / max_abs if max_abs > 0 else 0
    # Helle Gruen-Zellen brauchen frueher dunkle Schrift
    if value > zmid and intensity > 0.3:
        return "#1a1a2e"
    # Dunkle Rot-Zellen brauchen hellere Schrift
    if value < zmid and intensity > 0.6:
        return "#f0f0f0"
    return "#FFFFFF"


def _heatmap_text_colors(z_data, zmid=0):
    """Generiert adaptive Textfarben-Matrix fuer eine Heatmap."""
    flat = [v for row in z_data for v in row]
    max_abs = max(abs(v - zmid) for v in flat) if flat else 1
    return [[_heatmap_text_color(v, zmid, max_abs) for v in row] for row in z_data]


def _add_heatmap_annotations(fig, z_data, x_labels, y_labels, zmid=0, fmt="+.2f", suffix="%"):
    """Fuegt Text-Annotations mit adaptiver Farbe zu einer Heatmap hinzu."""
    flat = [v for row in z_data for v in row]
    max_abs = max(abs(v - zmid) for v in flat) if flat else 1
    for i, y_label in enumerate(y_labels):
        for j, x_label in enumerate(x_labels):
            val = z_data[i][j]
            color = _heatmap_text_color(val, zmid, max_abs)
            fig.add_annotation(
                x=x_label, y=y_label,
                text=f"{val:{fmt}}{suffix}",
                showarrow=False,
                font=dict(size=10, color=color),
            )


# ══════════════════════════════════════════════════════════════
# KONSTANTEN
# ══════════════════════════════════════════════════════════════

WEEKDAY_LABELS_5 = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag"]
WEEKDAY_LABELS_7 = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
WEEKDAY_LABELS_SHORT_5 = ["Mo", "Di", "Mi", "Do", "Fr"]
WEEKDAY_LABELS_SHORT_7 = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

# Dynamisch: wird in main() gesetzt basierend auf Daten
WEEKDAY_LABELS = WEEKDAY_LABELS_5
WEEKDAY_LABELS_SHORT = WEEKDAY_LABELS_SHORT_5

RETURN_MODES = {
    "Close → Close (t0 → t1)": {
        "desc": "Schlusskurs heute vs. Schlusskurs morgen",
        "calc": lambda df: (df["Close"].shift(-1) / df["Close"] - 1) * 100
    },
    "Close → Open (t0 → t1)": {
        "desc": "Schlusskurs heute vs. Eröffnung morgen (Overnight)",
        "calc": lambda df: (df["Open"].shift(-1) / df["Close"] - 1) * 100
    },
    "Open → Close (t0)": {
        "desc": "Eröffnung vs. Schluss am selben Tag (Intraday)",
        "calc": lambda df: (df["Close"] / df["Open"] - 1) * 100
    },
    "Open → Close (t0 → t1)": {
        "desc": "Eröffnung heute vs. Schluss morgen",
        "calc": lambda df: (df["Close"].shift(-1) / df["Open"] - 1) * 100
    },
}


# ══════════════════════════════════════════════════════════════
# BERECHNUNG
# ══════════════════════════════════════════════════════════════

def calculate_weekday_stats(df, return_mode, years_back,
                            filter_mode="Kein Filter",
                            sma_days=200, rsi_days=14, rsi_threshold=30,
                            cycle_filter=None):
    """
    Berechne Weekday-Performance mit waehlbarem Rendite-Modus und Filtern.

    Args:
        df: Raw DataFrame mit Open, Close, High, Low (DatetimeIndex)
        return_mode: Key aus RETURN_MODES
        years_back: Anzahl Jahre Lookback
        filter_mode: "Kein Filter", "Trendfilter (SMA)", "OBOS-Filter (RSI)"
        sma_days: Tage fuer SMA-Berechnung
        rsi_days: Tage fuer RSI-Berechnung
        rsi_threshold: RSI-Schwelle (kaufen wenn RSI darunter)
        cycle_filter: Liste von Praesidentenzyklus-Labels oder None

    Returns:
        dict mit by_weekday, by_month_weekday, filtered_count, total_count
    """
    df = df.copy()

    # ── Zeitraum filtern ──
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if len(df) < 20:
        return None

    # ── Praesidentenzyklus-Filter ──
    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])
        if len(df) < 20:
            return None

    # ── Rendite berechnen ──
    df["wd_return"] = RETURN_MODES[return_mode]["calc"](df)

    # ── Wochentag und Monat ──
    df["weekday"] = df.index.weekday  # 0=Mo, 4=Fr
    df["month"] = df.index.month

    # ── Filter anwenden ──
    df["filter_pass"] = True
    total_count = len(df)

    if filter_mode == "Trendfilter (SMA)":
        df["sma"] = df["Close"].rolling(sma_days, min_periods=sma_days).mean()
        df["filter_pass"] = df["Close"].shift(1) > df["sma"].shift(1)

    elif filter_mode == "OBOS-Filter (RSI)":
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(rsi_days).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_days).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["filter_pass"] = df["rsi"].shift(1) < rsi_threshold

    # Crypto handelt 7 Tage → Sa+So behalten; Aktien nur Mo-Fr
    _has_weekend = (df["weekday"] >= 5).any()
    if not _has_weekend:
        df = df[(df["weekday"] <= 4) & df["wd_return"].notna()]
    else:
        df = df[df["wd_return"].notna()]

    # Gefilterte Daten
    df_filtered = df[df["filter_pass"]].copy()
    filtered_count = len(df_filtered)

    if filtered_count < 10:
        return None

    # ── Statistik pro Wochentag ──
    _n_weekdays = 7 if _has_weekend else 5
    by_weekday = {}
    for wd in range(_n_weekdays):
        subset = df_filtered[df_filtered["weekday"] == wd]["wd_return"]
        if len(subset) == 0:
            by_weekday[wd] = {"avg": 0, "median": 0, "std": 0, "count": 0,
                              "win_rate": 0, "returns": []}
            continue

        wins = (subset > 0).sum()
        by_weekday[wd] = {
            "avg": subset.mean(),
            "median": subset.median(),
            "std": subset.std(),
            "count": len(subset),
            "win_rate": wins / len(subset) * 100,
            "returns": subset.tolist()
        }

    # ── Statistik pro Monat x Wochentag ──
    by_month_weekday = {}
    for month in range(1, 13):
        for wd in range(_n_weekdays):
            subset = df_filtered[(df_filtered["month"] == month) &
                                 (df_filtered["weekday"] == wd)]["wd_return"]
            if len(subset) == 0:
                by_month_weekday[(month, wd)] = {"avg": 0, "count": 0, "win_rate": 0}
                continue

            wins = (subset > 0).sum()
            by_month_weekday[(month, wd)] = {
                "avg": subset.mean(),
                "count": len(subset),
                "win_rate": wins / len(subset) * 100
            }

    return {
        "by_weekday": by_weekday,
        "by_month_weekday": by_month_weekday,
        "filtered_count": filtered_count,
        "total_count": total_count,
        "n_weekdays": _n_weekdays,
        "is_crypto": _has_weekend,
    }


# ══════════════════════════════════════════════════════════════
# CHARTS
# ══════════════════════════════════════════════════════════════

def build_weekday_bar_chart(stats, ticker, return_mode):
    """Balkendiagramm: Ø Rendite + Win Rate pro Wochentag."""

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Ø Tagesrendite (%)", "Win Rate (%)"),
        horizontal_spacing=0.12
    )

    wd_data = stats["by_weekday"]
    avgs = [wd_data[wd]["avg"] for wd in range(len(WEEKDAY_LABELS))]
    win_rates = [wd_data[wd]["win_rate"] for wd in range(len(WEEKDAY_LABELS))]
    counts = [wd_data[wd]["count"] for wd in range(len(WEEKDAY_LABELS))]

    # Farben: SE positiv/negativ
    bar_colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]

    # ── Rendite-Balken ──
    fig.add_trace(
        go.Bar(
            x=WEEKDAY_LABELS,
            y=avgs,
            marker_color=bar_colors,
            text=[f"{v:+.2f}%<br>n={c}" for v, c in zip(avgs, counts)],
            textposition="outside",
            textfont=dict(size=11),
            hovertemplate="<b>%{x}</b><br>Ø Rendite: %{y:+.2f}%<extra></extra>",
            showlegend=False
        ),
        row=1, col=1
    )

    # ── Win Rate Balken ──
    wr_colors = [SE_COLORS["positive"] if v >= 50 else SE_COLORS["negative"] for v in win_rates]
    fig.add_trace(
        go.Bar(
            x=WEEKDAY_LABELS,
            y=win_rates,
            marker_color=wr_colors,
            text=[f"{v:.1f}%" for v in win_rates],
            textposition="outside",
            textfont=dict(size=11),
            hovertemplate="<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>",
            showlegend=False
        ),
        row=1, col=2
    )

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=1, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=1, col=2)

    # We are here! — gelber Rahmen um aktuellen Wochentag
    today_wd = datetime.now().weekday()  # Gelber Rahmen immer sichtbar
    if 0 <= today_wd < len(WEEKDAY_LABELS):
        today_label = WEEKDAY_LABELS[today_wd]
        # Rendite-Balken
        fig.add_shape(type="rect",
            x0=today_wd - 0.4, x1=today_wd + 0.4,
            y0=0, y1=avgs[today_wd],
            line=dict(color="#FFD700", width=3),
            fillcolor="rgba(0,0,0,0)", layer="above",
            row=1, col=1)
        # Win Rate Balken
        fig.add_shape(type="rect",
            x0=today_wd - 0.4, x1=today_wd + 0.4,
            y0=0, y1=win_rates[today_wd],
            line=dict(color="#FFD700", width=3),
            fillcolor="rgba(0,0,0,0)", layer="above",
            row=1, col=2)

    mode_short = return_mode.split("(")[0].strip()
    fig = apply_se_theme(fig, title=f"{ticker} — Weekday Performance · {mode_short}", height=380)

    fig.update_yaxes(tickformat="+.2f", ticksuffix="%", row=1, col=1,
                     gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(range=[0, 100], ticksuffix="%", row=1, col=2,
                     gridcolor="rgba(255,255,255,0.06)")

    return fig


def build_heatmap(stats, ticker, return_mode=""):
    """Heatmap: Monat x Wochentag (Ø Rendite, farbcodiert).
    Nutzt das zentrale SE Heatmap-Design (wie Dekadenzyklus).
    Aktueller Monat + Wochentag wird mit gelbem Rahmen markiert.
    """

    mwd = stats["by_month_weekday"]
    now = datetime.now()
    current_month = now.month       # 1-12
    current_weekday = now.weekday() # 0=Mo, 4=Fr

    # Matrix aufbauen: Zeilen = Monate, Spalten = Wochentage
    z_values = []
    hover_texts = []

    for month in range(1, 13):
        row_z = []
        row_hover = []
        for wd in range(len(WEEKDAY_LABELS)):
            data = mwd.get((month, wd), {"avg": 0, "count": 0, "win_rate": 0})
            row_z.append(data["avg"])
            row_hover.append(
                f"<b>{MONTH_NAMES_DE[month-1]} · {WEEKDAY_LABELS[wd]}</b><br>"
                f"Ø Rendite: {data['avg']:+.2f}%<br>"
                f"Win Rate: {data['win_rate']:.0f}%<br>"
                f"n = {data['count']}"
            )
        z_values.append(row_z)
        hover_texts.append(row_hover)

    z_arr = np.array(z_values)

    fig = go.Figure(go.Heatmap(
        z=z_arr,
        x=WEEKDAY_LABELS_SHORT,
        y=MONTH_NAMES_DE,
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=0,
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>",
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color="#FFFFFF")),
            ticksuffix="%",
            tickformat="+.2f",
            tickfont=dict(color="#FFFFFF"),
        ),
    ))

    # Adaptive Textfarben (dunkel auf hellen Zellen)
    _add_heatmap_annotations(fig, z_values, WEEKDAY_LABELS_SHORT, MONTH_NAMES_DE, zmid=0, fmt="+.3f")

    _mode_label = f" · {return_mode.split('(')[0].strip()}" if return_mode else ""
    fig = apply_se_heatmap_theme(fig, title=f"{ticker} — Monat × Wochentag Heatmap{_mode_label}", height=480)
    fig.update_xaxes(side="bottom", type="category", tickformat="")
    fig.update_yaxes(autorange="reversed", type="category", tickformat="")
    # Colorbar-Ticks explizit nach Theme setzen (verhindert Float-Artefakte)
    fig.update_traces(colorbar=dict(tickformat="+.3f", ticksuffix="%"))

    # ── Gelber Rahmen um aktuelle Zelle (Monat + Wochentag) ──
    if 0 <= current_weekday <= 4:
        # x-Index = Wochentag (0-4), y-Index = Monat-1 (0-11)
        fig.add_shape(
            type="rect",
            x0=current_weekday - 0.5, x1=current_weekday + 0.5,
            y0=current_month - 1 - 0.5, y1=current_month - 1 + 0.5,
            line=dict(color="#FFD700", width=3.5),
            fillcolor="rgba(0,0,0,0)",
            layer="above",
        )

    return fig


# ══════════════════════════════════════════════════════════════
# ERWEITERTE ANALYSEN
# ══════════════════════════════════════════════════════════════

def calc_weekly_cumulative(df, years_back, cycle_filter=None):
    """Kumulierte Rendite Mo→Fr: Wie baut sich die Wochenperformance auf?"""
    df = df.copy()
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])

    df["weekday"] = df.index.weekday
    df["log_ret"] = np.log(df["Close"] / df["Close"].shift(1))
    _is_crypto = (df["weekday"] >= 5).any()
    if not _is_crypto:
        df = df[df["weekday"] <= 4]
    df = df.dropna(subset=["log_ret"])

    # Wochen gruppieren (Woche = Jahr + ISO-Woche)
    df["week_id"] = df.index.isocalendar().year.astype(str) + "_" + df.index.isocalendar().week.astype(str).str.zfill(2)

    _min_days_per_week = 5 if _is_crypto else 4
    all_curves = []
    for wid, wdf in df.groupby("week_id"):
        if len(wdf) < _min_days_per_week:
            continue
        wdf = wdf.sort_index()
        rets = wdf["log_ret"].values
        cum = np.cumsum(rets)
        curve = (np.exp(cum) - 1) * 100
        weekdays = wdf["weekday"].tolist()
        all_curves.append({"weekdays": weekdays, "curve": curve.tolist()})

    if not all_curves:
        return None, None

    # Durchschnitt pro Wochentag-Position
    wd_stats = {}
    for wd in range(len(WEEKDAY_LABELS)):
        vals = [c["curve"][c["weekdays"].index(wd)] for c in all_curves if wd in c["weekdays"]]
        if vals:
            wd_stats[wd] = {"avg": np.mean(vals), "std": np.std(vals), "n": len(vals)}

    return wd_stats, all_curves


def build_weekly_cumulative_chart(wd_stats, ticker, current_week_curve=None):
    """Linienchart: kumulierte Rendite Mo→Fr."""
    if not wd_stats:
        return None

    wds = sorted(wd_stats.keys())
    avg_curve = [wd_stats[w]["avg"] for w in wds]
    upper = [wd_stats[w]["avg"] + wd_stats[w]["std"] for w in wds]
    lower = [wd_stats[w]["avg"] - wd_stats[w]["std"] for w in wds]
    labels = [WEEKDAY_LABELS[w] for w in wds]

    fig = go.Figure()

    # Durchschnittskurve
    fig.add_trace(go.Scatter(x=labels, y=avg_curve, mode="lines+markers",
        line=dict(color="#00CED1", width=3), marker=dict(size=7, color="#00CED1"),
        name="Ø Wochenverlauf (linke Achse)",
        hovertemplate="<b>%{x}</b><br>Kum. Rendite: %{y:+.2f}%<extra></extra>"))

    # Aktueller Wochenverlauf (eigene Y-Achse rechts)
    if current_week_curve:
        cw_labels, cw_vals = current_week_curve
        fig.add_trace(go.Scatter(x=cw_labels, y=cw_vals, mode="lines+markers",
            line=dict(color="#F1C40F", width=2.5),
            marker=dict(size=8, color="#F1C40F", symbol="diamond"),
            name="Diese Woche (rechte Achse)",
            yaxis="y2",
            hovertemplate="<b>%{x}</b><br>Diese Woche: %{y:+.2f}%<extra></extra>"))

        fig.update_layout(
            yaxis2=dict(
                overlaying="y",
                side="right",
                showgrid=False,
                ticksuffix="%",
                tickformat="+.2f",
                title=None,
                tickfont=dict(color="#F1C40F", size=10),
            ),
        )

    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")

    # We are here!
    today_wd = datetime.now().weekday()  # Gelber Rahmen immer sichtbar
    if 0 <= today_wd < len(WEEKDAY_LABELS):
        today_label = WEEKDAY_LABELS[today_wd]
        if today_wd in wd_stats:
            fig.add_shape(**wah_vline(today_label))
            fig.add_annotation(**wah_annotation(
                x_val=today_label, y_val=avg_curve[wds.index(today_wd)] if today_wd in wds else 0,
                above=True, text=f"We are here! {today_label}"))

    n = wd_stats[0]["n"] if 0 in wd_stats else 0
    fig = apply_se_theme(fig, title=f"{ticker} — Kumulierter Wochenverlauf Mo→Fr ({n} Wochen)", height=380)
    return fig


def calc_current_week_curve(df):
    """Rendite-Kurve der aktuellen Woche."""
    today = pd.Timestamp(datetime.now().date())
    df = df.copy()
    df["weekday"] = df.index.weekday

    # Aktuelle Woche: letzten Montag finden
    start = today - pd.Timedelta(days=today.weekday())
    wdf = df[(df.index >= start) & (df.index <= today) & (df["weekday"] <= 4)]
    if len(wdf) < 1:
        return None

    wdf = wdf.sort_index()
    # Rendite relativ zum Close des letzten Freitags
    prev_friday = df[df.index < start].tail(1)
    if len(prev_friday) == 0:
        base = wdf["Open"].iloc[0]
    else:
        base = prev_friday["Close"].iloc[0]

    labels = [WEEKDAY_LABELS[w] for w in wdf["weekday"].tolist()]
    vals = [(c / base - 1) * 100 for c in wdf["Close"].tolist()]
    return labels, vals


def calc_overnight_intraday(df, years_back, cycle_filter=None):
    """Zerlege jeden Wochentag in Overnight (prev Close→Open) und Intraday (Open→Close)."""
    df = df.copy()
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])

    df["weekday"] = df.index.weekday
    df["overnight"] = (df["Open"] / df["Close"].shift(1) - 1) * 100
    df["intraday"] = (df["Close"] / df["Open"] - 1) * 100
    if not (df["weekday"] >= 5).any():
        df = df[df["weekday"] <= 4]
    df = df.dropna(subset=["overnight", "intraday"])

    results = {}
    for wd in range(len(WEEKDAY_LABELS)):
        sub = df[df["weekday"] == wd]
        if len(sub) < 10:
            results[wd] = {"overnight": 0, "intraday": 0, "n": 0}
            continue
        results[wd] = {
            "overnight": sub["overnight"].mean(),
            "intraday": sub["intraday"].mean(),
            "n": len(sub),
        }
    return results


def build_overnight_intraday_chart(oi_stats, ticker):
    """Gestackte Bars: Overnight + Intraday pro Wochentag."""
    wds = list(range(len(WEEKDAY_LABELS)))
    overnight = [oi_stats[w]["overnight"] for w in wds]
    intraday = [oi_stats[w]["intraday"] for w in wds]
    total = [o + i for o, i in zip(overnight, intraday)]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=WEEKDAY_LABELS, y=overnight, name="Overnight (Close→Open)",
        marker_color="#6C5CE7", text=[f"{v:+.2f}%" for v in overnight],
        textposition="inside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Overnight: %{y:+.2f}%<extra></extra>"))
    fig.add_trace(go.Bar(x=WEEKDAY_LABELS, y=intraday, name="Intraday (Open→Close)",
        marker_color="#00CEC9", text=[f"{v:+.2f}%" for v in intraday],
        textposition="inside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Intraday: %{y:+.2f}%<extra></extra>"))

    # Total-Annotations
    for i, (label, t) in enumerate(zip(WEEKDAY_LABELS, total)):
        fig.add_annotation(x=label, y=t, text=f"Σ {t:+.2f}%",
            showarrow=False, font=dict(size=10, color="#FFFFFF"),
            yshift=12 if t >= 0 else -12)

    fig.update_layout(barmode="relative")
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    # We are here!
    today_wd = datetime.now().weekday()  # Gelber Rahmen immer sichtbar
    if 0 <= today_wd < len(WEEKDAY_LABELS):
        fig.add_shape(**wah_rect(
            x0=today_wd - 0.4, x1=today_wd + 0.4,
            y0=min(0, total[today_wd]), y1=max(0, total[today_wd])))

    fig = apply_se_theme(fig, title=f"{ticker} — Overnight vs. Intraday pro Wochentag", height=400)
    return fig


def calc_consecutive_probs(df, years_back, cycle_filter=None):
    """Bedingte Wahrscheinlichkeit: Wenn Tag X positiv/negativ → was macht Tag X+1?"""
    df = df.copy()
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])

    df["weekday"] = df.index.weekday
    df["daily_ret"] = (df["Close"] / df["Close"].shift(1) - 1) * 100
    _has_weekend = (df["weekday"] >= 5).any()
    if not _has_weekend:
        df = df[df["weekday"] <= 4]
    df = df.dropna(subset=["daily_ret"])

    # Matrix: Von Wochentag X → Wochentag X+1
    _max_wd = 6 if _has_weekend else 4  # Crypto: Mo-Sa→Di-So, Aktien: Mo-Do→Di-Fr
    matrix = {}
    for from_wd in range(_max_wd + 1):  # Crypto: 0-6, Aktien: 0-4
        to_wd = (from_wd + 1) % (7 if _has_weekend else 5)
        for condition in ["pos", "neg"]:
            from_days = df[df["weekday"] == from_wd]
            key = (from_wd, to_wd, condition)
            pos_count, neg_count, total = 0, 0, 0

            for idx in from_days.index:
                ret_from = df.loc[idx, "daily_ret"]
                if condition == "pos" and ret_from <= 0:
                    continue
                if condition == "neg" and ret_from > 0:
                    continue

                # Nächsten Handelstag finden
                next_days = df[df.index > idx].head(1)
                if len(next_days) == 0:
                    continue
                next_ret = next_days["daily_ret"].iloc[0]
                total += 1
                if next_ret > 0:
                    pos_count += 1
                else:
                    neg_count += 1

            matrix[key] = {"pos_next": pos_count, "neg_next": neg_count, "total": total}

    return matrix


def build_consecutive_heatmap(matrix):
    """Heatmap: Bedingte Wahrscheinlichkeit dass Folgetag positiv ist."""
    _n_wd = len(WEEKDAY_LABELS)
    if _n_wd == 7:
        pairs = [(i, (i + 1) % 7) for i in range(7)]
        pair_labels = [f"{WEEKDAY_LABELS_SHORT[i]}→{WEEKDAY_LABELS_SHORT[(i+1)%7]}" for i in range(7)]
    else:
        pairs = [(0, 1), (1, 2), (2, 3), (3, 4)]
        pair_labels = ["Mo→Di", "Di→Mi", "Mi→Do", "Do→Fr"]

    z_data = [[], []]  # [0] = nach positivem Tag, [1] = nach negativem Tag
    hover_data = [[], []]

    for from_wd, to_wd in pairs:
        for row_idx, cond in enumerate(["pos", "neg"]):
            data = matrix.get((from_wd, to_wd, cond), {"pos_next": 0, "total": 0})
            pct = data["pos_next"] / data["total"] * 100 if data["total"] > 0 else 50
            z_data[row_idx].append(round(pct, 1))
            hover_data[row_idx].append(
                f"{WEEKDAY_LABELS_SHORT[from_wd]}{'↑' if cond == 'pos' else '↓'} → "
                f"{WEEKDAY_LABELS_SHORT[to_wd]}↑: {pct:.0f}% (n={data['total']})")

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=pair_labels,
        y=["Nach ↑ Tag", "Nach ↓ Tag"],
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=50,
        hovertext=hover_data,
        hovertemplate="%{hovertext}<extra></extra>",
        colorbar=dict(
            title=dict(text="P(↑)", font=dict(color=SE_COLORS["text_muted"], size=11)),
            ticksuffix="%", tickfont=dict(color=SE_COLORS["text_muted"], size=10)),
    ))

    _add_heatmap_annotations(fig, z_data, pair_labels, ["Nach ↑ Tag", "Nach ↓ Tag"],
                             zmid=50, fmt=".0f")

    # Gelber Rahmen um aktuelle Spalte (heutiger Wochentag-Uebergang)
    today_wd = datetime.now().weekday()  # Gelber Rahmen immer sichtbar
    if 0 <= today_wd <= 3:  # Mo-Do haben Folgetag
        fig.add_shape(type="rect",
            x0=today_wd - 0.5, x1=today_wd + 0.5,
            y0=-0.5, y1=1.5,
            line=dict(color="#FFD700", width=3.5),
            fillcolor="rgba(0,0,0,0)", layer="above")

    fig = apply_se_heatmap_theme(fig, title="Konsekutiv-Analyse: P(Folgetag positiv)", height=220)
    fig.update_yaxes(type="category", tickformat="")
    fig.update_xaxes(type="category", side="bottom", tickformat="")
    return fig


def calc_quarterly_weekday(df, years_back, cycle_filter=None):
    """Wochentag-Rendite aufgesplittet nach Quartal."""
    df = df.copy()
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])

    df["weekday"] = df.index.weekday
    df["quarter"] = df.index.quarter
    df["daily_ret"] = (df["Close"] / df["Close"].shift(1) - 1) * 100
    df = df[(df["weekday"] <= 4)].dropna(subset=["daily_ret"])

    results = {}
    for q in range(1, 5):
        for wd in range(len(WEEKDAY_LABELS)):
            sub = df[(df["quarter"] == q) & (df["weekday"] == wd)]["daily_ret"]
            results[(q, wd)] = {
                "avg": sub.mean() if len(sub) > 0 else 0,
                "n": len(sub),
                "win_rate": (sub > 0).mean() * 100 if len(sub) > 0 else 0,
            }
    return results


def build_quarterly_heatmaps(q_stats, ticker):
    """4 Mini-Heatmaps: Q1-Q4 x Mo-Fr."""
    fig = make_subplots(rows=2, cols=2,
        subplot_titles=("Q1 (Jan-Mrz)", "Q2 (Apr-Jun)", "Q3 (Jul-Sep)", "Q4 (Okt-Dez)"),
        horizontal_spacing=0.08, vertical_spacing=0.12)

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    # Sammle alle Werte fuer globale Farbskala
    all_vals = [q_stats[(q, wd)]["avg"] for q in range(1, 5) for wd in range(len(WEEKDAY_LABELS))]
    max_abs = max(abs(v) for v in all_vals) if all_vals else 1

    today_wd = datetime.now().weekday()  # Gelber Rahmen immer sichtbar
    today_q = (datetime.now().month - 1) // 3 + 1

    for q, (row, col) in zip(range(1, 5), positions):
        z_row = [q_stats[(q, wd)]["avg"] for wd in range(len(WEEKDAY_LABELS))]

        fig.add_trace(go.Heatmap(
            z=[z_row],
            x=WEEKDAY_LABELS_SHORT,
            y=[f"Q{q}"],
            colorscale=SE_HEATMAP_COLORSCALE,
            zmid=0,
            hovertemplate="<b>Q%{y} %{x}</b><br>Oe %{z:+.2f}%<extra></extra>",
            showscale=(q == 4),
            colorbar=dict(
                title=dict(text="Oe %", font=dict(color=SE_COLORS["text_muted"])),
                ticksuffix="%", tickfont=dict(color=SE_COLORS["text_muted"])),
        ), row=row, col=col)

        # Adaptive Text-Annotations
        for wd_idx, wd_label in enumerate(WEEKDAY_LABELS_SHORT):
            val = z_row[wd_idx]
            color = _heatmap_text_color(val, 0, max_abs)
            fig.add_annotation(
                x=wd_label, y=f"Q{q}",
                text=f"{val:+.2f}%",
                showarrow=False,
                font=dict(size=11, color=color),
                row=row, col=col)

        # Gelber Rahmen auf aktuelles Quartal + Wochentag
        if q == today_q and 0 <= today_wd < len(WEEKDAY_LABELS):
            fig.add_shape(type="rect",
                x0=today_wd - 0.5, x1=today_wd + 0.5,
                y0=-0.5, y1=0.5,
                line=dict(color="#FFD700", width=3.5),
                fillcolor="rgba(0,0,0,0)", layer="above",
                row=row, col=col)

    fig = apply_se_theme(fig, title=f"{ticker} — Wochentag-Performance nach Quartal", height=340)
    for row in [1, 2]:
        for col in [1, 2]:
            fig.update_xaxes(type="category", side="bottom", tickformat="", row=row, col=col)
            fig.update_yaxes(type="category", tickformat="", row=row, col=col)
    return fig


def calc_volatility_profile(df, years_back, cycle_filter=None):
    """Range (High-Low)/Close pro Wochentag."""
    df = df.copy()
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])

    df["weekday"] = df.index.weekday
    df["range_pct"] = (df["High"] - df["Low"]) / df["Close"] * 100
    _has_weekend = (df["weekday"] >= 5).any()
    if not _has_weekend:
        df = df[df["weekday"] <= 4]
    df = df.dropna(subset=["range_pct"])

    results = {}
    for wd in range(len(WEEKDAY_LABELS)):
        sub = df[df["weekday"] == wd]["range_pct"]
        if len(sub) < 10:
            results[wd] = {"avg": 0, "median": 0, "std": 0, "n": 0}
            continue
        results[wd] = {
            "avg": sub.mean(),
            "median": sub.median(),
            "std": sub.std(),
            "n": len(sub),
        }
    return results


def build_volatility_chart(vol_stats, ticker):
    """Bars: durchschnittliche Tages-Range pro Wochentag."""
    avgs = [vol_stats[wd]["avg"] for wd in range(len(WEEKDAY_LABELS))]
    medians = [vol_stats[wd]["median"] for wd in range(len(WEEKDAY_LABELS))]

    # Farbskala: höchste Vola = intensiveres Rot/Orange
    max_vol = max(avgs) if avgs else 1
    colors = [f"rgba(255,{int(165 - 100 * v / max_vol)},{int(80 - 50 * v / max_vol)},0.85)" for v in avgs]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=WEEKDAY_LABELS, y=avgs, marker_color=colors,
        name="Ø Range",
        text=[f"{v:.2f}%<br>Med: {m:.2f}%" for v, m in zip(avgs, medians)],
        textposition="outside", textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>Ø Range: %{y:.2f}%<br>n=%{customdata}<extra></extra>",
        customdata=[vol_stats[wd]["n"] for wd in range(len(WEEKDAY_LABELS))]))

    # Durchschnittslinie
    overall_avg = np.mean(avgs)
    fig.add_hline(y=overall_avg, line_dash="dash", line_color="#F1C40F",
                  annotation_text=f"Oe {overall_avg:.2f}%",
                  annotation_font_color="#F1C40F")

    # We are here!
    today_wd = datetime.now().weekday()  # Gelber Rahmen immer sichtbar
    if 0 <= today_wd < len(WEEKDAY_LABELS):
        fig.add_shape(**wah_rect(x0=today_wd - 0.4, x1=today_wd + 0.4, y0=0, y1=avgs[today_wd]))
        fig.add_annotation(**wah_annotation(
            x_val=WEEKDAY_LABELS[today_wd], y_val=avgs[today_wd],
            above=True, text="We are here!"))

    fig = apply_se_theme(fig, title=f"{ticker} — Volatilitäts-Profil (Tages-Range pro Wochentag)",
                         height=380, show_legend=False)
    fig.update_yaxes(ticksuffix="%")
    return fig


# ══════════════════════════════════════════════════════════════
# WEEKEND EFFEKT
# ══════════════════════════════════════════════════════════════

def calc_weekend_effect(df, years_back, cycle_filter=None,
                        filter_mode="Kein Filter",
                        sma_days=200, rsi_days=14, rsi_threshold=30):
    """
    Weekend-Effekt: Close Freitag → Open Montag.

    Berechnet die Ueber-Wochenende-Rendite (Freitag Schluss → Montag Eroeffnung)
    und aggregiert nach Monat, Jahr, und insgesamt.
    """
    df = df.copy()

    # ── Zeitraum filtern ──
    cutoff = df.index.max() - pd.DateOffset(years=years_back)
    df = df[df.index >= cutoff]

    if len(df) < 20:
        return None

    # ── Praesidentenzyklus-Filter ──
    if cycle_filter:
        df["_cycle"] = df.index.year.map(get_presidential_cycle_year)
        df = df[df["_cycle"].isin(cycle_filter)]
        df = df.drop(columns=["_cycle"])
        if len(df) < 20:
            return None

    # ── Filter anwenden (auf Freitags-Close) ──
    df["filter_pass"] = True
    total_count = len(df)

    if filter_mode == "Trendfilter (SMA)":
        df["sma"] = df["Close"].rolling(sma_days, min_periods=sma_days).mean()
        df["filter_pass"] = df["Close"] > df["sma"]

    elif filter_mode == "OBOS-Filter (RSI)":
        delta = df["Close"].diff()
        gain = delta.where(delta > 0, 0.0).rolling(rsi_days).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(rsi_days).mean()
        rs = gain / loss.replace(0, np.nan)
        df["rsi"] = 100 - (100 / (1 + rs))
        df["filter_pass"] = df["rsi"] < rsi_threshold

    df["weekday"] = df.index.weekday

    # ── Freitage finden ──
    fridays = df[df["weekday"] == 4].copy()
    if len(fridays) == 0:
        return None

    # ── Naechsten Montag finden (Open) ──
    weekend_returns = []
    for fri_date in fridays.index:
        if not fridays.loc[fri_date, "filter_pass"]:
            continue

        # Naechste Handelstage nach Freitag suchen
        next_days = df[df.index > fri_date].head(5)
        # Montag = weekday 0
        mondays = next_days[next_days["weekday"] == 0]
        if len(mondays) == 0:
            continue

        monday = mondays.iloc[0]
        fri_close = fridays.loc[fri_date, "Close"]
        mon_open = monday["Open"]

        if fri_close <= 0 or pd.isna(mon_open):
            continue

        ret = (mon_open / fri_close - 1) * 100
        weekend_returns.append({
            "date_friday": fri_date,
            "date_monday": mondays.index[0],
            "month": fri_date.month,
            "year": fri_date.year,
            "return": ret,
            "cycle": get_presidential_cycle_year(fri_date.year),
        })

    if not weekend_returns:
        return None

    wr_df = pd.DataFrame(weekend_returns)
    filtered_count = len(wr_df)

    # ── Statistik gesamt ──
    overall = {
        "avg": wr_df["return"].mean(),
        "median": wr_df["return"].median(),
        "std": wr_df["return"].std(),
        "win_rate": (wr_df["return"] > 0).mean() * 100,
        "count": len(wr_df),
        "returns": wr_df["return"].tolist(),
    }

    # ── Statistik pro Monat ──
    by_month = {}
    for month in range(1, 13):
        sub = wr_df[wr_df["month"] == month]["return"]
        if len(sub) == 0:
            by_month[month] = {"avg": 0, "median": 0, "std": 0,
                               "win_rate": 0, "count": 0, "returns": []}
            continue
        by_month[month] = {
            "avg": sub.mean(),
            "median": sub.median(),
            "std": sub.std(),
            "win_rate": (sub > 0).mean() * 100,
            "count": len(sub),
            "returns": sub.tolist(),
        }

    # ── Heatmap: Monat × Jahr ──
    by_month_year = {}
    for (month, year), grp in wr_df.groupby(["month", "year"]):
        by_month_year[(month, year)] = {
            "avg": grp["return"].mean(),
            "count": len(grp),
            "win_rate": (grp["return"] > 0).mean() * 100,
        }

    # ── Statistik pro Praesidentenzyklus ──
    by_cycle = {}
    for cycle_label, grp in wr_df.groupby("cycle"):
        by_cycle[cycle_label] = {
            "avg": grp["return"].mean(),
            "median": grp["return"].median(),
            "std": grp["return"].std(),
            "win_rate": (grp["return"] > 0).mean() * 100,
            "count": len(grp),
            "returns": grp["return"].tolist(),
        }

    return {
        "overall": overall,
        "by_month": by_month,
        "by_month_year": by_month_year,
        "by_cycle": by_cycle,
        "filtered_count": filtered_count,
        "total_count": total_count,
        "years": sorted(wr_df["year"].unique()),
    }


def build_weekend_bar_chart(we_stats, ticker):
    """Balkendiagramm: Weekend-Effekt Ø Rendite + Win Rate pro Monat."""

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Ø Weekend-Rendite (%)", "Win Rate (%)"),
        horizontal_spacing=0.12
    )

    months = list(range(1, 13))
    avgs = [we_stats["by_month"][m]["avg"] for m in months]
    win_rates = [we_stats["by_month"][m]["win_rate"] for m in months]
    counts = [we_stats["by_month"][m]["count"] for m in months]

    bar_colors = [SE_COLORS["positive"] if v >= 0 else SE_COLORS["negative"] for v in avgs]

    fig.add_trace(
        go.Bar(
            x=MONTH_NAMES_DE, y=avgs,
            marker_color=bar_colors,
            text=[f"{v:+.3f}%<br>n={c}" for v, c in zip(avgs, counts)],
            textposition="outside", textfont=dict(size=9),
            hovertemplate="<b>%{x}</b><br>Ø Weekend: %{y:+.3f}%<extra></extra>",
            showlegend=False
        ), row=1, col=1)

    wr_colors = [SE_COLORS["positive"] if v >= 50 else SE_COLORS["negative"] for v in win_rates]
    fig.add_trace(
        go.Bar(
            x=MONTH_NAMES_DE, y=win_rates,
            marker_color=wr_colors,
            text=[f"{v:.0f}%" for v in win_rates],
            textposition="outside", textfont=dict(size=9),
            hovertemplate="<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>",
            showlegend=False
        ), row=1, col=2)

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=1, col=1)
    fig.add_hline(y=50, line_dash="dash", line_color="rgba(255,255,255,0.3)", row=1, col=2)

    # Gesamtdurchschnitt als Referenzlinie
    overall_avg = we_stats["overall"]["avg"]
    fig.add_hline(y=overall_avg, line_dash="dot", line_color="#F1C40F",
                  annotation_text=f"Ø {overall_avg:+.3f}%",
                  annotation_font_color="#F1C40F", row=1, col=1)

    # We are here! — gelber Rahmen um aktuellen Monat
    current_month = datetime.now().month
    fig.add_shape(type="rect",
        x0=current_month - 1 - 0.4, x1=current_month - 1 + 0.4,
        y0=0, y1=avgs[current_month - 1],
        line=dict(color="#FFD700", width=3),
        fillcolor="rgba(0,0,0,0)", layer="above", row=1, col=1)
    fig.add_shape(type="rect",
        x0=current_month - 1 - 0.4, x1=current_month - 1 + 0.4,
        y0=0, y1=win_rates[current_month - 1],
        line=dict(color="#FFD700", width=3),
        fillcolor="rgba(0,0,0,0)", layer="above", row=1, col=2)

    n = we_stats["overall"]["count"]
    fig = apply_se_theme(fig,
        title=f"{ticker} — Weekend-Effekt: Fr Close → Mo Open ({n} Wochenenden)", height=400)
    fig.update_yaxes(tickformat="+.3f", ticksuffix="%", row=1, col=1,
                     gridcolor="rgba(255,255,255,0.06)")
    fig.update_yaxes(range=[0, 100], ticksuffix="%", row=1, col=2,
                     gridcolor="rgba(255,255,255,0.06)")
    return fig


def build_weekend_heatmap(we_stats, ticker):
    """Heatmap: Monat × Jahr des Weekend-Effekts."""

    years = we_stats["years"]
    if not years:
        return None

    # Jahreslabels mit Leerzeichen suffixen — verhindert dass Plotly
    # numerische Strings ("2021") als Zahlen auf linearer Achse interpretiert
    year_labels = [f" {y} " for y in years]
    z_values = []
    hover_texts = []
    text_values = []

    for month in range(1, 13):
        row_z = []
        row_hover = []
        row_text = []
        for year in years:
            data = we_stats["by_month_year"].get((month, year), {"avg": 0, "count": 0, "win_rate": 0})
            row_z.append(data["avg"])
            row_text.append(f"{data['avg']:+.2f}%")
            row_hover.append(
                f"<b>{MONTH_NAMES_DE[month-1]} {year}</b><br>"
                f"Ø Weekend: {data['avg']:+.3f}%<br>"
                f"Win Rate: {data['win_rate']:.0f}%<br>"
                f"n = {data['count']}"
            )
        z_values.append(row_z)
        hover_texts.append(row_hover)
        text_values.append(row_text)

    fig = go.Figure(go.Heatmap(
        z=z_values,
        x=year_labels,
        y=MONTH_NAMES_DE,
        text=text_values,
        texttemplate="%{text}",
        textfont=dict(size=9, color="#FFFFFF"),
        colorscale=SE_HEATMAP_COLORSCALE,
        zmid=0,
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>",
        colorbar=dict(
            title=dict(text="Ø %", font=dict(color="#FFFFFF")),
            ticksuffix="%", tickformat="+.3f",
            tickfont=dict(color="#FFFFFF"),
        ),
    ))

    fig = apply_se_heatmap_theme(fig, title=f"{ticker} — Weekend-Effekt Heatmap (Monat × Jahr)", height=480)
    fig.update_xaxes(side="bottom", type="category", categoryorder="array",
                     categoryarray=year_labels, tickformat="")
    fig.update_yaxes(autorange="reversed", type="category", tickformat="")

    # Gelber Rahmen um aktuelle Zelle
    current_month = datetime.now().month
    current_year = datetime.now().year
    if current_year in years:
        year_idx = years.index(current_year)
        fig.add_shape(type="rect",
            x0=year_idx - 0.5, x1=year_idx + 0.5,
            y0=current_month - 1 - 0.5, y1=current_month - 1 + 0.5,
            line=dict(color="#FFD700", width=3.5),
            fillcolor="rgba(0,0,0,0)", layer="above")

    return fig


def build_weekend_cycle_chart(we_stats, ticker):
    """Balkendiagramm: Weekend-Effekt nach Praesidentenzyklus."""
    by_cycle = we_stats["by_cycle"]
    if not by_cycle:
        return None

    # Feste Reihenfolge
    cycle_order = [
        "Year 1 (Post-Election)",
        "Year 2 (Midterm Election)",
        "Year 3 (Pre-Election)",
        "Year 4 (Election Year)",
    ]
    labels = []
    avgs = []
    counts = []
    colors = []

    for c in cycle_order:
        if c in by_cycle:
            labels.append(c.split("(")[1].rstrip(")"))
            avgs.append(by_cycle[c]["avg"])
            counts.append(by_cycle[c]["count"])
            colors.append(CYCLE_COLORS.get(c, "#888888"))

    if not labels:
        return None

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=labels, y=avgs,
        marker_color=colors,
        text=[f"{v:+.3f}%<br>n={c}" for v, c in zip(avgs, counts)],
        textposition="outside", textfont=dict(size=11),
        hovertemplate="<b>%{x}</b><br>Ø Weekend: %{y:+.3f}%<extra></extra>",
        showlegend=False,
    ))
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")

    fig = apply_se_theme(fig, title=f"{ticker} — Weekend-Effekt nach Präsidentenzyklus", height=350)
    fig.update_yaxes(tickformat="+.3f", ticksuffix="%")
    return fig


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.markdown("## 📅 Weekday Performance")
        st.markdown("---")

        ticker = ticker_select(key="wd_ticker", default=DEFAULT_TICKER)

        years_back = st.slider("Analyse-Zeitraum (Jahre)", 1, 30, 10, key="wd_years")

        st.markdown("---")
        st.markdown("### Rendite-Berechnung")

        return_mode = st.radio(
            "Modus",
            options=list(RETURN_MODES.keys()),
            index=0,
            help="Welche Kurse werden für die Rendite-Berechnung verwendet?"
        )
        st.caption(f"_{RETURN_MODES[return_mode]['desc']}_")

        st.markdown("---")
        st.markdown("### Filter")

        filter_mode = st.radio(
            "Einstiegsfilter",
            ["Kein Filter", "Trendfilter (SMA)", "OBOS-Filter (RSI)"],
            index=0,
            help="Filtert Tage heraus, die nicht zur Bedingung passen"
        )

        sma_days = 200
        rsi_days = 14
        rsi_threshold = 30

        if filter_mode == "Trendfilter (SMA)":
            sma_days = st.slider("SMA Periode (Tage)", 20, 400, 200,
                                 help="Nur kaufen wenn Close t-1 > SMA")

        elif filter_mode == "OBOS-Filter (RSI)":
            rsi_days = st.slider("RSI Periode (Tage)", 5, 30, 14)
            rsi_threshold = st.slider("RSI Schwelle (kaufen wenn darunter)", 10, 50, 30,
                                      help="Nur kaufen wenn RSI t-1 < Schwelle")

        st.markdown("---")
        st.markdown("### Präsidentenzyklus")
        cycle_filter = st.multiselect(
            "Zyklusjahre filtern",
            options=list(CYCLE_COLORS.keys()),
            default=None, key="wd_cycle",
            help="Nur Jahre mit bestimmtem Zyklusjahr beruecksichtigen (leer = alle)"
        )

        st.markdown("---")
        st.markdown("### Anzeige")
        _show_current_chart = st.checkbox("Aktuellen Chart anzeigen", value=True, key="wd_show_current_chart")

        # ── Technische Filter ──────────────────────────
        from shared.indicator_filter_ui import indicator_filter_sidebar
        ind_filters = indicator_filter_sidebar(key_prefix="wd")

    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)

    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return

    # ── Indikator-Filter anwenden ─────────────────────
    if ind_filters:
        from shared.indicators import apply_indicator_filter
        from shared.indicator_filter_ui import render_filter_badge
        _df_temp = raw_df.copy()
        if "Close" not in _df_temp.columns and "close" in _df_temp.columns:
            _df_temp = _df_temp.rename(columns={"close": "Close"})
        mask = apply_indicator_filter(_df_temp, ind_filters)
        total_days = len(raw_df)
        raw_df = raw_df[mask].copy()
        filtered_days = len(raw_df)
        render_filter_badge(ind_filters, total_days, filtered_days)

    # ── Berechnung ────────────────────────────────────
    stats = calculate_weekday_stats(
        raw_df, return_mode, years_back,
        filter_mode, sma_days, rsi_days, rsi_threshold,
        cycle_filter=cycle_filter if cycle_filter else None
    )

    if stats is None:
        st.warning("Nicht genügend Daten für die Analyse.")
        return

    # ── Crypto-Erkennung: Labels dynamisch setzen ────
    global WEEKDAY_LABELS, WEEKDAY_LABELS_SHORT
    if stats.get("is_crypto", False):
        WEEKDAY_LABELS = WEEKDAY_LABELS_7
        WEEKDAY_LABELS_SHORT = WEEKDAY_LABELS_SHORT_7
    else:
        WEEKDAY_LABELS = WEEKDAY_LABELS_5
        WEEKDAY_LABELS_SHORT = WEEKDAY_LABELS_SHORT_5

    # ── Zyklusfilter-Info ──────────────────────────────
    if cycle_filter:
        cycle_info = ", ".join([c.split("(")[1].rstrip(")") for c in cycle_filter])
        st.info(f"**Zyklusfilter aktiv:** {cycle_info}")

    # ── Filter-Info ───────────────────────────────────
    if filter_mode != "Kein Filter":
        pct = stats["filtered_count"] / stats["total_count"] * 100
        st.info(
            f"**Filter aktiv:** {filter_mode} · "
            f"{stats['filtered_count']} von {stats['total_count']} Tagen passieren den Filter ({pct:.0f}%)"
        )

    from shared.trading_day_header import render_trading_day_header
    render_trading_day_header(raw_df)

    # ── Kumulierter Wochenverlauf Mo→Fr ──────────────
    with st.expander("📈 Kumulierter Wochenverlauf Mo→Fr", expanded=True):
        wd_cum_stats, _ = calc_weekly_cumulative(raw_df, years_back,
            cycle_filter=cycle_filter if cycle_filter else None)
        cw_curve = calc_current_week_curve(raw_df) if st.session_state.get("wd_show_current_chart", True) else None
        cum_fig = build_weekly_cumulative_chart(wd_cum_stats, ticker, current_week_curve=cw_curve)
        if cum_fig:
            st.plotly_chart(cum_fig, use_container_width=True, key="wd_cum_chart")
            st.markdown(
                "<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
                "<b>Interpretation:</b> Zeigt, wie sich die Wochenrendite von Montag bis Freitag "
                "aufbaut. Die gelbe Linie zeigt die aktuelle Woche im Vergleich. "
                "Steigt die Kurve vor allem am Anfang der Woche, spricht das für "
                "frühen Kaufdruck (z.B. institutionelle Allokation am Montag).</p>",
                unsafe_allow_html=True)

    # ── Balkendiagramm ────────────────────────────────
    with st.expander("📊 Durchschnittsrendite & Win Rate pro Wochentag", expanded=True):
        bar_fig = build_weekday_bar_chart(stats, ticker, return_mode)
        st.plotly_chart(bar_fig, use_container_width=True)

    # ── Signifikanztest (optional) ────────────────────
    from shared.significance_gauge import run_significance_test, render_significance_section
    sig_groups = {WEEKDAY_LABELS[wd]: stats["by_weekday"][wd]["returns"]
                  for wd in range(len(WEEKDAY_LABELS)) if stats["by_weekday"][wd]["returns"]}
    sig_results = run_significance_test(sig_groups)
    render_significance_section(sig_results,
        expander_title="📊 Statistische Signifikanz der Wochentags-Effekte",
        cols_per_row=5,
        sort_order=WEEKDAY_LABELS,
        key_prefix="sig_main")

    # (Signifikanztests fuer andere Modi entfernt — Hauptmodus reicht)

    # ── Detailtabelle ─────────────────────────────────
    with st.expander("📋 Statistik pro Wochentag", expanded=True):
        wd_rows = []
        for wd in range(len(WEEKDAY_LABELS)):
            d = stats["by_weekday"][wd]
            wd_rows.append({
                "Wochentag": WEEKDAY_LABELS[wd],
                "Ø Rendite": f"{d['avg']:+.2f}%",
                "Median": f"{d['median']:+.2f}%",
                "Std.Abw.": f"{d['std']:.2f}%",
                "Win Rate": f"{d['win_rate']:.1f}%",
                "Anzahl": d["count"]
            })
        st.dataframe(pd.DataFrame(wd_rows), use_container_width=True, hide_index=True)

    # ── Overnight vs. Intraday (nur Aktien — Crypto handelt 24/7) ──
    _is_crypto = stats.get("is_crypto", False)
    if not _is_crypto:
      with st.expander("🌙 Overnight vs. Intraday Split", expanded=True):
        oi_stats = calc_overnight_intraday(raw_df, years_back,
            cycle_filter=cycle_filter if cycle_filter else None)
        oi_fig = build_overnight_intraday_chart(oi_stats, ticker)
        st.plotly_chart(oi_fig, use_container_width=True, key="wd_oi_chart")
        st.markdown(
            "<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            "<b>Interpretation:</b> Zerlegt die Tagesrendite in <b style='color:#6C5CE7;'>"
            "Overnight</b> (Schlusskurs gestern → Eroeffnung heute) und "
            "<b style='color:#00CEC9;'>Intraday</b> (Eroeffnung → Schluss). "
            "Wenn die Rendite ueberwiegend overnight entsteht, profitieren "
            "Buy-and-Hold-Anleger. Dominiert Intraday, ist aktives Trading relevant.</p>",
            unsafe_allow_html=True)

    # ── Weekend-Effekt (nur Aktien) ──────────────────
    if not _is_crypto:
      with st.expander("🌅 Weekend-Effekt (Fr Close → Mo Open)", expanded=True):
        we_stats = calc_weekend_effect(
            raw_df, years_back,
            cycle_filter=cycle_filter if cycle_filter else None,
            filter_mode=filter_mode, sma_days=sma_days,
            rsi_days=rsi_days, rsi_threshold=rsi_threshold)

        if we_stats is None:
            st.warning("Nicht genuegend Daten fuer die Weekend-Effekt Analyse.")
        else:
            # ── Kompakte Statistik-Karten ──
            ov = we_stats["overall"]
            _color_avg = SE_COLORS["positive"] if ov["avg"] >= 0 else SE_COLORS["negative"]
            _color_wr = SE_COLORS["positive"] if ov["win_rate"] >= 50 else SE_COLORS["negative"]
            st.markdown(f"""
            <div style="display:flex; gap:12px; flex-wrap:wrap; margin-bottom:12px;">
              <div style="background:#1a1a2e; border-radius:8px; padding:8px 14px; min-width:120px;">
                <span style="font-size:10px; color:#aaa;">Ø Weekend-Rendite</span><br>
                <span style="font-size:14px; font-weight:700; color:{_color_avg};">{ov['avg']:+.3f}%</span>
              </div>
              <div style="background:#1a1a2e; border-radius:8px; padding:8px 14px; min-width:120px;">
                <span style="font-size:10px; color:#aaa;">Median</span><br>
                <span style="font-size:14px; font-weight:700; color:#FFFFFF;">{ov['median']:+.3f}%</span>
              </div>
              <div style="background:#1a1a2e; border-radius:8px; padding:8px 14px; min-width:120px;">
                <span style="font-size:10px; color:#aaa;">Win Rate</span><br>
                <span style="font-size:14px; font-weight:700; color:{_color_wr};">{ov['win_rate']:.1f}%</span>
              </div>
              <div style="background:#1a1a2e; border-radius:8px; padding:8px 14px; min-width:120px;">
                <span style="font-size:10px; color:#aaa;">Std.Abw.</span><br>
                <span style="font-size:14px; font-weight:700; color:#FFFFFF;">{ov['std']:.3f}%</span>
              </div>
              <div style="background:#1a1a2e; border-radius:8px; padding:8px 14px; min-width:120px;">
                <span style="font-size:10px; color:#aaa;">Wochenenden</span><br>
                <span style="font-size:14px; font-weight:700; color:#FFFFFF;">{ov['count']}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # ── Balkendiagramm pro Monat ──
            we_bar_fig = build_weekend_bar_chart(we_stats, ticker)
            st.plotly_chart(we_bar_fig, use_container_width=True, key="wd_weekend_bar")

            # ── Signifikanztest pro Monat ──
            sig_we_groups = {MONTH_NAMES_DE[m-1]: we_stats["by_month"][m]["returns"]
                            for m in range(1, 13) if we_stats["by_month"][m]["returns"]}
            if sig_we_groups:
                sig_we_results = run_significance_test(sig_we_groups)
                render_significance_section(sig_we_results,
                    expander_title="📊 Signifikanz Weekend-Effekt pro Monat",
                    cols_per_row=6,
                    sort_order=MONTH_NAMES_DE,
                    key_prefix="sig_weekend")

            # ── Heatmap Monat × Jahr ──
            we_heatmap_fig = build_weekend_heatmap(we_stats, ticker)
            if we_heatmap_fig:
                st.plotly_chart(we_heatmap_fig, use_container_width=True, key="wd_weekend_heatmap")

            # ── Praesidentenzyklus ──
            we_cycle_fig = build_weekend_cycle_chart(we_stats, ticker)
            if we_cycle_fig:
                st.plotly_chart(we_cycle_fig, use_container_width=True, key="wd_weekend_cycle")

            st.markdown(
                "<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
                "<b>Interpretation:</b> Der Weekend-Effekt misst die Rendite ueber "
                "das Wochenende (Freitag Schluss → Montag Eroeffnung). Historisch zeigt "
                "sich oft ein negativer Weekend-Effekt bei Aktien — Montage eroeffnen "
                "unter dem Freitags-Schluss. Dieser Effekt variiert saisonal und kann "
                "durch Nachrichtenfluss am Wochenende (Earnings, Geopolitik) verstaerkt werden.</p>",
                unsafe_allow_html=True)

    # ── Konsekutiv-Analyse ────────────────────────────
    with st.expander("🔗 Konsekutiv-Analyse (Folgetag-Wahrscheinlichkeit)", expanded=True):
        consec_matrix = calc_consecutive_probs(raw_df, years_back,
            cycle_filter=cycle_filter if cycle_filter else None)
        consec_fig = build_consecutive_heatmap(consec_matrix)
        st.plotly_chart(consec_fig, use_container_width=True, key="wd_consec_heatmap")
        st.markdown(
            "<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            "<b>Interpretation:</b> Zeigt die Wahrscheinlichkeit, dass der Folgetag positiv ist, "
            "abhaengig davon ob der Vortag positiv (↑) oder negativ (↓) war. "
            "Werte ueber 55% deuten auf Trendkontinuation hin, unter 45% auf Mean Reversion.</p>",
            unsafe_allow_html=True)

    # ── Quartals-Heatmaps ─────────────────────────────
    with st.expander("📊 Wochentag-Performance nach Quartal", expanded=True):
        q_stats = calc_quarterly_weekday(raw_df, years_back,
            cycle_filter=cycle_filter if cycle_filter else None)
        q_fig = build_quarterly_heatmaps(q_stats, ticker)
        st.plotly_chart(q_fig, use_container_width=True, key="wd_quarterly_heatmap")
        st.markdown(
            "<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            "<b>Interpretation:</b> Zeigt ob Wochentags-Effekte saisonal variieren. "
            "Z.B. koennte der Montagseffekt nur in Q4 (Window Dressing, Jahresend-Rallye) "
            "signifikant sein, waehrend er in Q2/Q3 verschwindet.</p>",
            unsafe_allow_html=True)

    # ── Volatilitäts-Profil ───────────────────────────
    with st.expander("📉 Volatilitäts-Profil (Tages-Range)", expanded=True):
        vol_stats = calc_volatility_profile(raw_df, years_back,
            cycle_filter=cycle_filter if cycle_filter else None)
        vol_fig = build_volatility_chart(vol_stats, ticker)
        st.plotly_chart(vol_fig, use_container_width=True, key="wd_vol_chart")
        st.markdown(
            "<p style='color:#FFFFFF; font-size:12px; line-height:1.6;'>"
            "<b>Interpretation:</b> Die Tages-Range (High−Low)/Close zeigt die "
            "durchschnittliche Schwankungsbreite pro Wochentag. "
            "Hohe Werte = mehr Volatilität = größere Chancen für Day-Trader, "
            "aber auch höheres Risiko. Typisch: Montag und Freitag haben höhere Ranges.</p>",
            unsafe_allow_html=True)

    # ── Heatmap Monat x Wochentag ────────────────────
    with st.expander("🗓️ Monat × Wochentag Heatmap", expanded=True):
        heatmap_fig = build_heatmap(stats, ticker, return_mode=return_mode)
        st.plotly_chart(heatmap_fig, use_container_width=True, key=f"wd_heatmap_{return_mode}")
        # Hinweis bei einseitigen Modi
        _mode_key = return_mode.split("(")[0].strip()
        if "Open" in return_mode and "Close" in return_mode and "t0 →" not in return_mode:
            st.markdown(
                "<p style='color:#aaa; font-size:11px; line-height:1.5;'>"
                "<b>Hinweis:</b> Im Modus <i>Open → Close</i> (Intraday) sind die Werte oft "
                "überwiegend negativ — der Großteil der Aktienrenditen entsteht "
                "über Nacht (Overnight-Effekt). Dies ist kein Fehler, sondern ein "
                "dokumentiertes Marktphänomen.</p>",
                unsafe_allow_html=True)
        elif "Close → Open" in return_mode:
            st.markdown(
                "<p style='color:#aaa; font-size:11px; line-height:1.5;'>"
                "<b>Hinweis:</b> Im Modus <i>Close → Open</i> (Overnight) sind die Werte oft "
                "überwiegend positiv — der Großteil der Aktienrenditen entsteht "
                "über Nacht (Overnight-Effekt). Dies ist kein Fehler, sondern ein "
                "dokumentiertes Marktphänomen.</p>",
                unsafe_allow_html=True)

    # ── Top / Flop Kombinationen ──────────────────────
    with st.expander("🏆 Top / Flop Monat×Wochentag Kombinationen", expanded=True):
        mwd = stats["by_month_weekday"]
        combos = []
        for (month, wd), data in mwd.items():
            if data["count"] >= 3:
                combos.append({
                    "Monat": MONTH_NAMES_DE[month - 1],
                    "Wochentag": WEEKDAY_LABELS[wd],
                    "Ø Rendite": data["avg"],
                    "Win Rate": data["win_rate"],
                    "n": data["count"]
                })

        if combos:
            sorted_combos = sorted(combos, key=lambda x: x["Ø Rendite"], reverse=True)

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("<p style='font-size:14px; font-weight:700; color:#34d399; margin:0.5rem 0 0.3rem;'>🟢 Top 10 beste Kombinationen</p>", unsafe_allow_html=True)
                top_df = pd.DataFrame(sorted_combos[:10])
                top_df["Ø Rendite"] = top_df["Ø Rendite"].apply(lambda x: f"{x:+.2f}%")
                top_df["Win Rate"] = top_df["Win Rate"].apply(lambda x: f"{x:.0f}%")
                st.dataframe(top_df, use_container_width=True, hide_index=True)

            with col2:
                st.markdown("<p style='font-size:14px; font-weight:700; color:#ff6b6b; margin:0.5rem 0 0.3rem;'>🔴 Top 10 schlechteste Kombinationen</p>", unsafe_allow_html=True)
                flop_df = pd.DataFrame(sorted_combos[-10:][::-1])
                flop_df["Ø Rendite"] = flop_df["Ø Rendite"].apply(lambda x: f"{x:+.2f}%")
                flop_df["Win Rate"] = flop_df["Win Rate"].apply(lambda x: f"{x:.0f}%")
                st.dataframe(flop_df, use_container_width=True, hide_index=True)

    # ── Dateninfo ─────────────────────────────────────
    with st.expander("ℹ️ Dateninfo"):
        cycle_str = ", ".join(cycle_filter) if cycle_filter else "Kein Filter"
        st.markdown(f"""
        **Ticker:** {ticker}
        **Zeitraum:** Letzte {years_back} Jahre
        **Rendite-Modus:** {return_mode}
        **Beschreibung:** {RETURN_MODES[return_mode]['desc']}
        **Filter:** {filter_mode}
        **Präsidentenzyklus:** {cycle_str}
        **Handelstage analysiert:** {stats['filtered_count']}
        """)

    # ── Methodik ──────────────────────────────────────────
    with st.expander("ℹ️ Methodik"):
        _crypto_note = " Crypto-Assets handeln 7 Tage/Woche — Samstag und Sonntag werden automatisch einbezogen." if _is_crypto else ""
        st.markdown(f"""
### Datengrundlage

- **Ticker:** {ticker}
- **Analyse-Zeitraum:** {years_back} Jahre
- **Rendite-Modus:** {return_mode}
- **Filter:** {filter_mode}{_crypto_note}

### Rendite-Analyse

- **Wochentag-Rendite:** Für jeden Handelstag wird die Rendite gemäß dem gewählten Modus berechnet (z.B. Close→Close: Schlusskurs heute vs. Schlusskurs morgen).
- **Kumulierter Wochenverlauf:** Zeigt, wie sich die Wochenrendite von Montag bis {"Sonntag" if _is_crypto else "Freitag"} aufbaut. Jede Woche wird einzeln berechnet (log-Returns kumuliert), dann über alle Wochen gemittelt.
- **Win-Rate:** Anteil der Tage mit positiver Rendite (in %).
- **Signifikanz-Tachos:** t-Test pro Wochentag: p < 0,05 = statistisch signifikant (grün). Ein signifikanter Wochentag hat eine Rendite, die sich statistisch vom Zufall unterscheidet.

### Overnight vs. Intraday

- **Overnight:** Schlusskurs gestern → Eröffnung heute. Misst die Kursänderung über Nacht (Nachrichten, Gaps).
- **Intraday:** Eröffnung → Schluss. Misst die Kursänderung während der Handelszeit.
- {"**Hinweis:** Bei Crypto (24/7-Handel) ist diese Zerlegung nicht aussagekräftig und wird daher ausgeblendet." if _is_crypto else "Die Summe ergibt die Close→Close Rendite."}

### Konsekutiv-Analyse

- **Folgetag-Wahrscheinlichkeit:** Wie wahrscheinlich ist ein positiver Folgetag, wenn heute positiv (↑) oder negativ (↓) war?
- **Heatmap:** Zeigt die bedingte Wahrscheinlichkeit für jedes Wochentag-Paar (z.B. Montag↑ → Dienstag↑: 58%).

### Volatilitäts-Profil

- **Tages-Range:** (High – Low) / Close × 100. Misst die Schwankungsbreite an jedem Wochentag.
- **Interpretation:** Höhere Range = volatilerer Handelstag. Montage und Freitage sind bei Aktien oft volatiler als Mittwoche.

### Weekend-Effekt

- **Berechnung:** (Montag Open / Freitag Close − 1) × 100. Misst die Rendite über das Wochenende.
- **Balkendiagramm:** Ø Weekend-Rendite und Win Rate pro Monat (Jan–Dez).
- **Heatmap:** Monat × Jahr zeigt den Weekend-Effekt pro Monat und Jahr.
- **Signifikanz-Tachos:** t-Test pro Monat: p < 0,05 = statistisch signifikanter Weekend-Effekt.
- **Präsidentenzyklus:** Vergleich des Weekend-Effekts nach Zyklusjahr (Post-Election, Midterm, Pre-Election, Election).
- **Filter:** Trendfilter (SMA) und OBOS-Filter (RSI) werden auf den Freitag angewendet — nur Wochenenden, an denen der Filter aktiv war, werden berücksichtigt.

### Monat × Wochentag Heatmap

- **Matrix:** Zeilen = Monate (Jan–Dez), Spalten = Wochentage. Farbe = Ø Rendite.
- **Top 10 Kombinationen:** Die 10 besten und schlechtesten Monat-Wochentag-Paare nach Durchschnittsrendite.
        """)

    render_footer()


# ══════════════════════════════════════════════════════════════
# START
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
