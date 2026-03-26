# pages/9_🚦_Strategien.py
# Saisonalstrategien-Übersicht:
#   Tab 1 — Januar Trifecta Ampelsystem (SCR + First Five Days + January Barometer)
#   Tab 2 — Kaeppel Jahresübersicht (KTI, Election Cycle, Decennial)
#   Tab 3 — Strategie-Bibliothek (65+ Strategien, filterbar)

import sys, os, pathlib
try:
    _project_dir = str(pathlib.Path(__file__).resolve().parent.parent)
except NameError:
    _project_dir = os.getcwd()
if not os.path.isdir(os.path.join(_project_dir, "shared")):
    for _candidate in [os.getcwd(),
                       os.path.dirname(os.path.abspath(sys.argv[-1])) if sys.argv else ""]:
        if os.path.isdir(os.path.join(_candidate, "shared")):
            _project_dir = _candidate
            break
if _project_dir not in sys.path:
    sys.path.insert(0, _project_dir)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from shared.yahoo_downloader import download_data, preprocess
from shared.ticker_select import ticker_select
from shared.constants import DEFAULT_TICKER
from shared.strategies import januar_trifecta, kaeppel, STRATEGIES
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS
from shared.strategies.definitions import (
    KATEGORIEN, STAERKEN,
    get_strategies_by_category,
    get_strategies_by_strength,
)

st.set_page_config(
    page_title="SeasonAlpha – Strategien",
    page_icon="🚦",
    layout="wide",
)

from shared.design import inject_se_css
from shared.footer import render_footer
inject_se_css()

# ── Sidebar ────────────────────────────────────────────────────────────────────

analyse_jahr = datetime.now().year
last_election = 2024

with st.sidebar:
    st.header("⚙️ Einstellungen")
    ticker = ticker_select(key="tri_ticker", default=DEFAULT_TICKER)
    st.divider()
    show_current_year = st.checkbox(
        f"📍 Aktuelles Jahr ({analyse_jahr}) einblenden",
        value=True,
        help="Zeigt den bisherigen Kursverlauf des aktuellen Jahres als goldene Linie.",
    )
    st.divider()
    st.caption("Daten via Yahoo Finance · NYSE-Kalendar")

# ── Daten laden ────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Kursdaten werden geladen …")
def load_data(ticker: str) -> pd.DataFrame:
    raw = download_data(ticker)
    if raw is None or len(raw) == 0:
        raise ValueError(f"Keine Daten für '{ticker}' gefunden.")
    return preprocess(raw)

try:
    df = load_data(ticker)
    if df is None or len(df) == 0:
        raise ValueError("Leerer DataFrame")
except Exception as e:
    st.error(f"Fehler beim Laden der Daten für **{ticker}**: {e}")
    st.stop()

