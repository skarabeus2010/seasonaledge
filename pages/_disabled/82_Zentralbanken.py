"""
SeasonAlpha - Zentralbank-Effekt
==================================
Analyse der Rendite rund um Notenbank-Sitzungen (Fed, ECB, BOE, BOJ).
t0 = Entscheidungstag → normiert auf 0%.
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

from shared.constants import DEFAULT_TICKER, DEFAULT_YEARS
from shared.data import download_data, preprocess
from shared.fed_dates import get_fomc_dates
from shared.charts import apply_se_theme
from shared.constants import SE_COLORS
from shared.central_banks import (
    get_ecb_dates, get_boe_dates, get_boj_dates,
    get_fed_rate_changes, get_fed_minutes_dates,
    CENTRAL_BANK_REGISTRY
)

st.set_page_config(page_title="SeasonAlpha - Zentralbanken", page_icon="🏛️", layout="wide")

from shared.design import inject_se_css
inject_se_css()


# ══════════════════════════════════════════════════════════════
# BERECHNUNG
# ══════════════════════════════════════════════════════════════

EVENT_SOURCES = {
    "🇺🇸 Fed (FOMC)": lambda: [{"date": pd.Timestamp(d), "label": "FOMC"} for d in get_fomc_dates()],
    "🇺🇸 Fed Rate Hike": lambda: [{"date": pd.Timestamp(r["date"]), "label": f"Hike +{r['bps']}bp"} for r in get_fed_rate_changes("hike")],
    "🇺🇸 Fed Rate Cut": lambda: [{"date": pd.Timestamp(r["date"]), "label": f"Cut {r['bps']}bp"} for r in get_fed_rate_changes("cut")],
    "🇺🇸 Fed Minutes": lambda: [{"date": pd.Timestamp(d), "label": "Minutes"} for d in get_fed_minutes_dates()],
    "🇪🇺 ECB": lambda: [{"date": pd.Timestamp(d), "label": "ECB"} for d in get_ecb_dates()],
    "🇬🇧 BOE": lambda: [{"date": pd.Timestamp(d), "label": "BOE"} for d in get_boe_dates()],
    "🇯🇵 BOJ": lambda: [{"date": pd.Timestamp(d), "label": "BOJ"} for d in get_boj_dates()],
}


def analyze_event_effect(df, event_dates, days_before, days_after):
    """
    Event-Effekt-Analyse (generisch für alle Zentralbank-Events).
    t0 = Entscheidungstag (oder nächster Handelstag) → 0% normiert.
    """
    window_size = days_before + 1 + days_after
    t0_idx = days_before
    all_curves = []
    
    trading_index = df.index
    
    for event in event_dates:
        event_date = event["date"]
        
        try:
            # t0 = Event-Tag oder letzter Handelstag davor
            pre = df[df.index <= event_date]
            if len(pre) < days_before + 1:
                continue
            
            # Prüfe ob Event-Tag ein Handelstag ist
            if event_date in trading_index:
                # t0 ist der Event-Tag selbst
                t0_pos = trading_index.get_loc(event_date)
            else:
                # Nächster Handelstag vor dem Event
                pre_dates = trading_index[trading_index <= event_date]
                if len(pre_dates) == 0:
                    continue
                t0_pos = trading_index.get_loc(pre_dates[-1])
            
            # Fenster: days_before vor t0, t0 selbst, days_after nach t0
            start_pos = t0_pos - days_before
            end_pos = t0_pos + days_after + 1
            
            if start_pos < 0 or end_pos > len(df):
                continue
            
            window = df.iloc[start_pos:end_pos]
            
            if len(window) != window_size:
                continue
            
            # Normalisierung: t0 = 0%
            log_rets = window["log_return"].values
            cum_log = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
            raw_curve = 100 * np.exp(cum_log)
            
            t0_value = raw_curve[t0_idx]
            curve = ((raw_curve / t0_value - 1) * 100).tolist()
            total_return = curve[-1] - curve[0]
            
            event_year = event_date.year
            event_label = event.get("label", "Event")
            
            all_curves.append({
                "year": event_year,
                "date": event_date.strftime("%Y-%m-%d"),
                "event_label": event_label,
                "curve": curve,
                "total_return": total_return
            })
            
        except Exception:
            continue
    
    if not all_curves:
        return None
    
    # Durchschnittskurve
    avg_curve = [np.mean([c["curve"][i] for c in all_curves]) for i in range(window_size)]
    
    # Labels
    labels = []
    for i in range(window_size):
        offset = i - days_before
        if offset < 0:
            labels.append(f"t{offset}")
        elif offset == 0:
            labels.append("t0")
        else:
            labels.append(f"t+{offset}")
    
    # Statistiken
    returns = [c["total_return"] for c in all_curves]
    wins = [r for r in returns if r > 0]
    
    stats = {
        "avg_return": np.mean(returns),
        "median_return": np.median(returns),
        "win_rate": len(wins) / len(returns) * 100 if returns else 0,
        "std_dev": np.std(returns),
        "max_gain": max(returns),
        "max_loss": min(returns),
        "total_windows": len(all_curves),
        "winning": len(wins),
        "losing": len(returns) - len(wins)
    }
    
    sorted_curves = sorted(all_curves, key=lambda c: c["total_return"])
    
    return {
        "avg_curve": avg_curve,
        "all_curves": all_curves,
        "labels": labels,
        "stats": stats,
        "best": sorted_curves[-1],
        "worst": sorted_curves[0]
    }


# ══════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════

def build_event_chart(result, ticker, days_before, days_after, event_name,
                      show_individual=False):
    """Event-Effekt Chart (t0 = 0%)."""
    
    fig = go.Figure()
    labels = result["labels"]
    avg_curve = result["avg_curve"]
    x_indices = list(range(len(labels)))
    
    if show_individual:
        for entry in result["all_curves"]:
            fig.add_trace(go.Scatter(
                x=x_indices, y=entry["curve"], mode="lines",
                line=dict(color="rgba(150,150,150,0.12)", width=0.6),
                showlegend=False, hoverinfo="skip"
            ))
    
    t0_idx = days_before
    fig.add_vline(x=t0_idx, line_dash="dash",
        line_color="rgba(255,215,0,0.5)", line_width=1.5,
        annotation_text="t0 (Entscheidung)",
        annotation_position="top",
        annotation_font=dict(size=10, color="#FFD700"))
    
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.add_trace(go.Scatter(
        x=x_indices, y=avg_curve,
        mode="lines+markers",
        line=dict(color="#00CED1", width=3),
        marker=dict(size=6, color="#00CED1"),
        fill="tozeroy", fillcolor="rgba(0,206,209,0.08)",
        name=f"Ø {event_name} ({result['stats']['total_windows']} Events)",
        hovertemplate="%{text}<br>%{y:+.3f}%<extra></extra>",
        text=labels
    ))
    
    fig = apply_se_theme(fig, title=f"{ticker} — {event_name} Effekt (t-{days_before} bis t+{days_after})", height=430)
    return fig


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    with st.sidebar:
        st.markdown("## 🏛️ Zentralbank-Effekt")
        st.markdown("---")
        
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER, key="cb_ticker").upper().strip()
        
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider("Analyse-Zeitraum (Jahre)",
            options=period_options, value=DEFAULT_YEARS,
            format_func=lambda x: str(x), key="cb_period")
        years_back_is_max = (years_back_raw == "Max")
        
        st.markdown("---")
        st.markdown("### Event auswählen")
        
        selected_events = st.multiselect(
            "Zentralbank-Events",
            options=list(EVENT_SOURCES.keys()),
            default=["🇺🇸 Fed (FOMC)"],
            help="Mehrere Events können kombiniert werden"
        )
        
        st.markdown("---")
        
        days_before = st.slider("Tage VOR Event (t-y)", 1, 15, 5, key="cb_before",
            help="Handelstage vor dem Entscheidungstag")
        days_after = st.slider("Tage NACH Event (t+x)", 1, 15, 5, key="cb_after",
            help="Handelstage nach dem Entscheidungstag")
        
        show_individual = st.checkbox("Einzelne Events zeigen", value=False, key="cb_indiv")
    
    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)
    
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden.")
        return
    
    df = preprocess(raw_df)
    all_years = sorted(df["year"].unique())
    
    if years_back_is_max:
        selected_years = all_years
    else:
        years_back = int(years_back_raw)
        cutoff_year = datetime.now().year - years_back
        selected_years = [y for y in all_years if y >= cutoff_year]
    
    if not selected_events:
        st.warning("Bitte mindestens ein Event auswählen.")
        return
    
    # ── Events sammeln ────────────────────────────────
    all_event_dates = []
    event_name_parts = []
    
    for evt_key in selected_events:
        evt_func = EVENT_SOURCES[evt_key]
        dates = evt_func()
        # Nur Events in selected_years
        filtered = [d for d in dates if d["date"].year in selected_years]
        all_event_dates.extend(filtered)
        event_name_parts.append(evt_key.split(" ", 1)[1] if " " in evt_key else evt_key)
    
    if not all_event_dates:
        st.warning("Keine Events im gewählten Zeitraum gefunden.")
        return
    
    event_name = " + ".join(event_name_parts)
    
    st.markdown(f"**{len(all_event_dates)} Events** im Zeitraum gefunden")
    
    # ── Analyse ───────────────────────────────────────
    result = analyze_event_effect(df, all_event_dates, days_before, days_after)
    
    if result is None:
        st.warning("Nicht genug Daten für die Analyse.")
        return
    
    # ── Chart ─────────────────────────────────────────
    fig = build_event_chart(result, ticker, days_before, days_after, event_name, show_individual)
    st.plotly_chart(fig, use_container_width=True)
    
    # ── Metriken ──────────────────────────────────────
    stats = result["stats"]
    
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
    with c2:
        st.metric("Ø Rendite", f"{stats['avg_return']:+.3f}%")
    with c3:
        st.metric("Median", f"{stats['median_return']:+.3f}%")
    with c4:
        st.metric("Max Gewinn", f"{stats['max_gain']:+.2f}%")
    with c5:
        st.metric("Max Verlust", f"{stats['max_loss']:+.2f}%")
    
    st.caption(
        f"Basierend auf {stats['total_windows']} Event-Fenstern · "
        f"{stats['winning']} Gewinner / {stats['losing']} Verlierer · "
        f"Std.Abw: {stats['std_dev']:.3f}%"
    )
    
    # ── Best & Worst ──────────────────────────────────
    best = result["best"]
    worst = result["worst"]
    
    st.markdown("#### 🏆 Bester & schlechtester Event-Effekt")
    
    table_data = {
        "": ["🟢 Bester", "🔴 Schlechtester"],
        "Datum": [best["date"], worst["date"]],
        "Event": [best["event_label"], worst["event_label"]],
        "Rendite": [f"{best['total_return']:+.2f}%", f"{worst['total_return']:+.2f}%"]
    }
    st.table(pd.DataFrame(table_data).set_index(""))
    
    # ── Detailtabelle pro Event-Typ ───────────────────
    if len(selected_events) > 1:
        st.markdown("#### 📋 Performance pro Event-Typ")
        st.caption(f"Rendite wenn bei t-{days_before} gekauft und bei t+{days_after} verkauft")
        
        type_perf = {}
        for entry in result["all_curves"]:
            lbl = entry["event_label"]
            if lbl not in type_perf:
                type_perf[lbl] = []
            type_perf[lbl].append(entry["total_return"])
        
        rows = []
        for lbl in sorted(type_perf.keys()):
            rets = type_perf[lbl]
            wins = [r for r in rets if r > 0]
            rows.append({
                "Event": lbl,
                "Ø Rendite": f"{np.mean(rets):+.3f}%",
                "Median": f"{np.median(rets):+.3f}%",
                "Win Rate": f"{len(wins)/len(rets)*100:.0f}%",
                "Beste": f"{max(rets):+.2f}%",
                "Schlecht.": f"{min(rets):+.2f}%",
                "n": len(rets)
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    
    # ── Nächstes Event ────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📅 Nächste Termine")
    
    today = pd.Timestamp(datetime.now().date())
    future_events = [e for e in all_event_dates if e["date"] > today]
    future_events.sort(key=lambda x: x["date"])
    
    if future_events:
        next_rows = []
        for e in future_events[:8]:
            days_until = (e["date"] - today).days
            next_rows.append({
                "Datum": e["date"].strftime("%d.%m.%Y"),
                "Wochentag": e["date"].strftime("%A"),
                "Event": e["label"],
                "In Tagen": days_until
            })
        st.dataframe(pd.DataFrame(next_rows), use_container_width=True, hide_index=True)
    else:
        st.info("Keine zukünftigen Termine im gewählten Zeitraum.")


if __name__ == "__main__":
    main()
