# pages/11_📊_Intra_Decade_Seasonality.py
# Intra-Dekaden-Saisonalität

import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _c in [os.getcwd(), os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_c, "shared")):
            _project_dir = _c
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.yahoo_downloader import download_data, preprocess
from shared.calculations_decade import (
    build_decade_data, get_decade_summary_table,
    get_decade_digit, DECADE_COLORS, DECADE_LABELS,
)
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS
from shared.distribution_charts import (
    build_box_plot, build_decade_monthly_heatmap, build_context_panel_data,
)

st.set_page_config(
    page_title="SeasonalEdge – Intra-Decade Seasonality",
    page_icon="📊",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

TEMPLATE = "plotly_dark"
CURRENT_YEAR  = datetime.now().year
CURRENT_DIGIT = get_decade_digit(CURRENT_YEAR)

# ── Monatsbeschriftungen für X-Achse ─────────────────────────────────────────
MONTH_TICKS  = [int(i * 21) for i in range(12)]
MONTH_LABELS = ["Jan","Feb","Mär","Apr","Mai","Jun",
                "Jul","Aug","Sep","Okt","Nov","Dez"]

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Intra-Decade Seasonality")
    st.markdown("---")

    ticker = st.text_input(
        "Ticker",
        value="^DJI",
        help="Primär für Dow Jones (^DJI) — funktioniert mit jeder langen Zeitreihe",
    ).upper().strip()

    st.markdown("---")
    st.markdown("### Darstellung")

    smoothing = st.slider(
        "Glättung (Tage)", 1, 21, 5, 2,
        help="Zentrierter MA über die Ø-Kurven",
    )

    show_bands = st.checkbox("±1σ Konfidenzband", value=False,
                             help="Zeigt Standardabweichung pro Kohorte")
    show_individual = st.checkbox("Einzeljahre anzeigen", value=False,
                                  help="Alle Einzeljahre dünn im Hintergrund")
    show_current_year = st.checkbox("Aktuelles Jahr hervorheben", value=True,
                                    help="Zeigt das aktuelle Jahr als eigene Linie")

    st.markdown("---")
    st.markdown("### Rendite-Analyse")
    show_boxplot  = st.checkbox("Box-Plot Verteilung", value=True)
    show_context  = st.checkbox("Kontext-Panel (aktuelles Jahr)", value=True)
    show_heatmap  = st.checkbox("Heatmap Dekade × Monat", value=False)

    st.markdown("---")
    st.markdown("### Kohorten ein/ausblenden")
    st.caption("Welche Endziffern im Linien-Chart zeigen?")

    # Toggle-Checkboxen für alle 10 Ziffern — 2 Spalten
    show_digits: dict[int, bool] = {}
    cols = st.columns(2)
    for digit in range(10):
        label = f"X{digit} (aktuell ✨)" if digit == CURRENT_DIGIT else f"X{digit}"
        with cols[digit % 2]:
            show_digits[digit] = st.checkbox(label, value=True, key=f"dec_{digit}")

# ── Daten laden ───────────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Lade Kursdaten …")
def load_data(ticker: str) -> pd.DataFrame:
    raw = download_data(ticker)
    if raw is None or len(raw) == 0:
        raise ValueError(f"Keine Daten für '{ticker}'")
    return preprocess(raw)

try:
    df = load_data(ticker)
except Exception as e:
    st.error(f"**Fehler:** {e}")
    st.stop()

# ── Berechnung ────────────────────────────────────────────────────────────────
with st.spinner("Berechne Dekaden-Kohorten …"):
    decade_data = build_decade_data(df)

summary_df = get_decade_summary_table(decade_data)
data_start = df.index[0].year
data_end   = df.index[-1].year
total_years = len([y for y in range(data_start, data_end+1)
                   if len(df[df.index.year == y]) >= 200])

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(f"## 📊 Intra-Decade Seasonality — {ticker}")
st.caption(
    f"Zeitreihe: **{data_start}–{data_end}** · "
    f"**{total_years} vollständige Jahre** · "
    f"Aktuelles Jahr: **{CURRENT_YEAR}** (X{CURRENT_DIGIT}-Kohorte)"
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. LINIEN-CHART: Ø-Jahresverläufe pro Kohorte
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("### Ø-Jahresverlauf nach Dekaden-Endziffer")

fig = go.Figure()

for digit in range(10):
    if not show_digits.get(digit, True):
        continue
    d = decade_data[digit]
    if d["n"] == 0 or d["avg_curve"] is None:
        continue

    color = DECADE_COLORS[digit]
    is_current = (digit == CURRENT_DIGIT)
    lw = 3.0 if is_current else 1.8

    x = list(range(252))

    # Einzeljahre (dünn, transparent)
    if show_individual:
        for i, (year, curve) in enumerate(zip(d["years"], d["curves"])):
            fig.add_trace(go.Scatter(
                x=x, y=curve,
                mode="lines",
                line=dict(color=color, width=0.6),
                opacity=0.25,
                showlegend=False,
                hoverinfo="skip",
            ))

    # Glättung
    avg = pd.Series(d["avg_curve"]).rolling(smoothing, center=True, min_periods=1).mean().tolist()

    # Konfidenzband
    if show_bands and d["n"] >= 3:
        std = pd.Series(d["std_curve"]).rolling(smoothing, center=True, min_periods=1).mean().tolist()
        upper = [a + s for a, s in zip(avg, std)]
        lower = [a - s for a, s in zip(avg, std)]
        # Hex → rgba konvertieren
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.08)"
        fig.add_trace(go.Scatter(
            x=x + x[::-1],
            y=upper + lower[::-1],
            fill="toself",
            fillcolor=fill_color,
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Ø-Kurve
    end_val = avg[-1]
    name = f"X{digit} · n={d['n']} · {end_val:+.1f}%"
    if is_current:
        name = f"✨ X{digit} (aktuell) · n={d['n']} · {end_val:+.1f}%"

    fig.add_trace(go.Scatter(
        x=x, y=avg,
        mode="lines",
        name=name,
        line=dict(
            color=color, width=lw,
            dash="solid" if not is_current else "solid",
        ),
        opacity=1.0 if is_current else 0.85,
        hovertemplate=(
            f"<b>X{digit}-Jahre</b> (n={d['n']})<br>"
            "Handelstag %{x}<br>"
            "%{y:+.2f}%<extra></extra>"
        ),
    ))

# ── Aktuelles Jahr hervorheben ──
if show_current_year:
    current_year_df = df[df.index.year == CURRENT_YEAR]
    if len(current_year_df) >= 20:
        closes = current_year_df["Close"].values.astype(float)
        if closes[0] > 0:
            log_curve = (np.log(closes) - np.log(closes[0])) * 100
            # Auf 252 interpolieren (gleiche Laenge wie Kohorten)
            n_orig = len(log_curve)
            x_orig = np.linspace(0, 251, n_orig)
            x_new = np.arange(n_orig)  # Nur bis zum aktuellen Tag
            # Mapping: aktueller Handelstag -> Position auf 252-Skala
            current_x = np.linspace(0, 251 * n_orig / 252, n_orig).tolist()
            current_y = log_curve.tolist()

            fig.add_trace(go.Scatter(
                x=current_x, y=current_y,
                mode="lines",
                name=f"{CURRENT_YEAR} (aktuell)",
                line=dict(color="#F1C40F", width=3, dash="solid"),
                hovertemplate=(
                    f"<b>{CURRENT_YEAR}</b><br>"
                    "Handelstag %{x:.0f}<br>"
                    "%{y:+.2f}%<extra></extra>"
                ),
            ))

fig.add_hline(y=0, line_dash="dash",
              line_color="rgba(255,255,255,0.25)", line_width=1)

fig = apply_se_theme(fig, title="", height=500)

st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2. BALKEN-CHART: Ø-Performance pro Kohorte
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("### Ø-Jahresrendite nach Dekaden-Endziffer")

bar_x      = []
bar_y      = []
bar_colors = []
bar_text   = []
bar_hover  = []

for digit in range(10):
    d = decade_data[digit]
    bar_x.append(f"X{digit}")
    val = d["avg_return"] if d["n"] > 0 else 0.0
    bar_y.append(round(val, 2) if val is not None else 0.0)

    is_current = (digit == CURRENT_DIGIT)
    if is_current:
        bar_colors.append("#F1C40F")   # gelb für aktuelles Jahr
    elif val is not None and val >= 0:
        bar_colors.append("#2ECC71")
    else:
        bar_colors.append("#E74C3C")

    wr  = d["win_rate"]  if d["n"] > 0 else None
    n   = d["n"]
    vol = d["volatility"] if d["n"] > 0 else None
    suffix = " ✨ aktuell" if is_current else ""
    bar_text.append(
        f"{val:+.1f}%" if val is not None else "—"
    )
    bar_hover.append(
        f"<b>X{digit}-Jahre{suffix}</b><br>"
        f"Ø Rendite: {val:+.2f}%<br>"
        f"Win-Rate: {wr:.0f}%<br>"
        f"Volatilität: {vol:.1f}%<br>"
        f"n={n} Jahre<extra></extra>"
        if val is not None else f"<b>X{digit}-Jahre</b><br>Keine Daten<extra></extra>"
    )

fig2 = go.Figure(go.Bar(
    x=bar_x,
    y=bar_y,
    marker_color=bar_colors,
    marker_opacity=0.88,
    text=bar_text,
    textposition="outside",
    customdata=list(range(10)),
    hovertemplate=bar_hover,
))

fig2.add_hline(y=0, line_dash="dash",
               line_color="rgba(255,255,255,0.25)", line_width=1)

fig2 = apply_se_theme(fig2, title="", height=380)

st.plotly_chart(fig2, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# 2b. ANOMALIE-RADAR (KI)
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### Anomalie-Radar (KI)")
try:
    from shared.anomaly_engine import compute_ticker_anomaly_score
    with st.spinner("Anomalie-Radar berechnet..."):
        radar = compute_ticker_anomaly_score(df, lookback_days=10)
    if "error" not in radar:
        r_score = radar["anomaly_score"]
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
            f'Isolation Forest vergleicht die letzten 10 Handelstage mit '
            f'{radar["n_comparisons"]} historischen Fenstern am gleichen Kalenderzeitpunkt.'
        )
    else:
        st.caption(radar["error"])
except Exception as _e:
    st.caption(f"Anomalie-Radar nicht verfuegbar: {_e}")

# ══════════════════════════════════════════════════════════════════════════════
# 3. DATENTABELLE
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("### Übersicht nach Kohorte")

def _color_val(v):
    if not isinstance(v, (int, float)) or pd.isna(v):
        return ""
    if v > 0:
        return "color: #2ECC71; font-weight: bold"
    elif v < 0:
        return "color: #E74C3C; font-weight: bold"
    return ""

display_df = summary_df.drop(columns=["Ziffer"]).reset_index(drop=True)
# Ziffer pro Zeile aus summary_df merken (gleicher Index)
_digit_map = summary_df["Ziffer"].reset_index(drop=True)

def _highlight_current(row):
    digit = _digit_map.loc[row.name]
    if digit == CURRENT_DIGIT:
        return ["background-color: rgba(241,196,15,0.15)"] * len(row)
    return [""] * len(row)

styled = (
    display_df.style
    .apply(_highlight_current, axis=1, subset=None)
    .applymap(_color_val, subset=["Ø Rendite %", "Median %", "Win-Rate %"])
    .format({
        "Ø Rendite %":    lambda v: f"{v:+.2f}%" if pd.notna(v) else "—",
        "Median %":       lambda v: f"{v:+.2f}%" if pd.notna(v) else "—",
        "Win-Rate %":     lambda v: f"{v:.1f}%"  if pd.notna(v) else "—",
        "Volatilität %":  lambda v: f"{v:.2f}%"  if pd.notna(v) else "—",
    })
)

st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Kohorte":        st.column_config.TextColumn("Kohorte", width="small"),
        "Anzahl Jahre":   st.column_config.NumberColumn("n", width="small"),
        "Ø Rendite %":    st.column_config.TextColumn("Ø Rendite", width="small"),
        "Median %":       st.column_config.TextColumn("Median", width="small"),
        "Win-Rate %":     st.column_config.TextColumn("Win-Rate", width="small"),
        "Volatilität %":  st.column_config.TextColumn("Volatilität", width="small"),
        "Jahre":          st.column_config.TextColumn("Jahre in Kohorte", width="large"),
    },
)

# ══════════════════════════════════════════════════════════════════════════════
# 4. KONTEXT-PANEL: Was bedeutet das für das aktuelle Jahr?
# ══════════════════════════════════════════════════════════════════════════════

if show_context:
    d_current = decade_data[CURRENT_DIGIT]
    if d_current["n"] >= 2:
        st.markdown(f"### 🎯 Was bedeutet das für {CURRENT_YEAR}?")

        groups_all = {
            f"X{digit}": decade_data[digit]["returns"]
            for digit in range(10)
            if decade_data[digit]["n"] > 0
        }
        ctx = build_context_panel_data(groups_all, f"X{CURRENT_DIGIT}", "Jahr")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Kohorte", f"X{CURRENT_DIGIT}-Jahre")
        col2.metric("Ø Rendite", f"{ctx['mean']:+.2f}%")
        col3.metric("Median", f"{ctx['median']:+.2f}%")
        col4.metric("Win-Rate", f"{ctx['win_rate']:.0f}%")
        col5.metric("Volatilität (σ)", f"{ctx['std']:.2f}%")

        rating = ctx.get("rating", "—")
        st.markdown(
            f"**Historische Einordnung:** {rating}  \n"
            f"Beste X{CURRENT_DIGIT}-Jahr: **{ctx.get('best', 0):+.1f}%** · "
            f"Schlechteste: **{ctx.get('worst', 0):+.1f}%** · "
            f"n = {ctx['n']} Jahre ({', '.join(str(y) for y in sorted(d_current['years']))})"
        )

# ══════════════════════════════════════════════════════════════════════════════
# 5. BOX-PLOT: Rendite-Verteilung pro Kohorte
# ══════════════════════════════════════════════════════════════════════════════

if show_boxplot:
    st.markdown("### Rendite-Verteilung nach Kohorte")
    groups = {
        f"X{digit}": decade_data[digit]["returns"]
        for digit in range(10)
        if decade_data[digit]["n"] >= 2
    }
    if groups:
        fig_box = build_box_plot(
            groups=groups,
            colors=DECADE_COLORS,
            title=f"{ticker} — Jahresrenditen nach Dekaden-Endziffer",
            x_title="Dekaden-Endziffer",
            y_title="Log-Rendite (%)",
            current_key=f"X{CURRENT_DIGIT}",
        )
        st.plotly_chart(fig_box, use_container_width=True)

        with st.expander("So lesen Sie das Box-Plot-Diagramm"):
            st.markdown("""
**Box-Plots** zeigen die Verteilung der Jahresrenditen pro Dekaden-Kohorte auf einen Blick:

- **Box (Kasten):** Umfasst die mittleren 50% aller Werte (25. bis 75. Perzentil). Je schmaler die Box, desto konsistenter die Renditen.
- **Linie in der Box:** Der **Median** — die Hälfte aller Jahre lag darüber, die andere darunter.
- **Whiskers (Antennen):** Reichen bis zum 1,5-fachen des Interquartilsabstands. Werte innerhalb dieser Spanne gelten als typisch.
- **Punkte ausserhalb:** **Ausreisser** — ungewöhnlich starke oder schwache Jahre (z.B. Crash- oder Boom-Jahre).

**Interpretation:** Eine Box, die vollständig über der 0%-Linie liegt, zeigt eine historisch bullische Kohorte. Liegt sie darunter, war die Kohorte eher schwach. Die Breite der Box zeigt die Streuung — breitere Boxen bedeuten weniger Vorhersagbarkeit.
""")

# ══════════════════════════════════════════════════════════════════════════════
# 6. HEATMAP: Dekade × Monat
# ══════════════════════════════════════════════════════════════════════════════

if show_heatmap:
    st.markdown("### Ø Monatsrendite nach Dekade")
    fig_heat = build_decade_monthly_heatmap(df, ticker)
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Dateninfo ─────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Methodik"):
    st.markdown(f"""
    **Ticker:** {ticker}  
    **Datenzeitraum:** {data_start}–{data_end} ({total_years} vollständige Jahre)  
    **Normierung:** Erster Handelstag jedes Jahres = 0% (Log-Returns)  
    **Interpolation:** Jede Jahreskurve wird auf 252 Handelstage normiert (lineare Interpolation)  
    **Mindestlänge:** Jahre mit weniger als 200 Handelstagen werden ausgeschlossen  
    **Schalttage:** Kein Sonderhandling nötig — Interpolation auf 252 Punkte gleicht unterschiedliche Jahreslängen aus  
    **Aktuelle Kohorte:** {CURRENT_YEAR} → X{CURRENT_DIGIT} (gelb markiert)  
    **Glättung:** {smoothing}-Tage zentrierter Moving Average auf Ø-Kurve  
    """)
