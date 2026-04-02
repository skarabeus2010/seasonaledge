"""
10_📅_OPEX.py
=============
Options Expiration (OPEX) Analyse für SeasonAlpha.

Analysiert saisonale Muster rund um monatliche Options-Verfalltage
(3. Freitag im Monat) und Quarterly Triple Witching (Mrz/Jun/Sep/Dez).
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta
import calendar

from shared.yahoo_downloader import download_data, preprocess
from shared.symbols import SYMBOLS, get_dropdown_label, KATEGORIEN
from shared.nyse_holidays import get_all_opex_dates as _get_opex, get_upcoming_opex, is_nyse_holiday
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS

# ── Seiten-Konfiguration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OPEX Analyse · SeasonAlpha",
    page_icon="📅",
    layout="wide",
)

from shared.design import inject_se_css
inject_se_css()

st.title("📅 Options Expiration (OPEX) Analyse")
st.caption("Saisonale Muster rund um monatliche Verfalltage · 3. Freitag im Monat")

# ── OPEX-Logik ──────────────────────────────────────────────────────────────────
# Ausgelagert in shared/nyse_holidays.py
# get_all_opex_dates und is_nyse_holiday kommen von dort

def get_all_opex_dates(start_year: int, end_year: int) -> pd.DataFrame:
    """Wrapper: holt OPEX-Daten aus nyse_holidays, gibt DataFrame zurück."""
    rows = _get_opex(start_year, end_year)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df

def calculate_opex_windows(
    df: pd.DataFrame,
    opex_dates: pd.DataFrame,
    days_before: int,
    days_after: int,
) -> pd.DataFrame:
    """
    Berechnet die kumulierten Renditen rund um jeden OPEX-Termin.
    t=0 ist der OPEX-Freitag selbst.
    Gibt einen DataFrame mit einer Zeile pro OPEX-Event zurück.
    """
    df = df.copy()
    df = df.sort_index()
    trading_days = df.index.tolist()

    results = []

    for _, opex_row in opex_dates.iterrows():
        opex_dt = opex_row["date"]

        # Nächsten verfügbaren Handelstag finden (OPEX-Freitag kann Feiertag sein)
        candidates = [t for t in trading_days if t >= opex_dt]
        if not candidates:
            continue
        t0 = candidates[0]

        # Position im Trading-Days-Array
        try:
            idx = trading_days.index(t0)
        except ValueError:
            continue

        # Fenster: t-days_before bis t+days_after
        start_idx = idx - days_before
        end_idx   = idx + days_after

        if start_idx < 0 or end_idx >= len(trading_days):
            continue

        window = trading_days[start_idx : end_idx + 1]
        window_df = df.loc[window]

        if len(window_df) == 0:
            continue

        # Renditen für jeden Tag im Fenster relativ zu t-days_before
        base_close = window_df["Close"].iloc[0]
        rel_returns = {}
        for i, (ts, row) in enumerate(window_df.iterrows()):
            t_offset = i - days_before  # t=0 ist OPEX-Tag
            rel_returns[t_offset] = (row["Close"] / base_close - 1) * 100

        row_data = {
            "opex_date":   opex_dt,
            "t0":          t0,
            "year":        opex_row["year"],
            "month":       opex_row["month"],
            "month_name":  opex_row["month_name"],
            "is_triple":   opex_row["is_triple"],
            "type":        opex_row["type"],
        }
        row_data.update({f"t{k:+d}": v for k, v in rel_returns.items()})
        results.append(row_data)

    return pd.DataFrame(results)

def calculate_daily_returns_by_offset(
    df: pd.DataFrame,
    opex_dates: pd.DataFrame,
    days_before: int,
    days_after: int,
) -> pd.DataFrame:
    """
    Berechnet für jeden Tag-Offset (t-3, t-2, ..., t+3) die
    einzelne Tagesrendite (nicht kumuliert).
    """
    df = df.copy().sort_index()
    trading_days = df.index.tolist()
    results = []

    for _, opex_row in opex_dates.iterrows():
        opex_dt = opex_row["date"]
        candidates = [t for t in trading_days if t >= opex_dt]
        if not candidates:
            continue
        t0 = candidates[0]
        try:
            idx = trading_days.index(t0)
        except ValueError:
            continue

        for offset in range(-days_before, days_after + 1):
            target_idx = idx + offset
            if target_idx <= 0 or target_idx >= len(trading_days):
                continue
            ts = trading_days[target_idx]
            ret = df.loc[ts, "return"]
            if pd.isna(ret):
                continue
            results.append({
                "offset":      offset,
                "return_pct":  ret * 100,
                "year":        opex_row["year"],
                "month":       opex_row["month"],
                "is_triple":   opex_row["is_triple"],
                "type":        opex_row["type"],
                "opex_date":   opex_dt,
            })

    return pd.DataFrame(results)

# ── Sidebar ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Einstellungen")

    # Ticker-Auswahl
    all_tickers = list(SYMBOLS.keys())
    default_idx = all_tickers.index("SPY") if "SPY" in all_tickers else 0
    ticker = st.selectbox(
        "Symbol",
        options=all_tickers,
        index=default_idx,
        format_func=get_dropdown_label,
    )

    st.divider()

    # Zeitfenster
    st.subheader("📐 Zeitfenster")
    days_before = st.slider("Tage vor OPEX (t-x)", min_value=1, max_value=10, value=3)
    days_after  = st.slider("Tage nach OPEX (t+y)", min_value=1, max_value=10, value=3)

    st.divider()

    # Lookback
    st.subheader("📆 Analyse-Zeitraum")
    current_year = date.today().year
    start_year = st.slider("Von Jahr", min_value=1990, max_value=current_year - 2,
                           value=max(1990, current_year - 20))
    end_year   = st.slider("Bis Jahr", min_value=start_year + 1, max_value=current_year,
                           value=current_year)

    st.divider()

    # Optionale Tabs
    st.subheader("📋 Sichtbare Tabs")
    show_rendite   = st.checkbox("📊 Rendite-Analyse",   value=True)
    show_triple    = st.checkbox("❄️ Triple Witching",   value=True)
    show_kalender  = st.checkbox("📅 OPEX-Kalender",     value=True)
    show_backtest  = st.checkbox("🔄 Backtest",          value=True)

    st.divider()

    # ── Technische Filter ──────────────────────────
    from shared.indicator_filter_ui import indicator_filter_sidebar
    ind_filters = indicator_filter_sidebar(key_prefix="opex")

    st.caption("Daten via Yahoo Finance · OPEX = 3. Freitag im Monat")

# ── Daten laden ──────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Kursdaten werden geladen …")
def load_data(ticker: str) -> pd.DataFrame:
    df = download_data(ticker, period="max")
    if df is None or len(df) == 0:
        return pd.DataFrame()
    return preprocess(df)

df = load_data(ticker)

if df is None or len(df) == 0:
    st.error(f"Keine Daten für **{ticker}** verfügbar.")
    st.stop()

# ── Indikator-Filter anwenden ─────────────────────
if ind_filters:
    from shared.indicators import apply_indicator_filter
    from shared.indicator_filter_ui import render_filter_badge
    mask = apply_indicator_filter(df, ind_filters)
    total_days = len(df)
    df = df[mask].copy()
    filtered_days = len(df)
    render_filter_badge(ind_filters, total_days, filtered_days)

# Auf gewählten Zeitraum filtern
df_filtered = df[
    (df.index.year >= start_year) &
    (df.index.year <= end_year)
].copy()

if len(df_filtered) < 50:
    st.warning("Zu wenig Daten für den gewählten Zeitraum.")
    st.stop()

# OPEX-Daten berechnen
opex_all      = get_all_opex_dates(start_year, end_year)
opex_standard = opex_all[~opex_all["is_triple"]]
opex_triple   = opex_all[opex_all["is_triple"]]

daily_returns = calculate_daily_returns_by_offset(
    df_filtered, opex_all, days_before, days_after
)

if len(daily_returns) == 0:
    st.error("Keine OPEX-Events im gewählten Zeitraum berechnet.")
    st.stop()

# ── Farben & Stil ────────────────────────────────────────────────────────────────

FARBE_POS     = "#26a69a"   # Grün
FARBE_NEG     = "#ef5350"   # Rot
FARBE_TRIPLE  = "#ffa726"   # Orange
FARBE_OPEX    = "#42a5f5"   # Blau

def bar_color(values):
    return [FARBE_POS if v >= 0 else FARBE_NEG for v in values]

def offset_label(offset) -> str:
    offset = int(offset)
    if offset == 0:
        return "t=0\n(OPEX)"
    return f"t{offset:+d}"

offsets = list(range(-days_before, days_after + 1))
offset_labels = [offset_label(o) for o in offsets]

# ── Tab-Auswahl ──────────────────────────────────────────────────────────────────

tab_names = []
if show_rendite:  tab_names.append("📊 Rendite-Analyse")
if show_triple:   tab_names.append("❄️ Triple Witching")
if show_kalender: tab_names.append("📅 OPEX-Kalender")
if show_backtest: tab_names.append("🔄 Backtest")

if not tab_names:
    st.info("Bitte mindestens einen Tab in der Sidebar aktivieren.")
    st.stop()

tabs = st.tabs(tab_names)
tab_idx = 0

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 1: RENDITE-ANALYSE
# ══════════════════════════════════════════════════════════════════════════════════

if show_rendite:
    with tabs[tab_idx]:
        tab_idx += 1

        st.subheader(f"📊 Durchschnittliche Tagesrendite rund um OPEX · {ticker}")
        st.caption(f"Zeitraum: {start_year}–{end_year} · t=0 ist der OPEX-Freitag")

        # ── Metriken ─────────────────────────────────────────────────────────────
        agg = (
            daily_returns
            .groupby("offset")["return_pct"]
            .agg(["mean", "std", "count", lambda x: (x > 0).mean() * 100])
            .reset_index()
        )
        agg.columns = ["offset", "mean", "std", "count", "win_rate"]
        agg = agg.sort_values("offset")

        t0_row = agg[agg["offset"] == 0]
        best   = agg.loc[agg["mean"].idxmax()]
        worst  = agg.loc[agg["mean"].idxmin()]

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            v = t0_row["mean"].values[0] if len(t0_row) > 0 else 0
            st.metric("Ø Rendite t=0 (OPEX-Tag)", f"{v:+.3f}%")
        with col2:
            st.metric("Bester Tag im Fenster",
                      f"t{int(best['offset']):+d}",
                      f"{best['mean']:+.3f}%")
        with col3:
            st.metric("Schwächster Tag",
                      f"t{int(worst['offset']):+d}",
                      f"{worst['mean']:+.3f}%")
        with col4:
            n_events = daily_returns["opex_date"].nunique()
            st.metric("Analysierte OPEX-Events", n_events)

        st.divider()

        # ── Hauptchart: Ø Rendite pro Offset ─────────────────────────────────────
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.65, 0.35],
            subplot_titles=["Ø Tagesrendite (%) nach OPEX-Abstand",
                            "Win-Rate (%)"],
            vertical_spacing=0.12,
        )

        means     = [agg[agg["offset"] == o]["mean"].values[0]
                     if o in agg["offset"].values else 0 for o in offsets]
        win_rates = [agg[agg["offset"] == o]["win_rate"].values[0]
                     if o in agg["offset"].values else 50 for o in offsets]
        counts    = [int(agg[agg["offset"] == o]["count"].values[0])
                     if o in agg["offset"].values else 0 for o in offsets]

        # Balkendiagramm Rendite
        fig.add_trace(
            go.Bar(
                x=offset_labels,
                y=means,
                marker_color=bar_color(means),
                text=[f"{v:+.3f}%<br>n={c}" for v, c in zip(means, counts)],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Ø Rendite: %{y:.3f}%<br>Events: %{customdata}<extra></extra>",
                customdata=counts,
                name="Ø Rendite",
            ),
            row=1, col=1,
        )

        # OPEX-Tag Markierung
        opex_x = offset_labels[days_before]
        fig.add_vline(x=days_before, line_dash="dash", line_color="white",
                      line_width=1, opacity=0.5, row=1, col=1)

        # Win-Rate
        fig.add_trace(
            go.Bar(
                x=offset_labels,
                y=win_rates,
                marker_color=[FARBE_POS if w >= 50 else FARBE_NEG for w in win_rates],
                text=[f"{w:.1f}%" for w in win_rates],
                textposition="outside",
                name="Win-Rate",
                showlegend=False,
            ),
            row=2, col=1,
        )
        fig.add_hline(y=50, line_dash="dot", line_color="gray", row=2, col=1)

        fig = apply_se_theme(fig, title="", height=550, show_legend=False)
        fig.add_annotation(
            x=days_before, y=max(means) * 1.3 if max(means) > 0 else min(means) * 1.3,
            text="OPEX", showarrow=False, font=dict(color="white", size=11),
            row=1, col=1,
        )
        fig.update_yaxes(title_text="Rendite (%)", row=1, col=1)
        fig.update_yaxes(title_text="Win-Rate (%)", range=[0, 100], row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

        # ── Detailtabelle ─────────────────────────────────────────────────────────
        with st.expander("📋 Detailtabelle anzeigen"):
            display = agg.copy()
            display["offset"] = display["offset"].apply(lambda x: offset_label(x))
            display["mean"]     = display["mean"].apply(lambda x: f"{x:+.4f}%")
            display["std"]      = display["std"].apply(lambda x: f"{x:.4f}%")
            display["win_rate"] = display["win_rate"].apply(lambda x: f"{x:.1f}%")
            display.columns = ["Tag", "Ø Rendite", "Std.Abw.", "Anzahl", "Win-Rate"]
            st.dataframe(display, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 2: TRIPLE WITCHING
# ══════════════════════════════════════════════════════════════════════════════════

if show_triple:
    with tabs[tab_idx]:
        tab_idx += 1

        st.subheader("❄️ Triple Witching vs. Standard OPEX")
        st.caption("März · Juni · September · Dezember = Triple Witching (höchstes Volumen)")

        # Aufteilen
        dr_standard = daily_returns[~daily_returns["is_triple"]]
        dr_triple   = daily_returns[daily_returns["is_triple"]]

        def agg_by_offset(data):
            return (
                data.groupby("offset")["return_pct"]
                .agg(["mean", "count", lambda x: (x > 0).mean() * 100])
                .reset_index()
                .rename(columns={"<lambda_0>": "win_rate"})
                .sort_values("offset")
            )

        agg_std = agg_by_offset(dr_standard)
        agg_tri = agg_by_offset(dr_triple)

        # Metriken
        col1, col2, col3 = st.columns(3)
        with col1:
            n_std = dr_standard["opex_date"].nunique()
            n_tri = dr_triple["opex_date"].nunique()
            st.metric("Standard OPEX Events", n_std)
            st.metric("Triple Witching Events", n_tri)
        with col2:
            t0_std = agg_std[agg_std["offset"] == 0]["mean"].values
            v = t0_std[0] if len(t0_std) > 0 else 0
            st.metric("Ø OPEX-Tag Standard", f"{v:+.3f}%")
        with col3:
            t0_tri = agg_tri[agg_tri["offset"] == 0]["mean"].values
            v = t0_tri[0] if len(t0_tri) > 0 else 0
            st.metric("Ø OPEX-Tag Triple Witching", f"{v:+.3f}%")

        st.divider()

        # Vergleichschart
        fig = go.Figure()

        std_means = [agg_std[agg_std["offset"] == o]["mean"].values[0]
                     if o in agg_std["offset"].values else 0 for o in offsets]
        tri_means = [agg_tri[agg_tri["offset"] == o]["mean"].values[0]
                     if o in agg_tri["offset"].values else 0 for o in offsets]

        fig.add_trace(go.Bar(
            x=offset_labels, y=std_means,
            name="Standard OPEX",
            marker_color=FARBE_OPEX, opacity=0.8,
            text=[f"{v:+.3f}%" for v in std_means],
            textposition="outside",
        ))
        fig.add_trace(go.Bar(
            x=offset_labels, y=tri_means,
            name="Triple Witching",
            marker_color=FARBE_TRIPLE, opacity=0.8,
            text=[f"{v:+.3f}%" for v in tri_means],
            textposition="outside",
        ))
        fig.add_vline(x=days_before, line_dash="dash", line_color="white",
                      line_width=1, opacity=0.4)
        fig.add_annotation(x=days_before, y=0, text="OPEX",
                           showarrow=False, font=dict(color="white", size=10))
        fig = apply_se_theme(fig, title="Ø Rendite (%)", height=450)

        fig.update_yaxes(title="Ø Rendite (%)")
        st.plotly_chart(fig, use_container_width=True)

        # Nach Monat aufschlüsseln (nur Triple Witching Monate)
        st.subheader("📅 Triple Witching nach Quartal")
        tw_months = {3: "März (Q1)", 6: "Juni (Q2)", 9: "September (Q3)", 12: "Dezember (Q4)"}

        cols = st.columns(4)
        for i, (month, label) in enumerate(tw_months.items()):
            dr_month = dr_triple[dr_triple["month"] == month]
            t0_val = dr_month[dr_month["offset"] == 0]["return_pct"]
            mean_val = t0_val.mean() if len(t0_val) > 0 else 0
            wr = (t0_val > 0).mean() * 100 if len(t0_val) > 0 else 0
            delta_color = "normal" if mean_val >= 0 else "inverse"
            with cols[i]:
                st.metric(
                    label,
                    f"{mean_val:+.3f}%",
                    f"Win-Rate: {wr:.0f}%",
                    delta_color=delta_color,
                )

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 3: OPEX-KALENDER
# ══════════════════════════════════════════════════════════════════════════════════

if show_kalender:
    with tabs[tab_idx]:
        tab_idx += 1

        st.subheader("📅 OPEX-Kalender")

        today = pd.Timestamp(date.today())
        upcoming = opex_all[opex_all["date"] >= today].head(12)
        past = opex_all[opex_all["date"] < today].tail(6)

        # Nächster OPEX
        if len(upcoming) > 0:
            next_opex = upcoming.iloc[0]
            days_until = (next_opex["date"] - today).days
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Nächster OPEX",
                    next_opex["date"].strftime("%d.%m.%Y"),
                    f"in {days_until} Tagen",
                )
            with col2:
                st.metric("Typ", next_opex["type"])
            with col3:
                next_triple = upcoming[upcoming["is_triple"]].iloc[0] if upcoming["is_triple"].any() else None
                if next_triple is not None:
                    days_triple = (next_triple["date"] - today).days
                    st.metric("Nächstes Triple Witching",
                              next_triple["date"].strftime("%d.%m.%Y"),
                              f"in {days_triple} Tagen")

        st.divider()

        # Nächste 12 OPEX-Termine
        st.subheader("🗓️ Nächste 12 OPEX-Termine")
        display_upcoming = upcoming.copy()
        display_upcoming["Datum"]  = display_upcoming["date"].dt.strftime("%d.%m.%Y")
        display_upcoming["Monat"]  = display_upcoming["month_name"]
        display_upcoming["Jahr"]   = display_upcoming["year"]
        display_upcoming["Wochentag"] = display_upcoming["date"].dt.strftime("%A")
        display_upcoming["Typ"]    = display_upcoming["type"].apply(
            lambda x: f"⚡ {x}" if x == "Triple Witching" else f"📅 {x}"
        )
        st.dataframe(
            display_upcoming[["Datum", "Wochentag", "Monat", "Jahr", "Typ"]],
            use_container_width=True,
            hide_index=True,
        )

        # Jahresübersicht aktuelle Jahr
        st.subheader(f"📆 OPEX {date.today().year} — Jahresübersicht")
        year_opex = get_all_opex_dates(date.today().year, date.today().year)

        fig = go.Figure()
        for _, row in year_opex.iterrows():
            color = FARBE_TRIPLE if row["is_triple"] else FARBE_OPEX
            label = f"⚡ {row['month_name']}" if row["is_triple"] else row["month_name"]
            fig.add_trace(go.Scatter(
                x=[row["date"]],
                y=[1],
                mode="markers+text",
                marker=dict(size=18, color=color, symbol="diamond"),
                text=[label],
                textposition="top center",
                name=row["type"],
                showlegend=False,
                hovertemplate=f"<b>{row['date'].strftime('%d.%m.%Y')}</b><br>{row['type']}<extra></extra>",
            ))

        # Legende manuell
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(size=12, color=FARBE_OPEX, symbol="diamond"),
                                 name="Standard OPEX"))
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 marker=dict(size=12, color=FARBE_TRIPLE, symbol="diamond"),
                                 name="Triple Witching"))

        # Heute markieren
        fig.add_vline(x=today.strftime("%Y-%m-%d"), line_dash="dash", line_color="white",
                      line_width=1, opacity=0.6)

        fig = apply_se_theme(fig, title="", height=250)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════════
# TAB 4: BACKTEST
# ══════════════════════════════════════════════════════════════════════════════════

if show_backtest:
    with tabs[tab_idx]:
        tab_idx += 1

        st.subheader(f"🔄 Backtest: Long in OPEX-Woche · {ticker}")
        st.caption(
            f"Strategie: Kauf t{-days_before:+d} (Eröffnung) · Verkauf t{days_after:+d} (Schluss) · "
            f"Zeitraum: {start_year}–{end_year}"
        )

        # Kumulierte Renditen pro Event berechnen
        opex_windows = calculate_opex_windows(
            df_filtered, opex_all, days_before, days_after
        )

        if len(opex_windows) == 0:
            st.warning("Keine Events für den Backtest berechnet.")
        else:
            # Gesamt-Rendite pro Event = letzte kumulierte Rendite
            last_col = f"t{days_after:+d}"
            if last_col not in opex_windows.columns:
                st.warning(f"Spalte {last_col} nicht gefunden.")
            else:
                opex_windows["total_return"] = opex_windows[last_col]
                opex_windows["profitable"]   = opex_windows["total_return"] > 0

                # Metriken
                total_events  = len(opex_windows)
                win_events    = opex_windows["profitable"].sum()
                win_rate      = win_events / total_events * 100
                avg_return    = opex_windows["total_return"].mean()
                total_return  = opex_windows["total_return"].sum()
                max_win       = opex_windows["total_return"].max()
                max_loss      = opex_windows["total_return"].min()

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Analysierte Events", total_events)
                    st.metric("Gewinner", f"{win_events} ({win_rate:.0f}%)")
                with col2:
                    st.metric("Ø Rendite pro Trade", f"{avg_return:+.3f}%")
                    st.metric("Max. Gewinn", f"{max_win:+.2f}%")
                with col3:
                    delta_color = "normal" if total_return >= 0 else "inverse"
                    st.metric("Summe aller Renditen", f"{total_return:+.2f}%")
                    st.metric("Max. Verlust", f"{max_loss:+.2f}%")
                with col4:
                    # Sharpe-ähnliche Kennzahl
                    std_ret = opex_windows["total_return"].std()
                    sharpe = avg_return / std_ret if std_ret > 0 else 0
                    st.metric("Ø/Std (Risk-Adj.)", f"{sharpe:.2f}")

                st.divider()

                # Equity-Kurve (kumulierte Summe der Trade-Renditen)
                opex_windows_sorted = opex_windows.sort_values("opex_date")
                equity = opex_windows_sorted["total_return"].cumsum()

                fig = make_subplots(
                    rows=2, cols=1,
                    row_heights=[0.65, 0.35],
                    subplot_titles=[
                        "Kumulierte Strategie-Rendite (Summe OPEX-Trades)",
                        "Rendite pro Event (%)",
                    ],
                    vertical_spacing=0.12,
                )

                # Equity-Kurve
                fig.add_trace(go.Scatter(
                    x=opex_windows_sorted["opex_date"],
                    y=equity,
                    mode="lines",
                    fill="tozeroy",
                    line=dict(color=FARBE_POS if equity.iloc[-1] >= 0 else FARBE_NEG, width=2),
                    fillcolor=f"rgba(38,166,154,0.15)" if equity.iloc[-1] >= 0 else "rgba(239,83,80,0.15)",
                    name="Equity",
                ), row=1, col=1)

                # Nulllinie
                fig.add_hline(y=0, line_dash="dash", line_color="gray",
                              line_width=1, row=1, col=1)

                # Rendite pro Event
                colors_per_event = [FARBE_POS if r >= 0 else FARBE_NEG
                                    for r in opex_windows_sorted["total_return"]]
                fig.add_trace(go.Bar(
                    x=opex_windows_sorted["opex_date"],
                    y=opex_windows_sorted["total_return"],
                    marker_color=colors_per_event,
                    name="Trade-Rendite",
                    hovertemplate="<b>%{x|%d.%m.%Y}</b><br>Rendite: %{y:+.3f}%<extra></extra>",
                ), row=2, col=1)

                fig = apply_se_theme(fig, title="", height=550, show_legend=False)
                fig.update_yaxes(title_text="Kum. Rendite (%)", row=1, col=1)
                fig.update_yaxes(title_text="Rendite (%)", row=2, col=1)
                st.plotly_chart(fig, use_container_width=True)

                # Verteilung
                st.subheader("📊 Rendite-Verteilung")
                fig2 = go.Figure()
                fig2.add_trace(go.Histogram(
                    x=opex_windows["total_return"],
                    nbinsx=30,
                    marker_color=FARBE_OPEX,
                    opacity=0.8,
                    name="Rendite-Verteilung",
                ))
                fig2.add_vline(x=0, line_dash="dash", line_color="white", line_width=1)
                fig2.add_vline(x=avg_return, line_dash="dot",
                               line_color=FARBE_POS, line_width=2,
                               annotation_text=f"Ø {avg_return:+.3f}%",
                               annotation_position="top right")
                fig2 = apply_se_theme(fig2, title="Rendite (%)", height=300, show_legend=False)

                fig2.update_yaxes(title="Häufigkeit")

                fig2.update_xaxes(title="Rendite (%)")
                st.plotly_chart(fig2, use_container_width=True)

                # Detailtabelle
                with st.expander("📋 Alle Events anzeigen"):
                    disp = opex_windows_sorted[[
                        "opex_date", "year", "month_name", "type", "total_return", "profitable"
                    ]].copy()
                    disp["opex_date"]    = disp["opex_date"].dt.strftime("%d.%m.%Y")
                    disp["total_return"] = disp["total_return"].apply(lambda x: f"{x:+.3f}%")
                    disp["profitable"]   = disp["profitable"].apply(lambda x: "✅" if x else "❌")
                    disp.columns = ["OPEX-Datum", "Jahr", "Monat", "Typ", "Rendite", "Gewinner"]
                    st.dataframe(disp, use_container_width=True, hide_index=True)

                # ── Streak-Analyse ──────────────────────────
                with st.expander("🔥 Streak-Analyse (Gewinn-/Verlust-Serien)", expanded=True):
                    from shared.streak_analysis import render_streak_table
                    # Gruppiere nach Monat
                    _opex_streak_groups = []
                    MONTH_DE = ["Jan","Feb","Mär","Apr","Mai","Jun","Jul","Aug","Sep","Okt","Nov","Dez"]
                    for m in range(1, 13):
                        m_data = opex_windows_sorted[opex_windows_sorted["opex_date"].dt.month == m].sort_values("year", ascending=False)
                        if len(m_data) == 0:
                            continue
                        entries = [{"date": int(row["year"]), "ret": float(row["total_return"])}
                                   for _, row in m_data.iterrows()]
                        _opex_streak_groups.append({"label": MONTH_DE[m-1] + " OPEX", "entries": entries})
                    render_streak_table(
                        _opex_streak_groups,
                        col_header="OPEX Monat",
                        interpretation="Zeigt die aktuelle Gewinn-/Verlust-Serie pro OPEX-Monat. "
                        "Triple Witching (Mär/Jun/Sep/Dez) hat oft staerkere Effekte.",
                    )
