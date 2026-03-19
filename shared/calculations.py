"""
SeasonalEdge - Berechnungen
============================
Saisonale Analyse, Pressure Chart, Indikatoren, Kriege, ToM.
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
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from shared.constants import (
    PRESSURE_PERIODS, US_WARS, MONTH_NAMES_DE,
    CYCLE_COLORS, DECADE_COLORS
)


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
    """
    log_returns = year_df["log_return"].values
    cum_log = np.cumsum(log_returns)
    cum_log = np.insert(cum_log[:-1], 0, 0) if len(log_returns) > 0 else np.array([0])
    cumulative = (100 * np.exp(np.cumsum(np.insert(log_returns, 0, 0)[:-1]))).tolist()
    
    if len(cumulative) < len(year_df):
        cumulative.append(100 * np.exp(np.sum(log_returns)))
    elif len(cumulative) > len(year_df):
        cumulative = cumulative[:len(year_df)]
    
    return cumulative


def interpolate_to_365(days, values):
    """Interpoliere auf volle 365 Kalendertage."""
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
    """Baue normalisierte Jahreskurven für alle gewählten Jahre."""
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
    """Berechne den saisonalen Durchschnitt über alle Jahre."""
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

def calculate_pressure_curve(df, smoothing_window=5):
    """
    Pressure Chart: Addition der Ø-Tagesrenditen verschiedener Lookback-Perioden.
    """
    current_year = datetime.now().year
    all_years = sorted(df["year"].unique())
    max_years_available = current_year - min(all_years)
    
    available_periods = [p for p in PRESSURE_PERIODS if p <= max_years_available]
    
    if not available_periods:
        return None, 0, []
    
    period_daily_avgs = {}
    
    for period in available_periods:
        cutoff_year = current_year - period
        period_years = [y for y in all_years if y >= cutoff_year and y < current_year]
        
        if len(period_years) < 2:
            continue
        
        year_daily_returns = []
        for year in period_years:
            year_df = df[df["year"] == year].copy()
            if len(year_df) < 20:
                continue
            
            days = year_df["day_of_year"].tolist()
            log_rets = year_df["log_return"].values.tolist()
            
            full_rets = []
            for target_day in range(1, 366):
                if target_day in days:
                    idx = days.index(target_day)
                    full_rets.append(log_rets[idx])
                else:
                    full_rets.append(0.0)
            
            year_daily_returns.append(full_rets)
        
        if not year_daily_returns:
            continue
        
        avg_daily = [np.mean([yr[d] for yr in year_daily_returns]) * 100
                     for d in range(365)]
        period_daily_avgs[period] = avg_daily
    
    if not period_daily_avgs:
        return None, max_years_available, []
    
    summed_daily = [0.0] * 365
    for period, avg_daily in period_daily_avgs.items():
        for d in range(365):
            summed_daily[d] += avg_daily[d]
    
    pressure_curve = np.cumsum(summed_daily).tolist()
    
    if smoothing_window > 1:
        pressure_curve = pd.Series(pressure_curve).rolling(
            smoothing_window, center=True, min_periods=1
        ).mean().tolist()
    
    return pressure_curve, max_years_available, list(period_daily_avgs.keys())


# ══════════════════════════════════════════════════════════════
# SAISONALE INDIKATOREN
# ══════════════════════════════════════════════════════════════

def classify_december_low(df):
    """December Low Indikator: Dez-Tief des Vorjahres im Q1 unterschritten?"""
    years = sorted(df["year"].unique())
    classification = {}
    
    for year in years:
        prev_year = year - 1
        dec_prev = df[(df["year"] == prev_year) & (df["month"] == 12)]
        if len(dec_prev) == 0:
            continue
        
        dec_low = dec_prev["Low"].min() if "Low" in df.columns else dec_prev["Close"].min()
        
        q1 = df[(df["year"] == year) & (df["month"].isin([1, 2, 3]))]
        if len(q1) == 0:
            continue
        
        q1_low = q1["Low"].min() if "Low" in df.columns else q1["Close"].min()
        classification[year] = q1_low >= dec_low
    
    return classification


def classify_january_first5(df):
    """Januar Indikator: Erste 5 Handelstage positiv oder negativ?"""
    years = sorted(df["year"].unique())
    classification = {}
    
    for year in years:
        prev_year = year - 1
        prev_year_data = df[df["year"] == prev_year]
        if len(prev_year_data) == 0:
            continue
        
        last_close_prev = prev_year_data["Close"].iloc[-1]
        
        jan_data = df[(df["year"] == year) & (df["month"] == 1)]
        if len(jan_data) < 5:
            continue
        
        close_day5 = jan_data["Close"].iloc[4]
        classification[year] = close_day5 > last_close_prev
    
    return classification


