"""
SeasonAlpha — Plain Vanilla Strategien
=========================================
10 saisonale Trading-Strategien mit fixen Ein-/Ausstiegsregeln.
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

from shared.design import inject_se_css
from shared.footer import render_footer
from shared.ticker_select import ticker_select
from shared.constants import SE_COLORS, DEFAULT_TICKER
from shared.charts import apply_se_theme
from shared.data import download_data, preprocess
from shared.strategies.plain_vanilla import (
    STRATEGIES, apply_stop_loss, build_equity_curve, compute_strategy_stats,
)

# ── Page Config ──────────────────────────────────────
st.set_page_config(
    page_title="Plain Vanilla Strategien — SeasonAlpha",
    page_icon="🎯",
    layout="wide",
)
inject_se_css()

_PLOTLY_CFG = {"displayModeBar": False}


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    # ── Sidebar ──────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🎯 Plain Vanilla Strategien")
        st.markdown("---")

        ticker = ticker_select(key="pv_ticker", default=DEFAULT_TICKER)

        st.markdown("---")
        st.markdown("### Zeitraum")
        period_options = [5, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider(
            "Analyse-Zeitraum (Jahre)",
            options=period_options, value="Max",
            format_func=lambda x: str(x), key="pv_period",
        )

        st.markdown("---")
        st.markdown("### Stop-Loss")
        use_stop = st.checkbox("Stop-Loss aktivieren", value=False, key="pv_stop")
        stop_pct = 0.0
        stop_type = "fixed"
        if use_stop:
            stop_pct = st.slider("Stop-Loss (%)", 1.0, 20.0, 8.0, 0.5, key="pv_stop_pct")
            stop_type = st.radio("Typ", ["fixed", "trailing"], index=0, key="pv_stop_type",
                                 format_func=lambda x: "Fest" if x == "fixed" else "Trailing")

    # ── Daten laden ──────────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)

    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return

    df = preprocess(raw_df)

    # Zeitraum filtern
    if years_back_raw != "Max":
        cutoff_year = datetime.now().year - int(years_back_raw)
        df = df[df["year"] >= cutoff_year]
        raw_df = raw_df[raw_df.index >= df.index[0]] if len(df) > 0 else raw_df

    from shared.trading_day_header import render_trading_day_header
    render_trading_day_header(df)

    # ── Alle Strategien vorberechnen (für Kachel-Vorschau) ──
    all_results = {}
    for key, strat in STRATEGIES.items():
        try:
            trades = strat["func"](df)
            if use_stop and trades:
                trades = apply_stop_loss(raw_df, trades, stop_pct, stop_type)
            stats = compute_strategy_stats(trades) if trades else {}
            all_results[key] = {"trades": trades, "stats": stats}
        except Exception:
            all_results[key] = {"trades": [], "stats": {}}

    # ── Kachel-Auswahl (2×5 Grid) ──────────────────────
    st.markdown(
        f'<div style="text-align:center; margin-bottom:1.2rem;">'
        f'<span style="color:{SE_COLORS["text_muted"]}; font-size:13px; '
        f'letter-spacing:2px; text-transform:uppercase;">Strategie wählen</span>'
        f'<p style="color:{SE_COLORS["text_muted"]}; font-size:0.9rem; margin-top:0.3rem;">'
        f'Wählen Sie aus altbekannten Strategien eine, die zu Ihnen passt.</p></div>',
        unsafe_allow_html=True,
    )

    # Initialer State
    if "pv_selected" not in st.session_state:
        st.session_state["pv_selected"] = "sell_in_may"

    keys = list(STRATEGIES.keys())
    _cols_per_row = 4 if len(keys) > 10 else 5
    _n_rows = (len(keys) + _cols_per_row - 1) // _cols_per_row
    for row in range(_n_rows):
        cols = st.columns(_cols_per_row)
        for col_idx in range(_cols_per_row):
            idx = row * _cols_per_row + col_idx
            if idx >= len(keys):
                break
            key = keys[idx]
            strat = STRATEGIES[key]
            stats = all_results[key]["stats"]
            cagr = stats.get("cagr", 0)
            is_selected = (st.session_state["pv_selected"] == key)

            with cols[col_idx]:
                _border = f"border:2px solid {SE_COLORS['accent_warm']};" if is_selected else "border:1px solid rgba(255,255,255,0.08);"
                _bg = "background:linear-gradient(135deg,#131d2a,#1a2535);" if is_selected else "background:linear-gradient(135deg,#0f1923,#131d2a);"

                st.markdown(
                    f'<div style="{_bg}{_border}border-radius:12px;padding:14px 6px;'
                    f'text-align:center;min-height:100px;overflow:visible;">'
                    f'<div style="font-size:1.3rem;">{strat["icon"]}</div>'
                    f'<div style="color:{SE_COLORS["text_primary"]};font-size:10px;font-weight:600;'
                    f'margin:4px 0 2px;line-height:1.3;word-wrap:break-word;">{strat["name"]}</div>'
                    f'<div style="color:{"#34d399" if cagr > 0 else "#ff4444"};font-size:14px;'
                    f'font-weight:700;">{cagr:+.1f}%</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("Auswählen", key=f"pv_btn_{key}",
                             use_container_width=True, type="primary" if is_selected else "secondary"):
                    st.session_state["pv_selected"] = key
                    st.rerun()

    # ── Ausgewählte Strategie ────────────────────────────
    sel_key = st.session_state["pv_selected"]
    sel_strat = STRATEGIES[sel_key]
    sel_data = all_results[sel_key]
    sel_trades = sel_data["trades"]
    sel_stats = sel_data["stats"]

    st.markdown("---")

    # Info-Box
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#0f1923,#131d2a);'
        f'border:1px solid rgba(77,159,255,0.15);border-radius:12px;padding:16px 20px;margin-bottom:1rem;">'
        f'<div style="color:{SE_COLORS["accent_blue"]};font-size:1.1rem;font-weight:700;margin-bottom:6px;">'
        f'{sel_strat["icon"]} {sel_strat["name"]}</div>'
        f'<div style="color:{SE_COLORS["text_primary"]};font-size:0.9rem;margin-bottom:4px;">'
        f'{sel_strat["desc"]}</div>'
        f'<div style="color:{SE_COLORS["text_muted"]};font-size:0.85rem;">'
        f'{sel_strat["info"]}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # KPI-Karten
    if sel_stats:
        _card = (
            'background:linear-gradient(135deg,#0f1923,#131d2a);'
            'border:1px solid rgba(255,255,255,0.08);border-radius:10px;'
            'padding:12px 16px;text-align:center;'
        )
        _lbl = 'color:#8899aa;font-size:10px;text-transform:uppercase;letter-spacing:1px;'
        _val = 'font-size:18px;font-weight:700;font-variant-numeric:tabular-nums;margin:2px 0;'

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            _clr = "#34d399" if sel_stats["cagr"] > 0 else "#ff4444"
            st.markdown(f'<div style="{_card}"><div style="{_lbl}">CAGR</div>'
                        f'<div style="{_val}color:{_clr};">{sel_stats["cagr"]:+.1f}%</div></div>',
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div style="{_card}"><div style="{_lbl}">Max Drawdown</div>'
                        f'<div style="{_val}color:#ff4444;">{sel_stats["max_drawdown"]:.1f}%</div></div>',
                        unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div style="{_card}"><div style="{_lbl}">Win-Rate</div>'
                        f'<div style="{_val}color:{SE_COLORS["text_primary"]};">{sel_stats["win_rate"]:.0f}%</div></div>',
                        unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div style="{_card}"><div style="{_lbl}">Trades</div>'
                        f'<div style="{_val}color:{SE_COLORS["text_primary"]};">{sel_stats["n_trades"]}</div></div>',
                        unsafe_allow_html=True)
        with c5:
            st.markdown(f'<div style="{_card}"><div style="{_lbl}">$1.000 Endwert</div>'
                        f'<div style="{_val}color:{SE_COLORS["accent_warm"]};">${sel_stats["final_equity"]:,.0f}</div></div>',
                        unsafe_allow_html=True)

    # Equity-Chart
    if sel_trades:
        equity = build_equity_curve(sel_trades, start_capital=1000.0)
        if equity:
            eq_dates = [e[0] for e in equity]
            eq_vals = [e[1] for e in equity]

            fig = go.Figure()

            # Baseline für Fill (unsichtbar)
            _y_min = min(eq_vals) * 0.95
            fig.add_trace(go.Scatter(
                x=eq_dates, y=[_y_min] * len(eq_dates),
                mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=eq_dates, y=eq_vals,
                mode="lines",
                fill="tonexty",
                fillcolor="rgba(0,212,170,0.08)",
                line=dict(color=SE_COLORS["accent"], width=2.5),
                name="Portfolio",
                hovertemplate="<b>%{x|%d.%m.%Y}</b><br>$%{y:,.0f}<extra></extra>",
            ))

            fig.add_hline(y=1000, line_dash="dot", line_color="rgba(255,255,255,0.2)")

            _stop_info = f" (SL {stop_pct}% {stop_type})" if use_stop else ""
            fig = apply_se_theme(
                fig,
                title=f"{sel_strat['icon']} {sel_strat['name']} — {ticker} · $1.000 Portfolio{_stop_info}",
                height=450,
            )
            fig.update_yaxes(tickprefix="$", tickformat=",")
            st.plotly_chart(fig, use_container_width=True, config=_PLOTLY_CFG)

    # Trade-Tabelle
    if sel_trades:
        with st.expander(f"📋 Alle {len(sel_trades)} Trades", expanded=False):
            trade_df = pd.DataFrame(sel_trades)
            trade_df["entry_date"] = pd.to_datetime(trade_df["entry_date"]).dt.strftime("%d.%m.%Y")
            trade_df["exit_date"] = pd.to_datetime(trade_df["exit_date"]).dt.strftime("%d.%m.%Y")
            trade_df["return_pct"] = trade_df["return_pct"].apply(lambda x: f"{x:+.2f}%")

            display_cols = ["entry_date", "exit_date", "entry_price", "exit_price", "return_pct"]
            if "stopped" in trade_df.columns:
                display_cols.append("stopped")

            trade_df = trade_df[display_cols]
            trade_df.columns = ["Einstieg", "Ausstieg", "Entry $", "Exit $", "Rendite"] + \
                               (["Stop?"] if "stopped" in display_cols else [])

            st.dataframe(trade_df, use_container_width=True, hide_index=True)

    # ── Vergleichs-Modus ─────────────────────────────────
    with st.expander("📊 Alle Strategien vergleichen", expanded=False):
        fig_cmp = go.Figure()
        ranking = []

        colors = ["#00d4aa", "#4d9fff", "#e8a425", "#ff6b6b", "#a78bfa",
                  "#f472b6", "#34d399", "#fbbf24", "#60a5fa", "#c084fc"]

        for i, (key, strat) in enumerate(STRATEGIES.items()):
            data = all_results[key]
            if not data["trades"]:
                continue
            equity = build_equity_curve(data["trades"], 1000.0)
            if equity:
                fig_cmp.add_trace(go.Scatter(
                    x=[e[0] for e in equity],
                    y=[e[1] for e in equity],
                    mode="lines",
                    name=strat["name"],
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f"<b>{strat['name']}</b><br>%{{x|%Y}}: $%{{y:,.0f}}<extra></extra>",
                ))

            stats = data["stats"]
            ranking.append({
                "Strategie": strat["name"],
                "CAGR": f'{stats.get("cagr", 0):+.1f}%',
                "Max DD": f'{stats.get("max_drawdown", 0):.1f}%',
                "Win-Rate": f'{stats.get("win_rate", 0):.0f}%',
                "Trades": stats.get("n_trades", 0),
                "Endwert": f'${stats.get("final_equity", 0):,.0f}',
                "Sharpe": f'{stats.get("sharpe", 0):.2f}',
                "_cagr": stats.get("cagr", 0),
            })

        fig_cmp.add_hline(y=1000, line_dash="dot", line_color="rgba(255,255,255,0.2)")
        fig_cmp = apply_se_theme(fig_cmp, title=f"Alle Strategien im Vergleich — {ticker} · $1.000 Start", height=500)
        fig_cmp.update_yaxes(tickprefix="$", tickformat=",", type="log")
        st.plotly_chart(fig_cmp, use_container_width=True, config=_PLOTLY_CFG)

        # Ranking-Tabelle
        if ranking:
            rank_df = pd.DataFrame(ranking).sort_values("_cagr", ascending=False).drop(columns=["_cagr"]).reset_index(drop=True)
            rank_df.index = rank_df.index + 1
            rank_df.index.name = "#"
            st.dataframe(rank_df, use_container_width=True)

    # ── Erklärungen ──
    with st.expander("ℹ️ Erklärungen zu den Plain Vanilla Strategien"):
        st.markdown("""