# ── Tabs ───────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "🚦 Januar Trifecta",
    "📊 Kaeppel Jahresübersicht",
    "📚 Strategie-Bibliothek",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — JANUAR TRIFECTA AMPELSYSTEM
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader(f"🚦 Januar Trifecta Ampelsystem — {analyse_jahr}")
    st.caption(
        "Drei Signale kombiniert ergeben ein Jahresprognose-Signal nach Yale Hirsch / "
        "Stock Trader's Almanac. Alle drei positiv → statistisch starkes Bullen-Jahr."
    )

    # Trifecta berechnen
    try:
        result = januar_trifecta.calculate_trifecta(df, analyse_jahr)
    except Exception as e:
        st.warning(f"Berechnung nicht möglich: {e}. "
                   "Möglicherweise fehlen Daten für das gewählte Jahr.")
        result = None

    if result:
        # ── Ampel-Anzeige ──────────────────────────────────────────────────
        col_ampel, col_text = st.columns([1, 3])

        with col_ampel:
            st.markdown(
                f"""
                <div style="
                    background-color: {result['farbe']};
                    border-radius: 16px;
                    padding: 32px 24px;
                    text-align: center;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                ">
                    <div style="font-size: 64px;">{result['emoji']}</div>
                    <div style="font-size: 28px; font-weight: bold;
                                color: white; margin-top: 8px;">
                        {result['signal']}
                    </div>
                    <div style="font-size: 14px; color: rgba(255,255,255,0.85);
                                margin-top: 6px;">
                        {result['erfuellt_count']} / 3 erfüllt
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_text:
            st.markdown(f"### {result['interpretation']}")
            st.markdown("---")

            # Drei Bedingungen im Detail
            bedingungen_info = {
                "santa_claus_rally": {
                    "label": "🎅 Santa Claus Rally",
                    "beschreibung": "Letzte 5 Handelstage Dez + erste 2 Jan",
                },
                "first_five_days": {
                    "label": "5️⃣ First Five Days",
                    "beschreibung": "Erste 5 Handelstage im Januar",
                },
                "january_barometer": {
                    "label": "🌡️ January Barometer",
                    "beschreibung": "Gesamte Januar-Performance",
                },
            }

            for key, info in bedingungen_info.items():
                b = result["bedingungen"][key]
                if b.get("erfuellt") is None:
                    icon, farbe = "⚪", "#6c757d"
                    rendite_txt = "Keine Daten"
                elif b["erfuellt"]:
                    icon, farbe = "✅", "#2ECC71"
                    rendite_txt = f"+{b['rendite']:.2f}%"
                else:
                    icon, farbe = "❌", "#E74C3C"
                    rendite_txt = f"{b['rendite']:.2f}%"

                st.markdown(
                    f"""
                    <div style="border-left: 4px solid {farbe};
                                padding: 8px 16px; margin-bottom: 10px;
                                background: rgba(0,0,0,0.05); border-radius: 0 8px 8px 0;">
                        <strong>{icon} {info['label']}</strong>
                        &nbsp;&nbsp;
                        <span style="color:{farbe}; font-weight:bold;">{rendite_txt}</span>
                        <br>
                        <small style="color:#888;">{info['beschreibung']}</small>
                        {f'<br><small style="color:#aaa;">📅 {b["start_date"].strftime("%d.%m.%Y")} → {b["end_date"].strftime("%d.%m.%Y")}</small>' if b.get("start_date") else ""}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.divider()

    # ── Historische Trefferquote ───────────────────────────────────────────
    st.subheader("📈 Historische Auswertung")

    with st.spinner("Berechne historische Trifecta-Daten …"):
        try:
            history_df = januar_trifecta.calculate_trifecta_history(
                df, start_year=1990, end_year=datetime.now().year - 1
            )
        except Exception as e:
            history_df = None
            st.warning(f"Historische Auswertung nicht verfügbar: {e}")

    if history_df is not None and len(history_df) > 0:

        # Statistiken pro Signal
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        total = len(history_df)

        gruen_df  = history_df[history_df["Signal"] == "Grün"]
        gelb_df   = history_df[history_df["Signal"] == "Gelb"]
        orange_df = history_df[history_df["Signal"] == "Orange"]
        rot_df    = history_df[history_df["Signal"] == "Rot"]

        def _avg_rendite(sub_df):
            col = "Jahresrendite_Feb_Dez_%"
            vals = sub_df[col].dropna()
            return vals.mean() if len(vals) > 0 else float("nan")

        with col_s1:
            st.metric("🟢 Grün",
                      f"{len(gruen_df)}x ({len(gruen_df)/total*100:.0f}%)",
                      f"Ø {_avg_rendite(gruen_df):.1f}% (Feb–Dez)")
        with col_s2:
            st.metric("🟡 Gelb",
                      f"{len(gelb_df)}x ({len(gelb_df)/total*100:.0f}%)",
                      f"Ø {_avg_rendite(gelb_df):.1f}% (Feb–Dez)")
        with col_s3:
            st.metric("🟠 Orange",
                      f"{len(orange_df)}x ({len(orange_df)/total*100:.0f}%)",
                      f"Ø {_avg_rendite(orange_df):.1f}% (Feb–Dez)")
        with col_s4:
            st.metric("🔴 Rot",
                      f"{len(rot_df)}x ({len(rot_df)/total*100:.0f}%)",
                      f"Ø {_avg_rendite(rot_df):.1f}% (Feb–Dez)")

        # ── Durchschnittsverlauf je Ampelfarbe ──────────────────────────
        st.subheader("📈 Durchschnittsverlauf nach Ampelfarbe")

        import numpy as np

        MONTH_TICKS_252 = [int(i * 21) for i in range(12)]
        MONTH_LABELS_252 = ["Jan","Feb","Mar","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]

        farb_map = {
            "Grün": "#2ECC71", "Gelb": "#F1C40F",
            "Orange": "#E67E22", "Rot": "#E74C3C",
        }

        fig_curves = go.Figure()
        drawdown_data = {}

        for signal, color in farb_map.items():
            signal_years = history_df[history_df["Signal"] == signal]["Jahr"].tolist()
            curves = []
            for year in signal_years:
                ydf = df[df.index.year == year]
                if len(ydf) < 20:
                    continue
                closes = ydf["Close"].values.astype(float)
                if closes[0] <= 0:
                    continue
                norm = (closes / closes[0] - 1) * 100
                x_orig = np.linspace(0, 251, len(norm))
                interp = np.interp(np.arange(252), x_orig, norm)
                curves.append(interp)

            if len(curves) < 1:
                continue

            avg_curve = np.mean(curves, axis=0)

            fig_curves.add_trace(go.Scatter(
                x=list(range(252)), y=avg_curve.tolist(),
                mode="lines", name=f"{signal} (n={len(curves)})",
                line=dict(color=color, width=2.5),
                hovertemplate=f"<b>{signal}</b><br>HT %{{x}}<br>%{{y:+.2f}}%<extra></extra>",
            ))

            # Max Drawdown berechnen
            dd_list = []
            for c in curves:
                cum = c + 100  # Normiert auf 100
                peak = np.maximum.accumulate(cum)
                dd = ((cum - peak) / peak * 100)
                dd_list.append(float(dd.min()))
            drawdown_data[signal] = {
                "avg_dd": round(float(np.mean(dd_list)), 1),
                "worst_dd": round(float(min(dd_list)), 1),
                "n": len(curves),
                "avg_return": round(float(avg_curve[-1]), 1),
            }

        # ── Aktuelles Jahr als "We are here" Linie (nur bis heute) ──
        if show_current_year:
            current_year = datetime.now().year
            cydf = df[df.index.year == current_year]
            if len(cydf) >= 5:
                closes_cy = cydf["Close"].values.astype(float)
                if closes_cy[0] > 0:
                    n_days = len(closes_cy)
                    norm_cy = (closes_cy / closes_cy[0] - 1) * 100
                    # 1:1 Mapping: Handelstag i → x-Position i (kein Stretching!)
                    x_positions = list(range(n_days))
                    fig_curves.add_trace(go.Scatter(
                        x=x_positions, y=norm_cy.tolist(),
                        mode="lines", name=f"📍 {current_year} (aktuell)",
                        line=dict(color="#FFD700", width=3, dash="dash"),
                        hovertemplate=f"<b>{current_year}</b><br>HT %{{x}}<br>%{{y:+.2f}}%<extra></extra>",
                    ))
                    # Marker am letzten Punkt
                    fig_curves.add_trace(go.Scatter(
                        x=[n_days - 1], y=[float(norm_cy[-1])],
                        mode="markers+text",
                        marker=dict(color="#FFD700", size=10, symbol="diamond",
                                    line=dict(color="white", width=1.5)),
                        text=[f"  {current_year}"],
                        textposition="middle right",
                        textfont=dict(color="#FFD700", size=11, family="Arial Black"),
                        showlegend=False,
                        hoverinfo="skip",
                    ))

        fig_curves.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)", line_width=1)
        fig_curves = apply_se_theme(
            fig_curves,
            title=f"{ticker} — Ø Jahresverlauf nach Trifecta-Signal",
            height=450,
        )
        fig_curves.update_xaxes(
            tickmode="array", tickvals=MONTH_TICKS_252, ticktext=MONTH_LABELS_252,
        )
        fig_curves.update_yaxes(title="Rendite (%)", tickformat="+.1f", ticksuffix="%")
        st.plotly_chart(fig_curves, use_container_width=True)

        # ── Max Drawdown Übersicht ────────────────────────────────────
        st.subheader("📉 Max. Drawdown nach Ampelfarbe")
        dd_cols = st.columns(len(drawdown_data))
        for i, (signal, dd) in enumerate(drawdown_data.items()):
            with dd_cols[i]:
                emoji = {"Grün": "🟢", "Gelb": "🟡", "Orange": "🟠", "Rot": "🔴"}[signal]
                st.metric(
                    f"{emoji} {signal} (n={dd['n']})",
                    f"Ø DD: {dd['avg_dd']:.1f}%",
                    f"Worst: {dd['worst_dd']:.1f}% | Ø Rendite: {dd['avg_return']:+.1f}%",
                    delta_color="inverse",
                )

        st.divider()

        # ── Chart: Jahresrendite nach Signal ──────────────────────────
        st.subheader("📊 Jahresrendite (Feb-Dez) nach Trifecta-Signal")

        fig = go.Figure()
        for signal, color in farb_map.items():
            sub = history_df[history_df["Signal"] == signal]
            if len(sub) == 0:
                continue
            fig.add_trace(go.Bar(
                x=sub["Jahr"],
                y=sub["Jahresrendite_Feb_Dez_%"],
                name=signal,
                marker_color=color,
                marker_opacity=0.85,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"Signal: {signal}<br>"
                    "Rendite Feb–Dez: %{y:.1f}%<extra></extra>"
                ),
            ))

        fig = apply_se_theme(fig, title=f"{ticker} — Jahresrendite (Feb–Dez) nach Trifecta-Signal", height=420)
        fig.add_hline(y=0, line_color="rgba(128,128,128,0.4)")
        st.plotly_chart(fig, use_container_width=True)

        # Detailtabelle
        with st.expander("📋 Alle Jahre anzeigen"):
            display_df = history_df[[
                "Jahr", "Emoji", "Signal", "Anzahl_erfuellt",
                "SCR_Rendite_%", "FFD_Rendite_%", "JanB_Rendite_%",
                "Jahresrendite_Feb_Dez_%"
            ]].rename(columns={
                "Emoji": "",
                "Anzahl_erfuellt": "Erfüllt",
                "SCR_Rendite_%": "SCR %",
                "FFD_Rendite_%": "FFD %",
                "JanB_Rendite_%": "JanB %",
                "Jahresrendite_Feb_Dez_%": "Jahr-Rendite %",
            }).sort_values("Jahr", ascending=False)

            st.dataframe(
                display_df.style.applymap(
                    lambda v: f"color: {'#2ECC71' if isinstance(v, float) and v > 0 else '#E74C3C' if isinstance(v, float) and v < 0 else ''}",
                    subset=["SCR %", "FFD %", "JanB %", "Jahr-Rendite %"]
                ),
                use_container_width=True,
                hide_index=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — KAEPPEL JAHRESÜBERSICHT
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader(f"📊 Kaeppel Jahresübersicht — {analyse_jahr}")
    st.caption(
        "Jay Kaeppel's bekannte Seasonal-Indikatoren auf einen Blick. "
        "Quelle: 'Seasonal Stock Market Trends' (2009) + Known Trend Index (KTI)."
    )

    summary = kaeppel.get_kaeppel_year_summary(analyse_jahr, int(last_election))
    ec      = summary["election_cycle"]
    dec5    = summary["decennial_5"]

    # ── Jahres-Ampel ──────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("#### 🗳️ Präsidentschaftszyklus")
        farbe = ec["farbe"]
        st.markdown(
            f"""
            <div style="background:{farbe}22; border:2px solid {farbe};
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:36px; font-weight:bold; color:{farbe};">
                    Jahr {ec['zyklus_jahr']}
                </div>
                <div style="font-size:18px; color:{farbe}; margin-top:4px;">
                    {ec['signal']}
                </div>
                <div style="font-size:12px; color:#888; margin-top:8px;">
                    {ec['interpretation']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown("#### 🔟 Dekadenzyklus")
        farbe = dec5["farbe"]
        label = f"Endet auf {dec5['letzte_ziffer']}"
        st.markdown(
            f"""
            <div style="background:{farbe}22; border:2px solid {farbe};
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:36px; font-weight:bold; color:{farbe};">
                    {label}
                </div>
                <div style="font-size:18px; color:{farbe}; margin-top:4px;">
                    {dec5['signal']}
                </div>
                <div style="font-size:12px; color:#888; margin-top:8px;">
                    {dec5['interpretation']}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown("#### 📅 Long-Monate")
        monate_str = " · ".join(summary["long_monate_namen"])
        st.markdown(
            f"""
            <div style="background:#3498DB22; border:2px solid #3498DB;
                        border-radius:12px; padding:16px; text-align:center;">
                <div style="font-size:18px; font-weight:bold; color:#3498DB;">
                    {monate_str}
                </div>
                <div style="font-size:12px; color:#888; margin-top:8px;">
                    Kaeppel Simple Monthly Seasonal<br>
                    Long nur in diesen 4 Monaten
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Aktueller KTI-Score ───────────────────────────────────────────────
    st.subheader("🎯 Known Trend Index (KTI) — Heute")
    st.caption(
        "Der KTI kombiniert 5 Seasonal-Signale zu einem Score (0–5). "
        "≥4 → Aggressiv Long · ≥3 → Moderat Long · ≤1 → Defensiv/Cash"
    )

    today = pd.Timestamp.now().normalize()
    # Holidays für KTI aus shared/holidays wenn vorhanden
    try:
        from shared.holidays import get_nyse_holidays
        hols_this_year  = [h["date"] for h in get_nyse_holidays(today.year)]
        hols_last_year  = [h["date"] for h in get_nyse_holidays(today.year - 1)]
        holidays_by_year = {
            today.year - 1: hols_last_year,
            today.year:     hols_this_year,
        }
    except Exception:
        holidays_by_year = None

    kti = kaeppel.calculate_kti_score(
        current_date=today,
        df=df,
        holidays_by_year=holidays_by_year,
        election_year=int(last_election),
    )

    col_score, col_detail = st.columns([1, 2])

    with col_score:
        farbe = kti["farbe"]
        st.markdown(
            f"""
            <div style="background:{farbe}; border-radius:16px;
                        padding:28px; text-align:center;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                <div style="font-size:52px; font-weight:bold; color:white;">
                    {kti['score']}<span style="font-size:24px;">/5</span>
                </div>
                <div style="font-size:20px; color:white; margin-top:6px;">
                    {kti['signal']}
                </div>
                <div style="font-size:11px; color:rgba(255,255,255,0.8); margin-top:6px;">
                    {today.strftime('%d.%m.%Y')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_detail:
        st.markdown(f"**{kti['interpretation']}**")
        st.markdown("")

        komponenten_labels = {
            "holiday_effect":    "🎉 Holiday Effect (±3 Tage um Feiertage)",
            "turn_of_month":     "📅 Turn-of-Month (letzte 4 + erste 3 Handelstage)",
            "monthly_best_days": f"📆 Monthly Best Days (Kaeppel Long-Monat?)",
            "election_cycle":    f"🗳️ Election Cycle (Jahr 3 = Pre-Election?)",
            "decennial_cycle":   f"🔟 Decennial Cycle (Jahr endet auf 5?)",
        }

        for key, label in komponenten_labels.items():
            aktiv = kti["komponenten"].get(key, False)
            icon  = "✅" if aktiv else "⬜"
            st.markdown(f"{icon} {label}")

    st.divider()

    # ── Historischer Präsidentschaftszyklus ───────────────────────────────
    st.subheader("📈 Präsidentschaftszyklus — Historische Performance")

    with st.spinner("Berechne Zyklus-Renditen …"):
        zyklus_rows = []
        for y in range(int(last_election) - 20, datetime.now().year):
            ec_y = kaeppel.get_election_cycle_year(y, int(last_election))
            year_data = df[df.index.year == y]
            if len(year_data) < 10:
                continue
            rendite = (
                (year_data["Close"].iloc[-1] - year_data["Close"].iloc[0])
                / year_data["Close"].iloc[0] * 100
            )
            zyklus_rows.append({
                "Jahr": y,
                "Zyklus-Jahr": ec_y["zyklus_jahr"],
                "Signal": ec_y["signal"],
                "Farbe": ec_y["farbe"],
                "Jahresrendite_%": round(rendite, 1),
            })

    if zyklus_rows:
        zyklus_df = pd.DataFrame(zyklus_rows)
        farb_map_ec = {1: "#E74C3C", 2: "#E67E22", 3: "#2ECC71", 4: "#F1C40F"}

        fig2 = go.Figure()
        for zj in [1, 2, 3, 4]:
            sub = zyklus_df[zyklus_df["Zyklus-Jahr"] == zj]
            labels = {1: "Jahr 1 (Post-Election)", 2: "Jahr 2 (Mid-Term)",
                      3: "Jahr 3 (Pre-Election)", 4: "Jahr 4 (Election)"}
            fig2.add_trace(go.Bar(
                x=sub["Jahr"],
                y=sub["Jahresrendite_%"],
                name=labels[zj],
                marker_color=farb_map_ec[zj],
                marker_opacity=0.85,
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"Zyklus-Jahr: {zj} ({labels[zj]})<br>"
                    "Jahresrendite: %{y:.1f}%<extra></extra>"
                ),
            ))

        # Durchschnitte pro Zyklus-Jahr
        for zj, col in farb_map_ec.items():
            avg = zyklus_df[zyklus_df["Zyklus-Jahr"] == zj]["Jahresrendite_%"].mean()
            if not pd.isna(avg):
                fig2.add_annotation(
                    x=0.5, xref="paper",
                    y=avg,
                    text=f"Ø J{zj}: {avg:.1f}%",
                    showarrow=False,
                    font=dict(color=col, size=10),
                    xanchor="left",
                )

        fig2 = apply_se_theme(fig2, title=f"{ticker} — Jahresrendite nach Präsidentschaftszyklus-Jahr", height=420)
        fig2.add_hline(y=0, line_color="rgba(128,128,128,0.4)")
        st.plotly_chart(fig2, use_container_width=True)

        # Durchschnitte in Metriken
        col1, col2, col3, col4 = st.columns(4)
        for col_ui, zj, label in [
            (col1, 1, "Post-Election"), (col2, 2, "Mid-Term"),
            (col3, 3, "Pre-Election"), (col4, 4, "Election"),
        ]:
            sub = zyklus_df[zyklus_df["Zyklus-Jahr"] == zj]["Jahresrendite_%"]
            with col_ui:
                st.metric(
                    f"Jahr {zj} ({label})",
                    f"Ø {sub.mean():.1f}%",
                    f"n={len(sub)}",
                )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — STRATEGIE-BIBLIOTHEK
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader("📚 Strategie-Bibliothek")
    st.caption(f"**{len(STRATEGIES)} Saisonalstrategien** aus Wissenschaft und Praxis — filterbar nach Kategorie, Stärke und Stichwort.")

    # Filter
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        kat_options = ["Alle"] + sorted(set(s["kategorie"] for s in STRATEGIES))
        selected_kat = st.selectbox("Kategorie", kat_options)

    with col_f2:
        staerke_options = ["Alle"] + STAERKEN
        selected_staerke = st.selectbox("Mindeststärke", staerke_options)

    with col_f3:
        search_text = st.text_input("🔍 Suche (Name, Tag)", placeholder="z.B. FOMC, gold, kaeppel …")

    # Filtern
    filtered = STRATEGIES.copy()

    if selected_kat != "Alle":
        filtered = [s for s in filtered if s["kategorie"] == selected_kat]

    if selected_staerke != "Alle":
        rank = {s: i for i, s in enumerate(STAERKEN)}
        min_rank = rank.get(selected_staerke, 0)
        filtered = [s for s in filtered if rank.get(s["staerke"], 0) >= min_rank]

    if search_text.strip():
        q = search_text.lower().strip()
        filtered = [
            s for s in filtered
            if q in s["name"].lower()
            or q in " ".join(s.get("tags", [])).lower()
            or q in s["asset"].lower()
        ]

    st.markdown(f"**{len(filtered)} Strategien** gefunden")

    # Stärke-Farbgebung
    staerke_farben = {
        "gering":       "#95A5A6",
        "gering–mittel":"#F39C12",
        "mittel":       "#F1C40F",
        "mittel–hoch":  "#27AE60",
        "hoch":         "#2ECC71",
    }

    # Tabelle aufbauen
    rows = []
    for s in filtered:
        modul_badge = f"✅ `{s['modul']}`" if s.get("modul") else "—"
        farbe = staerke_farben.get(s["staerke"], "#888")
        rows.append({
            "Name":        s["name"],
            "Kategorie":   s["kategorie"],
            "Asset":       s["asset"],
            "Zeitfenster": s["zeitfenster"],
            "Logik":       s["logik"],
            "Stärke":      s["staerke"],
            "Modul":       s.get("modul") or "—",
            "Quelle":      s["quelle"],
        })

    if rows:
        lib_df = pd.DataFrame(rows)

        # Farbige Stärke-Spalte via Styler
        def color_staerke(val):
            farbe = staerke_farben.get(val, "#888")
            return f"color: {farbe}; font-weight: bold;"

        st.dataframe(
            lib_df.style.applymap(color_staerke, subset=["Stärke"]),
            use_container_width=True,
            hide_index=True,
            height=600,
            column_config={
                "Name":        st.column_config.TextColumn("Strategie", width="medium"),
                "Kategorie":   st.column_config.TextColumn("Kat.", width="small"),
                "Asset":       st.column_config.TextColumn("Asset", width="medium"),
                "Zeitfenster": st.column_config.TextColumn("Zeitfenster", width="medium"),
                "Logik":       st.column_config.TextColumn("Long/Short-Logik", width="large"),
                "Stärke":      st.column_config.TextColumn("Stärke", width="small"),
                "Modul":       st.column_config.TextColumn("Code", width="small"),
                "Quelle":      st.column_config.TextColumn("Quelle", width="medium"),
            },
        )
    else:
        st.info("Keine Strategien für die gewählten Filter gefunden.")

    # Zusammenfassung nach Kategorie
    st.divider()
    st.subheader("📊 Übersicht nach Kategorie")

    kat_counts = {}
    for s in STRATEGIES:
        kat_counts[s["kategorie"]] = kat_counts.get(s["kategorie"], 0) + 1

    fig3 = go.Figure(go.Bar(
        x=list(kat_counts.keys()),
        y=list(kat_counts.values()),
        marker_color="#3498DB",
        marker_opacity=0.8,
        text=list(kat_counts.values()),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} Strategien<extra></extra>",
    ))
    fig3 = apply_se_theme(fig3, title="Anzahl Strategien pro Kategorie", height=350)
    st.plotly_chart(fig3, use_container_width=True)

render_footer()