# ══════════════════════════════════════════════════════════════
# KRIEG / FRIEDEN
# ══════════════════════════════════════════════════════════════

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
# TURN OF THE MONTH (ToM) ANALYSE
# ══════════════════════════════════════════════════════════════

def analyze_turn_of_month(df, days_before, days_after, selected_months, selected_years):
    """
    Turn-of-the-Month: t0 = letzter Handelstag des Monats → 0% normiert.
    """
    window_size = days_before + 1 + days_after
    t0_idx = days_before
    all_curves = []
    
    for year in selected_years:
        for month in selected_months:
            try:
                month_data = df[(df["year"] == year) & (df["month"] == month)].copy()
                
                if len(month_data) < days_before + 1:
                    continue
                
                pre_window = month_data.iloc[-(days_before + 1):]
                
                next_month = month + 1 if month < 12 else 1
                next_year = year if month < 12 else year + 1
                
                next_month_data = df[(df["year"] == next_year) & (df["month"] == next_month)].copy()
                
                if len(next_month_data) < days_after:
                    continue
                
                post_window = next_month_data.iloc[:days_after]
                
                tom_window = pd.concat([pre_window, post_window])
                
                if len(tom_window) != window_size:
                    continue
                
                log_rets = tom_window["log_return"].values
                cum_log = np.cumsum(np.insert(log_rets, 0, 0)[:-1])
                raw_curve = 100 * np.exp(cum_log)
                
                t0_value = raw_curve[t0_idx]
                curve = ((raw_curve / t0_value - 1) * 100).tolist()
                
                total_return = curve[-1] - curve[0]
                
                all_curves.append({
                    "year": year,
                    "month": month,
                    "curve": curve,
                    "total_return": total_return
                })
                
            except Exception:
                continue
    
    if not all_curves:
        return None
    
    avg_curve = []
    for i in range(window_size):
        day_values = [c["curve"][i] for c in all_curves]
        avg_curve.append(np.mean(day_values))
    
    labels = []
    for i in range(window_size):
        offset = i - days_before
        if offset < 0:
            labels.append(f"t{offset}")
        elif offset == 0:
            labels.append("t0")
        else:
            labels.append(f"t+{offset}")
    
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


def build_tom_chart(tom_result, ticker, days_before, days_after, selected_months,
                    show_individual_tom=False):
    """Erstelle den Turn-of-the-Month Chart (t0 = 0%)."""
    
    fig = go.Figure()
    
    labels = tom_result["labels"]
    avg_curve = tom_result["avg_curve"]
    x_indices = list(range(len(labels)))
    
    if show_individual_tom:
        for entry in tom_result["all_curves"]:
            fig.add_trace(go.Scatter(
                x=x_indices, y=entry["curve"],
                mode="lines",
                line=dict(color="rgba(150,150,150,0.15)", width=0.7),
                showlegend=False, hoverinfo="skip"
            ))
    
    t0_idx = days_before
    fig.add_vline(
        x=t0_idx, line_dash="dash",
        line_color="rgba(255,215,0,0.5)", line_width=1.5,
        annotation_text="t0 (letzter HT)",
        annotation_position="top",
        annotation_font=dict(size=10, color="#FFD700")
    )
    
    fig.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)", line_width=1)
    
    fig.add_trace(go.Scatter(
        x=x_indices, y=avg_curve,
        mode="lines+markers",
        line=dict(color="#00CED1", width=3),
        marker=dict(size=6, color="#00CED1"),
        fill="tozeroy", fillcolor="rgba(0,206,209,0.1)",
        name=f"Ø ToM ({tom_result['stats']['total_windows']} Fenster)",
        hovertemplate="%{text}<br>%{y:+.3f}%<extra></extra>",
        text=labels
    ))
    
    if len(selected_months) <= 3:
        month_str = ", ".join([MONTH_NAMES_DE[m - 1] for m in selected_months])
    elif len(selected_months) == 12:
        month_str = "Alle Monate"
    else:
        month_str = f"{len(selected_months)} Monate"
    
    from shared.charts import apply_se_theme
    fig = apply_se_theme(
        fig,
        title=f"{ticker} — Turn of the Month (t-{days_before} bis t+{days_after}) · {month_str}",
        height=420,
    )
    fig.update_xaxes(tickmode="array", tickvals=x_indices, ticktext=labels, title="Handelstage relativ zum Monatswechsel")
    fig.update_yaxes(title="Rendite relativ zu t0 (%)", tickformat="+.2f", ticksuffix="%")
    
    return fig
