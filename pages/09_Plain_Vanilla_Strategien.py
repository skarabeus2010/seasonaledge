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
    STRATEGIES, STRATEGY_CATEGORIES, apply_stop_loss, build_equity_curve, compute_strategy_stats,
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

    # ── Nur ausgewählte Strategie berechnen (Performance!) ──
    # Kacheln zeigen "?" bis sie ausgewählt werden
    all_results = {}

    def _calc_strategy(key):
        """Lazy: Berechnet Strategie nur bei Bedarf."""
        if key in all_results:
            return all_results[key]
        try:
            strat = STRATEGIES[key]
            trades = strat["func"](df)
            if use_stop and trades:
                trades = apply_stop_loss(raw_df, trades, stop_pct, stop_type)
            stats = compute_strategy_stats(trades) if trades else {}
            all_results[key] = {"trades": trades, "stats": stats}
        except Exception:
            all_results[key] = {"trades": [], "stats": {}}
        return all_results[key]

    # Ausgewählte Strategie sofort berechnen
    if "pv_selected" not in st.session_state:
        st.session_state["pv_selected"] = "sell_in_may"
    _calc_strategy(st.session_state["pv_selected"])

    # ── Kachel-Auswahl mit Tabs ──────────────────────
    st.markdown(
        f'<div style="text-align:center; margin-bottom:0.5rem;">'
        f'<span style="color:{SE_COLORS["text_muted"]}; font-size:13px; '
        f'letter-spacing:2px; text-transform:uppercase;">Strategie wählen</span>'
        f'<p style="color:{SE_COLORS["text_muted"]}; font-size:0.9rem; margin-top:0.3rem;">'
        f'Wählen Sie aus altbekannten Strategien eine, die zu Ihnen passt.</p></div>',
        unsafe_allow_html=True,
    )

    # Tabs nach Kategorie
    sorted_cats = sorted(STRATEGY_CATEGORIES.items(), key=lambda x: x[1]["order"])
    tab_labels = [cat["label"] for _, cat in sorted_cats]
    tabs = st.tabs(tab_labels)

    for tab_idx, (cat_key, cat_info) in enumerate(sorted_cats):
        with tabs[tab_idx]:
            cat_strategies = {k: v for k, v in STRATEGIES.items() if v.get("category") == cat_key}
            cat_keys = list(cat_strategies.keys())
            cols = st.columns(min(len(cat_keys), 5))

            for i, key in enumerate(cat_keys):
                strat = STRATEGIES[key]
                is_selected = (st.session_state["pv_selected"] == key)

                # CAGR nur anzeigen wenn bereits berechnet
                if key in all_results:
                    cagr = all_results[key]["stats"].get("cagr", 0)
                    _cagr_html = f'<div style="color:{"#34d399" if cagr > 0 else "#ff4444"};font-size:14px;font-weight:700;">{cagr:+.1f}%</div>'
                else:
                    _cagr_html = f'<div style="color:{SE_COLORS["text_muted"]};font-size:12px;">—</div>'

                with cols[i % len(cols)]:
                    _border = f"border:2px solid {SE_COLORS['accent_warm']};" if is_selected else "border:1px solid rgba(255,255,255,0.08);"
                    _bg = "background:linear-gradient(135deg,#131d2a,#1a2535);" if is_selected else "background:linear-gradient(135deg,#0f1923,#131d2a);"

                    st.markdown(
                        f'<div style="{_bg}{_border}border-radius:12px;padding:14px 8px;'
                        f'text-align:center;min-height:100px;">'
                        f'<div style="font-size:1.3rem;">{strat["icon"]}</div>'
                        f'<div style="color:{SE_COLORS["text_primary"]};font-size:12px;font-weight:600;'
                        f'margin:4px 0 2px;line-height:1.3;">{strat["name"]}</div>'
                        f'{_cagr_html}'
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
    with st.expander("📊 Alle Strategien vergleichen (berechnet alle — kann dauern)", expanded=False):
        # Alle Strategien berechnen wenn Vergleich geöffnet
        with st.spinner("Berechne alle 24 Strategien..."):
            for key in STRATEGIES:
                _calc_strategy(key)

        fig_cmp = go.Figure()
        ranking = []

        colors = ["#00d4aa", "#4d9fff", "#e8a425", "#ff6b6b", "#a78bfa",
                  "#f472b6", "#34d399", "#fbbf24", "#60a5fa", "#c084fc"]

        for i, (key, strat) in enumerate(STRATEGIES.items()):
            data = all_results.get(key, {"trades": [], "stats": {}})
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

### 💎 Ultimate Monthly Days System

Vereint die stärksten Monatstage, Feiertags-Effekte und die Weihnachtsrallye in einem System. Investiert an TDOM 1-4, 9-12 und den letzten 2 Handelstagen, zusätzlich am Tag vor jedem der 8 großen Börsenfeiertage, sowie in der erweiterten Santa-Claus-Phase (Thanksgiving bis 5. Januar). An allen übrigen Tagen ist das Kapital in Cash.

### 📡 KTI Long-Only (Jay Kaeppel)

Der Known Trends Index (KTI) ist ein zusammengesetzter Indikator, der bis zu 14 gleichzeitig aktive saisonale Trends misst. Jeder aktive Trend gibt +1 Punkt (September -1). Komponenten: Monatstage, November-Mai, Sommer-Rallye, Wahlzyklus-Phasen, 40-Wochen- und 212-Wochen-Zyklus, Dekaden-Trends, 20-Jahres-Zyklus und Feiertage. Bei KTI ≥ 3 wird investiert, darunter Cash.

### 🔥 KTI + Hebel

Die aggressive Variante des KTI-Systems. Bei KTI ≥ 5 (viele gleichzeitig bullische Trends) wird mit doppeltem Hebel investiert. Bei KTI 3-4 normal long, unter 3 in Cash. Der durchschnittliche Hebel pro Trade wird berechnet und auf die Rendite angewendet.

### 5️⃣ First Five Days of January

Einer der ältesten Januar-Indikatoren: Wenn die ersten 5 Handelstage im Januar einen Nettogewinn aufweisen, wird ab Februar eine Long-Position eröffnet und bis Dezember gehalten. Seit 1937 erzielte dieses Signal eine annualisierte Rendite von über 10 %.

### 🔚 Last Five Days of January

Komplementär zum First-Five-Indikator: Hier zählt die Performance der letzten 5 Handelstage im Januar. Ein positives Signal führte in über 83 % der Fälle zu höheren Kursen am Jahresende.

### 🌡️ Januar-Barometer

"So geht der Januar, so geht das Jahr." Wenn der gesamte Monat Januar einen Nettogewinn verzeichnet, wird ab Februar investiert. Seit 1937 wuchsen 1.000 USD bei bullischen Signalen auf fast 90.000 USD an.

### 🎆 Ein-Tages-Feiertagsstrategie

Der stärkste Einzeltag des Jahres: Kauf 2 Handelstage vor einem der 8 großen US-Börsenfeiertage, Verkauf 1 Handelstag vor dem Feiertag. Ein einziger Tag pro Feiertag — aber konstant profitabel seit 1933.

### 🎇 Ultimate Holiday Trading System (UHTS)

Erweiterte Feiertagsstrategie mit Hebel: 3 Handelstage vor dem Feiertag Long, am Tag unmittelbar davor wird auf ~1,5x Hebel erhöht, Ausstieg 3 Handelstage danach. Obwohl man nur ~18 % der Zeit im Markt ist, liefert das System bemerkenswerte Ergebnisse.

### 🎄 Nach-Weihnachten bis Silvester

Das kürzeste Zeitfenster aller Strategien: Kauf am ersten Handelstag nach Weihnachten, Verkauf am letzten Handelstag des Jahres (Silvester). In den letzten 107 Jahren war diese Phase in 78,7 % der Fälle profitabel.

### 2️⃣ Zweiter Handelstag des Monats

Microstructure-Effekt: Kauf zum Handelsschluss am 1. Handelstag, Verkauf am 2. Handelstag. Dies ist historisch der stärkste Einzeltag des Monats — institutionelle Mittelflüsse am Monatsanfang treiben die Kurse.

### 📆 Mid-Decade Rallye

Langfristiger Intradekaden-Trend: Kauf am 30. September eines auf "4" endenden Jahres, Verkauf am 31. März des auf "6" endenden Jahres. Dieser 18-monatige Zeitraum erzielte seit 1900 einen durchschnittlichen Gewinn von über 40 %.

### 🔄 20-Jahres-Zyklus

Der seltenste aller Zyklen: Nur alle 20 Jahre. Kauf am 30. September eines auf "2" endenden Jahres in einem geraden Jahrzehnt (z.B. 1902, 1922, 1982), Verkauf am 31. Dezember des auf "5" endenden Jahres. Bisheriger Durchschnittsgewinn: über 60 %.

### 🗳️ Wahljahr letzte 7 Monate

Investiert von Ende Mai bis Jahresende im Präsidentschaftswahljahr. Seit 1900 war dieses Fenster in über 80 % der Fälle profitabel mit einem durchschnittlichen Gewinn von 10,5 %. Hintergrund: Im Wahljahr wird Fiskalpolitik aufgedreht.

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
