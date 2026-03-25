"""
SeasonAlpha — Crash-Fruehwarnung (KI)
=========================================
Isolation Forest Regime-Erkennung auf SPY.
Ampelsystem + Erklaerung + historische Regime-Phasen.
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
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import SE_COLORS
from shared.data import download_data, preprocess
from shared.charts import apply_se_theme
from shared.anomaly_engine import compute_market_regime, TRAFFIC_LIGHT_LABELS

st.set_page_config(
    page_title="Crash-Fruehwarnung — SeasonAlpha",
    page_icon="🚨",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

# ── Daten laden ──────────────────────────────────────
st.markdown("## Crash-Fruehwarnung (KI)")
st.caption("Isolation Forest Regime-Erkennung auf Basis des S&P 500 (SPY)")

with st.spinner("Lade SPY Daten..."):
    raw_df = download_data("SPY")

if raw_df is None or raw_df.empty:
    st.error("Keine Daten fuer SPY verfuegbar.")
    st.stop()

df = preprocess(raw_df)

# ── Regime berechnen ─────────────────────────────────
with st.spinner("KI analysiert Markt-Regime..."):
    regime = compute_market_regime(df)

tl = TRAFFIC_LIGHT_LABELS.get(regime["traffic_light"], TRAFFIC_LIGHT_LABELS["grey"])

# ── Ampel-Anzeige ────────────────────────────────────
st.markdown("---")

ac1, ac2 = st.columns([1, 3])

with ac1:
    st.markdown(
        f'<div style="background:#0c1420;border:3px solid {tl["color"]};border-radius:20px;'
        f'padding:2rem;text-align:center;">'
        f'<div style="font-size:4rem;">{tl["emoji"]}</div>'
        f'<div style="color:{tl["color"]};font-weight:800;font-size:1.3rem;margin-top:.5rem;">{tl["label"]}</div>'
        f'<div style="color:#5a6e85;font-size:.85rem;margin-top:.3rem;">Risk-Score: {regime["risk_score"]:.0f}/100</div>'
        f'</div>', unsafe_allow_html=True)

with ac2:
    st.markdown(f'### {tl["desc"]}')
    st.markdown("")

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Risk-Score", f'{regime["risk_score"]:.0f}/100')
    mc2.metric("Volatilitaet (5d)", f'{regime.get("volatility_5d", 0):.3f}%')
    mc3.metric("Volatilitaet (20d)", f'{regime.get("volatility_20d", 0):.3f}%')
    mc4.metric("Drawdown", f'{regime.get("drawdown", 0):.1f}%')

    mc5, mc6 = st.columns(2)
    mc5.metric("Rendite (5d)", f'{regime.get("return_5d", 0):+.2f}%')
    mc6.metric("Rendite (20d)", f'{regime.get("return_20d", 0):+.2f}%')

# ── SPY Chart mit Regime-Markierung ──────────────────
st.markdown("---")
st.subheader("S&P 500 (SPY) — letzte 6 Monate")

recent = df.tail(126)
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=recent.index, y=recent["Close"],
    mode="lines",
    line=dict(color=SE_COLORS["accent_blue"], width=1.5),
    fill="tozeroy", fillcolor="rgba(77,159,255,0.05)",
    hovertemplate="%{x|%d.%m.%Y}: %{y:.2f}<extra></extra>",
))

fig = apply_se_theme(fig, title="SPY — 6 Monate", height=350, show_legend=False)
fig.update_yaxes(title="Kurs (USD)")
st.plotly_chart(fig, use_container_width=True)

# ── Erklaerung ───────────────────────────────────────
st.markdown("---")
st.subheader("So funktioniert die Crash-Fruehwarnung")

st.markdown("""
**Methode: Isolation Forest (Machine Learning)**

Die KI analysiert taeglich 7 Markt-Features des S&P 500:

| Feature | Beschreibung |
|---------|-------------|
| Tagesrendite | Heutige prozentuale Veraenderung |
| Volatilitaet (5d) | Standardabweichung der letzten 5 Handelstage |
| Volatilitaet (10d) | Standardabweichung der letzten 10 Handelstage |
| Volatilitaet (20d) | Standardabweichung der letzten 20 Handelstage |
| Rendite (5d) | Kumulative Rendite der letzten 5 Tage |
| Rendite (20d) | Kumulative Rendite der letzten 20 Tage |
| Drawdown | Abstand vom 20-Tage-Hoch |

Der Isolation Forest lernt aus der gesamten Historie was "normales" Marktverhalten ist.
Tage die stark von diesem Muster abweichen erhalten einen hohen Anomalie-Score.

**Ampel-System:**

| Ampel | Risk-Score | Bedeutung |
|-------|-----------|-----------|
| 🟢 Ruhig | 0–39 | Markt verhaelt sich normal — keine Auffaelligkeiten |
| 🟡 Erhoehte Vorsicht | 40–69 | Ungewoehnliche Muster erkannt — erhoehte Aufmerksamkeit |
| 🔴 Stress-Regime | 70–100 | Stark anomales Verhalten — historisch selten |

**Wichtig:** Die Ampel ist ein statistisches Fruehwarnsystem, keine Handelsempfehlung.
Ein rotes Signal bedeutet nicht zwingend einen Crash, sondern dass sich der Markt
ungewoehnlich verhaelt. Historisch gingen viele (aber nicht alle) groessere Korrekturen
eine erhoehte Anomalie-Phase voraus.
""")

# ── Disclaimer ──
st.markdown("---")
st.caption(
    "Historische Muster garantieren keine zukuenftigen Ergebnisse. "
    "Keine Anlageberatung. Der Isolation Forest wurde auf SPY-Daten trainiert."
)