### Was sind Plain Vanilla Strategien?

Plain Vanilla Strategien sind einfache, regelbasierte Handelsansätze mit fixen Ein- und Ausstiegszeitpunkten. Sie benötigen keine komplexe Optimierung — die Regeln stehen fest und werden Jahr für Jahr identisch angewendet.

---

### 📅 Sell in May (Halloween-Effekt)

Die bekannteste saisonale Strategie überhaupt. "Sell in May and go away, but remember to come back in November." Investiert von November bis April, Cash von Mai bis Oktober. Der Effekt ist seit über 100 Jahren in fast allen Aktienmärkten nachweisbar.

### 📊 LBR-gefilterte November-Mai

Eine Verfeinerung von Sell in May: Statt fix am letzten Oktober-Tag einzusteigen, wartet diese Strategie auf ein bullisches Signal des LBR-Oszillators (Linda Bradford Raschke). Ebenso wird im Frühjahr erst bei einem bärischen LBR-Signal ausgestiegen. Der Filter vermeidet Einstiege in schwache Marktphasen.

### 📈 Nasdaq-Trend (November bis Juni)

Erweiterte Sell-in-May Variante: 8 Monate investiert (November bis Juni) statt nur 6. Besonders bei wachstumsstarken Titeln wie dem Nasdaq zeigt der Juni oft noch positive Renditen, die durch einen früheren Ausstieg im Mai verpasst werden.

