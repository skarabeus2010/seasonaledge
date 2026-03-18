"""
SeasonalEdge - Schritt 1: Data Layer + Seasonal Chart
=====================================================
Streamlit-App für saisonale Analyse von Finanzinstrumenten.

Starten mit: streamlit run seasonal_app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

# ══════════════════════════════════════════════════════════════
# KONFIGURATION
# ══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="SeasonalEdge",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_TICKER = "AAPL"
DEFAULT_YEARS = 20

# Farben (aus dem Skill)
COLOR_SEASONAL_AVG = "#00CED1"
COLOR_INDIVIDUAL = "rgba(150,150,150,0.25)"
COLOR_CONFIDENCE = "rgba(0,206,209,0.15)"
COLOR_CURRENT_YEAR = "#FFD700"
COLOR_PRESSURE = "#FF69B4"  # Pink für Pressure
COLOR_WAR = "#FF4500"       # Orange-Rot für Kriegszeiten

CYCLE_COLORS = {
    "Year 1 (Post-Election)": "#FF6B6B",
    "Year 2 (Midterm Election)": "#FFA07A",
    "Year 3 (Pre-Election)": "#4ECDC4",
    "Year 4 (Election Year)": "#45B7D1"
}

DECADE_COLORS = {
    0: "#FF6B6B", 1: "#FF8E72", 2: "#FFA07A", 3: "#FFD93D",
    4: "#6BCB77", 5: "#4ECDC4", 6: "#45B7D1", 7: "#4682C8",
    8: "#9664B4", 9: "#C875C4"
}
DECADE_LABELS = {
    0: "X0er (1900, 1910, ...2020)", 1: "X1er (1901, 1911, ...2021)",
    2: "X2er (1902, 1912, ...2022)", 3: "X3er (1903, 1913, ...2023)",
    4: "X4er (1904, 1914, ...2024)", 5: "X5er (1905, 1915, ...2025)",
    6: "X6er (1906, 1916, ...2026)", 7: "X7er (1907, 1917, ...2027)",
    8: "X8er (1908, 1918, ...2028)", 9: "X9er (1909, 1919, ...2029)"
}


# ══════════════════════════════════════════════════════════════
# DATA LAYER
# ══════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def download_data(ticker, period="max"):
    """
    Lade OHLC-Daten von Yahoo Finance.
    Cached für 1 Stunde.
    """
    try:
        df = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        if df.empty:
            return None
        
        return df
    except Exception as e:
        st.error(f"Fehler beim Laden von {ticker}: {e}")
        return None


def preprocess(df):
    """
    Bereite die Rohdaten für die saisonale Analyse vor.
    Fügt Spalten hinzu: return (simple), log_return, day_of_year, year, month
    """
    df = df.copy()
    df["return"] = df["Close"].pct_change()
    df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
    df["day_of_year"] = df.index.dayofyear
    df["year"] = df.index.year
    df["month"] = df.index.month
    df = df.dropna(subset=["return"])
    return df


# ══════════════════════════════════════════════════════════════
# SEASONAL ANALYSIS
# ══════════════════════════════════════════════════════════════

def get_presidential_cycle_year(year):
    """Bestimme die Position im Präsidentenzyklus."""
    cycle_position = (year - 2024) % 4
    if cycle_position == 0:
        return "Year 4 (Election Year)"
    elif cycle_position == 1 or cycle_position == -3:
        return "Year 1 (Post-Election)"
    elif cycle_position == 2 or cycle_position == -2:
        return "Year 2 (Midterm Election)"
    else:
        return "Year 3 (Pre-Election)"


def get_decade_digit(year):
    """Letzte Ziffer des Jahres: 2025 → 5, 1987 → 7"""
    return year % 10


def normalize_year(year_df):
    """
    Normalisiere ein Jahr auf Startwert 100.
    Methode: Kumulative Log-Returns → zurück in Prozent.
    Log-Returns sind additiv und mathematisch korrekt summierbar.
    """
    log_returns = year_df["log_return"].values
    cum_log = np.cumsum(log_returns)
    # Erster Tag = 0 (kein Return), dann kumulativ
    cum_log = np.insert(cum_log[:-1], 0, 0) if len(log_returns) > 0 else np.array([0])
    # Zurück in Prozent-Skala: 100 * exp(cum_log)
    cumulative = (100 * np.exp(np.cumsum(np.insert(log_returns, 0, 0)[:-1]))).tolist()
    
    # Sicherheitscheck: letzter Wert hinzufügen falls nötig
    if len(cumulative) < len(year_df):
        cumulative.append(100 * np.exp(np.sum(log_returns)))
    elif len(cumulative) > len(year_df):
        cumulative = cumulative[:len(year_df)]
    
    return cumulative


def interpolate_to_365(days, values):
    """
    Interpoliere auf volle 365 Kalendertage.
    Nötig, weil Handelstage Lücken haben (Wochenenden, Feiertage).
    """
    full_year = []
    
    for target_day in range(1, 366):
        if target_day in days:
            idx = days.index(target_day)
            full_year.append(values[idx])
        elif target_day < days[0]:
            full_year.append(values[0])
        elif target_day > days[-1]:
            full_year.append(values[-1])
        else:
            # Finde die nächsten bekannten Tage links und rechts
            prev_days = [d for d in days if d < target_day]
            next_days = [d for d in days if d > target_day]
            
            if prev_days and next_days:
                prev_day = prev_days[-1]
                next_day = next_days[0]
                prev_val = values[days.index(prev_day)]
                next_val = values[days.index(next_day)]
                
                weight = (target_day - prev_day) / (next_day - prev_day)
                interpolated = prev_val + weight * (next_val - prev_val)
                full_year.append(interpolated)
            else:
                full_year.append(values[-1])
    
    return full_year


def build_year_data(df, selected_years):
    """
    Baue normalisierte Jahreskurven für alle gewählten Jahre.
    
    Returns:
        dict: {year: {"days": [...], "cumulative": [...], "full_365": [...], "df": year_df}}
    """
    year_data = {}
    
    for year in selected_years:
        year_df = df[df["year"] == year].copy()
        
        if len(year_df) < 20:
            continue
        
        cumulative = normalize_year(year_df)
        days = year_df["day_of_year"].tolist()
        full_365 = interpolate_to_365(days, cumulative)
        
        year_data[year] = {
            "days": days,
            "cumulative": cumulative,
            "full_365": full_365,
            "df": year_df
        }
    
    return year_data


def calculate_seasonal_average(year_data):
    """
    Berechne den saisonalen Durchschnitt über alle Jahre.
    Jedes Jahr ist auf 365 Tage interpoliert und startet bei 100.
    """
    if not year_data:
        return [], []
    
    all_curves = [yd["full_365"] for yd in year_data.values()]
    
    avg = []
    std = []
    
    for day_idx in range(365):
        day_values = [curve[day_idx] for curve in all_curves]
        avg.append(np.mean(day_values))
        std.append(np.std(day_values))
    
    return avg, std


def count_trading_days(year_data, start_day, end_day):
    """Zähle die durchschnittliche Anzahl Handelstage im Zeitraum."""
    counts = []
    for yd in year_data.values():
        period_days = [d for d in yd["days"] if start_day <= d <= end_day]
        if period_days:
            counts.append(len(period_days))
    return int(np.mean(counts)) if counts else 0


def calculate_period_stats(year_data, start_day, end_day):
    """Berechne Statistiken für einen gewählten Zeitraum."""
    period_returns = []
    
    for year, yd in year_data.items():
        start_val = yd["full_365"][start_day - 1]
        end_val = yd["full_365"][min(end_day - 1, 364)]
        ret = (end_val - start_val) / start_val * 100
        period_returns.append(ret)
    
    if not period_returns:
        return {}
    
    wins = [r for r in period_returns if r > 0]
    
    return {
        "win_rate": len(wins) / len(period_returns) * 100,
        "avg_return": np.mean(period_returns),
        "median_return": np.median(period_returns),
        "max_gain": max(period_returns),
        "max_loss": min(period_returns),
        "std_dev": np.std(period_returns),
        "total_years": len(period_returns),
        "winning_years": len(wins),
        "losing_years": len(period_returns) - len(wins)
    }


# ══════════════════════════════════════════════════════════════
# PRESSURE CHART
# ══════════════════════════════════════════════════════════════

PRESSURE_PERIODS = [10, 20, 30, 40, 60, 80]


def calculate_pressure_curve(df, smoothing_window=5):
    """
    Pressure Chart: EINE Linie, die aus der Addition der durchschnittlichen
    Tagesrenditen verschiedener Lookback-Perioden entsteht.
    
    Berechnung:
    1. Für jede Periode (10, 20, 30, 40, 60, 80 Jahre):
       - Berechne die durchschnittliche tägliche Rendite pro Kalendertag
       - Das ergibt eine 365-Tage-Kurve mit dem Ø Daily Return pro Tag
    2. Addiere alle verfügbaren Perioden-Kurven tageweise
    3. Kumuliere die Summe → eine einzige Pressure-Kurve
    
    Je mehr Perioden an einem Tag positiv sind, desto stärker der Aufwärtsdruck.
    """
    current_year = datetime.now().year
    all_years = sorted(df["year"].unique())
    max_years_available = current_year - min(all_years)
    
    available_periods = [p for p in PRESSURE_PERIODS if p <= max_years_available]
    
    if not available_periods:
        return None, 0, []
    
    # Für jede Periode: durchschnittliche tägliche Rendite pro Kalendertag (365 Werte)
    period_daily_avgs = {}
    
    for period in available_periods:
        cutoff_year = current_year - period
        period_years = [y for y in all_years if y >= cutoff_year and y < current_year]
        
        if len(period_years) < 2:
            continue
        
        # Sammle die täglichen Returns aller Jahre, interpoliert auf 365 Tage
        year_daily_returns = []
        for year in period_years:
            year_df = df[df["year"] == year].copy()
            if len(year_df) < 20:
                continue
            
            # Tägliche Log-Returns auf 365 Kalendertage interpolieren
            days = year_df["day_of_year"].tolist()
            log_rets = year_df["log_return"].values.tolist()
            
            # Interpoliere Returns auf volle 365 Tage
            full_rets = []
            for target_day in range(1, 366):
                if target_day in days:
                    idx = days.index(target_day)
                    full_rets.append(log_rets[idx])
                else:
                    full_rets.append(0.0)  # Kein Handelstag = 0 Return
            
            year_daily_returns.append(full_rets)
        
        if not year_daily_returns:
            continue
        
        # Durchschnittlicher täglicher Return pro Kalendertag
        avg_daily = [np.mean([yr[d] for yr in year_daily_returns]) * 100 
                     for d in range(365)]
        period_daily_avgs[period] = avg_daily
    
    if not period_daily_avgs:
        return None, max_years_available, []
    
    # ADDIERE alle Perioden-Kurven tageweise
    summed_daily = [0.0] * 365
    for period, avg_daily in period_daily_avgs.items():
        for d in range(365):
            summed_daily[d] += avg_daily[d]
    
    # Kumuliere die Summe → Pressure-Kurve (Start bei 0)
    pressure_curve = np.cumsum(summed_daily).tolist()
    
    # Glätten
    if smoothing_window > 1:
        pressure_curve = pd.Series(pressure_curve).rolling(
            smoothing_window, center=True, min_periods=1
        ).mean().tolist()
    
    return pressure_curve, max_years_available, list(period_daily_avgs.keys())


def build_pressure_chart(pressure_curve, ticker, available_periods, max_years):
    """Erstelle den Pressure Chart als Plotly Figure."""
    
    fig = go.Figure()
    
    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    month_starts = [datetime(2024, m, 1).timetuple().tm_yday for m in range(1, 13)]
    x_days = list(range(1, 366))
    
    # Farbcodierung: grün über 0, rot unter 0
    colors = ["#4CAF50" if v >= 0 else "#F44336" for v in pressure_curve]
    
    # Hauptlinie
    fig.add_trace(go.Scatter(
        x=x_days, y=pressure_curve,
        mode="lines",
        line=dict(color="#00CED1", width=2.5),
        name=f"Pressure ({'+'.join(str(p) for p in available_periods)}J)",
        fill="tozeroy",
        fillcolor="rgba(0,206,209,0.1)",
        hovertemplate="Tag %{x}<br>Pressure: %{y:+.2f}<extra></extra>"
    ))
    
    # Nulllinie
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(t=40, r=20, b=50, l=60),
        title=dict(
            text=f"{ticker} — Pressure Chart ({len(available_periods)} Perioden addiert)",
            font=dict(size=16, color="#e0e0e0")
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=month_starts,
            ticktext=month_names,
            gridcolor="rgba(255,255,255,0.06)",
            range=[1, 365]
        ),
        yaxis=dict(
            title="Kumulierter saisonaler Druck",
            gridcolor="rgba(255,255,255,0.06)",
            tickformat="+.1f",
            zeroline=True,
            zerolinecolor="rgba(255,255,255,0.2)"
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="right", x=1,
            font=dict(size=11)
        ),
        hovermode="x unified"
    )
    
    # Y-Achse dynamisch
    y_pad = max(abs(min(pressure_curve)), abs(max(pressure_curve))) * 0.15
    fig.update_yaxes(range=[min(pressure_curve) - y_pad, max(pressure_curve) + y_pad])
    
    return fig


# ══════════════════════════════════════════════════════════════
# SAISONALE INDIKATOREN
# ══════════════════════════════════════════════════════════════

def classify_december_low(df):
    """
    December Low Indikator: Klassifiziere jedes Jahr danach, ob das
    Dezember-Tief des Vorjahres im Q1 (Jan-Mär) unterschritten wurde.
    
    Returns:
        dict: {year: True/False} — True = Dez-Tief wurde NICHT unterschritten (bullish)
    """
    years = sorted(df["year"].unique())
    classification = {}
    
    for year in years:
        prev_year = year - 1
        
        # Dezember-Tief des Vorjahres
        dec_prev = df[(df["year"] == prev_year) & (df["month"] == 12)]
        if len(dec_prev) == 0:
            continue
        
        dec_low = dec_prev["Low"].min() if "Low" in df.columns else dec_prev["Close"].min()
        
        # Q1 des aktuellen Jahres (Jan-Mär)
        q1 = df[(df["year"] == year) & (df["month"].isin([1, 2, 3]))]
        if len(q1) == 0:
            continue
        
        q1_low = q1["Low"].min() if "Low" in df.columns else q1["Close"].min()
        
        # True = Dez-Tief wurde NICHT unterschritten (bullish)
        classification[year] = q1_low >= dec_low
    
    return classification


def classify_january_first5(df):
    """
    Januar Indikator (First 5 Days): Klassifiziere jedes Jahr danach, ob
    die ersten 5 Handelstage im Januar positiv oder negativ waren.
    
    Vergleich: Letzter Handelstag des Vorjahres vs. 5. Handelstag des neuen Jahres.
    
    Returns:
        dict: {year: True/False} — True = erste 5 Tage POSITIV (bullish)
    """
    years = sorted(df["year"].unique())
    classification = {}
    
    for year in years:
        prev_year = year - 1
        
        # Letzter Handelstag des Vorjahres
        prev_year_data = df[df["year"] == prev_year]
        if len(prev_year_data) == 0:
            continue
        
        last_close_prev = prev_year_data["Close"].iloc[-1]
        
        # Erste 5 Handelstage des aktuellen Jahres (Januar)
        jan_data = df[(df["year"] == year) & (df["month"] == 1)]
        if len(jan_data) < 5:
            continue
        
        close_day5 = jan_data["Close"].iloc[4]  # 5. Handelstag (0-basiert)
        
        # True = positiv (bullish)
        classification[year] = close_day5 > last_close_prev
    
    return classification


# US-Kriege mit US-Beteiligung (aus US-Wars.MD)
US_WARS = [
    {"name": "Spanisch-Amerikanischer Krieg", "start": 1898, "end": 1898},
    {"name": "Philippinisch-Amerikanischer Krieg", "start": 1899, "end": 1902},
    {"name": "Erster Weltkrieg (US)", "start": 1917, "end": 1918},
    {"name": "Zweiter Weltkrieg (US)", "start": 1941, "end": 1945},
    {"name": "Koreakrieg", "start": 1950, "end": 1953},
    {"name": "Vietnamkrieg", "start": 1965, "end": 1975},
    {"name": "Golfkrieg", "start": 1990, "end": 1991},
    {"name": "Krieg in Afghanistan", "start": 2001, "end": 2021},
    {"name": "Irakkrieg", "start": 2003, "end": 2011},
]


def get_war_years():
    """Alle Jahre in denen die USA in mindestens einem Krieg waren."""
    war_years = set()
    for war in US_WARS:
        for y in range(war["start"], war["end"] + 1):
            war_years.add(y)
    return war_years


def get_peace_years(all_years):
    """Alle Jahre in denen die USA NICHT im Krieg waren."""
    war_years = get_war_years()
    return [y for y in all_years if y not in war_years]


# ══════════════════════════════════════════════════════════════
# CHART
# ══════════════════════════════════════════════════════════════

def build_seasonal_chart(year_data, avg, std, ticker, smoothing_window,
                          show_individual, show_bands, show_current_year,
                          selected_range, selected_cycles=None, selected_decades=None,
                          indicator_years=None, indicator_label=None, indicator_color=None,
                          pressure_curve=None, war_years_data=None, war_label=None):
    """Erstelle den interaktiven Plotly Seasonal Chart."""
    
    fig = go.Figure()
    
    # Monatslabels für X-Achse
    month_names = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                   "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    month_starts = []
    for m in range(1, 13):
        day = datetime(2024, m, 1).timetuple().tm_yday
        month_starts.append(day)
    
    x_days = list(range(1, 366))
    
    # ── Zeitraummarkierung ────────────────────────────
    if selected_range:
        fig.add_vrect(
            x0=selected_range[0], x1=selected_range[1],
            fillcolor="rgba(255,255,255,0.05)",
            line_width=0,
            annotation_text="",
        )
        fig.add_vline(x=selected_range[0], line_dash="dash", 
                      line_color="rgba(255,255,255,0.3)", line_width=1)
        fig.add_vline(x=selected_range[1], line_dash="dash",
                      line_color="rgba(255,255,255,0.3)", line_width=1)
    
    # ── Einzelne Jahre (grau, transparent) ────────────
    if show_individual:
        for year, yd in year_data.items():
            fig.add_trace(go.Scatter(
                x=x_days,
                y=yd["full_365"],
                mode="lines",
                line=dict(color=COLOR_INDIVIDUAL, width=0.8),
                name=str(year),
                showlegend=False,
                hoverinfo="skip"
            ))
    
    # ── Confidence Bands (±1 Std.Abw.) ────────────────
    if show_bands and std:
        upper = [avg[i] + std[i] for i in range(365)]
        lower = [avg[i] - std[i] for i in range(365)]
        
        fig.add_trace(go.Scatter(
            x=x_days, y=upper,
            mode="lines", line=dict(width=0),
            showlegend=False, hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=x_days, y=lower,
            mode="lines", line=dict(width=0),
            fill="tonexty",
            fillcolor=COLOR_CONFIDENCE,
            name="±1σ Band",
            showlegend=True,
            hoverinfo="skip"
        ))
    
    # ── Präsidentenzyklus-Linien ──────────────────────
    if selected_cycles:
        for cycle_type in selected_cycles:
            matching_years = [y for y in year_data.keys()
                            if get_presidential_cycle_year(y) == cycle_type]
            
            if not matching_years:
                continue
            
            cycle_curves = [year_data[y]["full_365"] for y in matching_years]
            cycle_avg = [np.mean([c[d] for c in cycle_curves]) for d in range(365)]
            
            # Glätten
            if smoothing_window > 1:
                cycle_avg = pd.Series(cycle_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=cycle_avg,
                mode="lines",
                line=dict(color=CYCLE_COLORS[cycle_type], width=2, dash="dash"),
                name=f"{cycle_type} ({len(matching_years)}y)",
            ))
    
    # ── Dekadenzyklus-Linien ──────────────────────────
    if selected_decades:
        for digit in selected_decades:
            matching_years = [y for y in year_data.keys()
                            if get_decade_digit(y) == digit]
            
            if not matching_years:
                continue
            
            decade_curves = [year_data[y]["full_365"] for y in matching_years]
            decade_avg = [np.mean([c[d] for c in decade_curves]) for d in range(365)]
            
            # Glätten
            if smoothing_window > 1:
                decade_avg = pd.Series(decade_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=decade_avg,
                mode="lines",
                line=dict(color=DECADE_COLORS[digit], width=2, dash="dot"),
                name=f"X{digit}er Jahre ({len(matching_years)}y)",
            ))
    
    # ── Indikator-Linie (December Low / Januar) ───────
    if indicator_years and indicator_label and indicator_color:
        indicator_matching = [y for y in year_data.keys() if y in indicator_years]
        
        if len(indicator_matching) >= 2:
            ind_curves = [year_data[y]["full_365"] for y in indicator_matching]
            ind_avg = [np.mean([c[d] for c in ind_curves]) for d in range(365)]
            
            if smoothing_window > 1:
                ind_avg = pd.Series(ind_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=ind_avg,
                mode="lines",
                line=dict(color=indicator_color, width=2.5, dash="dashdot"),
                name=f"{indicator_label} ({len(indicator_matching)}y)",
                hovertemplate=f"{indicator_label}<br>Tag %{{x}}<br>Wert: %{{y:.2f}}<extra></extra>"
            ))
    
    # ── Saisonaler Durchschnitt (Hauptlinie) ──────────
    if avg:
        avg_display = avg.copy()
        
        if smoothing_window > 1:
            avg_display = pd.Series(avg_display).rolling(
                smoothing_window, center=True, min_periods=1
            ).mean().tolist()
        
        fig.add_trace(go.Scatter(
            x=x_days, y=avg_display,
            mode="lines",
            line=dict(color=COLOR_SEASONAL_AVG, width=3.5),
            name=f"Saisonaler Ø ({len(year_data)} Jahre)",
            hovertemplate="Tag %{x}<br>Wert: %{y:.2f}<extra></extra>"
        ))
    
    # ── War-Verlauf (Durchschnitt Kriegsjahre) ────────
    if war_years_data and war_label:
        war_matching = [y for y in year_data.keys() if y in war_years_data]
        
        if len(war_matching) >= 2:
            war_curves = [year_data[y]["full_365"] for y in war_matching]
            war_avg = [np.mean([c[d] for c in war_curves]) for d in range(365)]
            
            if smoothing_window > 1:
                war_avg = pd.Series(war_avg).rolling(
                    smoothing_window, center=True, min_periods=1
                ).mean().tolist()
            
            fig.add_trace(go.Scatter(
                x=x_days, y=war_avg,
                mode="lines",
                line=dict(color=COLOR_WAR, width=2.5, dash="dash"),
                name=f"{war_label} ({len(war_matching)}y)",
                hovertemplate=f"{war_label}<br>Tag %{{x}}<br>Wert: %{{y:.2f}}<extra></extra>"
            ))
    
    # ── Aktuelles Jahr (hervorgehoben) ────────────────
    # Wichtig: Das aktuelle Jahr wird IMMER aus den Rohdaten gebaut,
    # auch wenn es nicht in year_data ist (z.B. weil < 20 Handelstage)
    if show_current_year:
        current_year = datetime.now().year
        if current_year in year_data:
            yd = year_data[current_year]
            today_doy = datetime.now().timetuple().tm_yday
            display_days = [d for d in yd["days"] if d <= today_doy]
            display_vals = yd["cumulative"][:len(display_days)]
            
            if display_days:
                fig.add_trace(go.Scatter(
                    x=display_days, y=display_vals,
                    mode="lines",
                    line=dict(color=COLOR_CURRENT_YEAR, width=2.5),
                    name=f"{current_year} (aktuell)",
                    hovertemplate=f"{current_year}<br>Tag %{{x}}<br>Wert: %{{y:.2f}}<extra></extra>"
                ))
    
    # ── Layout ────────────────────────────────────────
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=550,
        margin=dict(t=40, r=20, b=50, l=60),
        title=dict(
            text=f"{ticker} — Saisonalität ({len(year_data)} Jahre)",
            font=dict(size=18, color="#e0e0e0")
        ),
        xaxis=dict(
            tickmode="array",
            tickvals=month_starts,
            ticktext=month_names,
            gridcolor="rgba(255,255,255,0.06)",
            range=[1, 365]
        ),
        yaxis=dict(
            title="Normalisierte Rendite (Start = 100)",
            gridcolor="rgba(255,255,255,0.06)",
            tickformat=".1f"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        hovermode="x unified"
    )
    
    # Y-Achse dynamisch anpassen — berücksichtigt ALLE sichtbaren Traces
    all_y_values = []
    
    # Saisonaler Durchschnitt
    if avg:
        all_y_values.extend(avg)
    
    # Konfidenzband
    if show_bands and std and avg:
        all_y_values.extend([avg[i] + std[i] for i in range(365)])
        all_y_values.extend([avg[i] - std[i] for i in range(365)])
    
    # Einzelne Jahre
    if show_individual:
        for yd in year_data.values():
            all_y_values.extend(yd["full_365"])
    
    # Aktuelles Jahr
    if show_current_year:
        current_year = datetime.now().year
        if current_year in year_data:
            all_y_values.extend(year_data[current_year]["cumulative"])
    
    # Präsidentenzyklus-Linien
    if selected_cycles:
        for cycle_type in selected_cycles:
            matching = [y for y in year_data.keys()
                       if get_presidential_cycle_year(y) == cycle_type]
            if matching:
                curves = [year_data[y]["full_365"] for y in matching]
                cycle_avg = [np.mean([c[d] for c in curves]) for d in range(365)]
                all_y_values.extend(cycle_avg)
    
    # Dekadenzyklus-Linien
    if selected_decades:
        for digit in selected_decades:
            matching = [y for y in year_data.keys()
                       if get_decade_digit(y) == digit]
            if matching:
                curves = [year_data[y]["full_365"] for y in matching]
                decade_avg = [np.mean([c[d] for c in curves]) for d in range(365)]
                all_y_values.extend(decade_avg)
    
    # Indikator-Linie
    if indicator_years and indicator_label:
        ind_matching = [y for y in year_data.keys() if y in indicator_years]
        if len(ind_matching) >= 2:
            ind_curves = [year_data[y]["full_365"] for y in ind_matching]
            ind_avg = [np.mean([c[d] for c in ind_curves]) for d in range(365)]
            all_y_values.extend(ind_avg)
    
    if all_y_values:
        y_min = min(all_y_values) - 2
        y_max = max(all_y_values) + 2
        fig.update_yaxes(range=[y_min, y_max])
    
    return fig


# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════

def main():
    # ── Sidebar ───────────────────────────────────────
    with st.sidebar:
        st.markdown("## 📈 SeasonalEdge")
        st.markdown("---")
        
        # Ticker-Eingabe
        ticker = st.text_input("Ticker", value=DEFAULT_TICKER).upper().strip()
        
        # Zeitraum — letzte Option ist "Max"
        period_options = [3, 5, 7, 10, 15, 20, 25, 30, "Max"]
        years_back_raw = st.select_slider(
            "Analyse-Zeitraum (Jahre)",
            options=period_options,
            value=DEFAULT_YEARS,
            format_func=lambda x: str(x)
        )
        # "Max" wird später aufgelöst wenn wir die Daten kennen
        years_back_is_max = (years_back_raw == "Max")
        
        st.markdown("---")
        st.markdown("### Chart-Optionen")
        
        smoothing = st.slider("Glättung (Tage)", 1, 21, 5, 2,
                             help="Moving Average für die Durchschnittslinie")
        
        show_individual = st.checkbox("Einzelne Jahre anzeigen", value=False)
        show_bands = st.checkbox("Konfidenzband (±1σ)", value=True)
        show_current = st.checkbox("Aktuelles Jahr hervorheben", value=True)
        
        st.markdown("---")
        st.markdown("### Präsidentenzyklus")
        
        cycle_options = list(CYCLE_COLORS.keys())
        selected_cycles = st.multiselect(
            "Zyklen anzeigen",
            options=cycle_options,
            default=None,
            help="Leere Auswahl = keine Zykluslinien"
        )
        
        st.markdown("---")
        st.markdown("### Dekadenzyklus")
        
        current_digit = get_decade_digit(datetime.now().year)
        selected_decades = st.multiselect(
            "Endziffer anzeigen",
            options=list(range(10)),
            format_func=lambda x: f"X{x}er Jahre" + (" ← aktuell" if x == current_digit else ""),
            default=None,
            help="Durchschnitt aller Jahre mit gleicher Endziffer (z.B. X5er = 1905, 1915, ...2025)"
        )
        
        st.markdown("---")
        st.markdown("### Pressure Chart")
        show_pressure = st.checkbox("Pressure im Hauptchart", value=False,
                                    help="Addiert die Ø-Tagesrenditen der letzten 10, 20, 30, 40, 60, 80 Jahre")
        
        st.markdown("---")
        st.markdown("### War-Verlauf")
        war_mode = st.selectbox(
            "US-Kriegsjahre",
            ["Aus", "Kriegsjahre (Ø Verlauf)", "Friedensjahre (Ø Verlauf)", "Beide"],
            help="Durchschnittlicher saisonaler Verlauf in Jahren mit/ohne US-Kriegsbeteiligung"
        )
        
        st.markdown("---")
        st.markdown("### Saisonale Indikatoren")
        
        # December Low Indikator
        dec_low_mode = st.selectbox(
            "December Low Indikator",
            ["Aus", "Dez-Tief NICHT unterschritten (bullish)", "Dez-Tief unterschritten (bearish)"],
            help="Filtert Jahre danach, ob das Dezember-Tief des Vorjahres im Q1 (Jan-Mär) unterschritten wurde"
        )
        
        # Januar Indikator
        jan_indicator_mode = st.selectbox(
            "Januar Indikator (First 5 Days)",
            ["Aus", "Erste 5 Tage POSITIV (bullish)", "Erste 5 Tage NEGATIV (bearish)"],
            help="Filtert Jahre danach, ob die ersten 5 Handelstage im Januar positiv oder negativ waren"
        )
        
        st.markdown("---")
        st.markdown("### Zeitraum-Analyse")
        
        # Preset-Buttons
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("Jan-Effekt", use_container_width=True):
                st.session_state.range_start = 1
                st.session_state.range_end = 31
            if st.button("Sell in May", use_container_width=True):
                st.session_state.range_start = 121
                st.session_state.range_end = 274
        with col_p2:
            if st.button("Fall Rally", use_container_width=True):
                st.session_state.range_start = 274
                st.session_state.range_end = 334
            if st.button("Santa Rally", use_container_width=True):
                st.session_state.range_start = 335
                st.session_state.range_end = 365
        
        range_start = st.number_input(
            "Von (Tag des Jahres)", 1, 365,
            value=st.session_state.get("range_start", 1)
        )
        range_end = st.number_input(
            "Bis (Tag des Jahres)", 1, 365,
            value=st.session_state.get("range_end", 365)
        )
    
    # ── Daten laden ───────────────────────────────────
    with st.spinner(f"Lade {ticker} Daten..."):
        raw_df = download_data(ticker)
    
    if raw_df is None or raw_df.empty:
        st.error(f"Keine Daten für '{ticker}' gefunden. Prüfe den Ticker.")
        return
    
    df = preprocess(raw_df)
    
    # Jahre filtern — "Max" nutzt alle verfügbaren Jahre
    all_years = sorted(df["year"].unique())
    
    if years_back_is_max:
        years_back = datetime.now().year - min(all_years)
        selected_years = all_years
    else:
        years_back = int(years_back_raw)
        cutoff_year = datetime.now().year - years_back
        selected_years = [y for y in all_years if y >= cutoff_year]
    
    # Aktuelles Jahr IMMER einschließen (für "Aktuelles Jahr hervorheben")
    current_year = datetime.now().year
    if current_year in all_years and current_year not in selected_years:
        selected_years.append(current_year)
        selected_years.sort()
    
    if len(selected_years) < 2:
        st.warning("Nicht genügend Daten für den gewählten Zeitraum.")
        return
    
    # ── Berechnung ────────────────────────────────────
    year_data = build_year_data(df, selected_years)
    avg, std = calculate_seasonal_average(year_data)
    
    # ── Indikatoren berechnen ─────────────────────────
    indicator_years = None
    indicator_label = None
    indicator_color = None
    
    # December Low Indikator
    if dec_low_mode != "Aus":
        dec_classification = classify_december_low(df)
        if "NICHT" in dec_low_mode:
            # Bullish: Dez-Tief wurde NICHT unterschritten
            indicator_years = [y for y, bullish in dec_classification.items() 
                             if bullish and y in year_data]
            indicator_label = "Dez-Low gehalten"
            indicator_color = "#4CAF50"  # Grün
        else:
            # Bearish: Dez-Tief wurde unterschritten
            indicator_years = [y for y, bullish in dec_classification.items() 
                             if not bullish and y in year_data]
            indicator_label = "Dez-Low gebrochen"
            indicator_color = "#F44336"  # Rot
    
    # Januar Indikator (überschreibt December Low falls beide aktiv)
    if jan_indicator_mode != "Aus":
        jan_classification = classify_january_first5(df)
        if "POSITIV" in jan_indicator_mode:
            indicator_years = [y for y, positive in jan_classification.items() 
                             if positive and y in year_data]
            indicator_label = "Jan First 5 ↑"
            indicator_color = "#4CAF50"
        else:
            indicator_years = [y for y, positive in jan_classification.items() 
                             if not positive and y in year_data]
            indicator_label = "Jan First 5 ↓"
            indicator_color = "#F44336"
    
    # ── Pressure berechnen ────────────────────────────
    pressure_curve_data = None
    pressure_info = None
    if show_pressure:
        pressure_curve_data, max_years, avail_periods = calculate_pressure_curve(
            df, smoothing_window=smoothing
        )
        unavailable = [p for p in PRESSURE_PERIODS if p > max_years]
        if unavailable and avail_periods:
            pressure_info = (
                f"⚠️ Pressure Chart nur über die letzten **{max(avail_periods)} Jahre** verfügbar "
                f"(Datenreihe: {max_years} Jahre). "
                f"Perioden {', '.join(str(p) for p in unavailable)} Jahre nicht darstellbar."
            )
    
    # ── War-Verlauf berechnen ─────────────────────────
    war_years_data = None
    war_label = None
    peace_years_data = None
    peace_label = None
    
    if war_mode != "Aus":
        all_war_years = get_war_years()
        all_peace_years = set(get_peace_years(list(year_data.keys())))
        
        if war_mode in ["Kriegsjahre (Ø Verlauf)", "Beide"]:
            war_years_data = [y for y in year_data.keys() if y in all_war_years]
            war_label = "Kriegsjahre"
        
        if war_mode in ["Friedensjahre (Ø Verlauf)", "Beide"]:
            peace_years_data = [y for y in year_data.keys() if y in all_peace_years]
            peace_label = "Friedensjahre"
    
    # ── Chart ─────────────────────────────────────────
    selected_range = (range_start, range_end) if range_start < range_end else None
    
    fig = build_seasonal_chart(
        year_data=year_data,
        avg=avg,
        std=std,
        ticker=ticker,
        smoothing_window=smoothing,
        show_individual=show_individual,
        show_bands=show_bands,
        show_current_year=show_current,
        selected_range=selected_range,
        selected_cycles=selected_cycles if selected_cycles else None,
        selected_decades=selected_decades if selected_decades else None,
        indicator_years=indicator_years,
        indicator_label=indicator_label,
        indicator_color=indicator_color,
        pressure_curve=pressure_curve_data,
        war_years_data=war_years_data,
        war_label=war_label
    )
    
    # Friedensjahre als zweite Linie (wenn "Beide")
    if peace_years_data and peace_label:
        peace_matching = [y for y in year_data.keys() if y in peace_years_data]
        if len(peace_matching) >= 2:
            x_days = list(range(1, 366))
            peace_curves = [year_data[y]["full_365"] for y in peace_matching]
            peace_avg = [np.mean([c[d] for c in peace_curves]) for d in range(365)]
            if smoothing > 1:
                peace_avg = pd.Series(peace_avg).rolling(
                    smoothing, center=True, min_periods=1
                ).mean().tolist()
            fig.add_trace(go.Scatter(
                x=x_days, y=peace_avg,
                mode="lines",
                line=dict(color="#4CAF50", width=2.5, dash="dash"),
                name=f"{peace_label} ({len(peace_matching)}y)",
                hovertemplate=f"{peace_label}<br>Tag %{{x}}<br>Wert: %{{y:.2f}}<extra></extra>"
            ))
    
    # Pressure als sekundäre Y-Achse im Hauptchart
    if pressure_curve_data:
        x_days = list(range(1, 366))
        fig.add_trace(go.Scatter(
            x=x_days, y=pressure_curve_data,
            mode="lines",
            line=dict(color=COLOR_PRESSURE, width=2),
            name="Pressure",
            yaxis="y2",
            hovertemplate="Pressure: %{y:+.2f}<extra></extra>"
        ))
        fig.update_layout(
            yaxis2=dict(
                title="Pressure",
                titlefont=dict(color=COLOR_PRESSURE, size=11),
                tickfont=dict(color=COLOR_PRESSURE, size=10),
                overlaying="y",
                side="right",
                showgrid=False,
                tickformat="+.1f",
                zeroline=True,
                zerolinecolor="rgba(255,105,180,0.2)"
            )
        )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Pressure Hinweis
    if pressure_info:
        st.info(pressure_info)
    
    # ── Statistik-Box für gewählten Zeitraum ──────────
    if selected_range:
        stats = calculate_period_stats(year_data, range_start, range_end)
        td = count_trading_days(year_data, range_start, range_end)
        
        if stats:
            # Monatsnamen für die Anzeige
            from calendar import month_abbr
            start_month = datetime.strptime(str(range_start), "%j").strftime("%d. %b")
            end_month = datetime.strptime(str(min(range_end, 365)), "%j").strftime("%d. %b")
            
            st.markdown(f"### 📊 Zeitraum: {start_month} – {end_month} ({range_end - range_start} Kalendertage, ~{td} Handelstage)")
            
            c1, c2, c3, c4, c5 = st.columns(5)
            
            with c1:
                st.metric("Win Rate", f"{stats['win_rate']:.1f}%")
            with c2:
                st.metric("Ø Rendite", f"{stats['avg_return']:+.2f}%")
            with c3:
                st.metric("Median", f"{stats['median_return']:+.2f}%")
            with c4:
                st.metric("Max Gewinn", f"{stats['max_gain']:+.2f}%")
            with c5:
                st.metric("Max Verlust", f"{stats['max_loss']:+.2f}%")
            
            st.caption(
                f"Basierend auf {stats['total_years']} Jahren · "
                f"{stats['winning_years']} Gewinner / {stats['losing_years']} Verlierer · "
                f"Std.Abw: {stats['std_dev']:.2f}%"
            )
    
    # ── Dateninfo ─────────────────────────────────────
    with st.expander("ℹ️ Dateninfo"):
        period_label = "Max" if years_back_is_max else f"{years_back}"
        st.markdown(f"""
        **Ticker:** {ticker}  
        **Datenzeitraum:** {df.index[0].strftime('%d.%m.%Y')} – {df.index[-1].strftime('%d.%m.%Y')}  
        **Analyse-Zeitraum:** {period_label} ({min(selected_years)} – {max(selected_years)}, {len(year_data)} Jahre verwendet)  
        **Methode:** Kumulative Log-Returns (jedes Jahr startet bei 100, mathematisch korrekt summierbar)  
        **Glättung:** {smoothing}-Tage zentrierter Moving Average  
        """)
        
        current_year = datetime.now().year
        cycle = get_presidential_cycle_year(current_year)
        st.markdown(f"**Aktueller Präsidentenzyklus:** {current_year} = {cycle}")
        
        if indicator_years and indicator_label:
            st.markdown(f"**Aktiver Indikator:** {indicator_label} — {len(indicator_years)} Jahre matchen")


# ══════════════════════════════════════════════════════════════
# START
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
