"""
3_📅_Feiertags_Effekt.py
========================
Feiertags-Effekt Analyse für SeasonalEdge.

Analysiert saisonale Rendite-Muster rund um Börsenfeiertage.
Feiertage werden automatisch aus exchange_holidays.py geladen —
passend zur Börse des gewählten Tickers.

Tabs:
  1. Rendite-Chart    — kumulierte Ø-Rendite t-x bis t+y je Feiertag
  2. Best / Worst     — Ranking aller Feiertage nach Fenster-Rendite
  3. Kaeppel System   — Kaeppel Ultimate Holiday Backtest (3/3)
  4. Detailtabelle    — Pivot Jahr × Offset + Histogramme
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import date

from shared.yahoo_downloader import download_data, preprocess
from shared.symbols import SYMBOLS, get_dropdown_label
from shared.exchange_holidays import get_exchange_for_ticker
from shared.nyse_holidays import (
    _good_friday,
    _nth_weekday,
    _easter_monday,
    _whit_monday,
    _monday_if_sunday,
    _observed,
)

# ── Seiten-Konfiguration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Feiertags-Effekt · SeasonalEdge",
    page_icon="🎉",
    layout="wide",
)

# ── Feiertags-Definitionen ──────────────────────────────────────────────────────

NYSE_HOLIDAY_FUNCS = {
    "New Year's Day":   lambda y: _monday_if_sunday(date(y, 1, 1)),
    "MLK Day":          lambda y: _nth_weekday(y, 1, 0, 3),
    "Presidents' Day":  lambda y: _nth_weekday(y, 2, 0, 3),
    "Good Friday":      lambda y: _good_friday(y),
    "Memorial Day":     lambda y: _nth_weekday(y, 5, 0, -1),
    "Juneteenth":       lambda y: _observed(date(y, 6, 19)) if y >= 2022 else None,
    "Independence Day": lambda y: _observed(date(y, 7, 4)),
    "Labor Day":        lambda y: _nth_weekday(y, 9, 0, 1),
    "Thanksgiving":     lambda y: _nth_weekday(y, 11, 3, 4),
    "Christmas Day":    lambda y: _observed(date(y, 12, 25)),
}

XETRA_HOLIDAY_FUNCS = {
    "Neujahr":          lambda y: _monday_if_sunday(date(y, 1, 1)),
    "Karfreitag":       lambda y: _good_friday(y),
    "Ostermontag":      lambda y: _easter_monday(y),
    "Tag der Arbeit":   lambda y: _monday_if_sunday(date(y, 5, 1)),
    "Pfingstmontag":    lambda y: _whit_monday(y),
    "Tag d. Einheit":   lambda y: _monday_if_sunday(date(y, 10, 3)),
    "1. Weihnachtstag": lambda y: _observed(date(y, 12, 25)),
    "2. Weihnachtstag": lambda y: _observed(date(y, 12, 26)),
}

LSE_HOLIDAY_FUNCS = {
    "New Year's Day":   lambda y: _monday_if_sunday(date(y, 1, 1)),
    "Good Friday":      lambda y: _good_friday(y),
    "Easter Monday":    lambda y: _easter_monday(y),
    "Early May BH":     lambda y: _nth_weekday(y, 5, 0, 1),
    "Spring BH":        lambda y: _nth_weekday(y, 5, 0, -1),
    "Summer BH":        lambda y: _nth_weekday(y, 8, 0, -1),
    "Christmas Day":    lambda y: _observed(date(y, 12, 25)),
    "Boxing Day":       lambda y: _observed(date(y, 12, 26)),
}

EURONEXT_HOLIDAY_FUNCS = {
    "Nouvel An":        lambda y: _monday_if_sunday(date(y, 1, 1)),
    "Vendredi Saint":   lambda y: _good_friday(y),
    "Lundi de Paques":  lambda y: _easter_monday(y),
    "Fete du Travail":  lambda y: _monday_if_sunday(date(y, 5, 1)),
    "Victoire 1945":    lambda y: _monday_if_sunday(date(y, 5, 8)),
    "Lundi Pentecote":  lambda y: _whit_monday(y),
    "Bastille Day":     lambda y: _monday_if_sunday(date(y, 7, 14)),
    "Assomption":       lambda y: _monday_if_sunday(date(y, 8, 15)),
    "Toussaint":        lambda y: _monday_if_sunday(date(y, 11, 1)),
    "Armistice":        lambda y: _monday_if_sunday(date(y, 11, 11)),
    "Noel":             lambda y: _observed(date(y, 12, 25)),
    "Lendemain Noel":   lambda y: _observed(date(y, 12, 26)),
}

TSE_HOLIDAY_FUNCS = {
    "Neujahr":          lambda y: date(y, 1, 1),
    "Erwachsenentag":   lambda y: _nth_weekday(y, 1, 0, 2),
    "Nationaltag":      lambda y: date(y, 2, 11),
    "Kaisers Geb.":     lambda y: date(y, 2, 23) if y >= 2020 else date(y, 12, 23),
    "Showa Day":        lambda y: date(y, 4, 29),
    "Verfassungstag":   lambda y: date(y, 5, 3),
    "Gruener Tag":      lambda y: date(y, 5, 4),
    "Kindertag":        lambda y: date(y, 5, 5),
    "Meerestag":        lambda y: _nth_weekday(y, 7, 0, 3),
    "Bergtag":          lambda y: date(y, 8, 11) if y >= 2016 else None,
    "Senioren-Tag":     lambda y: _nth_weekday(y, 9, 0, 3),
    "Sporttag":         lambda y: _nth_weekday(y, 10, 0, 2),
    "Kulturtag":        lambda y: date(y, 11, 3),
    "Arbeitsdanktag":   lambda y: date(y, 11, 23),
}

EXCHANGE_HOLIDAY_FUNCS = {
    "NYSE":     NYSE_HOLIDAY_FUNCS,
    "NASDAQ":   NYSE_HOLIDAY_FUNCS,
    "XETRA":    XETRA_HOLIDAY_FUNCS,
    "LSE":      LSE_HOLIDAY_FUNCS,
    "EURONEXT": EURONEXT_HOLIDAY_FUNCS,
    "TSE":      TSE_HOLIDAY_FUNCS,
    "SIX":      XETRA_HOLIDAY_FUNCS,
}

# ── Farben ───────────────────────────────────────────────────────────────────────
FARBE_POS   = "#26a69a"
FARBE_NEG   = "#ef5350"
FARBE_HAUPT = "#42a5f5"
FARBE_GOLD  = "#ffa726"
TEMPLATE    = "plotly_dark"
FARBEN      = ["#42a5f5","#26a69a","#ffa726","#ef5350",
               "#ab47bc","#66bb6a","#26c6da","#ff7043","#ec407a","#8d6e63"]

def bar_color(values):
    return [FARBE_POS if v >= 0 else FARBE_NEG for v in values]

def offset_label(o):
    if o == 0:
        return "t=0"
    return f"t{int(o):+d}"

# ── Sidebar ──────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Einstellungen")

    all_tickers = list(SYMBOLS.keys())
    default_idx = all_tickers.index("SPY") if "SPY" in all_tickers else 0
    ticker = st.selectbox(
        "Symbol",
        options=all_tickers,
        index=default_idx,
        format_func=get_dropdown_label,
    )

    st.divider()
    st.subheader("Zeitfenster")
    days_before = st.slider("Tage VOR Feiertag (t-x)", 1, 10, 3)
    days_after  = st.slider("Tage NACH Feiertag (t+y)", 1, 10, 3)

    st.divider()
    st.subheader("Zeitraum")
    current_year = date.today().year
    start_year = st.slider("Von Jahr", 1990, current_year - 3, max(1990, current_year - 20))
    end_year   = st.slider("Bis Jahr", start_year + 2, current_year, current_year)

    st.divider()
    st.caption("Feiertage automatisch nach Boerse des Tickers")

# ── Daten laden ──────────────────────────────────────────────────────────────────
st.title("🎉 Feiertags-Effekt Analyse")

@st.cache_data(show_spinner="Kursdaten werden geladen ...")
def load_data(ticker):
    df = download_data(ticker, period="max")
    if df is None or len(df) == 0:
        return pd.DataFrame()
    return preprocess(df)

df_raw = load_data(ticker)
if df_raw is None or len(df_raw) == 0:
    st.error(f"Keine Daten fuer **{ticker}** verfuegbar.")
    st.stop()

df = df_raw[
    (df_raw.index.year >= start_year) &
    (df_raw.index.year <= end_year)
].copy().sort_index()

if len(df) < 100:
    st.warning("Zu wenig Daten fuer den gewahlten Zeitraum.")
    st.stop()

trading_days = df.index.tolist()

# ── Exchange & Feiertage ─────────────────────────────────────────────────────────
exchange      = get_exchange_for_ticker(ticker)
holiday_funcs = EXCHANGE_HOLIDAY_FUNCS.get(exchange, NYSE_HOLIDAY_FUNCS)

st.caption(
    f"Boerse: **{exchange}** | "
    f"{len(holiday_funcs)} Feiertage | "
    f"Zeitraum: {start_year}-{end_year} | "
    f"Handelstage: {len(df):,}"
)

@st.cache_data(show_spinner=False)
def build_holiday_dates(exchange, start_year, end_year):
    funcs = EXCHANGE_HOLIDAY_FUNCS.get(exchange, NYSE_HOLIDAY_FUNCS)
    result = {}
    for name, fn in funcs.items():
        dates = []
        for year in range(start_year, end_year + 1):
            try:
                d = fn(year)
                if d is not None:
                    dates.append(d)
            except Exception:
                pass
        if dates:
            result[name] = dates
    return result

holiday_dates = build_holiday_dates(exchange, start_year, end_year)

# ── Feiertag-Auswahl ─────────────────────────────────────────────────────────────
st.subheader("Feiertag-Auswahl")
col_a, col_b = st.columns([3, 1])
with col_a:
    selected = st.multiselect(
        "Feiertage auswaehlen",
        options=list(holiday_dates.keys()),
        default=list(holiday_dates.keys())[:4],
    )
with col_b:
    show_kaeppel = st.toggle(
        "Kaeppel System",
        value=False,
        help="3 Tage vor + 3 Tage nach = 7 Handelstage Long",
    )

if not selected:
    st.warning("Bitte mindestens einen Feiertag auswaehlen.")
    st.stop()

# ── Kern-Berechnung ──────────────────────────────────────────────────────────────

def get_next_trading_day(target_date, trading_days):
    target_ts = pd.Timestamp(target_date)
    candidates = [t for t in trading_days if t >= target_ts]
    return candidates[0] if candidates else None

def calculate_window(df, trading_days, holiday_name, holiday_list, days_before, days_after):
    rows = []
    for h_date in holiday_list:
        t0 = get_next_trading_day(h_date, trading_days)
        if t0 is None:
            continue
        try:
            idx0 = trading_days.index(t0)
        except ValueError:
            continue

        base_idx = idx0 - days_before
        if base_idx < 0 or idx0 + days_after >= len(trading_days):
            continue

        base_close = df["Close"].iloc[base_idx]
        if pd.isna(base_close) or base_close <= 0:
            continue

        for offset in range(-days_before, days_after + 1):
            pos = base_idx + days_before + offset
            if pos < 0 or pos >= len(trading_days):
                continue
            ts    = trading_days[pos]
            close = df.loc[ts, "Close"]
            ret   = (close / base_close - 1) * 100
            rows.append({
                "holiday":    holiday_name,
                "holiday_dt": pd.Timestamp(h_date),
                "year":       h_date.year,
                "offset":     offset,
                "cum_ret":    ret,
                "win":        ret > 0,
            })
    return pd.DataFrame(rows)

@st.cache_data(show_spinner="Feiertags-Effekte werden berechnet ...")
def compute_all(ticker, exchange, start_year, end_year, days_before, days_after, selected):
    result = {}
    _hd   = build_holiday_dates(exchange, start_year, end_year)
    _df   = load_data(ticker)
    _df   = _df[(_df.index.year >= start_year) & (_df.index.year <= end_year)].copy().sort_index()
    _tdays = _df.index.tolist()
    for name in selected:
        if name not in _hd:
            continue
        data = calculate_window(_df, _tdays, name, _hd[name], days_before, days_after)
        if len(data) > 0:
            result[name] = data
    return result

all_data = compute_all(ticker, exchange, start_year, end_year, days_before, days_after, tuple(selected))

if not all_data:
    st.error("Keine auswertbaren Daten fuer die gewaehlten Feiertage.")
    st.stop()

offsets       = list(range(-days_before, days_after + 1))
offset_labels = [offset_label(o) for o in offsets]

# ── Tabs ─────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Rendite-Chart",
    "🏆 Best / Worst",
    "📘 Kaeppel System",
    "🔢 Detailtabelle",
])

# ── TAB 1: RENDITE-CHART ─────────────────────────────────────────────────────────
with tab1:
    st.subheader(f"Kumulierte Rendite rund um Feiertage | {ticker}")
    st.caption(
        f"t=0 = erster Handelstag nach/am Feiertag | "
        f"Basis: Close bei t{-days_before:+d} = 0% | "
        f"{start_year}-{end_year}"
    )

    fig = go.Figure()
    for i, (hname, hdata) in enumerate(all_data.items()):
        agg = (
            hdata.groupby("offset")["cum_ret"]
            .agg(mean="mean", count="count")
            .reset_index()
        )
        means  = [float(agg[agg["offset"]==o]["mean"].values[0]) if o in agg["offset"].values else 0.0 for o in offsets]
        counts = [int(agg[agg["offset"]==o]["count"].values[0]) if o in agg["offset"].values else 0 for o in offsets]

        color = FARBEN[i % len(FARBEN)]
        fig.add_trace(go.Scatter(
            x=offset_labels, y=means,
            mode="lines+markers",
            name=hname,
            line=dict(color=color, width=2),
            marker=dict(size=7, color=color),
            customdata=counts,
            hovertemplate=f"<b>{hname}</b><br>Tag: %{{x}}<br>Rendite: %{{y:.3f}}%<br>n=%{{customdata}}<extra></extra>",
        ))

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
    # add_vline funktioniert nicht mit String-Labels auf der x-Achse → add_shape verwenden
    fig.add_shape(
        type="line",
        x0=days_before, x1=days_before,
        y0=0, y1=1, xref="x", yref="paper",
        line=dict(dash="dot", color="rgba(255,255,255,0.4)", width=1),
    )
    fig.add_annotation(
        x=days_before, y=1, xref="x", yref="paper",
        text="Feiertag", showarrow=False,
        font=dict(color="rgba(255,255,255,0.5)", size=11),
        yshift=8,
    )
    fig.update_layout(
        template=TEMPLATE, height=460,
        hovermode="x unified",
        yaxis_title="Kum. Rendite (%)",
        xaxis_title="Handelstag relativ zum Feiertag",
        legend=dict(orientation="h", yanchor="bottom", y=-0.35, x=0),
        margin=dict(b=100),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()
    metric_cols = st.columns(min(len(all_data), 5))
    for i, (hname, hdata) in enumerate(list(all_data.items())[:5]):
        window_data = hdata[hdata["offset"] == days_after]["cum_ret"]
        if len(window_data) == 0:
            continue
        total_ret = window_data.mean()
        win_rate  = (window_data > 0).mean() * 100
        with metric_cols[i % 5]:
            st.metric(
                label=hname,
                value=f"{total_ret:+.3f}%",
                delta=f"Win {win_rate:.0f}% | n={len(window_data)}",
                delta_color="normal" if total_ret >= 0 else "inverse",
            )

# ── TAB 2: BEST / WORST ──────────────────────────────────────────────────────────
with tab2:
    st.subheader(f"Feiertags-Ranking | {ticker} | {start_year}-{end_year}")
    st.caption(f"Gemessen: Gesamt-Rendite ueber {days_before+days_after+1} Tage (t{-days_before:+d} bis t{days_after:+d})")

    summary = []
    for hname, hdata in all_data.items():
        window = hdata[hdata["offset"] == days_after]["cum_ret"]
        if len(window) == 0:
            continue
        summary.append({
            "Feiertag":      hname,
            "_mean":         window.mean(),
            "Rendite":       f"{window.mean():+.4f}%",
            "Std.Abw.":      f"{window.std():.4f}%",
            "Win-Rate":      f"{(window>0).mean()*100:.1f}%",
            "Bestes Jahr":   f"{window.max():+.2f}%",
            "Schwaeche":     f"{window.min():+.2f}%",
            "n":             len(window),
        })

    if summary:
        sdf = pd.DataFrame(summary).sort_values("_mean", ascending=False)
        means_num = sdf["_mean"].tolist()

        fig2 = go.Figure(go.Bar(
            x=sdf["Feiertag"], y=means_num,
            marker_color=bar_color(means_num),
            text=[f"{v:+.3f}%" for v in means_num],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Rendite: %{y:.3f}%<extra></extra>",
        ))
        fig2.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
        fig2.update_layout(
            template=TEMPLATE, height=400,
            yaxis_title="Rendite (%)", showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(sdf.drop(columns=["_mean"]).reset_index(drop=True),
                     use_container_width=True, hide_index=True)

# ── TAB 3: KAEPPEL SYSTEM ───────────────────────────────────────────────────────
with tab3:
    st.subheader("Kaeppel Ultimate Holiday System")
    st.info(
        "**Strategie:** Long 3 Handelstage VOR jedem Feiertag, "
        "Exit 3 Handelstage NACH dem Feiertag (= 7 Handelstage). "
        "Alle Feiertage des Jahres kombiniert. "
        "Laut Kaeppel: 22 von 25 Jahren profitabel (S&P 500).",
        icon="📗",
    )

    @st.cache_data(show_spinner="Kaeppel-Backtest ...")
    def run_kaeppel(ticker, exchange, start_year, end_year):
        _hd    = build_holiday_dates(exchange, start_year, end_year)
        _df    = load_data(ticker)
        _df    = _df[(_df.index.year >= start_year) & (_df.index.year <= end_year)].copy().sort_index()
        _tdays = _df.index.tolist()

        all_holidays = sorted([d for dl in _hd.values() for d in dl])
        trades = []
        for h_date in all_holidays:
            t0 = get_next_trading_day(h_date, _tdays)
            if t0 is None:
                continue
            try:
                idx0 = _tdays.index(t0)
            except ValueError:
                continue
            entry_idx = idx0 - 3
            exit_idx  = idx0 + 3
            if entry_idx < 0 or exit_idx >= len(_tdays):
                continue
            entry_ts    = _tdays[entry_idx]
            exit_ts     = _tdays[exit_idx]
            entry_price = _df.loc[entry_ts, "Close"]
            exit_price  = _df.loc[exit_ts, "Close"]
            ret         = (exit_price / entry_price - 1) * 100
            trades.append({
                "Feiertag":   next((n for n, dl in _hd.items() if h_date in dl), "?"),
                "Datum":      pd.Timestamp(h_date),
                "Entry":      entry_ts,
                "Exit":       exit_ts,
                "Entry-Kurs": entry_price,
                "Exit-Kurs":  exit_price,
                "Rendite":    ret,
                "Win":        ret > 0,
                "Jahr":       h_date.year,
            })
        return pd.DataFrame(trades)

    trades_df = run_kaeppel(ticker, exchange, start_year, end_year)

    if len(trades_df) == 0:
        st.warning("Keine Trades im gewaehlten Zeitraum.")
    else:
        yearly = (
            trades_df.groupby("Jahr")["Rendite"]
            .agg(total="sum", count="count", wins=lambda x: (x > 0).sum())
            .reset_index()
        )
        yearly["Win-Rate"]  = yearly["wins"] / yearly["count"] * 100
        yearly["Profitabel"] = yearly["total"] > 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Profitable Jahre",
                  f"{yearly['Profitabel'].sum()} / {len(yearly)}",
                  f"{yearly['Profitabel'].mean()*100:.0f}%")
        m2.metric("Gesamt-Rendite", f"{trades_df['Rendite'].sum():+.1f}%")
        m3.metric("Win-Rate Trades", f"{trades_df['Win'].mean()*100:.1f}%")
        m4.metric("Anzahl Trades", str(len(trades_df)))

        st.divider()

        # Equity-Kurve
        equity = [100.0]
        for _, row in trades_df.sort_values("Entry").iterrows():
            equity.append(equity[-1] * (1 + row["Rendite"] / 100))

        fig3 = go.Figure(go.Scatter(
            x=list(range(len(equity))), y=equity,
            mode="lines", line=dict(color=FARBE_HAUPT, width=2),
            fill="tozeroy", fillcolor="rgba(66,165,245,0.1)",
        ))
        fig3.add_hline(y=100, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
        fig3.update_layout(
            template=TEMPLATE, height=280,
            title="Equity-Kurve (Start = 100)",
            yaxis_title="Equity", xaxis_title="Trade Nr.",
            showlegend=False,
        )
        st.plotly_chart(fig3, use_container_width=True)

        # Jahres-Balken
        fig4 = go.Figure(go.Bar(
            x=yearly["Jahr"], y=yearly["total"],
            marker_color=bar_color(yearly["total"].tolist()),
            text=[f"{v:+.1f}%" for v in yearly["total"]],
            textposition="outside",
        ))
        fig4.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
        fig4.update_layout(
            template=TEMPLATE, height=300,
            title="Jahres-Rendite (alle Feiertage kombiniert)",
            yaxis_title="Summe Renditen (%)", showlegend=False,
        )
        st.plotly_chart(fig4, use_container_width=True)

        with st.expander("Alle Trades anzeigen"):
            disp = trades_df.copy()
            disp["Datum"]      = disp["Datum"].dt.strftime("%d.%m.%Y")
            disp["Entry"]      = disp["Entry"].dt.strftime("%d.%m.%Y")
            disp["Exit"]       = disp["Exit"].dt.strftime("%d.%m.%Y")
            disp["Entry-Kurs"] = disp["Entry-Kurs"].apply(lambda x: f"{x:.2f}")
            disp["Exit-Kurs"]  = disp["Exit-Kurs"].apply(lambda x: f"{x:.2f}")
            disp["Rendite"]    = disp["Rendite"].apply(lambda x: f"{x:+.3f}%")
            disp["Win"]        = disp["Win"].map({True: "✅", False: "❌"})
            st.dataframe(
                disp[["Jahr","Feiertag","Datum","Entry","Exit","Entry-Kurs","Exit-Kurs","Rendite","Win"]],
                use_container_width=True, hide_index=True,
            )

# ── TAB 4: DETAILTABELLE ─────────────────────────────────────────────────────────
with tab4:
    st.subheader("Detailansicht pro Feiertag")

    selected_detail = st.selectbox(
        "Feiertag waehlen",
        options=list(all_data.keys()),
        key="detail_select",
    )

    if selected_detail in all_data:
        detail = all_data[selected_detail].copy()

        pivot = detail.pivot_table(
            index=["year", "holiday_dt"],
            columns="offset",
            values="cum_ret",
            aggfunc="first",
        ).reset_index()

        new_cols = ["Jahr", "Datum"] + [offset_label(int(c)) for c in pivot.columns[2:]]
        pivot.columns = new_cols
        pivot["Datum"] = pd.to_datetime(pivot["Datum"]).dt.strftime("%d.%m.%Y")
        for col in new_cols[2:]:
            pivot[col] = pd.to_numeric(pivot[col], errors="coerce").apply(
                lambda x: f"{x:+.3f}%" if not pd.isna(x) else "-"
            )
        st.dataframe(pivot, use_container_width=True, hide_index=True)

        st.divider()
        col_h1, col_h2 = st.columns(2)

        with col_h1:
            t0_vals = detail[detail["offset"] == 0]["cum_ret"].dropna()
            if len(t0_vals) > 0:
                fig5 = go.Figure(go.Histogram(
                    x=t0_vals, nbinsx=20,
                    marker_color=FARBE_HAUPT, opacity=0.85,
                ))
                fig5.add_vline(x=0, line_dash="dash", line_color="white", line_width=1)
                fig5.add_vline(x=t0_vals.mean(), line_dash="dot",
                               line_color=FARBE_GOLD, line_width=2,
                               annotation_text=f"Ø {t0_vals.mean():+.3f}%",
                               annotation_position="top right",
                               annotation_font_color=FARBE_GOLD)
                fig5.update_layout(
                    template=TEMPLATE, height=280,
                    title=f"Verteilung t=0 | {selected_detail}",
                    xaxis_title="Rendite (%)", yaxis_title="Haeufigkeit",
                    showlegend=False,
                )
                st.plotly_chart(fig5, use_container_width=True)

        with col_h2:
            end_vals = detail[detail["offset"] == days_after]["cum_ret"].dropna()
            if len(end_vals) > 0:
                fig6 = go.Figure(go.Histogram(
                    x=end_vals, nbinsx=20,
                    marker_color=FARBE_GOLD, opacity=0.85,
                ))
                fig6.add_vline(x=0, line_dash="dash", line_color="white", line_width=1)
                fig6.add_vline(x=end_vals.mean(), line_dash="dot",
                               line_color=FARBE_HAUPT, line_width=2,
                               annotation_text=f"Ø {end_vals.mean():+.3f}%",
                               annotation_position="top right",
                               annotation_font_color=FARBE_HAUPT)
                fig6.update_layout(
                    template=TEMPLATE, height=280,
                    title=f"Gesamtfenster t{-days_before:+d} bis t{days_after:+d} | {selected_detail}",
                    xaxis_title="Rendite (%)", yaxis_title="Haeufigkeit",
                    showlegend=False,
                )
                st.plotly_chart(fig6, use_container_width=True)