### 🔄 Month-End Muster

Nutzt den statistisch gut belegten Turn-of-the-Month-Effekt: Rund um den Monatswechsel fließen institutionelle Gelder (Gehälter, Pensionsfonds, Sparraten) in den Markt. Einstieg am vorletzten Handelstag, Ausstieg am 4. Handelstag des Folgemonats.

### 🗓️ Monthly 10 System

Kombiniert mehrere Intra-Monat-Effekte: Die ersten 4 Handelstage (Monatsanfang), TDOM 9-12 (Monatsmitte) und die letzten 2 Handelstage (Monatsende) sind historisch die stärksten Phasen. An den restlichen Tagen ist das Kapital in Cash.

### 🎅 Santa Claus Rallye (Erweitert)

Die erweiterte Weihnachtsrallye: Einstieg 3 Handelstage vor Thanksgiving (Ende November), Ausstieg am 5. Handelstag im Januar. Deckt die saisonal stärkste Phase des Jahres ab — Jahresend-Rallye, Window Dressing und Januar-Effekt.

### 🔁 212-Wochen-Zyklus

Ein langfristiger Marktzyklus von 1.484 Kalendertagen (~4,06 Jahre). Startpunkt: 16. Mai 1938. Bei jedem Zyklus-Start wird für 6 Monate investiert. Der Zyklus basiert auf der Beobachtung, dass Aktienmärkte in regelmäßigen Mehrjahres-Wellen schwingen.

### ⚡ 40-Wochen-Zyklus (Bullische Phase)

Ein kürzerer Zyklus von 280 Kalendertagen (~40 Wochen). Startpunkt: 21. April 1967. Die erste Hälfte des Zyklus (20 Wochen = 140 Tage) gilt als bullische Phase, die zweite als bärisch. Investiert wird nur in der ersten Hälfte.

### 🏛️ Midterm Election Trade

Kurzfristiger Trade rund um die US-Zwischenwahlen (alle 4 Jahre im November des 2. Präsidentschaftsjahres). Einstieg 5 Handelstage vor der Wahl, Ausstieg 3 Handelstage danach. Nutzt die Unsicherheitsauflösung nach dem Wahlergebnis.

### 🚫 September-Vermeidung

Die einfachste Strategie: 11 Monate investiert, nur im September in Cash. September ist historisch der schwächste Börsenmonat — in über 100 Jahren Dow Jones im Schnitt negativ. Durch Vermeidung dieses einen Monats verbessert sich die Gesamtperformance.

### 🇺🇸 Ultimate Election Cycle System (UECS)

Das umfassendste Präsidentenzyklus-System. Kombiniert 6 verschiedene Zeitfenster innerhalb des 4-Jahres-Zyklus: (1) Kurzfristiger Trade um die Midterm-Wahl, (2) März bis Juli des Vorwahljahres, (3) Oktober des Midterm-Jahres bis September des Vorwahljahres, (4) November/Dezember des Vorwahljahres, (5) Juni bis Dezember des Wahljahres, und (6) das gesamte Post-Election-Jahr wenn es auf "5" endet (z.B. 2025). Überlappende Phasen werden automatisch zusammengeführt.

---

### Hinweise zur Interpretation

- **CAGR** (Compound Annual Growth Rate): Durchschnittliche jährliche Rendite unter Berücksichtigung des Zinseszinseffekts.
- **Max Drawdown**: Größter Rückgang vom Höchststand — zeigt das Verlustrisiko der Strategie.
- **Win-Rate**: Anteil der profitablen Trades. Eine hohe Win-Rate allein sagt wenig aus — die Höhe der Gewinne und Verluste ist entscheidend.
- **Stop-Loss**: Optional in der Sidebar aktivierbar. Begrenzt Verluste pro Trade, kann aber auch profitable Trades vorzeitig beenden.
- Die Ergebnisse basieren auf historischen Daten und garantieren keine zukünftigen Renditen.
        """)

    # ── Disclaimer ──
    st.markdown("---")
    st.caption("Historische Muster garantieren keine zukünftigen Ergebnisse. Keine Anlageberatung.")

    render_footer()


main()
